#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output

DOCUMENTATION = """
---
module: dokku_acl_app
short_description: Manage access control list for a given dokku application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  users:
    description:
      - The list of users who can manage the app
    required: True
    aliases: []
  state:
    description:
      - Whether the ACLs should be present or absent
    required: False
    default: present
    choices: ["present", "absent" ]
    aliases: []
author: Leopold Talirz
requirements:
  - the `dokku-acl` plugin
"""

EXAMPLES = """
- name: let leopold manage hello-world
  dokku_acl_app:
    app: hello-world
    users:
      - leopold
- name: remove leopold from hello-world
  dokku_acl_app:
    app: hello-world
    users:
      - leopold
    state: absent
"""


def dokku_acl_app_set(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    has_changed = False

    # get users for app
    command = "dokku acl:list {0}".format(data["app"])
    output, error = subprocess_check_output(command, redirect_stderr=True)

    if error is not None:
        meta["error"] = error
        return (is_error, has_changed, meta)

    users = set(output)

    if data["state"] == "absent":
        for user in data["users"]:
            if user not in users:
                continue

            command = "dokku --quiet acl:remove {0} {1}".format(data["app"], user)
            output, error = subprocess_check_output(command)
            has_changed = True
            if error is not None:
                meta["error"] = error
                return (is_error, has_changed, meta)
    else:
        for user in data["users"]:
            if user in users:
                continue

            command = "dokku --quiet acl:add {0} {1}".format(data["app"], user)
            output, error = subprocess_check_output(command)
            has_changed = True
            if error is not None:
                meta["error"] = error
                return (is_error, has_changed, meta)

    is_error = False
    return (is_error, has_changed, meta)


def main():
    fields = {
        "app": {"required": True, "type": "str"},
        "users": {"required": True, "type": "list"},
        "state": {
            "required": False,
            "default": "present",
            "choices": ["absent", "present"],
            "type": "str",
        },
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_acl_app_set(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
