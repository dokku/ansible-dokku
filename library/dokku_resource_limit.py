#!/usr/bin/python
# -*- coding: utf-8 -*-
# from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
import subprocess
import re

DOCUMENTATION = """
---
module: dokku_resource_limit
short_description: Manage limits for a given dokku application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  resources:
    description:
      - The Resource type and quantity
    required: True
    default: null
    aliases: []
  process-type:
    description:
      - The process type selector
    required: False
    default: null
    alias: []
  clear-before:
    description:
      - Clear all limits before apply
    required: False
    default: "False"
    choices: [ "True", "False" ]
    aliases: []
  state:
    description:
      - The state of resources
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Alexandre Pavanello e Silva
requirements: [ ]

"""

EXAMPLES = """
- name: Create a dokku app cpu and memory limit
  dokku_resource_limit:
    app: hello-world
    resources:
      cpu: 100
      memory: 100

- name: Create a limit per-process type dokku app
  dokku_resource_limit:
    app: hello-world
    process-type: web
    resources:
      cpu: 100
      memory: 100

- name: Clear before apply new limits
  dokku_resource_limit:
    app: hello-world
    state: present
    clear-before: True
    resources:
      cpu: 100
      memory: 100

- name: Remove all resource/limits
  dokku_app:
    app: hello-world
    state: absent
"""


def force_list(var):
    if isinstance(var, list):
        return var
    return list(var)


def subprocess_check_output(command, split="\n"):
    error = None
    output = []
    try:
        output = subprocess.check_output(command, shell=True)
        if isinstance(output, bytes):
            output = output.decode("utf-8")
        output = str(output).rstrip("\n")
        if split is None:
            return output, error

        output = output.split(split)
        output = force_list(filter(None, output))
        output = [o.strip() for o in output]
    except subprocess.CalledProcessError as e:
        error = str(e)
    return output, error


def dokku_resource_clear(data):
    error = None
    process_type = ""
    if data["process-type"]:
        process_type = "--process-type {0}".format(data["process-type"])
    command = "dokku resource:limit-clear {0} {1}".format(process_type, data["app"])
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        error = str(e)
    return error


def dokku_resource_limit_report(data):

    process_type = ""
    if data["process-type"]:
        process_type = "--process-type {0}".format(data["process-type"])
    command = "dokku resource:limit {0} {1}".format(process_type, data["app"])

    output, error = subprocess_check_output(command)
    if error is not None:
        return output, error
    output = [re.sub(r"\s+", "", line) for line in output]
    report = {}

    allowed_keys = [
        "cpu",
        "memory",
        "memory-swap",
        "network",
        "network-ingress",
        "network-egress",
        "nvidia-gpu",
    ]

    for line in output:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key not in allowed_keys:
            continue
        report[key] = value
    return report, error


def dokku_resource_limit_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    allowed_keys = [
        "cpu",
        "memory",
        "memory-swap",
        "network",
        "network-ingress",
        "network-egress",
        "nvidia-gpu",
    ]

    if "resources" not in data:
        meta["error"] = "missing required arguments: resources"
        return (is_error, has_changed, meta)

    report, error = dokku_resource_limit_report(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    for k, v in data["resources"].items():
        if k not in allowed_keys:
            is_error = True
            has_changed = False
            meta["error"] = "Unknow resource {0}, allowed ressource: {1}".format(
                k, allowed_keys
            )
            return (is_error, has_changed, meta)
        if report[k] != str(v):
            has_changed = True

    if data["clear-before"] is True:

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
    if data["process-type"]:
        process_type = "--process-type {0}".format(data["process-type"])

    command = "dokku resource:limit {0} {1} {2}".format(
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


def dokku_resource_limit_absent(data):
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
        "process-type": {"required": False, "type": "str"},
        "resources": {"required": False, "type": "dict"},
        "clear-before": {"required": False, "type": "bool"},
        "state": {
            "required": False,
            "default": "present",
            "choices": ["present", "absent"],
            "type": "str",
        },
    }
    choice_map = {
        "present": dokku_resource_limit_present,
        "absent": dokku_resource_limit_absent,
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
