#!/usr/bin/python
# -*- coding: utf-8 -*-
# from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
import subprocess

DOCUMENTATION = '''
---
module: dokku_app
short_description: Create or destroy dokku apps
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  state:
    description:
      - The state of the app
    required: False
    default: present
    choices: [ "present", "absent" ]
    aliases: []
modified by: Elliott Castillo
author: Jose Diaz-Gonzalez
requirements: [ ]
'''

EXAMPLES = '''
- name: Create a dokku app
  dokku_app:
    app: hello-world

- name: Delete the app
  dokku_app:
    app: hello-world
    state: absent
'''


def force_list(l):
    if isinstance(l, list):
        return l
    return list(l)


def dokku_apps_exists(app):
    exists = False
    error = None
    command = 'dokku --quiet apps:exists {0}'.format(app)
    try:
        subprocess.check_call(command, shell=True)
        exists = True
    except subprocess.CalledProcessError as e:
        error = str(e)
    return exists, error


def dokku_app_present(data):
    is_error = True
    has_changed = False
    meta = {'present': False}

    exists, error = dokku_apps_exists(data['app'])
    if exists:
        is_error = False
        meta['present'] = True
        return (is_error, has_changed, meta)

    command = 'dokku apps:create {0}'.format(data['app'])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta['present'] = True
    except subprocess.CalledProcessError as e:
        meta['error'] = str(e)

    return (is_error, has_changed, meta)


def dokku_app_absent(data=None):
    is_error = True
    has_changed = False
    meta = {"present": True}

    exists, error = dokku_apps_exists(data['app'])
    if not exists:
        is_error = False
        meta['present'] = False
        return (is_error, has_changed, meta)

    command = 'dokku --force apps:destroy {0}'.format(data['app'])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta['present'] = False
    except subprocess.CalledProcessError as e:
        meta['error'] = str(e)

    return (is_error, has_changed, meta)


def dokku_app_rename(data):
    is_error = True
    has_changed = False
    meta = {'present': False}

    exists, error = dokku_apps_exists(data['app'])
    rename_exists, error2 = dokku_apps_exists(data['rename'])
    if rename_exists:
        meta['error'] = "The name {0} is already taken by an existing app. Cannot continue.".format(data['rename'])
    elif exists:
        is_error = False
        meta['present'] = True

        command = 'dokku apps:rename {0} {1}'.format(data['app'], data['rename'])
        try:
            subprocess.check_call(command, shell=True)
            is_error = False
            has_changed = True
            meta['present'] = True
        except subprocess.CalledProcessError as e:
            meta['error'] = str(e)
    else:
        meta['error'] = "The app named {0} does not exist. Cannot rename it".format(data['app'])

    return (is_error, has_changed, meta)


def dokku_app_clone(data):
    is_error = True
    has_changed = False
    meta = {'present': False}

    exists, error = dokku_apps_exists(data['app'])
    clone_name_exists, error2 = dokku_apps_exists(data['clone'])
    if not clone_name_exists: # if the app that should be used to clone does not exist error out
        meta['error'] = "The app {0} does not currently exist. Cannot clone.".format(data['clone'])
    elif exists: # if the app you want to create already exists do no-op
        is_error = False
        meta['present'] = True
        return (is_error, has_changed, meta)
    else:
        is_error = False
        meta['present'] = True

        command = 'dokku apps:clone {0} {1}'.format(data['clone'], data['app'])
        try:
            subprocess.check_call(command, shell=True)
            is_error = False
            has_changed = True
            meta['present'] = True
        except subprocess.CalledProcessError as e:
            meta['error'] = str(e)

    return (is_error, has_changed, meta)


def main():
    fields = {
        'app': {
            'required': True,
            'type': 'str',
        },
        'state': {
            'required': False,
            'default': 'present',
            'choices': [
                'present',
                'absent'
            ],
            'type': 'str',
        },
        'rename': {
            'required': False,
            'type': 'str',
            'default': '',
        },
        'clone': {
            'required': False,
            'type': 'str',
            'default': '',
        },

    }
    choice_map = {
        'present': dokku_app_present,
        'absent': dokku_app_absent,
    }

    module = AnsibleModule(
        argument_spec=fields,
        supports_check_mode=False
    )

    is_error = False
    
    has_changed = False
    has_changed1 = False
    has_changed2 = False
    has_changed3 = False

    result = {}
    result1 = {}
    result2 = {}
    result3 = {}

    if (not module.params['rename'] == '' or not module.params['clone'] == '') and module.params['state'] == 'absent':
        module.fail_json(msg="cannot delete the app and (rename or clone it) at the same time", meta="yoyoma")
    elif not module.params['rename'] == '' and not module.params['clone'] == '':
        module.fail_json(msg="cannot have both rename and clone enabled at the same time", meta="yoyo")
    elif not module.params['rename'] == '': # app rename function
        is_error, has_changed2, result2 = dokku_app_rename(module.params)
        if is_error:
            module.fail_json(msg=result2['error'], meta=result2)
    elif not module.params['clone'] == '': # app clone function
        is_error, has_changed3, result3 = dokku_app_clone(module.params)
        if is_error:
            module.fail_json(msg=result3['error'], meta=result3)
    else: # app create or app destroy functions
        is_error, has_changed1, result1 = choice_map.get(
        module.params['state'])(module.params)
        if is_error:
            module.fail_json(msg=result['error'], meta=result)
    
    has_changed = True if has_changed1 or has_changed2 or has_changed3 else False
    module.exit_json(changed=has_changed, result_create_delete=result1, result_rename=result2, result_clone=result3)


if __name__ == '__main__':
    main()
