# CES Supervisor Server

A dedicated place for the code that runs on the CES Supervisor Server.

The server hosts all of the EMR data, which is uploaded to it monthly.
It can launch EMRs for any of the sites for which there is data.

The user-facing part of this is `manage_emr.py`.

To use `manage_emr.py`, you will need to create a file `.env` in the same
directory, which has just the line

```
PASSWORD=<password>
```

Where `<password>` is the password for the data archives and the mysql
databases.

You'll also need to install dotenv. `pip3 install python-dotenv`.
