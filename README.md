# CES Supervisor Server

A dedicated place for the code that runs on the CES Supervisor Server.

The server hosts all of the EMR data, which is uploaded to it monthly.
It can launch EMRs for any of the sites for which there is data.

The user-facing part of this is `manage_emr.py`.

## Setup

To use `manage_emr.py`, you will need to create a file `.env` in the same
directory, which has just the line

```
PASSWORD=<password>
```

Where `<password>` is the password for the data archives and the mysql
databases.

You'll also need to install dotenv. `pip3 install python-dotenv`.

## Explanation

Each site has its own server out in the mountains. Each one also has a
corresponding OpenMRS SDK install on the CES Supervisor Server. Data is
exported from the real server and imported (using this tool) onto the 
Supervisor Server periodically. Users of the Supervisor Server can run 
any of the servers with the latest imported data, and view that data as
if in the real EMR.

All of the SDK servers use a single copy of openmrs-module-mirebalais and
openmrs-config-ces. The tool can update to the application to the latest
`master` of each.

Note that importing data also overwrites the existing users. Each time you
import new data, you will need to re-import users afterward.
