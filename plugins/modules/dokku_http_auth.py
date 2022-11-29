#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output

DOCUMENTATION = """
---
module: dokku_http_auth
short_description: Manage HTTP Basic Authentication for a dokku app
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  state:
    description:
      - The state of the http-auth plugin
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
  username:
    description:
      - The HTTP Auth Username (required for 'present' state)
    required: False
    aliases: []
  password:
    description:
      - The HTTP Auth Password (required for 'present' state)
    required: False
    aliases: []
author: Simo Aleksandrov
requirements:
  - the `dokku-http-auth` plugin
"""

EXAMPLES = """
- name: Enable the http-auth plugin
  dokku_http_auth:
    app: hello-world
    state: present
    username: samsepi0l
    password: hunter2

- name: Disable the http-auth plugin
  dokku_http_auth:
    app: hello-world
    state: absent
"""


def dokku_http_auth_enabled(data):
    command = "dokku --quiet http-auth:report {0}"
    response, error = subprocess_check_output(command.format(data["app"]))

    if error:
        return None, error

    report = response[0].split(":")[1]
    return report.strip() == "true", error


def dokku_http_auth_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    enabled, error = dokku_http_auth_enabled(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    if enabled:
        is_error = False
        meta["present"] = True
        return (is_error, has_changed, meta)

    command = "dokku --quiet http-auth:on {0} {1} {2}".format(
        data["app"], data["username"], data["password"]
    )
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_http_auth_absent(data=None):
    is_error = True
    has_changed = False
    meta = {"present": True}

    enabled, error = dokku_http_auth_enabled(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    if enabled is False:
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    command = "dokku --quiet http-auth:off {0}".format(data["app"])
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
        "username": {"required": False, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
    }
    choice_map = {
        "present": dokku_http_auth_present,
        "absent": dokku_http_auth_absent,
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
