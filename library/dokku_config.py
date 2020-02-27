#!/usr/bin/python
# -*- coding: utf-8 -*-
# from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
import json
import pipes
import subprocess
import logging

try:
    basestring
except NameError:
    basestring = str


DOCUMENTATION = '''
---
module: dokku_config
short_description: Manage environment variables for a given dokku application
options:
  app:
    description:
      - The name of the app... if global envar, use: --global
    required: True
    default: null
    aliases: []
  restart:
    description:
      - True or False for restarting the app to restart after applying the envar
    required: False
    default: False
    aliases: []
  config:
    description:
      - A map of environment variables where key => value
    required: True
    default: {}
    aliases: []
  unset:
    description:
      - A list of envar KEYS to unset. If you put the KEY in CONFIG and in UNSET it applies the key and then unsets it resulting in a "changed" state
    required: False
    default: []
    aliases: []
author: Jose Diaz-Gonzalez
modified by: Elliott Castillo
requirements: [ ]
'''

EXAMPLES = '''
- name: set KEY=VALUE
  dokku_config:
    app: hello-world
    restart: "True"
    config:
      KEY: VALUE_1
      KEY_2: VALUE_2
    unset: ["KEY_3", "KEY_4", "KEY_5"]
'''


def force_list(l):
    if isinstance(l, list):
        return l
    return list(l)


def subprocess_check_output(command, split='\n'):
    error = None
    output = []
    try:
        output = subprocess.check_output(command, shell=True)
        if isinstance(output, bytes):
            output = output.decode("utf-8")
        output = str(output).rstrip('\n')
        if split is None:
            return output, error

        output = output.split(split)
        output = force_list(filter(None, output))
        output = [o.strip() for o in output]
    except subprocess.CalledProcessError as e:
        error = str(e)
    return output, error


def dokku_config(app):
    if app == '--global':
        command = 'dokku config:export --format json --global'
        output, error = subprocess_check_output(command, split=None)
    else:
        command = 'dokku config:export --format json {0}'.format(app)
        output, error = subprocess_check_output(command, split=None)

    if error is None:
        try:
            output = json.loads(output)
        except ValueError as e:
            error = str(e)
    # error = output
    return output, error


def dokku_config_set(data):
    is_error = True
    has_changed = False
    meta = {'present': False}
    meta = {'error1': None}
    options = []
    
    values = []
    invalid_values = []
    existing, error = dokku_config(data['app'])
    for key, value in data['config'].items():
        # if it's not a valid string or unicode string, add to invalid, skip
        if not isinstance(value, basestring):
            invalid_values.append(key)
            continue
        # if the value of the envar is unchanged, skip
        if value == existing.get(key, None):
            continue
        values.append('{0}={1}'.format(key, pipes.quote(value)))

    if invalid_values:
        template = 'All values must be keys, found invalid types for {0}'
        meta['error1'] = template.format(', '.join(invalid_values))
        return (is_error, has_changed, meta)

    if len(values) == 0:
        is_error = False
        has_changed = False
        return (is_error, has_changed, meta)
    
    if not data['restart']:
        options.append('--no-restart') 
    
    # you can further modify this to add other params such as "encoded" or other options in future dokku versions

    if data['app'] == '--global':
        command = 'dokku config:set {1} --global {0}'.format(' '.join(values), ' '.join(options))
    else:
        command = 'dokku config:set {2} {0} {1}'.format(data['app'], ' '.join(values), ' '.join(options))
    
    # config:set command execution
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
    except subprocess.CalledProcessError as e:
        meta['error1'] = str(e)

    return (is_error, has_changed, meta)

def dokku_config_unset(data):
    unset_values = []
    is_error = True
    has_changed = False
    meta = {'present': False}
    meta.update({'error2': None})
    options = []
    
    # get existing keys
    existing, error = dokku_config(data['app'])
    # config:unset command execution
    dl = force_list(data['unset'])
    meta.update({'unset': data['unset']})
    # if the delete list is not empty
    if dl:
        # construct the list of values that are to be unset
        for ki in dl:
            if ki in existing.keys():
                unset_values.append(ki)
        unset_values = force_list(unset_values)
        # if there are values to unset
        if unset_values:
            if data['app'] == '--global':
                unset_command = 'dokku config:unset --global {0}'.format(' '.join(unset_values))
            else:
                unset_command = 'dokku config:unset {2} {0} {1}'.format(data['app'], ' '.join(unset_values), ' '.join(options))
    
            try:
                subprocess.check_call(unset_command, shell=True)
                is_error = False
                has_changed = True
            except subprocess.CalledProcessError as e:
                meta['error2'] = str(e)
        else:
            is_error = False
            has_changed = False
    else:
        is_error = False

    return (is_error, has_changed, meta)

def main():
    fields = {
        'app': {
            'required': True,
            'type': 'str',
        },
        'restart': {
            'required': False,
            'type': 'bool',
            'default': False
        },
        'config': {
            'required': True,
            'type': 'dict',
            'no_log': True,
        },
        'unset': {
            'required': False,
            'type': 'list',
            'default': []
        },
    }

    module = AnsibleModule(
        argument_spec=fields,
        supports_check_mode=False
    )

    is_error2 = False
    has_changed2 = False
    result2 = {}
    
    # Do the config:set operation
    is_error1, has_changed1, result1 = dokku_config_set(module.params)

    # Do the config:unset operation
    if not module.params['unset'] == []:
        is_error2, has_changed2, result2 = dokku_config_unset(module.params)
    
    # check the error indicator for each operation
    is_error = True if is_error1 or is_error2 else False
    has_changed = True if has_changed1 or has_changed2 else False

    if is_error:
        module.fail_json(msg=result1['error1'], config_set_operation=result1, config_unset_operation=result2)
    module.exit_json(changed=has_changed, config_set_operation=result1, config_unset_operation=result2)


if __name__ == '__main__':
    main()
