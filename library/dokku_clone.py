#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_app import dokku_app_ensure_present
from ansible.module_utils.dokku_git import dokku_git_sha

DOCUMENTATION = """
---
module: dokku_clone
short_description: Clone a git repository and deploy app.
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
      - Whether to build the app after cloning.
    required: False
    default: true
    aliases: []
author: Jose Diaz-Gonzalez
"""

EXAMPLES = """

- name: clone a git repository and build app
  dokku_clone:
      app: example-app
      repository: https://github.com/heroku/node-js-getting-started
      version: b10a4d7a20a6bbe49655769c526a2b424e0e5d0b
- name: clone specific tag from git repository and build app
  dokku_clone:
      app: example-app
      repository: https://github.com/heroku/node-js-getting-started
      version: b10a4d7a20a6bbe49655769c526a2b424e0e5d0b
- name: sync git repository without building app
  dokku_clone:
      app: example-app
      repository: https://github.com/heroku/node-js-getting-started
      build: false
"""


def dokku_clone(data):

    # create app (if not exists)
    is_error, has_changed, meta = dokku_app_ensure_present(data)
    meta["present"] = False  # meaning: requested *version* of app is present
    if is_error:
        return (is_error, has_changed, meta)

    sha_old = dokku_git_sha(data["app"])

    # sync with remote repository
    command_git_sync = "dokku git:sync {app} {repository}".format(
        app=data["app"], repository=data["repository"]
    )
    if data["version"]:
        command_git_sync += " {version}".format(version=data["version"])
    if data["build"]:
        command_git_sync += " --build"
    try:
        subprocess.check_output(command_git_sync, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        is_error = True
        if "is not a dokku command" in str(e.output):
            meta["error"] = (
                "Please upgrade to dokku>=0.23.0 in order to use the 'git:sync' command."
            )
        else:
            meta["error"] = str(e.output)
        return (is_error, has_changed, meta)
    finally:
        meta["present"] = True  # meaning: requested *version* of app is present

    if data["build"] or dokku_git_sha(data["app"]) != sha_old:
        has_changed = True

    return (is_error, has_changed, meta)


def main():
    fields = {
        "app": {"required": True, "type": "str"},
        "repository": {"required": True, "type": "str"},
        "version": {"required": False, "type": "str"},
        "build": {"default": True, "required": False, "type": "bool"},
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_clone(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
