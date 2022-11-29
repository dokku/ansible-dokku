#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dokku_utils import subprocess_check_output
import os
import pwd
import subprocess

DOCUMENTATION = """
---
module: dokku_storage
short_description: Manage storage for dokku applications
options:
  app:
    description:
      - The name of the app
    required: False
    default: null
    aliases: []
  create_host_dir:
    description:
      - Whether to create the host directory or not
    required: False
    default: False
    aliases: []
  group:
    description:
      - A group or gid that should own the created folder
    required: False
    default: 32767
    aliases: []
  mounts:
    description:
      - |
        A list of mounts to create, colon (:) delimited, in the format: `host_dir:container_dir`
    required: False
    default: []
    aliases: []
  user:
    description:
      - A user or uid that should own the created folder
    required: False
    default: 32767
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
- name: mount a path
  dokku_storage:
    app: hello-world
    mounts:
      - /var/lib/dokku/data/storage/hello-world:/data

- name: mount a path and create the host_dir directory
  dokku_storage:
    app: hello-world
    mounts:
      - /var/lib/dokku/data/storage/hello-world:/data
    create_host_dir: true

- name: unmount a path
  dokku_storage:
    app: hello-world
    mounts:
      - /var/lib/dokku/data/storage/hello-world:/data
    state: absent

- name: unmount a path and destroy the host_dir directory (and contents)
  dokku_storage:
    app: hello-world
    mounts:
      - /var/lib/dokku/data/storage/hello-world:/data
    destroy_host_dir: true
    state: absent
"""


def get_gid(group):
    gid = group
    try:
        gid = int(group)
    except ValueError:
        gid = pwd.getpwnam(group).pw_gid
    return gid


def get_state(b_path):
    """Find out current state"""

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


def get_uid(user):
    uid = user
    try:
        uid = int(user)
    except ValueError:
        uid = pwd.getpwnam(user).pw_uid
    return uid


def dokku_storage_list(data):
    command = "dokku --quiet storage:list {0}".format(data["app"])
    return subprocess_check_output(command)


def dokku_storage_mount_exists(data):
    state = get_state("/home/dokku/{0}".format(data["app"]))

    if state not in ["directory", "file"]:
        error = "app {0} does not exist".format(data["app"])
        return False, error

    output, error = dokku_storage_list(data)
    if error:
        return False, error

    mount = "{0}:{1}".format(data["host_dir"], data["container_dir"])
    if mount in output:
        return True, None

    return False, None


def dokku_storage_create_dir(data, is_error, has_changed, meta):
    if not data["create_host_dir"]:
        return (is_error, has_changed, meta)

    old_state = get_state(data["host_dir"])
    if old_state not in ["absent", "directory"]:
        is_error = True
        meta["error"] = "host directory is {0}".format(old_state)
        return (is_error, has_changed, meta)

    try:
        if old_state == "absent":
            os.makedirs(data["host_dir"], 0o777)
        os.chmod(data["host_dir"], 0o777)
        uid = get_uid(data["user"])
        gid = get_gid(data["group"])
        os.chown(data["host_dir"], uid, gid)
    except OSError as exc:
        is_error = True
        meta["error"] = str(exc)
        return (is_error, has_changed, meta)

    if old_state != get_state(data["host_dir"]):
        has_changed = True

    return (is_error, has_changed, meta)


def dokku_storage_destroy_dir(data, is_error, has_changed, meta):
    if not data["destroy_host_dir"]:
        return (is_error, has_changed, meta)

    old_state = get_state(data["host_dir"])
    if old_state not in ["absent", "directory"]:
        is_error = True
        meta["error"] = "host directory is {0}".format(old_state)
        return (is_error, has_changed, meta)

    try:
        if old_state == "directory":
            os.rmdir(data["host_dir"])
    except OSError as exc:
        is_error = True
        meta["error"] = str(exc)
        return (is_error, has_changed, meta)

    if old_state != get_state(data["host_dir"]):
        has_changed = True

    return (is_error, has_changed, meta)


def dokku_storage_absent(data):
    is_error = False
    has_changed = False
    meta = {"present": False}

    mounts = data.get("mounts", []) or []
    if len(mounts) == 0:
        is_error = True
        meta["error"] = "missing required arguments: mounts"
        return (is_error, has_changed, meta)

    for mount in mounts:
        data["host_dir"], data["container_dir"] = mount.split(":", 1)
        is_error, has_changed, meta = dokku_storage_destroy_dir(
            data, is_error, has_changed, meta
        )

        if is_error:
            return (is_error, has_changed, meta)

        exists, error = dokku_storage_mount_exists(data)
        if error:
            is_error = True
            meta["error"] = error
            return (is_error, has_changed, meta)
        elif not exists:
            is_error = False
            continue

        command = "dokku --quiet storage:unmount {0} {1}:{2}".format(
            data["app"], data["host_dir"], data["container_dir"]
        )
        try:
            subprocess.check_call(command, shell=True)
            is_error = False
            has_changed = True
        except subprocess.CalledProcessError as e:
            is_error = True
            meta["error"] = str(e)
            meta["present"] = True

        if is_error:
            return (is_error, has_changed, meta)
    return (is_error, has_changed, meta)


def dokku_storage_present(data):
    is_error = False
    has_changed = False
    meta = {"present": False}

    mounts = data.get("mounts", []) or []
    if len(mounts) == 0:
        is_error = True
        meta["error"] = "missing required arguments: mounts"
        return (is_error, has_changed, meta)

    for mount in mounts:
        data["host_dir"], data["container_dir"] = mount.split(":", 1)
        is_error, has_changed, meta = dokku_storage_create_dir(
            data, is_error, has_changed, meta
        )

        if is_error:
            return (is_error, has_changed, meta)

        exists, error = dokku_storage_mount_exists(data)
        if error:
            is_error = True
            meta["error"] = error
            return (is_error, has_changed, meta)
        elif exists:
            is_error = False
            continue

        command = "dokku --quiet storage:mount {0} {1}:{2}".format(
            data["app"], data["host_dir"], data["container_dir"]
        )
        try:
            subprocess.check_call(command, shell=True)
            is_error = False
            has_changed = True
            meta["present"] = True
        except subprocess.CalledProcessError as e:
            is_error = True
            meta["error"] = str(e)

        if is_error:
            return (is_error, has_changed, meta)
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
        "mounts": {"required": False, "type": "list", "default": []},
        "create_host_dir": {"required": False, "default": False, "type": "bool"},
        "destroy_host_dir": {"required": False, "default": False, "type": "bool"},
        "user": {"required": False, "default": "32767", "type": "str"},
        "group": {"required": False, "default": "32767", "type": "str"},
    }
    choice_map = {
        "present": dokku_storage_present,
        "absent": dokku_storage_absent,
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
