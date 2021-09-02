#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output
import json
import pipes
import subprocess

try:
    basestring
except NameError:
    basestring = str


DOCUMENTATION = """
---
module: dokku_config
short_description: Manage environment variables for a given dokku application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  config:
    description:
      - A map of environment variables where key => value
    required: True
    default: {}
    aliases: []
  restart:
    description:
      - Whether to restart the application or not. If the task is idempotent
        then setting restart to true will not perform a restart.
    required: false
    default: true
author: Jose Diaz-Gonzalez
requirements: [ ]
"""

EXAMPLES = """
- name: set KEY=VALUE
  dokku_config:
    app: hello-world
    config:
      KEY: VALUE_1
      KEY_2: VALUE_2

- name: set KEY=VALUE without restart
  dokku_config:
    app: hello-world
    restart: false
    config:
      KEY: VALUE_1
      KEY_2: VALUE_2
"""


def dokku_config(app):
    command = "dokku config:export --format json {0}".format(app)
    output, error = subprocess_check_output(command, split=None)

    if error is None:
        try:
            output = json.loads(output)
        except ValueError as e:
            error = str(e)

    return output, error


def dokku_config_set(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    values = []
    invalid_values = []
    existing, error = dokku_config(data["app"])
    for key, value in data["config"].items():
        if not isinstance(value, basestring):
            invalid_values.append(key)
            continue

        if value == existing.get(key, None):
            continue
        values.append("{0}={1}".format(key, pipes.quote(value)))

    if invalid_values:
        template = "All values must be strings, found invalid types for {0}"
        meta["error"] = template.format(", ".join(invalid_values))
        return (is_error, has_changed, meta)

    if len(values) == 0:
        is_error = False
        has_changed = False
        return (is_error, has_changed, meta)

    command = "dokku config:set {0}{1} {2}".format(
        "--no-restart " if data["restart"] is False else "",
        data["app"],
        " ".join(values),
    )

    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def main():
    fields = {
        "app": {"required": True, "type": "str"},
        "config": {"required": True, "type": "dict", "no_log": True},
        "restart": {"required": False, "type": "bool"},
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_config_set(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
