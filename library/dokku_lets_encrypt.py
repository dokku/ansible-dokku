#!/usr/bin/python
# -*- coding: utf-8 -*-
# from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule
import subprocess

DOCUMENTATION = '''
---
module: dokku_lets_encrypt
short_description: Create or destroy dokku apps
options:
  app:
    description:
      - The app to create a certificate for
    required: True
    default: null
    aliases: []
author: Michael Bianco
requirements: [ ]
'''

# TODO document DOKKU_LETSENCRYPT_EMAIL environment var
EXAMPLES = '''
- name: Create a dokku app
  dokku_lets_encrypt:
    app: helloworld.com
'''

def dokku_certificate_exists(app):
    exists = False
    error = None
    command = 'dokku letsencrypt:ls'

    # TODO cut off the first line, and pull the app names (first column in output) to check for existence
    try:
        subprocess.check_call(command, shell=True)
        exists = True
    except subprocess.CalledProcessError as e:
        error = str(e)
    return exists, error

def main():
    fields = {
        'app': {
            'required': True,
            'type': 'str',
        }
    }

    module = AnsibleModule(
        argument_spec=fields,
        supports_check_mode=False
    )

    is_error = True
    has_changed = True
    meta = {"present": True}

    # TODO important to make sure additional domains aren't in place, especially the dokku.me domain
    # TODO this was not working when it was run via ansible, but it ran just fine locally
    # generate a certificate for all urls attached to the app
    command = 'dokku letsencrypt {0}'.format(module.params['app'])
    try:
        subprocess.run(command, shell=True, check=True)
        is_error = False
        has_changed = True
    except subprocess.CalledProcessError as e:
        meta['error'] = str(e)

    if is_error:
      module.fail_json(msg=result['error'], meta=result)

    is_error = True

    # setup automatic renewal, there's no harm is running this multiple times
    command = 'dokku letsencrypt:cron-job --add'
    try:
        subprocess.run(command, shell=True, check=True)
        is_error = False
        has_changed = True
    except subprocess.CalledProcessError as e:
        meta['error'] = str(e)

    module.exit_json(changed=has_changed, meta=result)

if __name__ == '__main__':
    main()
