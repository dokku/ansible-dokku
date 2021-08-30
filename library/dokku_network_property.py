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
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  network:
    description:
      - The name of the network to attach to
    required: True
    default: null
    aliases: []
  property:
    description:
      - The attach network property
    required: True
    default: null
    choices: [ "initial-network", "attach-post-create", "attach-post-deploy" ]
    aliases: []
author: Philipp Sessler
requirements: [ ]
"""

EXAMPLES = """
- name: Associates a network after a container is created but before it is started
  dokku_network_property:
    app: hello-world
    network: example-network
    property: attach-post-create

- name: Associates the network at container creation
  dokku_network_property:
    app: hello-world
    network: example-network
    property: initial-network

- name: Setting a global network property
  dokku_network_property:
    app: --global
    network: example-network
    property: attach-post-create

- name: De-associate the container with the network.
  dokku_network_property:
    app: hello-world
    network: example-network
"""


def dokku_network_property_set(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    command = "dokku network:set {0} {1} {2}".format(
        data["app"],
        data["network"],
        data["property"] if "property" in data else "",
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
        "app": {"required": True, "type": "str"},
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
