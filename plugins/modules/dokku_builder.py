#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: dokku_builder
short_description: Manage the builder configuration for a given dokku application
options:
  app:
    description:
      - The name of the app. This is required only if global is set to False.
    required: True
    default: null
    aliases: []
  property:
    description:
      - The property to be changed (e.g., `build-dir`, `selected`)
    required: True
    aliases: []
  value:
    description:
      - The value of the builder property (leave empty to unset)
    required: False
    aliases: []
  global:
    description:
      - If the property being set is global
    required: False
    default: False
    aliases: []
author: Simo Aleksandrov
"""

EXAMPLES = """
- name: Overriding the auto-selected builder
  dokku_builder:
    app: node-js-app
    property: selected
    value: dockerfile
- name: Setting the builder to the default value
  dokku_builder:
    app: node-js-app
    property: selected
- name: Changing the build build directory
  dokku_builder:
    app: monorepo
    property: build-dir
    value: backend
- name: Overriding the auto-selected builder globally
  dokku_builder:
    global: true
    property: selected
    value: herokuish
"""


def dokku_builder(data):
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

    command = "dokku builder:set {0} {1} {2}".format(
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
        "app": {"required": False, "type": "str"},
        "property": {"required": True, "type": "str"},
        "value": {"required": False, "type": "str", "no_log": True},
        "global": {"required": False, "type": "bool"},
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_builder(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
