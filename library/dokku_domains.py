#!/usr/bin/python
# -*- coding: utf-8 -*-
# from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
import pipes
import subprocess

DOCUMENTATION = '''
---
module: dokku_domains
short_description: Manages domains for a given application
options:
  app:
    description:
      - The name of the app
    required: True
    default: null
    aliases: []
  domains:
    description:
      - A list of domains
    required: True
    default: null
    aliases: []
  state:
    description:
      - The state of the application's domains
    required: False
    default: present
    choices: [ "enable", "disable", "clear", "present", "absent" ]
    aliases: []
author: Jose Diaz-Gonzalez
requirements: [ ]
'''

EXAMPLES = '''
- name: domains:add hello-world dokku.me
  dokku_domains:
    app: hello-world
    domains:
      - dokku.me

- name: domains:remove hello-world dokku.me
  dokku_domains:
    app: hello-world
    domains:
      - dokku.me
    state: absent

- name: domains:clear hello-world
  dokku_domains:
    app: hello-world
    state: clear

- name: domains:enable hello-world
  dokku_domains:
    app: hello-world
    state: enable

- name: domains:disable hello-world
  dokku_domains:
    app: hello-world
    state: disable
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


def dokku_global_domains():
    command = 'dokku --quiet domains'
    return subprocess_check_output(command)


def dokku_domains(data):
    command = 'dokku --quiet domains {0}'.format(data['app'])
    return subprocess_check_output(command)


def dokku_domains_disable(data):
    is_error = True
    has_changed = False
    meta = {'present': True}

    domains = dokku_domains(data)
    if 'No domain names set for plugins' in domains:
        is_error = False
        meta['present'] = False
        return (is_error, has_changed, meta)

    command = 'dokku --quiet domains:disable {0}'.format(
        data['app'])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta['present'] = False
    except subprocess.CalledProcessError as e:
        meta['error'] = str(e)

    return (is_error, has_changed, meta)


def dokku_domains_enable(data):
    is_error = True
    has_changed = False
    meta = {'present': False}

    domains = dokku_domains(data)
    if 'No domain names set for plugins' not in domains:
        is_error = False
        meta['present'] = True
        return (is_error, has_changed, meta)

    command = 'dokku --quiet domains:enable {0}'.format(
        data['app'])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta['present'] = True
    except subprocess.CalledProcessError as e:
        meta['error'] = str(e)

    return (is_error, has_changed, meta)


def dokku_domains_absent(data):
    is_error = True
    has_changed = False
    meta = {'present': True}

    existing, error = dokku_domains(data)
    if error:
        meta['error'] = error
        return (is_error, has_changed, meta)

    to_remove = [d for d in data['domains'] if d in existing]
    to_remove = [pipes.quote(d) for d in to_remove]

    if len(to_remove) == 0:
        is_error = False
        meta['present'] = False
        return (is_error, has_changed, meta)

    command = 'dokku --quiet domains:remove {0} {1}'.format(
        data['app'],
        ' '.join(to_remove))
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta['present'] = False
    except subprocess.CalledProcessError as e:
        meta['error'] = str(e)

    return (is_error, has_changed, meta)


def dokku_domains_present(data):
    is_error = True
    has_changed = False
    meta = {'present': False}

    existing, error = dokku_domains(data)
    if error:
        meta['error'] = error
        return (is_error, has_changed, meta)

    to_add = [d for d in data['domains'] if d not in existing]
    to_add = [pipes.quote(d) for d in to_add]

    if len(to_add) == 0:
        is_error = False
        meta['present'] = True
        return (is_error, has_changed, meta)

    command = 'dokku --quiet domains:add {0} {1}'.format(
        data['app'],
        ' '.join(to_add))
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta['present'] = True
    except subprocess.CalledProcessError as e:
        meta['error'] = str(e)

    return (is_error, has_changed, meta)


def dokku_domains_clear(data):
    is_error = True
    has_changed = False
    meta = {'present': False}

    command = 'dokku --quiet domains:clear {0}'.format(
        data['app'])
    try:
        subprocess.check_call(command, shell=True)
        is_error = False
        has_changed = True
        meta['present'] = True
    except subprocess.CalledProcessError as e:
        meta['error'] = str(e)

    return (is_error, has_changed, meta)


def dokku_domains_set(data):
    is_error = True
    has_changed = False
    meta = {'present': False}

    existing, error = dokku_domains(data)
    if error:
        meta['error'] = error
        return (is_error, has_changed, meta)

    to_set = [pipes.quote(d) for d in data['domains']]

    command = 'dokku --quiet domains:set {0} {1}'.format(
        data['app'],
        ' '.join(to_set))
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
        'domains': {
            'required': True,
            'type': 'list',
        },
        'state': {
            'required': False,
            'default': 'present',
            'choices': [
                'absent',
                'clear',
                'enable',
                'disable',
                'present',
                'set',
            ],
            'type': 'str',
        },
    }
    choice_map = {
        'absent': dokku_domains_absent,
        'clear': dokku_domains_clear,
        'disable': dokku_domains_disable,
        'enable': dokku_domains_enable,
        'present': dokku_domains_present,
        'set': dokku_domains_set,
    }

    module = AnsibleModule(
        argument_spec=fields,
        supports_check_mode=False
    )
    is_error, has_changed, result = choice_map.get(
        module.params['state'])(module.params)

    if is_error:
        module.fail_json(msg=result['error'], meta=result)
    module.exit_json(changed=has_changed, meta=result)


if __name__ == '__main__':
    main()
