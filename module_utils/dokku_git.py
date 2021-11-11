#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Utility functions for dokku git related plugins"""
import subprocess


def dokku_git_sha(app):
    """Get SHA of current app repository.

    Returns `None` if app does not exist.
    """
    command_git_report = "dokku git:report {app} --git-sha".format(app=app)
    try:
        sha = subprocess.check_output(
            command_git_report, stderr=subprocess.STDOUT, shell=True
        )
    except subprocess.CalledProcessError:
        sha = None

    return sha
