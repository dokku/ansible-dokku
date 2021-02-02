#!/usr/bin/python
# -*- coding: utf-8 -*-
# from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
import os
import subprocess


DOCUMENTATION = """
---
module: dokku_clone
short_description: Deploys a repository to an undeployed application.
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  repository:
    description:
      - Git repository url
    required: True
    default: null
    aliases: []
  version:
    description:
      - Git tree (tag or branch name). If not provided, default branch is used.
    required: False
    default: null
    aliases: []
  build:
    description:
      - Whether to build the app (only when repository changes)
    required: False
    default: True
    aliases: []
author: Jose Diaz-Gonzalez
"""

EXAMPLES = """
- name: clone a git repository
  dokku_clone:
    app: hello-world
    repository: https://github.com/hello-world/hello-world.git
- name: clone specific tag of a git repository
  dokku_clone:
    app: hello-world
    repository: https://github.com/hello-world/hello-world.git
"""


def get_state(b_path):
    """ Find out current state """

    if os.path.lexists(b_path):
        if os.path.islink(b_path):
            return "link"
        elif os.path.isdir(b_path):
            return "directory"
        elif os.stat(b_path).st_nlink > 1:
            return "hard"
        # could be many other things, but defaulting to file
        return "file"

    return "absent"


def dokku_clone(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    index_state = get_state("/home/dokku/{0}/HEAD".format(data["app"]))
    if index_state == "file":
        is_error = False
        meta["present"] = True
        return (is_error, has_changed, meta)

    if index_state != "absent":
        meta["error"] = "git HEAD for app {0} is of file type {1}".format(
            data["app"], index_state
        )
        return (is_error, has_changed, meta)

    command = "dokku git:sync"
    if data["build"]:
        command += " --build"

    command += " {app} {repository}".format(
        app=data["app"], repository=data["repository"]
    )

    if data["version"]:
        command += command + " {version}".format(version=data["version"])

    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        is_error = True
        meta["error"] = e.output

    return (is_error, has_changed, meta)


def main():
    fields = {
        "app": {"required": True, "type": "str"},
        "repository": {"required": True, "type": "str"},
        "version": {"required": False, "type": "str"},
        "build": {"required": False, "type": "bool"},
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_clone(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
