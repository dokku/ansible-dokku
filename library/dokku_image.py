#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_app import dokku_app_ensure_present
from ansible.module_utils.dokku_git import dokku_git_sha

DOCUMENTATION = """
---
module: dokku_image
short_description: Pull Docker image and deploy app
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  image:
    description:
      - Docker image
    required: True
    default: null
    aliases: []
  user_name:
    description:
      - Git user.name for customizing the author's name
    required: False
    default: null
    aliases: []
  user_email:
    description:
      - Git user.email for customizing the author's email
    required: False
    default: null
    aliases: []
  build_dir:
    description:
      - Specify custom build directory for a custom build context
    required: False
    default: null
    aliases: []
author: Simo Aleksandrov
"""

EXAMPLES = """
- name: Pull and deploy meilisearch
  dokku_image:
      app: meilisearch
      image: getmeili/meilisearch:v0.24.0rc1
- name: Pull and deploy image with custom author
  dokku_image:
      app: hello-world
      user_name: Elliot Alderson
      user_email: elliotalderson@protonmail.ch
      image: hello-world:latest
- name: Pull and deploy image with custom build dir
  dokku_image:
      app: hello-world
      build_dir: /path/to/build
      image: hello-world:latest
"""


def dokku_image(data):
    # create app (if not exists)
    is_error, has_changed, meta = dokku_app_ensure_present(data)
    meta["present"] = False  # meaning: requested *version* of app is present
    if is_error:
        return (is_error, has_changed, meta)

    sha_old = dokku_git_sha(data["app"])

    # get image
    command_git_from_image = "dokku git:from-image {app} {image}".format(
        app=data["app"], image=data["image"]
    )
    if data["user_name"]:
        command_git_from_image += " {user_name}".format(user_name=data["user_name"])
    if data["user_email"]:
        command_git_from_image += " {user_email}".format(user_email=data["user_email"])
    if data["build_dir"]:
        command_git_from_image += ' --build-dir "{build_dir}"'.format(
            build_dir=data["build_dir"]
        )
    try:
        subprocess.check_output(
            command_git_from_image, stderr=subprocess.STDOUT, shell=True
        )
    except subprocess.CalledProcessError as e:
        is_error = True
        if "is not a dokku command" in str(e.output):
            meta["error"] = (
                "Please upgrade to dokku>=0.24.0 in order to use the 'git:from-image' command."
            )
        elif "No changes detected, skipping git commit" in str(e.output):
            is_error = False
            has_changed = False
        else:
            meta["error"] = str(e.output)
        return (is_error, has_changed, meta)
    finally:
        meta["present"] = True  # meaning: requested *version* of app is present

    if dokku_git_sha(data["app"]) != sha_old:
        has_changed = True

    return (is_error, has_changed, meta)


def main():
    fields = {
        "app": {"required": True, "type": "str"},
        "image": {"required": True, "type": "str"},
        "user_name": {"required": False, "type": "str"},
        "user_email": {"required": False, "type": "str"},
        "build_dir": {"required": False, "type": "str"},
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_image(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
