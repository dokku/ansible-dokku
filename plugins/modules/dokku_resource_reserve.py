#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output
import subprocess
import re

DOCUMENTATION = """
---
module: dokku_resource_reserve
short_description: Manage resource reservations for a given dokku application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  resources:
    description:
      - The Resource type and quantity (required when state=present)
    required: False
    default: null
    aliases: []
  process_type:
    description:
      - The process type selector
    required: False
    default: null
    alias: []
  clear_before:
    description:
      - Clear all reserves before apply
    required: False
    default: "False"
    choices: [ "True", "False" ]
    aliases: []
  state:
    description:
      - The state of the resource reservations
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Alexandre Pavanello e Silva
requirements: [ ]

"""

EXAMPLES = """
- name: Reserve CPU and memory for a dokku app
  dokku_resource_reserve:
    app: hello-world
    resources:
      cpu: 100
      memory: 100

- name: Create a reservation per process type of a dokku app
  dokku_resource_reserve:
    app: hello-world
    process_type: web
    resources:
      cpu: 100
      memory: 100

- name: Clear all reservations before applying
  dokku_resource_reserve:
    app: hello-world
    state: present
    clear_before: True
    resources:
      cpu: 100
      memory: 100

- name: Remove all resource reservations
  dokku_resource_reserve:
    app: hello-world
    state: absent
"""


def dokku_resource_clear(data):
    error = None
    process_type = ""
    if data["process_type"]:
        process_type = "--process-type {0}".format(data["process_type"])
    command = "dokku resource:reserve-clear {0} {1}".format(process_type, data["app"])
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        error = str(e)
    return error


def dokku_resource_reserve_report(data):

    process_type = ""
    if data["process_type"]:
        process_type = "--process-type {0}".format(data["process_type"])
    command = "dokku --quiet resource:reserve {0} {1}".format(process_type, data["app"])

    output, error = subprocess_check_output(command)
    if error is not None:
        return output, error
    output = [re.sub(r"\s+", "", line) for line in output]

    report = {}

    for line in output:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        report[key] = value

    return report, error


def dokku_resource_reserve_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    if "resources" not in data:
        meta["error"] = "missing required arguments: resources"
        return (is_error, has_changed, meta)

    report, error = dokku_resource_reserve_report(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    for k, v in data["resources"].items():
        if k not in report.keys():
            is_error = True
            has_changed = False
            meta["error"] = "Unknown resource {0}, choose one of: {1}".format(
                k, list(report.keys())
            )
            return (is_error, has_changed, meta)
        if report[k] != str(v):
            has_changed = True

    if data["clear_before"] is True:

        error = dokku_resource_clear(data)
        if error:
            meta["error"] = error
            is_error = True
            has_changed = False
            return (is_error, has_changed, meta)
        has_changed = True

    if not has_changed:
        meta["present"] = True
        is_error = False
        return (is_error, has_changed, meta)

    values = []
    for key, value in data["resources"].items():
        values.append("--{0} {1}".format(key, value))

    process_type = ""
    if data["process_type"]:
        process_type = "--process-type {0}".format(data["process_type"])

    command = "dokku resource:reserve {0} {1} {2}".format(
        " ".join(values), process_type, data["app"]
    )
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)
    return (is_error, has_changed, meta)


def dokku_resource_reserve_absent(data):
    is_error = True
    has_changed = False
    meta = {"present": True}

    error = dokku_resource_clear(data)
    if error:
        meta["error"] = error
        is_error = True
        has_changed = False
        return (is_error, has_changed, meta)

    is_error = False
    has_changed = True
    meta = {"present": False}

    return (is_error, has_changed, meta)


def main():
    fields = {
        "app": {"required": True, "type": "str"},
        "process_type": {"required": False, "type": "str"},
        "resources": {"required": False, "type": "dict"},
        "clear_before": {"required": False, "type": "bool"},
        "state": {
            "required": False,
            "default": "present",
            "choices": ["present", "absent"],
            "type": "str",
        },
    }
    choice_map = {
        "present": dokku_resource_reserve_present,
        "absent": dokku_resource_reserve_absent,
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
