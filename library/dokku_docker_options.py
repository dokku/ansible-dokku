#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output
import pipes
import subprocess
import re

DOCUMENTATION = """
---
module: dokku_docker_options
short_description: Manage docker-options for a given dokku application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  option:
    description:
      - A single docker option
    required: True
    default: null
    aliases: []
  phase:
    description:
      - The phase in which to set the options
    required: False
    default: null
    choices: [ "build", "deploy", "run" ]
    aliases: []
  state:
    description:
      - The state of the docker options
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Jose Diaz-Gonzalez
requirements: [ ]
"""

EXAMPLES = """
- name: docker-options:add hello-world deploy
  dokku_docker_options:
    app: hello-world
    phase: deploy
    option: "-v /var/run/docker.sock:/var/run/docker.sock"

- name: docker-options:remove hello-world deploy
  dokku_docker_options:
    app: hello-world
    phase: deploy
    option: "-v /var/run/docker.sock:/var/run/docker.sock"
    state: absent
"""


def dokku_docker_options(data):
    options = {"build": "", "deploy": "", "run": ""}
    command = "dokku --quiet docker-options:report {0}".format(data["app"])
    output, error = subprocess_check_output(command)
    if error is None:
        for line in output:
            match = re.match(
                "Docker options (?P<type>build|deploy|run):(?P<options>.+)",
                line.strip(),
            )
            if match:
                options[match.group("type")] = match.group("options").strip()
    return options, error


def dokku_docker_options_absent(data):
    is_error = True
    has_changed = False
    meta = {"present": True}

    existing, error = dokku_docker_options(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    if data["option"] not in existing[data["phase"]]:
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    command = "dokku --quiet docker-options:remove {0} {1} {2}".format(
        data["app"], data["phase"], pipes.quote(data["option"])
    )
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = False
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_docker_options_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    existing, error = dokku_docker_options(data)
    if error:
        meta["error"] = error
        return (is_error, has_changed, meta)

    if data["option"] in existing[data["phase"]]:
        is_error = False
        meta["present"] = True
        return (is_error, has_changed, meta)

    command = "dokku --quiet docker-options:add {0} {1} {2}".format(
        data["app"], data["phase"], pipes.quote(data["option"])
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
        "state": {
            "required": False,
            "default": "present",
            "choices": ["present", "absent"],
            "type": "str",
        },
        "phase": {
            "required": True,
            "choices": ["build", "deploy", "run"],
            "type": "str",
        },
        "option": {"required": True, "type": "str"},
    }
    choice_map = {
        "present": dokku_docker_options_present,
        "absent": dokku_docker_options_absent,
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
