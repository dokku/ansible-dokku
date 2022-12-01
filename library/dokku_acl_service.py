#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output

DOCUMENTATION = """
---
module: dokku_acl_service
short_description: Manage access control list for a given dokku service
options:
  service:
    description:
      - The name of the service
    required: True
    default: null
    aliases: []
  type:
    description:
      - The type of the service
    required: True
    default: null
    aliases: []
  users:
    description:
      - The list of users who can manage the service
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
- name: let leopold manage mypostgres postgres service
  dokku_acl_service:
    service: mypostgres
    type: postgres
    users:
      - leopold
- name: remove leopold from mypostgres postgres service
  dokku_acl_service:
    service: hello-world
    type: postgres
    users:
      - leopold
    state: absent
"""


def dokku_acl_service_set(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    has_changed = False

    # get users for service
    command = "dokku --quiet acl:list-service {0} {1}".format(
        data["type"], data["service"]
    )
    output, error = subprocess_check_output(command, redirect_stderr=True)

    if error is not None:
        meta["error"] = error
        return (is_error, has_changed, meta)

    users = set(output)

    if data["state"] == "absent":
        for user in data["users"]:
            if user not in users:
                continue

            command = "dokku --quiet acl:remove-service {0} {1} {2}".format(
                data["type"], data["service"], user
            )
            output, error = subprocess_check_output(command)
            has_changed = True
            if error is not None:
                meta["error"] = error
                return (is_error, has_changed, meta)
    else:
        for user in data["users"]:
            if user in users:
                continue

            command = "dokku --quiet acl:add-service {0} {1} {2}".format(
                data["type"], data["service"], user
            )
            output, error = subprocess_check_output(command, redirect_stderr=True)
            has_changed = True
            if error is not None:
                meta["error"] = error
                return (is_error, has_changed, meta)

    is_error = False
    return (is_error, has_changed, meta)


def main():
    fields = {
        "service": {"required": True, "type": "str"},
        "type": {"required": True, "type": "str"},
        "users": {"required": True, "type": "list"},
        "state": {
            "required": False,
            "default": "present",
            "choices": ["absent", "present"],
            "type": "str",
        },
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_acl_service_set(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
