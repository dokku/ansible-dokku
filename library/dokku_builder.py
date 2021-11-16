#!/usr/bin/python
# -*- coding: utf-8 -*-
import pipes
import re
import subprocess

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output

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
  key:
    description:
      - Key of the builder property
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
    key: selected
    value: dockerfile
- name: Setting the builder to the default value
  dokku_builder:
    app: node-js-app
    key: selected
- name: Changing the build build directory
  dokku_builder:
    app: monorepo
    key: build-dir
    value: backend
- name: Overriding the auto-selected builder globally
  dokku_builder:
    global: true
    key: selected
    value: herokuish
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
            command_prefix,
            "--global" if data["global"] else data["app"],
            key,
            pipes.quote(value),
        )
    else:
        command = "dokku --quiet {0}:set {1} {2}".format(
            command_prefix, "--global" if data["global"] else data["app"], key
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


def build_report(output, re_compiled, allowed_report_keys):
    output = [re.sub(r"\s\s+", "", line) for line in output]
    report = {}
    for line in output:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = re_compiled.sub(r"", key.replace(" ", "-").lower())
        if key not in allowed_report_keys:
            continue

        report[key] = value.strip()
    return report


def dokku_module_report(command_prefix, data, re_compiled, allowed_report_keys):
    command = "dokku --quiet {0}:report {1}".format(command_prefix, data["app"])
    output, error = subprocess_check_output(command)
    if error is not None:
        return output, error
    return build_report(output, re_compiled, allowed_report_keys), error


def dokku_module_report_global(command_prefix, data, re_compiled, allowed_report_keys):
    command = "dokku --quiet {0}:report --global".format(command_prefix)
    output, error = subprocess_check_output(command)
    if error is not None:
        return output, error
    return (
        build_report(
            output, re_compiled, map(lambda key: "global {0}", allowed_report_keys)
        ),
        error,
    )


def dokku_builder(
    command_prefix,
    data,
    re_compiled,
    allowed_report_keys,
    required_present_fields,
    setable_fields,
):
    is_error = True
    has_changed = False
    meta = {"changed": []}

    error = dokku_module_require_fields(data, required_present_fields)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    report, error = (
        dokku_module_report_global(
            command_prefix, data, re_compiled, allowed_report_keys
        )
        if data["global"]
        else dokku_module_report(command_prefix, data, re_compiled, allowed_report_keys)
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

    if len(changed_keys) > 0:
        meta["changed"] = changed_keys

    return (is_error, has_changed, meta)


def main():
    fields = {
        "app": {"required": True, "type": "str"},
        "key": {"required": True, "type": "str"},
        "value": {"required": False, "type": "str", "no_log": True},
        "global": {"required": False, "type": "bool"},
    }

    allowed_report_keys = ["build", "selected"]
    command_prefix = "builder"
    required_present_fields = ["app", "key"]
    setable_fields = ["build dir", "selected"]
    RE_PREFIX = re.compile("^builder-")

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_builder(
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
