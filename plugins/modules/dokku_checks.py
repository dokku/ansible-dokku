#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output

DOCUMENTATION = """
---
module: dokku_checks
short_description: Manage the Zero Downtime checks for a dokku app
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  state:
    description:
      - The state of the checks functionality
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Simo Aleksandrov
"""

EXAMPLES = """
- name: Disable the zero downtime deployment
  dokku_checks:
    app: hello-world
    state: absent

- name: Re-enable the zero downtime deployment (enabled by default)
  dokku_checks:
    app: hello-world
    state: present
"""


def dokku_checks_enabled(data):
    command = "dokku --quiet checks:report {0}"
    response, error = subprocess_check_output(command.format(data["app"]))

    if error:
        return None, error

    report = response[0].split(":")[1]
    return report.strip() != "_all_", error


def dokku_checks_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    enabled, error = dokku_checks_enabled(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    if enabled:
        is_error = False
        meta["present"] = True
        return (is_error, has_changed, meta)

    command = "dokku --quiet checks:enable {0}".format(data["app"])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_checks_absent(data=None):
    is_error = True
    has_changed = False
    meta = {"present": True}

    enabled, error = dokku_checks_enabled(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    if enabled is False:
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    command = "dokku --quiet checks:disable {0}".format(data["app"])
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
        "app": {"required": True, "type": "str"},
        "state": {
            "required": False,
            "default": "present",
            "choices": ["present", "absent"],
            "type": "str",
        },
    }
    choice_map = {
        "present": dokku_checks_present,
        "absent": dokku_checks_absent,
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
