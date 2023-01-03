#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
import subprocess

DOCUMENTATION = """
---
module: dokku_service_create
short_description: Creates a given service
options:
  name:
    description:
      - The name of the service
    required: True
    default: null
    aliases: []
  service:
    description:
      - The type of service to create
    required: True
    default: null
    aliases: []
author: Jose Diaz-Gonzalez
requirements: [ ]
"""

EXAMPLES = """
- name: redis:create default
  dokku_service_create:
    name: default
    service: redis

- name: postgres:create default
  dokku_service_create:
    name: default
    service: postgres

- name: postgres:create default with custom image
  environment:
    POSTGRES_IMAGE: postgis/postgis
    POSTGRES_IMAGE_VERSION: 13-master
  dokku_service_create:
    name: default
    service: postgres

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


def dokku_service_create(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    exists, error = dokku_service_exists(data["service"], data["name"])
    if exists:
        is_error = False
        meta["present"] = True
        return (is_error, has_changed, meta)

    command = "dokku {0}:create {1}".format(data["service"], data["name"])
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
        "service": {"required": True, "type": "str"},
        "name": {"required": True, "type": "str"},
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_service_create(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
