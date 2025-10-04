#!/usr/bin/env python3

import os
import json
from pgadmin.setup import db

# Path to the servers.json file
servers_json_path = "/pgadmin4/servers.json"

# Define the server configuration
server_config = {
    "Servers": {
        "1": {
            "Name": "Media Manager DB",
            "Group": "Servers",
            "Host": "postgres",
            "Port": 5432,
            "MaintenanceDB": "postgres",
            "Username": "youruser",
            "SSLMode": "prefer",
            "PassFile": "/pgadmin4/passfile"
        }
    }
}

# Create the passfile with the password
passfile_path = "/pgadmin4/passfile"
with open(passfile_path, "w") as f:
    f.write("postgres:5432:media_manager:youruser:yourpassword\n")

# Write the server configuration to servers.json
with open(servers_json_path, "w") as f:
    json.dump(server_config, f, indent=4)

print("Server configuration added to pgAdmin.")
