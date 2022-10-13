#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output
import pipes
import re
import subprocess

DOCUMENTATION = """
---
module: dokku_ports
short_description: Manage ports for a given dokku application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  mappings:
    description:
      - A list of port mappings
    required: True
    default: null
    aliases: []
  state:
    description:
      - The state of the port mappings
    required: False
    default: present
    choices: [ "clear", "present", "absent" ]
    aliases: []
author: Jose Diaz-Gonzalez
requirements: [ ]
"""

EXAMPLES = """
- name: proxy:ports-set hello-world http:80:80
  dokku_ports:
    app: hello-world
    mappings:
        - http:80:8080

- name: proxy:ports-remove hello-world http:80:80
  dokku_ports:
    app: hello-world
    mappings:
        - http:80:8080
    state: absent

- name: proxy:ports-clear hello-world
  dokku_ports:
    app: hello-world
    state: clear
"""


def dokku_proxy_port_mappings(data):
    mappings = []
    command = "dokku --quiet proxy:report {0}".format(data["app"])
    output, error = subprocess_check_output(command)
    if error is None:
        for line in output:
            match = re.match("Proxy port map:(?P<mapping>.+)", line.strip())
            if match:
                mappings = match.group("mapping").strip().split(" ")
    return mappings, error


def dokku_proxy_ports_absent(data):
    is_error = True
    has_changed = False
    meta = {"present": True}

    if "mappings" not in data:
        meta["error"] = "missing required arguments: mappings"
        return (is_error, has_changed, meta)

    existing, error = dokku_proxy_port_mappings(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    to_remove = [m for m in data["mappings"] if m in existing]
    to_remove = [pipes.quote(m) for m in to_remove]

    if len(to_remove) == 0:
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    command = "dokku --quiet proxy:ports-remove {0} {1}".format(
        data["app"], " ".join(to_remove)
    )
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = False
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_proxy_ports_clear(data):
    is_error = True
    has_changed = False
    meta = {"present": True}

    command = "dokku --quiet proxy:ports-clear {0}".format(data["app"])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = False
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_proxy_ports_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    if "mappings" not in data:
        meta["error"] = "missing required arguments: mappings"
        return (is_error, has_changed, meta)

    existing, error = dokku_proxy_port_mappings(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    to_add = [m for m in data["mappings"] if m not in existing]
    to_set = [pipes.quote(m) for m in data["mappings"]]

    if len(to_add) == 0:
        is_error = False
        meta["present"] = True
        return (is_error, has_changed, meta)

    command = "dokku --quiet proxy:ports-set {0} {1}".format(
        data["app"], " ".join(to_set)
    )
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
        "app": {"required": True, "type": "str"},
        "mappings": {"required": False, "type": "list"},
        "state": {
            "required": False,
            "default": "present",
            "choices": ["absent", "clear", "present"],
            "type": "str",
        },
    }
    choice_map = {
        "absent": dokku_proxy_ports_absent,
        "clear": dokku_proxy_ports_clear,
        "present": dokku_proxy_ports_present,
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
