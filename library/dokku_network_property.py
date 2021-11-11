#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
import subprocess

DOCUMENTATION = """
---
module: dokku_network_property
short_description: Set or clear a network property for a given dokku application
options:
  global:
    description:
      - Whether to change the global network property
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
      - >
        The network property to be be modified. This can be any property supported
        by dokku (e.g., `initial-network`, `attach-post-create`, `attach-post-deploy`,
        `bind-all-interfaces`, `static-web-listener`, `tld`).
    required: True
    default: null
    aliases: []
  value:
    description:
      - The value of the network property (leave empty to unset)
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
    value: example-network

- name: Associates the network at container creation
  dokku_network_property:
    app: hello-world
    property: initial-network
    value: example-network

- name: Setting a global network property
  dokku_network_property:
    global: true
    property: attach-post-create
    value: example-network

- name: Clearing a network property
  dokku_network_property:
    app: hello-world
    property: attach-post-create
"""


def dokku_network_property_set(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    if data["global"] and data["app"]:
        is_error = True
        meta["error"] = 'When "global" is set to true, "app" must not be provided.'
        return (is_error, has_changed, meta)

    # Check if "value" is set and evaluates to a non-empty string, otherwise use an empty string
    value = data["value"] if "value" in data else None
    if not value:
        value = ""

    command = "dokku network:set {0} {1} {2}".format(
        "--global" if data["global"] else data["app"],
        data["property"],
        value,
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
        "property": {"required": True, "type": "str"},
        "value": {"required": False, "type": "str"},
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_network_property_set(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
