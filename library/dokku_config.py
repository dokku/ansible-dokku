#!/usr/bin/python
# -*- coding: utf-8 -*-
# from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
import pipes
import subprocess

DOCUMENTATION = '''
---
module: dokku_config
short_description: Manage environment variables for a given dokku application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  config:
    description:
      - A map of environment variables where key => value
    required: True
    default: {}
    aliases: []
author: Jose Diaz-Gonzalez
requirements: [ ]
'''

EXAMPLES = '''
- name: set KEY=VALUE
  dokku_config:
    app: hello-world
    config:
      KEY: VALUE_1
      KEY_2: VALUE_2
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
        output = str(output).rstrip('\n').split(split)
        output = force_list(filter(None, output))
        output = [o.strip() for o in output]
    except subprocess.CalledProcessError as e:
        error = str(e)
    return output, error


def dokku_config(app):
    command = 'dokku config --export {0}'.format(app)
    output, error = subprocess_check_output(command)


    def parse_content(content):
        parts = content.split('=', 1)
        return parts[0][7:], parts[1][1:-1]

    if error is None:
        response = {}
        content = ''
        for line in output:
            if line.startswith('export ') and content != '':
                key, value = parse_content(content)
                response[key] = value.strip()
                content = ''

            content += line

        if len(content.strip()) != 0:
            key, value = parse_content(content)
            response[key] = value.strip()

        output = response

    return output, error


def dokku_config_set(data):
    is_error = True
    has_changed = False
    meta = {'present': False}

    values = []
    existing, error = dokku_config(data['app'])
    for key, value in data['config'].items():
        if value == existing.get(key, None):
            continue
        values.append('{0}={1}'.format(key, pipes.quote(value)))

    if len(values) == 0:
        is_error = False
        has_changed = False
        return (is_error, has_changed, meta)

    command = 'dokku config:set {0} {1}'.format(data['app'], ' '.join(values))
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
    except subprocess.CalledProcessError as e:
        meta['error'] = str(e)

    return (is_error, has_changed, meta)


def main():
    fields = {
        'app': {
            'required': True,
            'type': 'str',
        },
        'config': {
            'required': True,
            'type': 'dict',
            'no_log': True
        },
    }

    module = AnsibleModule(
        argument_spec=fields,
        supports_check_mode=False
    )
    is_error, has_changed, result = dokku_config_set(
        module.params)

    if is_error:
        module.fail_json(msg=result['error'], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == '__main__':
    main()
