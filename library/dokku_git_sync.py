#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output
import pipes
import re
import subprocess

DOCUMENTATION = """
---
module: dokku_git_sync
short_description: Manages syncing git code from a remote repository for an app
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  remote:
    description:
      - The git remote url to use
    required: False
    default: null
    aliases: []
  state:
    description:
      - The state of the git-sync integration
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Jose Diaz-Gonzalez
requirements:
  - the `dokku-git-sync` plugin (_commercial_)
"""

EXAMPLES = """
- name: git-sync:enable hello-world
  dokku_git_sync:
    app: hello-world
    remote: git@github.com:hello-world/hello-world.git

- name: git-sync:disable hello-world
  dokku_git_sync:
    app: hello-world
    state: absent
"""


def to_bool(v):
    return v.lower() == "true"


def to_str(v):
    return "true" if v else "false"


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
        "remote": {"required": False, "type": "str", "default": None},
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

    allowed_report_keys = ["remote"]
    command_prefix = "git-sync"
    required_present_fields = ["remote"]
    setable_fields = ["remote"]
    RE_PREFIX = re.compile("^git-sync-")

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
