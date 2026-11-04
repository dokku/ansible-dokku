#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output
import json
import subprocess

DOCUMENTATION = """
---
module: dokku_global_cert
short_description: Manages global ssl configuration.
description:
  - Manages ssl configuration for the server.
  - Will not update certificates
  - Only checks for presence of the crt file, not the key
options:
  key:
    description:
      - Path to the ssl certificate key
    required: True
    default: null
    aliases: []
  cert:
    description:
      - Path to the ssl certificate
    required: True
    default: null
    aliases: []
  state:
    description:
      - The state of the ssl configuration
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Jose Diaz-Gonzalez
requirements:
  - the `dokku-global-cert` plugin
"""

EXAMPLES = """
- name: Adds an ssl certificate and key
  dokku_global_cert:
    key: /etc/nginx/ssl/global-hello-world.key
    cert: /etc/nginx/ssl/global-hello-world.crt

- name: Removes an ssl certificate and key
  dokku_global_cert:
    state: absent
"""


def to_bool(v):
    return v.lower() == "true"


def dokku_global_cert(data):
    command = "dokku global-cert:report --global --format json"
    output, error = subprocess_check_output(command, split=None)

    if error is None:
        try:
            output = json.loads(output)
        except ValueError as e:
            error = str(e)

    if "enabled" in output:
        output["enabled"] = to_bool(output["enabled"])

    return output, error


def dokku_global_cert_absent(data=None):
    has_changed = False
    is_error = True
    meta = {"present": True}

    report, error = dokku_global_cert(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    if not report["enabled"]:
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    command = "dokku --quiet global-cert:remove"
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = False
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_global_cert_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    report, error = dokku_global_cert(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    if report["enabled"]:
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    command = "dokku --quiet global-cert:set {0} {1}".format(data["cert"], data["key"])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def main():
    fields = {
        "key": {"required": False, "type": "str"},
        "cert": {"required": False, "type": "str"},
        "state": {
            "required": False,
            "default": "present",
            "choices": ["present", "absent"],
            "type": "str",
        },
    }
    choice_map = {
        "present": dokku_global_cert_present,
        "absent": dokku_global_cert_absent,
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
