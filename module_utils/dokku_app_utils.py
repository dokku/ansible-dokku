#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess


def dokku_apps_exists(app):
    exists = False
    error = None
    command = "dokku --quiet apps:exists {0}".format(app)
    try:
        subprocess.check_call(command, shell=True)
        exists = True
    except subprocess.CalledProcessError as e:
        error = str(e)
    return exists, error


def dokku_app_present(data):
    """Create app if it does not exist."""
    is_error = True
    has_changed = False
    meta = {"present": False}

    exists, error = dokku_apps_exists(data["app"])
    if exists:
        is_error = False
        meta["present"] = True
        return (is_error, has_changed, meta)

    command = "dokku apps:create {0}".format(data["app"])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = True
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)


def dokku_app_absent(data=None):
    """Remove app if it exists."""
    is_error = True
    has_changed = False
    meta = {"present": True}

    exists, error = dokku_apps_exists(data["app"])
    if not exists:
        is_error = False
        meta["present"] = False
        return (is_error, has_changed, meta)

    command = "dokku --force apps:destroy {0}".format(data["app"])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta["present"] = False
    except subprocess.CalledProcessError as e:
        meta["error"] = str(e)

    return (is_error, has_changed, meta)
