#!/usr/bin/env python3
import os
import json
import subprocess

# Path to the servers.json file in the container
SERVERS_JSON_PATH = "/pgadmin4/servers.json"

def main():
    # Ensure the servers.json file exists and is readable
    if not os.path.exists(SERVERS_JSON_PATH):
        print(f"Error: {SERVERS_JSON_PATH} not found.")
        return

    # Read the servers.json file
    with open(SERVERS_JSON_PATH, "r") as f:
        servers = json.load(f)

    # Print the servers for debugging (optional)
    print("Servers configured in pgAdmin:")
    for server_id, server in servers["Servers"].items():
        print(f"- {server['Name']} ({server['Host']}:{server['Port']})")

    # Optionally, you can add logic here to register the servers via pgAdmin's CLI or API
    # For example, using the pgAdmin CLI or Python's requests library to call the pgAdmin API

if __name__ == "__main__":
    main()
