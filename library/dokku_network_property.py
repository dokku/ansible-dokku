#!/usr/bin/python
# -*- coding: utf-8 -*-
# from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
import subprocess

DOCUMENTATION = """
---
module: dokku_network_property
short_description: Set or clear a network property for a given dokku application
options:
  global:
    description:
      - Whether to change the global network property.
    default: False
    aliases: []
  app:
    description:
      - The name of the app. This is required only if global is set to False.
    required: True
    default: null
    aliases: []
  property:
    description:
      - The network property of the app to be modified
    required: True
    default: null
    choices: [ "initial-network", "attach-post-create", "attach-post-deploy", "bind-all-interfaces", "static-web-listener", "tld" ]
    aliases: []
  network:
    description:
      - The name of the network to attach to
    required: False
    default: null
    aliases: []
author: Philipp Sessler
requirements: [ ]
"""

EXAMPLES = """
- name: Associates a network after a container is created but before it is started
  dokku_network_property:
    app: hello-world
    property: attach-post-create
    network: example-network

- name: Associates the network at container creation
  dokku_network_property:
    app: hello-world
    property: initial-network
    network: example-network

- name: Setting a global network property
  dokku_network_property:
    global: true
    property: attach-post-create
    network: example-network

- name: Clearing a network property
  dokku_network_property:
    app: hello-world
    property: attach-post-create
"""


def dokku_network_property_set(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    command = "dokku network:set {0} {1} {2}".format(
        "--global" if data["global"] else data["app"],
        data["property"],
        data["network"] if "network" in data else "",
    )

    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def main():
    fields = {
        "global": {"required": False, "default": False, "type": "bool"},
        "app": {"required": False, "type": "str"},
        "network": {"required": True, "type": "str"},
        "property": {
            "required": False,
            "choices": ["initial-network", "attach-post-create", "attach-post-deploy"],
            "type": "str",
        },
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_network_property_set(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
