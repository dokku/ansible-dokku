#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
import subprocess

DOCUMENTATION = """
---
module: dokku_proxy
short_description: Enable or disable the proxy for a dokku app
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  state:
    description:
      - The state of the proxy
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Jose Diaz-Gonzalez
requirements: [ ]
"""

EXAMPLES = """
- name: Enable the default proxy
  dokku_proxy:
    app: hello-world

- name: Disable the default proxy
  dokku_proxy:
    app: hello-world
    state: absent
"""


def force_list(var):
    if isinstance(var, list):
        return var
    return list(var)


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


def dokku_proxy(data):
    command = "dokku --quiet config:get {0} DOKKU_DISABLE_PROXY"
    response, error = subprocess_check_output(command.format(data["app"]))
    if error:
        return "0", error
    return response[0], error


def dokku_proxy_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    disabled, error = dokku_proxy(data)
    if disabled == "0":
        is_error = False
        meta["present"] = True
        return (is_error, has_changed, meta)

    command = "dokku --quiet proxy:enable {0}".format(data["app"])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_proxy_absent(data=None):
    is_error = True
    has_changed = False
    meta = {"present": True}

    disabled, error = dokku_proxy(data)
    if disabled == "1":
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    command = "dokku --force proxy:disable {0}".format(data["app"])
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
        "present": dokku_proxy_present,
        "absent": dokku_proxy_absent,
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
