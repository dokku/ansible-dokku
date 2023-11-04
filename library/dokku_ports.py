#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output, get_dokku_version
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
- name: ports:set hello-world http:80:80
  dokku_ports:
    app: hello-world
    mappings:
        - http:80:8080

- name: ports:remove hello-world http:80:80
  dokku_ports:
    app: hello-world
    mappings:
        - http:80:8080
    state: absent

- name: ports:clear hello-world
  dokku_ports:
    app: hello-world
    state: clear
"""


def dokku_proxy_port_mappings(data):
    mappings = []

    if use_legacy_command():
        command = "dokku --quiet proxy:report {0}".format(data["app"])
    else:
        command = "dokku --quiet ports:report {0} --ports-map".format(data["app"])

    output, error = subprocess_check_output(command)
    if error is None:
        if use_legacy_command():
            for line in output:
                match = re.match("Proxy port map:(?P<mapping>.+)", line.strip())
                if match:
                    mappings = match.group("mapping").strip().split(" ")
        else:
            if output:
                mappings = output[0].strip().split(" ")

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

    if use_legacy_command():
        subcommand = "proxy:ports-remove"
    else:
        subcommand = "ports:remove"

    command = "dokku --quiet {0} {1} {2}".format(
        subcommand, data["app"], " ".join(to_remove)
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

    if use_legacy_command():
        subcommand = "proxy:ports-clear"
    else:
        subcommand = "ports:clear"

    command = "dokku --quiet {0} {1}".format(subcommand, data["app"])
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

    if use_legacy_command():
        subcommand = "proxy:ports-set"
    else:
        subcommand = "ports:set"

    command = "dokku {0} {1} {2}".format(subcommand, data["app"], " ".join(to_set))
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def use_legacy_command() -> bool:
    """
    The commands for managing ports changed with dokku version 0.31.0.
    Use the legacy commands if the installed version of dokku is older than that.

    https://github.com/dokku/dokku/blob/master/docs/networking/port-management.md#port-management
    """
    dokku_version = get_dokku_version()
    return dokku_version < (0, 31, 0)


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
