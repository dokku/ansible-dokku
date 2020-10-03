#!/usr/bin/python
# -*- coding: utf-8 -*-
# from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
import subprocess

DOCUMENTATION = """
---
module: dokku_app
short_description: Create or destroy dokku apps
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  state:
    description:
      - The state of the app
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Jose Diaz-Gonzalez
requirements: [ ]
"""

EXAMPLES = """
- name: Create a dokku app
  dokku_app:
    app: hello-world

- name: Delete that repo
  dokku_app:
    app: hello-world
    state: absent
"""


def dokku_apps_exists(app):
    exists = False
    error = None
    command = "dokku --quiet apps:exists {0}".format(app)
    try:
        subprocess.check_call(command, shell=True)
        exists = True
    except subprocess.CalledProcessError as e:
        error = str(e)
    return exists, error


def dokku_app_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    exists, error = dokku_apps_exists(data["app"])
    if exists:
        is_error = False
        meta["present"] = True
        return (is_error, has_changed, meta)

    command = "dokku apps:create {0}".format(data["app"])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_app_absent(data=None):
    is_error = True
    has_changed = False
    meta = {"present": True}

    exists, error = dokku_apps_exists(data["app"])
    if not exists:
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    command = "dokku --force apps:destroy {0}".format(data["app"])
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
        "present": dokku_app_present,
        "absent": dokku_app_absent,
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
