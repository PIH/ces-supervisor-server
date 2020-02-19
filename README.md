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

### Adding a site

Sites are added not using an SDK install, but by manually copying stuff.
See the script `~/pih-emr/make-site-dirs.sh` on the server itself.
The steps are as follows.

1. Pick a name. Letters, numbers, and underscores. We'll refer to it as `<name>`.
1. Copy an existing application data directory (e.g. `~/openmrs/capitan`
  to `~/openmrs/<name>`).
1. Create a new database `<name>` in the dockerized MySQL.
1. `GRANT ALL PRIVILEGES ON <name>.* TO 'openmrs'@'localhost';`
1. Import a database export into that database.
1. Run the following SQL, replacing `<name>` as appropriate: `UPDATE location_tag_map SET location_id = (SELECT location_id FROM location WHERE name LIKE "<name>") WHERE location_id = 3`
1. Update the server's port in `~/openmrs/<name>/openmrs-server.properties`
  by changing the values of `server.port` and `tomcat.port`. Choose the next
  available port after all the other servers. It should be
  `8000 + (number of preexisting servers)`.
1. Add the server to the `SITES` array in `manage_emr.py`.
