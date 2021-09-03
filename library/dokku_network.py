#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
import subprocess

DOCUMENTATION = """
---
module: dokku_network
short_description: Create or destroy container networks for dokku apps
options:
  name:
    description:
      - The name of the network
    required: True
    default: null
    aliases: []
  state:
    description:
      - The state of the network
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Philipp Sessler
requirements: [ ]
"""

EXAMPLES = """
- name: Create a network
  dokku_network:
    name: example-network

- name: Delete that network
  dokku_network:
    name: example-network
    state: absent
"""


def dokku_network_exists(network):
    exists = False
    error = None
    command = "dokku --quiet network:exists {0}".format(network)
    try:
        subprocess.check_call(command, shell=True)
        exists = True
    except subprocess.CalledProcessError as e:
        error = str(e)
    return exists, error


def dokku_network_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    exists, error = dokku_network_exists(data["name"])
    if exists:
        is_error = False
        meta["present"] = True
        return (is_error, has_changed, meta)

    command = "dokku network:create {0}".format(data["name"])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_network_absent(data=None):
    is_error = True
    has_changed = False
    meta = {"present": True}

    exists, error = dokku_network_exists(data["name"])
    if not exists:
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    command = "dokku --force network:destroy {0}".format(data["name"])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = False
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def main():
    fields = {
        "name": {"required": True, "type": "str"},
        "state": {
            "required": False,
            "default": "present",
            "choices": ["present", "absent"],
            "type": "str",
        },
    }
    choice_map = {
        "present": dokku_network_present,
        "absent": dokku_network_absent,
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = choice_map.get(module.params["state"])(
        module.params
    )

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
