#!/usr/bin/python
# -*- coding: utf-8 -*-
# from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_app import (
    dokku_app_present,
)
import subprocess


DOCUMENTATION = """
---
module: dokku_clone
short_description: Clone repository and deploy app.
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


def dokku_git_sha(data):
    """Get SHA of current app repository.

    Returns `None` if app does not exist.
    """
    command_git_report = "dokku git:report {app} --git-sha".format(app=data["app"])
    try:
        sha = subprocess.check_output(
            command_git_report, stderr=subprocess.STDOUT, shell=True
        )
    except subprocess.CalledProcessError:
        sha = None

    return sha


def dokku_clone(data):

    # create app (if not exists)
    is_error, has_changed, meta = dokku_app_present(data)
    meta[
        "present"
    ] = False  # should indicate that requested *version* of app is present
    if is_error:
        return (is_error, has_changed, meta)

    sha_old = dokku_git_sha(data)

    # sync with remote repository
    command_git_sync = "dokku git:sync {app} {repository}".format(
        app=data["app"], repository=data["repository"]
    )
    if data["version"]:
        command_git_sync += command_git_sync + " {version}".format(
            version=data["version"]
        )
    try:
        subprocess.check_output(command_git_sync, stderr=subprocess.STDOUT, shell=True)
        is_error = False
    except subprocess.CalledProcessError as e:
        is_error = True
        meta["error"] = e.output
        return (is_error, has_changed, meta)

    sha_new = dokku_git_sha(data)
    if sha_new == sha_old:
        meta["present"] = True
        return (is_error, has_changed, meta)
    else:
        has_changed = True

    # rebuild app
    command_ps_rebuild = "dokku ps:rebuild {app}".format(app=data["app"])
    try:
        subprocess.check_output(
            command_ps_rebuild, stderr=subprocess.STDOUT, shell=True
        )
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
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_clone(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
