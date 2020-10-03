#!/usr/bin/python
# -*- coding: utf-8 -*-
# from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
import pipes
import re
import subprocess

DOCUMENTATION = """
---
module: dokku_ecr
short_description: Manage the ecr configuration for a given dokku application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  account-id:
    description:
      - The ecr aws account-id
    required: False
    aliases: []
  image-repo:
    description:
      - The image name to use when pushing to ecr
    required: False
    aliases: []
  region:
    description:
      - The ecr region
    required: False
    default: us-east-1
    aliases: []
  state:
    description:
      - The state of the ecr integration
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Jose Diaz-Gonzalez
requirements:
  - the `dokku-ecr` plugin (_commercial_)
"""

EXAMPLES = """
- name: ecr:enable hello-world
  dokku_ecr:
    app: hello-world

- name: ecr:enable hello-world with args
  dokku_ecr:
    app: hello-world
    image-repo: prod-hello-world

- name: ecr:disable hello-world
  dokku_ecr:
    app: hello-world
    state: absent
"""


def force_list(var):
    if isinstance(var, list):
        return var
    return list(var)


def to_bool(v):
    return v.lower() == "true"


def to_str(v):
    return "true" if v else "false"


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


def dokku_module_set(command_prefix, data, key, value=None):
    has_changed = False
    error = None

    if value:
        command = "dokku --quiet {0}:set {1} {2} {3}".format(
            command_prefix, data["app"], key, pipes.quote(value)
        )
    else:
        command = "dokku --quiet {0}:set {1} {2}".format(
            command_prefix, data["app"], key
        )

    try:
        subprocess.check_call(command, shell=True)
        has_changed = True
    except subprocess.CalledProcessError as e:
        error = str(e)

    return (has_changed, error)


def dokku_module_set_blank(command_prefix, data, setable_fields):
    error = None
    errors = []
    changed_keys = []
    has_changed = False

    for key in setable_fields:
        changed, error = dokku_module_set(command_prefix, data, key)
        if changed:
            has_changed = True
            changed_keys.append(key)
        if error:
            errors.append(error)

    if len(errors) > 0:
        error = ",".join(errors)

    return (has_changed, changed_keys, error)


def dokku_module_set_values(command_prefix, data, report, setable_fields):
    error = None
    errors = []
    changed_keys = []
    has_changed = False

    if "enabled" in data:
        data["enabled"] = to_str(data["enabled"])
    if "enabled" in report:
        report["enabled"] = to_str(report["enabled"])

    for key, value in report.items():
        if key not in setable_fields:
            continue
        if data.get(key, None) is None:
            continue
        if data[key] == value:
            continue

        changed, error = dokku_module_set(command_prefix, data, key, data[key])
        if error:
            errors.append(error)
        if changed:
            has_changed = True
            changed_keys.append(key)

    if len(errors) > 0:
        error = ",".join(errors)

    return (has_changed, changed_keys, error)


def dokku_module_require_fields(data, required_fields):
    error = None
    missing_keys = []

    if len(required_fields) > 0:
        for key in required_fields:
            if data.get(key, None) is None:
                missing_keys.append(key)

    if len(missing_keys) > 0:
        error = "missing required arguments: {0}".format(", ".join(missing_keys))

    return error


def dokku_module_report(command_prefix, data, re_compiled, allowed_report_keys):
    command = "dokku --quiet {0}:report {1}".format(command_prefix, data["app"])
    output, error = subprocess_check_output(command)
    if error is not None:
        return output, error

    output = [re.sub(r"\s\s+", "", line) for line in output]
    report = {}

    for line in output:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = re_compiled.sub(r"", key.replace(" ", "-").lower())
        if key not in allowed_report_keys:
            continue

        value = value.strip()
        if key == "enabled":
            value = to_bool(value)
        report[key] = value

    return report, error


def dokku_module_absent(
    command_prefix,
    data,
    re_compiled,
    allowed_report_keys,
    required_present_fields,
    setable_fields,
):
    has_changed = False
    is_error = True
    meta = {"present": True, "changed": []}

    report, error = dokku_module_report(
        command_prefix, data, re_compiled, allowed_report_keys
    )
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    if not report["enabled"]:
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    data["enabled"] = "false"
    has_changed, changed_keys, error = dokku_module_set_blank(
        command_prefix, data, setable_fields
    )
    if error:
        meta["error"] = error
    else:
        is_error = False
        meta["present"] = False

    if len(changed_keys) > 0:
        meta["changed"] = changed_keys

    return (is_error, has_changed, meta)


def dokku_module_present(
    command_prefix,
    data,
    re_compiled,
    allowed_report_keys,
    required_present_fields,
    setable_fields,
):
    is_error = True
    has_changed = False
    meta = {"present": False, "changed": []}

    data["enabled"] = "true"
    error = dokku_module_require_fields(data, required_present_fields)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    report, error = dokku_module_report(
        command_prefix, data, re_compiled, allowed_report_keys
    )
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    has_changed, changed_keys, error = dokku_module_set_values(
        command_prefix, data, report, setable_fields
    )
    if error:
        meta["error"] = error
    else:
        is_error = False
        meta["present"] = True

    if len(changed_keys) > 0:
        meta["changed"] = changed_keys

    return (is_error, has_changed, meta)


def main():
    fields = {
        "app": {"required": True, "type": "str"},
        "account-id": {"required": False, "type": "str"},
        "image-repo": {"required": False, "type": "str"},
        "region": {"required": False, "type": "str", "default": "us-east-1"},
        "state": {
            "required": False,
            "default": "present",
            "choices": ["absent", "present"],
            "type": "str",
        },
    }
    choice_map = {
        "absent": dokku_module_absent,
        "present": dokku_module_present,
    }

    allowed_report_keys = ["enabled", "account-id", "image-repo", "region"]
    command_prefix = "ecr"
    required_present_fields = ["account-id", "image-repo", "region"]
    setable_fields = ["account-id", "image-repo", "region"]
    RE_PREFIX = re.compile("^ecr-")

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = choice_map.get(module.params["state"])(
        command_prefix=command_prefix,
        data=module.params,
        re_compiled=RE_PREFIX,
        allowed_report_keys=allowed_report_keys,
        required_present_fields=required_present_fields,
        setable_fields=setable_fields,
    )

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
