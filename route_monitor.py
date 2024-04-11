"""
Copyright (c) 2023 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

import json
from syslog import LOG_ERR, syslog
from typing import Optional

from cisco.vrf import *
from cli import clid

LOCAL_FILE = "/bootflash/py_route_monitor.json"
VRF = "default"


def get_routes() -> dict:
    """
    Query route table
    """
    print("Querying route table...")
    routes = json.loads(clid(f"show ip route vrf {VRF}"))
    prefixes = routes["TABLE_vrf"]["ROW_vrf"]["TABLE_addrf"]["ROW_addrf"][
        "TABLE_prefix"
    ]["ROW_prefix"]
    prefix_list = []
    if isinstance(prefixes, list):
        for prefix in prefixes:
            # Skip connected / interface routes
            # if prefix["attached"] == "true":
            #    continue
            route = prefix["ipprefix"]
            # Check if multiple next-hops
            if isinstance(prefix["TABLE_path"]["ROW_path"], list):
                for nexthop in prefix["TABLE_path"]["ROW_path"]:
                    prefix_list.append(
                        {
                            route: {
                                "nexthop": nexthop["ipnexthop"],
                                "proto": nexthop["clientname"],
                            }
                        }
                    )
            else:
                prefix_list.append(
                    {
                        route: {
                            "nexthop": prefix["TABLE_path"]["ROW_path"]["ipnexthop"],
                            "proto": prefix["TABLE_path"]["ROW_path"]["clientname"],
                        }
                    }
                )
    elif isinstance(prefixes, dict):
        # Check if multiple next-hops
        if isinstance(prefixes["TABLE_path"]["ROW_path"], list):
            for nexthop in prefixes["TABLE_path"]["ROW_path"]:
                prefix_list.append(
                    {
                        prefixes["ipprefix"]: {
                            "nexthop": nexthop["ipnexthop"],
                            "proto": nexthop["clientname"],
                        }
                    }
                )
        else:
            prefix_list.append(
                {
                    prefixes["ipprefix"]: {
                        "nexthop": prefixes["TABLE_path"]["ROW_path"]["ipnexthop"],
                        "proto": prefixes["TABLE_path"]["ROW_path"]["clientname"],
                    }
                }
            )
    print(f"Done. Collected {len(prefix_list)} routes from routing table.")
    return prefix_list


def write_route_file(routes: dict) -> None:
    """
    Write route list to file
    """
    print(f"Storing current routing table state in file: {LOCAL_FILE}")
    with open(LOCAL_FILE, "w") as file:
        file.write(json.dumps(routes))
    print("Done. Route file saved.")


def read_route_file() -> Optional[dict]:
    """
    Read in local file of routes
    """
    print(f"Attempting to read last state of routing table from file: {LOCAL_FILE}")
    try:
        with open(LOCAL_FILE, "r") as file:
            print("Done.")
            return json.load(file)
    except FileNotFoundError:
        print(
            "No previous state was stored. Assuming script is new & file will be created after first run."
        )
        return None


def compare_routes(last: dict, current: dict) -> dict:
    """
    Compare routing tables
    """
    print("Beginning route table comparison...")
    results = {}
    results["removed"] = []
    results["added"] = []
    results["changed"] = []
    # If equal, return early
    if current == last:
        print("Done. No changes in routing table detected.")
        return results
    # Check added routes
    for route in last:
        if route not in current:
            print(f"Found removed route: {route}")
            results["removed"].append(route)
    # Check new routes
    for route in current:
        if route not in last:
            print(f"Found added route: {route}")
            results["added"].append(route)
    print("Finished collecting routing table changes.")
    print(f"{len(results['removed'])} removed, and {len(results['added'])} added.")
    return results


def send_syslog(diff: dict) -> None:
    """
    Send alert on any changed routes
    """
    print("Sending syslog messages to notify route changes...")
    for route in diff["removed"]:
        prefix = list(route.keys())[0]
        syslog(
            LOG_ERR,
            f"ROUTE REMOVED - PREFIX: {prefix}, NEXT HOP: {route[prefix]['nexthop']}, PROTOCOL: {route[prefix]['proto']}",
        )
    for route in diff["added"]:
        prefix = list(route.keys())[0]
        syslog(
            LOG_ERR,
            f"ROUTE ADDED - PREFIX: {prefix}, NEXT HOP: {route[prefix]['nexthop']}, PROTOCOL: {route[prefix]['proto']}",
        )
    print("Done. Syslog messages sent.")


def run():
    print("Route monitor script started")
    # Query current routing table
    current_prefixes = get_routes()
    # Open last file & compare diffs
    previous_prefixes = read_route_file()
    if previous_prefixes:
        # Compare diff
        diff = compare_routes(previous_prefixes, current_prefixes)
        # Send syslog on any changes
        send_syslog(diff)
    # Write new routes file
    write_route_file(current_prefixes)
    print("Route monitor script finished")


if __name__ == "__main__":
    run()
