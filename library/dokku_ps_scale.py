#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output
import subprocess
import re

DOCUMENTATION = """
---
module: dokku_ps_scale
short_description: Manage process scaling for a given dokku application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  scale:
    description:
      - A map of scale values where proctype => qty
    required: True
    default: {}
    aliases: []
  skip_deploy:
    description:
      - Whether to skip the corresponding deploy or not. If the task is idempotent
        then leaving skip_deploy as false will not trigger a deploy.
    required: false
    default: false
author: Gavin Ballard
requirements: [ ]
"""

EXAMPLES = """
- name: scale web and worker processes
  dokku_ps_scale:
    app: hello-world
    scale:
      web: 4
      worker: 4

- name: scale web and worker processes without deploy
  dokku_ps_scale:
    app: hello-world
    skip_deploy: true
    scale:
      web: 4
      worker: 4
"""


def dokku_ps_scale(data):
    command = "dokku --quiet ps:scale {0}".format(data["app"])
    output, error = subprocess_check_output(command)

    if error is not None:
        return output, error

    # strip all spaces from output lines
    output = [re.sub(r"\s+", "", line) for line in output]

    scale = {}
    for line in output:
        if ":" not in line:
            continue
        proctype, qty = line.split(":", 1)
        scale[proctype] = int(qty)

    return scale, error


def dokku_ps_scale_set(data):
    is_error = True
    has_changed = False
    meta = {"present": False}

    proctypes_to_scale = []

    existing, error = dokku_ps_scale(data)

    for proctype, qty in data["scale"].items():
        if qty == existing.get(proctype, None):
            continue
        proctypes_to_scale.append("{0}={1}".format(proctype, qty))

    if len(proctypes_to_scale) == 0:
        is_error = False
        has_changed = False
        return (is_error, has_changed, meta)

    command = "dokku ps:scale {0}{1} {2}".format(
        "--skip-deploy " if data["skip_deploy"] is True else "",
        data["app"],
        " ".join(proctypes_to_scale),
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
        "scale": {"required": True, "type": "dict", "no_log": True},
        "skip_deploy": {"required": False, "type": "bool"},
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=False)
    is_error, has_changed, result = dokku_ps_scale_set(module.params)

    if is_error:
        module.fail_json(msg=result["error"], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == "__main__":
    main()
