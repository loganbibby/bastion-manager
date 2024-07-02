#!/usr/bin/env python3

import sys
import json
import time
from datetime import datetime
from pathlib import Path
import subprocess


THIS_DIR = Path(__file__).parent.resolve()

CONFIG_FILE = THIS_DIR / "bastion_config.json"

# load config file
with open(CONFIG_FILE, "r") as fh:
    config = json.load(fh)

def connect(remote_name, *args, **kwargs):
    if remote_name in config["remotes"]:
        remote = config["remotes"][remote_name]
    else:
        print(f"Remote config could not be found for {remote_name}")
        sys.exit()

    bastion_name = remote.get("bastion")

    if bastion_name in config["bastions"]:
        bastion = config["bastions"][bastion_name]
    else:
        print(f"Remote {remote_name} specified a bastion that could not be found: {bastion_name}")
        sys.exit()

    full_config = {
        "max_connection_attempts": config.get("max_connection_attempts", 5),
        "time_between_connection_attempts": config.get("time_between_connection_attempts", 5)
    }

    full_config.update(remote)
    full_config.update(bastion)

    ssh_options = (
        config.get("ssh_options", []) +
        full_config.get("ssh_options", []) +
        full_config.get("remote_ssh_options", [])
    )

    cmd = ("ssh -i {key_dir}/{key_file} -N -L "
          "0.0.0.0:{local_port}:{remote_host}:{remote_port}"
          " {ssh_options}{user}@{host}").format(
            key_dir=config["key_dir"],
            ssh_options=f"-o {' -o '.join(ssh_options)} " if ssh_options else "",
            **full_config
          )

    print(f"Starting connection to {remote_name} through {bastion_name}")
    print(f"Local port: {full_config['local_port']}")

    print(cmd)

    connection_attempts = 0

    while True:
        if full_config["max_connection_attempts"] and connection_attempts >= full_config["max_connection_attempts"]:
            print(f"Reached max connection attempts of {connection_attempts}")
            break

        connection_attempts += 1

        try:
            subprocess.run(cmd, shell=True, check=True)
        except KeyboardInterrupt:
            print("\n\nConnection closed.\nGoodbye!")
            break
        except subprocess.CalledProcessError:
            print(f"Connection terminated unexpectedly at {datetime.now().strftime('%H:%M:%s')}, retrying in {full_config['time_between_connection_attempts']} seconds")
            time.sleep(full_config["time_between_connection_attempts"])


def show_remotes(*args, **kwargs):
    print("Available remotes:")
    for remote_name in config["remotes"].keys():
        print(f" * {remote_name}")


commands = {
    "show_remotes": show_remotes,
    "connect": connect,
}

if __name__ == "__main__":
    args = []

    if len(sys.argv) != 2:
        command = "show_remotes"
    else:
        command = sys.argv[1]

    if command in config["remotes"]:
        args.append(command)
        command = "connect"

    if command not in commands:
        print(f"Command not recognized: {command}")
        print("Available commands:")

        for command in commands.keys():
            print(f" * {command}")

    commands[command](*args)
