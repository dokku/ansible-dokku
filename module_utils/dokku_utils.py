#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Utility functions for the dokku library"""
import subprocess
import re
from typing import Tuple


def force_list(var):
    if isinstance(var, list):
        return var
    return list(var)


# Add an option to redirect stderr to stdout, because some dokku commands output to stderr
def subprocess_check_output(command, split="\n", redirect_stderr=False):
    error = None
    output = []
    try:
        if redirect_stderr:
            output = subprocess.check_output(
                command, shell=True, stderr=subprocess.STDOUT
            )
        else:
            output = subprocess.check_output(command, shell=True)
        if isinstance(output, bytes):
            output = output.decode("utf-8")
        output = str(output).rstrip("\n")
        if split is None:
            return output, error
        output = output.split(split)
        output = force_list(filter(None, output))
        output = [o.strip() for o in output]
    except subprocess.CalledProcessError as e:
        error = str(e)
    return output, error


# Get the version of dokku installed
# Example: (0, 31, 4)
def get_dokku_version() -> Tuple[int, int, int]:
    command = "dokku --version"
    output = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)
    pattern = r"\d+\.\d+\.\d+"
    match = re.search(pattern, output.stdout)
    if match is None:
        raise ValueError("Could not find Dokku version in command output.")
    version_data = match.group().split(".")
    version = tuple(map(int, version_data))
    return version
