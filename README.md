# Cisco Nexus Route Monitor

The purpose of this script is to monitor the routing table on a Cisco Nexus switch & generate syslog messages on any changes.

This script will:

- Check routes on the Nexus routing table
- Store a local copy of the last-known table state
- Each subsequent run will compare the current table to the last known state
- If any differences, generate syslog messages

## Contacts

- Matt Schmitz (<mattsc@cisco.com>)

## Solution Components

- Cisco Nexus 9000v (NX-OS 10.3(1) with Python 3.7.10)

> Note: This code requires an NX-OS software release that is capable of using Python 3

## Installation/Configuration

### **Step 1 - Clone repo**

```bash
git clone https://github.com/gve-sw/gve_devnet_nxos_syslog_route_monitor
```

### **Step 2 - Copy script to Nexus**

Copy the `route_monitor.py` file to the remote Nexus device bootflash. This can be accomplished via the standard methods: TFTP, HTTP, FTP, SCP, etc

### **Step 3 - Ensure Syslog is configured**

The script relies on the Nexus configuration for syslog. Any messages sent via the script will be forwarded to the local Nexus syslog process. Therefore, if alerts need to be received by a remote syslog host, please ensure that one is configured on the switch.

Example:

```text
nx(config)# logging server 192.0.2.50
```

## Usage

### **Create Scheduled task**

Using the built-in Nexus task scheduler, we can allow the script to execute on regular intervals. This will define how frequently the routing table is compared & syslog alerts are generated.

First, enable the scheduler feature:

```text
nx(config)# feature scheduler
```

Then, create a job to run the script:

```text
nx(config)# scheduler job name route_monitor
nx(config-job)# python3 bootflash:/route_monitor.py
```

Finally, create a schedule to execute the script on the desired interval:

```text
nx(config)# scheduler schedule name check_routes
nx(config-schedule)# job name route_monitor
nx(config-schedule)# time start now repeat 0:0:5
```

For example, the above schedule begins immediately & executes the Python script every 5 minutes.

Upon any route changes, syslog messages will be generated like the example shown below:

```text
Nov 13 12:24:30 192.0.2.1 2023 Nov 13 17:23:27 UTC: %USER-3-SYSTEM_MSG: ROUTE REMOVED - PREFIX: 203.0.113.0/24, NEXT HOP: 192.0.2.8, PROTOCOL: bgp-65100 - /routemonitor.py
Nov 13 12:24:30 192.0.2.1 2023 Nov 13 17:23:27 UTC: %USER-3-SYSTEM_MSG: ROUTE ADDED - PREFIX: 203.0.113.0/24, NEXT HOP: 192.0.2.100, PROTOCOL: bgp-65100 - /routemonitor.py
```

## Troubleshooting

To check the configured tasks & see last execution status, use `show scheduler`:

```text
nx(config)# show scheduler schedule
Schedule Name       : check_routes
--------------------------
User Name           : admin
Schedule Type       : Run every 0 Days 0 Hrs 5 Mins
Start Time          : Mon Nov 13 16:53:45 2023
Last Execution Time : Mon Nov 13 17:39:45 2023
Last Completion Time: Mon Nov 13 17:39:46 2023
Execution count     : 47
-----------------------------------------------
     Job Name            Last Execution Status
-----------------------------------------------
route_monitor                      Success (0)
```

If the `Last Execution Status` above shows an error, check the script logs with `show scheduler logfile`. The below example demonstates a successful execution:

```text
nx(config)# show scheduler logfile
==============================================================================
Job Name       : route_monitor                      Job Status: Success (0)
Schedule Name  : check_routes                              User Name : admin
Completion time: Mon Nov 13 17:42:46 2023
--------------------------------- Job Output ---------------------------------

`python3 bootflash:/route_monitor.py`
stty: 'standard input': Inappropriate ioctl for device
Route monitor script started
Querying route table...
Done. Collected 5 routes from routing table.
Attempting to read last state of routing table from file: /bootflash/py_route_monitor.json
Done.
Beginning route table comparison...
Done. No changes in routing table detected.
Sending syslog messages to notify route changes...
Done. Syslog messages sent.
Storing current routing table state in file: /bootflash/py_route_monitor.json
Done. Route file saved.
Route monitor script finished
==============================================================================
```

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER

<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
