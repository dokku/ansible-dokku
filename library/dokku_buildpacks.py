#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output
from shlex import quote as shell_escape
from typing import TypedDict

DOCUMENTATION = """
---
module: dokku_buildpacks
short_description: Manage buildpack settings for a given dokku application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  buildpacks:
    description:
      - A list of buildpacks to set on the app
    required: True
    default: null
    aliases: []
author: Andrew Kvalheim
requirements: [ ]
"""

EXAMPLES = """
- name: buildpacks:add hello-world […], buildpacks:add hello-world […]
  dokku_buildpacks:
    app: hello-world
    buildpacks:
      - https://github.com/heroku/heroku-buildpack-ruby.git
      - https://github.com/heroku/heroku-buildpack-nodejs.git

- name: buildpacks:clear hello-world
  dokku_buildpacks:
    app: hello-world
    buildpacks: []
"""

Diff = TypedDict("Diff", {"before": str, "after": str})
Params = TypedDict("Params", {"app": str, "buildpacks": list[str]})


def dokku_buildpacks(
    params: Params, check_mode: bool
) -> tuple[str, None] | tuple[None, None | Diff]:
    app, expected = params["app"], params["buildpacks"]

    error, actual = dokku_buildpacks_list(app)
    if error is not None:
        return error, None

    if actual == expected:
        return None, None

    # OPTIMIZE: Instead of clearing and reconstructing the entire list, use
    # indexed add/set/remove to only change entries as necessary.
    if actual:
        if not check_mode:
            error = dokku_buildpacks_clear(app)
            if error is not None:
                return error, None
    for buildpack in expected:
        if not check_mode:
            error = dokku_buildpacks_add(app, buildpack)
            if error is not None:
                return error, None

    return None, {"before": "\n".join(actual), "after": "\n".join(expected)}


def dokku_buildpacks_add(app: str, buildpack: str) -> None | str:
    command = "dokku --quiet buildpacks:add {} {}".format(
        shell_escape(app), shell_escape(buildpack)
    )

    _, error = subprocess_check_output(command)

    return error


def dokku_buildpacks_clear(app: str) -> None | str:
    command = "dokku --quiet buildpacks:clear {}".format(shell_escape(app))

    _, error = subprocess_check_output(command)

    return error


def dokku_buildpacks_list(app: str) -> tuple[str, None] | tuple[None, list[str]]:
    command = "dokku --quiet buildpacks:list {}".format(shell_escape(app))

    lines, error = subprocess_check_output(command)
    if error is not None:
        return error, None

    buildpacks = lines

    return None, buildpacks


def main():
    argument_spec = {
        "app": {"required": True, "type": "str"},
        "buildpacks": {"required": True, "type": "list"},
    }
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    error, diff = dokku_buildpacks(module.params, module.check_mode)
    if error is not None:
        module.fail_json(error)

    module.exit_json(changed=diff is not None, diff=diff)


if __name__ == "__main__":
    main()
