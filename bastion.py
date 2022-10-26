#!/usr/bin/env python3

import sys
import json
import subprocess

CONFIG_FILE = "bastion_config.json"

# load config file
with open(CONFIG_FILE, "r") as fh:
    config = json.load(fh)

args = sys.argv
remote_name = sys.argv[1]


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

full_config = remote
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
        ssh_options=f"-o {' '.join(ssh_options)} " if ssh_options else "",
        **full_config
      )

print(f"Starting connection to {remote_name} through {bastion_name}")
print(f"Local port: {full_config['local_port']}")

try:
    subprocess.run(cmd, shell=True)
except KeyboardInterrupt:
    print("\n\nConnection closed.\nGoodbye!")
