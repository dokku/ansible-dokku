#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_app import dokku_apps_exists
import subprocess

DOCUMENTATION = """
---
module: dokku_service_link
short_description: Links and unlinks a given service to an application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  name:
    description:
      - The name of the service
    required: True
    default: null
    aliases: []
  service:
    description:
      - The type of service to link
    required: True
    default: null
    aliases: []
  state:
    description:
      - The state of the service link
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
author: Jose Diaz-Gonzalez
requirements: [ ]
"""

EXAMPLES = """
- name: redis:link default hello-world
  dokku_service_link:
    app: hello-world
    name: default
    service: redis

- name: postgres:link default hello-world
  dokku_service_link:
    app: hello-world
    name: default
    service: postgres

- name: redis:unlink default hello-world
  dokku_service_link:
    app: hello-world
    name: default
    service: redis
    state: absent
"""


def dokku_service_exists(service, name):
    exists = False
    error = None
    command = "dokku --quiet {0}:exists {1}".format(service, name)
    try:
        subprocess.check_call(command, shell=True)
        exists = True
    except subprocess.CalledProcessError as e:
        error = str(e)
    return exists, error


def dokku_service_linked(service, name, app):
    linked = False
    error = None
    command = "dokku --quiet {0}:linked {1} {2}".format(service, name, app)
    try:
        subprocess.check_call(command, shell=True)
        linked = True
    except subprocess.CalledProcessError as e:
        error = str(e)
    return linked, error


def dokku_service_link_absent(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    exists, error = dokku_service_exists(data["service"], data["name"])
    if not exists:
        meta["error"] = error
        return (is_error, has_changed, meta)

    app_exists, error = dokku_apps_exists(data["app"])
    if not app_exists:
        meta["error"] = error
        return (is_error, has_changed, meta)

    linked, error = dokku_service_linked(data["service"], data["name"], data["app"])
    if not linked:
        is_error = False
        return (is_error, has_changed, meta)

    command = "dokku --quiet {0}:unlink {1} {2}".format(
        data["service"], data["name"], data["app"]
    )
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_service_link_present(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    exists, error = dokku_service_exists(data["service"], data["name"])
    if not exists:
        meta["error"] = error
        return (is_error, has_changed, meta)

    app_exists, error = dokku_apps_exists(data["app"])
    if not app_exists:
        meta["error"] = error
        return (is_error, has_changed, meta)

    linked, error = dokku_service_linked(data["service"], data["name"], data["app"])
    if linked:
        is_error = False
        return (is_error, has_changed, meta)

    command = "dokku --quiet {0}:link {1} {2}".format(
        data["service"], data["name"], data["app"]
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
        "name": {"required": True, "type": "str"},
        "service": {"required": True, "type": "str"},
        "state": {
            "required": False,
            "default": "present",
            "choices": ["present", "absent"],
            "type": "str",
        },
    }
    choice_map = {
        "present": dokku_service_link_present,
        "absent": dokku_service_link_absent,
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
