#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output
import subprocess

DOCUMENTATION = """
---
module: dokku_letsencrypt
short_description: Enable or disable the letsencrypt plugin for a dokku app
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  state:
    description:
      - The state of the letsencrypt plugin
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Gavin Ballard
requirements:
  - the `dokku-letsencrypt` plugin
"""

EXAMPLES = """
- name: Enable the letsencrypt plugin
  dokku_letsencrypt:
    app: hello-world

- name: Disable the letsencrypt plugin
  dokku_letsencrypt:
    app: hello-world
    state: absent
"""


def dokku_letsencrypt_enabled(data):
    command = "dokku --quiet letsencrypt:list | awk '{{print $1}}'"
    response, error = subprocess_check_output(command.format(data["app"]))

    if error:
        return None, error

    return data["app"] in response, error


def dokku_letsencrypt_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    enabled, error = dokku_letsencrypt_enabled(data)
    if enabled:
        is_error = False
        meta["present"] = True
        return (is_error, has_changed, meta)

    command = "dokku --quiet letsencrypt:enable {0}".format(data["app"])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_letsencrypt_absent(data=None):
    is_error = True
    has_changed = False
    meta = {"present": True}

    enabled, error = dokku_letsencrypt_enabled(data)
    if enabled is False:
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    command = "dokku --quiet letsencrypt:disable {0}".format(data["app"])
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
        "present": dokku_letsencrypt_present,
        "absent": dokku_letsencrypt_absent,
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
