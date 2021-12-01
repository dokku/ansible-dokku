# Ansible Role: Dokku

[![Ansible Role](https://img.shields.io/ansible/role/39276.svg)](https://galaxy.ansible.com/dokku_bot/ansible_dokku) [![Release](https://img.shields.io/github/release/dokku/ansible-dokku.svg)](https://github.com/dokku/ansible-dokku/releases) [![Build Status](https://github.com/dokku/ansible-dokku/workflows/CI/badge.svg)](https://github.com/dokku/ansible-dokku/actions)

This Ansible role helps install Dokku on Debian/Ubuntu variants. Apart
from installing Dokku, it also provides various modules that can be
used to interface with dokku from your own Ansible playbooks.


## Table Of Contents

- [Requirements](#requirements)
- [Dependencies](#dependencies)
- [Role Variables](#role-variables)
- [Libraries](#libraries)
- [Example Playbooks](#example-playbooks)
- [Contributing](#contributing)
- [License](#license)

## Requirements

Minimum Ansible Version: 2.2

### Platform Requirements

Supported Platforms

- Ubuntu: xenial
- Ubuntu: yakkety
- Ubuntu: zesty
- Ubuntu: artful
- Ubuntu: bionic
- Ubuntu: focal
- Debian: stretch
- Debian: buster
- Debian: bullseye

## Dependencies

- geerlingguy.docker ansible role
- nginxinc.nginx ansible role
- Dokku (for library usage)

## Role Variables

### dokku_daemon_install

- default: `True`
- type: `boolean`
- description: Whether to install the dokku-daemon

### dokku_daemon_version

- default: `0.0.2`
- type: `string`
- description: The version of dokku-daemon to install

### dokku_hostname

- default: `dokku.me`
- type: `string`
- description: Hostname, used as vhost domain and for showing app URL after deploy

### dokku_key_file

- default: `/root/.ssh/id_rsa.pub`
- type: `string`
- description: Path on disk to an SSH key to add to the Dokku user (Will be ignored on `dpkg-reconfigure`)

### dokku_manage_nginx

- default: `True`
- type: `boolean`
- description: Whether we should manage the 00-default nginx site

### dokku_packages_state

- default: `present`
- type: `string`
- description: State of dokku packages. Accepts 'present' and 'latest'

### dokku_plugins

- default: `{}`
- type: `list`
- description: A list of plugins to install. The host _must_ have network access to the install url, and git access if required. Plugins should be specified in the following format:

```yaml
- name: postgres
  url: https://github.com/dokku/dokku-postgres.git

- name: redis
  url: https://github.com/dokku/dokku-redis.git
```

### dokku_skip_key_file

- default: `false`
- type: `string`
- description: Do not check for the existence of the dokku/key_file. Setting this to "true", will require you to manually add an SSH key later on.

### dokku_users

- default: `null`
- type: `list`
- description: A list of users who should have access to Dokku. This will _not_ grant them generic SSH access, but rather only access as the `dokku` user. Users should be specified in the following format:

```yaml
- name: Jane Doe
  username: jane
  ssh_key: JANES_PUBLIC_SSH_KEY
- name: Camilla
  username: camilla
  ssh_key: CAMILLAS_PUBLIC_SSH_KEY
```

### dokku_version (deprecated)

- default: `''`
- type: `string`
- description: The version of dokku to install.
Scheduled for deletion after 07/2021. Use `dokku_packages_state` instead.

### dokku_vhost_enable

- default: `true`
- type: `string`
- description: Use vhost-based deployments (e.g., .dokku.me)

### dokku_web_config

- default: `false`
- type: `string`
- description: Use web-based config for hostname and keyfile

### herokuish_version (deprecated)

- default: `''`
- type: `string`
- description: The version of herokuish to install.
Scheduled for deletion after 07/2021. Use `dokku_packages_state` instead.

### plugn_version (deprecated)

- default: `''`
- type: `string`
- description: The version of plugn to install.
Scheduled for deletion after 07/2021. Use `dokku_packages_state` instead.

### sshcommand_version (deprecated)

- default: `''`
- type: `string`
- description: The version of sshcommand to install.
Scheduled for deletion after 07/2021. Use `dokku_packages_state` instead.

## Libraries

### dokku_acl_app

Manage access control list for a given dokku application

#### Requirements

- the `dokku-acl` plugin

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|Whether the ACLs should be present or absent|
|users<br /><sup>*required*</sup>||The list of users who can manage the app|

#### Example

```yaml
- name: let leopold manage hello-world
  dokku_acl_app:
    app: hello-world
    users:
      - leopold
- name: remove leopold from hello-world
  dokku_acl_app:
    app: hello-world
    users:
      - leopold
    state: absent
```

### dokku_acl_service

Manage access control list for a given dokku service

#### Requirements

- the `dokku-acl` plugin

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|service<br /><sup>*required*</sup>||The name of the service|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|Whether the ACLs should be present or absent|
|type<br /><sup>*required*</sup>||The type of the service|
|users<br /><sup>*required*</sup>||The list of users who can manage the service|

#### Example

```yaml
- name: let leopold manage mypostgres postgres service
  dokku_acl_service:
    service: mypostgres
    type: postgres
    users:
      - leopold
- name: remove leopold from mypostgres postgres service
  dokku_acl_service:
    service: hello-world
    type: postgres
    users:
      - leopold
    state: absent
```

### dokku_app

Create or destroy dokku apps

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the app|

#### Example

```yaml
- name: Create a dokku app
  dokku_app:
    app: hello-world

- name: Delete that repo
  dokku_app:
    app: hello-world
    state: absent
```

### dokku_builder

Manage the builder configuration for a given dokku application

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app. This is required only if global is set to False.|
|global|*Default:* False|If the property being set is global|
|property<br /><sup>*required*</sup>||The property to be changed (e.g., `build-dir`, `selected`)|
|value||The value of the builder property (leave empty to unset)|

#### Example

```yaml
- name: Overriding the auto-selected builder
  dokku_builder:
    app: node-js-app
    property: selected
    value: dockerfile
- name: Setting the builder to the default value
  dokku_builder:
    app: node-js-app
    property: selected
- name: Changing the build build directory
  dokku_builder:
    app: monorepo
    property: build-dir
    value: backend
- name: Overriding the auto-selected builder globally
  dokku_builder:
    global: true
    property: selected
    value: herokuish
```

### dokku_certs

Manages ssl configuration for an app.

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|cert<br /><sup>*required*</sup>||Path to the ssl certificate|
|key<br /><sup>*required*</sup>||Path to the ssl certificate key|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the ssl configuration|

#### Example

```yaml
- name: Adds an ssl certificate and key to an app
  dokku_certs:
    app: hello-world
    key: /etc/nginx/ssl/hello-world.key
    cert: /etc/nginx/ssl/hello-world.crt

- name: Removes an ssl certificate and key from an app
  dokku_certs:
    app: hello-world
    state: absent
```

### dokku_checks

Manage the Zero Downtime checks for a dokku app

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the checks functionality|

#### Example

```yaml
- name: Disable the zero downtime deployment
  dokku_checks:
    app: hello-world
    state: absent

- name: Re-enable the zero downtime deployment (enabled by default)
  dokku_checks:
    app: hello-world
    state: present
```

### dokku_clone

Clone a git repository and deploy app.

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|build|*Default:* True|Whether to build the app after cloning.|
|repository<br /><sup>*required*</sup>||Git repository url|
|version||Git tree (tag or branch name). If not provided, default branch is used.|

#### Example

```yaml
- name: clone a git repository and build app
  dokku_clone:
      app: example-app
      repository: https://github.com/heroku/node-js-getting-started
      version: b10a4d7a20a6bbe49655769c526a2b424e0e5d0b
- name: clone specific tag from git repository and build app
  dokku_clone:
      app: example-app
      repository: https://github.com/heroku/node-js-getting-started
      version: b10a4d7a20a6bbe49655769c526a2b424e0e5d0b
- name: sync git repository without building app
  dokku_clone:
      app: example-app
      repository: https://github.com/heroku/node-js-getting-started
      build: false
```

### dokku_config

Manage environment variables for a given dokku application

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|config<br /><sup>*required*</sup>|*Default:* {}|A map of environment variables where key => value|
|restart|*Default:* True|Whether to restart the application or not. If the task is idempotent then setting restart to true will not perform a restart.|

#### Example

```yaml
- name: set KEY=VALUE
  dokku_config:
    app: hello-world
    config:
      KEY: VALUE_1
      KEY_2: VALUE_2

- name: set KEY=VALUE without restart
  dokku_config:
    app: hello-world
    restart: false
    config:
      KEY: VALUE_1
      KEY_2: VALUE_2
```

### dokku_docker_options

Manage docker-options for a given dokku application

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|option<br /><sup>*required*</sup>||A single docker option|
|phase|*Choices:* <ul><li>build</li><li>deploy</li><li>run</li></ul>|The phase in which to set the options|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the docker options|

#### Example

```yaml
- name: docker-options:add hello-world deploy
  dokku_docker_options:
    app: hello-world
    phase: deploy
    option: "-v /var/run/docker.sock:/var/run/docker.sock"

- name: docker-options:remove hello-world deploy
  dokku_docker_options:
    app: hello-world
    phase: deploy
    option: "-v /var/run/docker.sock:/var/run/docker.sock"
    state: absent
```

### dokku_domains

Manages domains for a given application

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app. This is required only if global is set to False.|
|domains<br /><sup>*required*</sup>||A list of domains|
|global|*Default:* False|Whether to change the global domains or app-specific domains.|
|state|*Choices:* <ul><li>enable</li><li>disable</li><li>clear</li><li>**present** (default)</li><li>absent</li></ul>|The state of the application's domains|

#### Example

```yaml
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
```

### dokku_git_sync

Manages syncing git code from a remote repository for an app

#### Requirements

- the `dokku-git-sync` plugin (_commercial_)

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|remote||The git remote url to use|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the git-sync integration|

#### Example

```yaml
- name: git-sync:enable hello-world
  dokku_git_sync:
    app: hello-world
    remote: git@github.com:hello-world/hello-world.git

- name: git-sync:disable hello-world
  dokku_git_sync:
    app: hello-world
    state: absent
```

### dokku_global_cert

Manages global ssl configuration.

#### Requirements

- the `dokku-global-cert` plugin

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|cert<br /><sup>*required*</sup>||Path to the ssl certificate|
|key<br /><sup>*required*</sup>||Path to the ssl certificate key|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the ssl configuration|

#### Example

```yaml
- name: Adds an ssl certificate and key
  dokku_global_cert:
    key: /etc/nginx/ssl/global-hello-world.key
    cert: /etc/nginx/ssl/global-hello-world.crt

- name: Removes an ssl certificate and key
  dokku_global_cert:
    state: absent
```

### dokku_http_auth

Manage HTTP Basic Authentication for a dokku app

#### Requirements

- the `dokku-http-auth` plugin

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|password||The HTTP Auth Password (required for 'present' state)|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the http-auth plugin|
|username||The HTTP Auth Username (required for 'present' state)|

#### Example

```yaml
- name: Enable the http-auth plugin
  dokku_http_auth:
    app: hello-world
    state: present
    username: samsepi0l
    password: hunter2

- name: Disable the http-auth plugin
  dokku_http_auth:
    app: hello-world
    state: absent
```

### dokku_image

Pull Docker image and deploy app

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|build_dir||Specify custom build directory for a custom build context|
|image<br /><sup>*required*</sup>||Docker image|
|user_email||Git user.email for customizing the author's email|
|user_name||Git user.name for customizing the author's name|

#### Example

```yaml
- name: Pull and deploy meilisearch
  dokku_image:
      app: meilisearch
      image: getmeili/meilisearch:v0.24.0rc1
- name: Pull and deploy image with custom author
  dokku_image:
      app: hello-world
      user_name: Elliot Alderson
      user_email: elliotalderson@protonmail.ch
      image: hello-world:latest
- name: Pull and deploy image with custom build dir
  dokku_image:
      app: hello-world
      build_dir: /path/to/build
      image: hello-world:latest
```

### dokku_letsencrypt

Enable or disable the letsencrypt plugin for a dokku app

#### Requirements

- the `dokku-letsencrypt` plugin

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the letsencrypt plugin|

#### Example

```yaml
- name: Enable the letsencrypt plugin
  dokku_letsencrypt:
    app: hello-world

- name: Disable the letsencrypt plugin
  dokku_letsencrypt:
    app: hello-world
    state: absent
```

### dokku_network

Create or destroy container networks for dokku apps

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|name<br /><sup>*required*</sup>||The name of the network|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the network|

#### Example

```yaml
- name: Create a network
  dokku_network:
    name: example-network

- name: Delete that network
  dokku_network:
    name: example-network
    state: absent
```

### dokku_network_property

Set or clear a network property for a given dokku application

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app. This is required only if global is set to False.|
|global|*Default:* False|Whether to change the global network property|
|property<br /><sup>*required*</sup>||The network property to be be modified. This can be any property supported by dokku (e.g., `initial-network`, `attach-post-create`, `attach-post-deploy`, `bind-all-interfaces`, `static-web-listener`, `tld`).|
|value||The value of the network property (leave empty to unset)|

#### Example

```yaml
- name: Associates a network after a container is created but before it is started
  dokku_network_property:
    app: hello-world
    property: attach-post-create
    value: example-network

- name: Associates the network at container creation
  dokku_network_property:
    app: hello-world
    property: initial-network
    value: example-network

- name: Setting a global network property
  dokku_network_property:
    global: true
    property: attach-post-create
    value: example-network

- name: Clearing a network property
  dokku_network_property:
    app: hello-world
    property: attach-post-create
```

### dokku_ports

Manage ports for a given dokku application

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|mappings<br /><sup>*required*</sup>||A list of port mappings|
|state|*Choices:* <ul><li>clear</li><li>**present** (default)</li><li>absent</li></ul>|The state of the port mappings|

#### Example

```yaml
- name: proxy:ports-set hello-world http:80:80
  dokku_ports:
    app: hello-world
    mappings:
        - http:80:8080

- name: proxy:ports-remove hello-world http:80:80
  dokku_ports:
    app: hello-world
    mappings:
        - http:80:8080
    state: absent

- name: proxy:ports-clear hello-world
  dokku_ports:
    app: hello-world
    state: clear
```

### dokku_proxy

Enable or disable the proxy for a dokku app

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the proxy|

#### Example

```yaml
- name: Enable the default proxy
  dokku_proxy:
    app: hello-world

- name: Disable the default proxy
  dokku_proxy:
    app: hello-world
    state: absent
```

### dokku_ps_scale

Manage process scaling for a given dokku application

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|scale<br /><sup>*required*</sup>|*Default:* {}|A map of scale values where proctype => qty|
|skip_deploy|*Default:* False|Whether to skip the corresponding deploy or not. If the task is idempotent then leaving skip_deploy as false will not trigger a deploy.|

#### Example

```yaml
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
```

### dokku_registry

Manage the registry configuration for a given dokku application

#### Requirements

- the `dokku-registry` plugin

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|image||Alternative to app name for image repository name|
|password||The registry password (required for 'present' state)|
|server||The registry server hostname (required for 'present' state)|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the registry integration|
|username||The registry username (required for 'present' state)|

#### Example

```yaml
- name: registry:enable hello-world
  dokku_registry:
    app: hello-world
    password: password
    server: localhost:8080
    username: user

- name: registry:enable hello-world with args
  dokku_registry:
    app: hello-world
    image: other-image
    password: password
    server: localhost:8080
    username: user

- name: registry:disable hello-world
  dokku_registry:
    app: hello-world
    state: absent
```

### dokku_resource_limit

Manage resource limits for a given dokku application

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|clear_before|*Choices:* <ul><li>True</li><li>**False** (default)</li></ul>|Clear all resource limits before applying|
|process_type||The process type selector|
|resources||The Resource type and quantity (required when state=present)|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the resource limits|

#### Example

```yaml
- name: Limit CPU and memory of a dokku app
  dokku_resource_limit:
    app: hello-world
    resources:
      cpu: 100
      memory: 100

- name: name: Limit resources per process type of a dokku app
  dokku_resource_limit:
    app: hello-world
    process_type: web
    resources:
      cpu: 100
      memory: 100

- name: Clear limits before applying new limits
  dokku_resource_limit:
    app: hello-world
    state: present
    clear_before: True
    resources:
      cpu: 100
      memory: 100

- name: Remove all resource limits
  dokku_resource_limit:
    app: hello-world
    state: absent
```

### dokku_resource_reserve

Manage resource reservations for a given dokku application

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|clear_before|*Choices:* <ul><li>True</li><li>**False** (default)</li></ul>|Clear all reserves before apply|
|process_type||The process type selector|
|resources||The Resource type and quantity (required when state=present)|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the resource reservations|

#### Example

```yaml
- name: Reserve CPU and memory for a dokku app
  dokku_resource_reserve:
    app: hello-world
    resources:
      cpu: 100
      memory: 100

- name: Create a reservation per process type of a dokku app
  dokku_resource_reserve:
    app: hello-world
    process_type: web
    resources:
      cpu: 100
      memory: 100

- name: Clear all reservations before applying
  dokku_resource_reserve:
    app: hello-world
    state: present
    clear_before: True
    resources:
      cpu: 100
      memory: 100

- name: Remove all resource reservations
  dokku_resource_reserve:
    app: hello-world
    state: absent
```

### dokku_service_create

Creates a given service

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|name<br /><sup>*required*</sup>||The name of the service|
|service<br /><sup>*required*</sup>||The type of service to create|

#### Example

```yaml
- name: redis:create default
  dokku_service_create:
    name: default
    service: redis

- name: postgres:create default
  dokku_service_create:
    name: default
    service: postgres

- name: postgres:create default with custom image
  environment:
    POSTGRES_IMAGE: postgis/postgis
    POSTGRES_IMAGE_VERSION: 13-master
  dokku_service_create:
    name: default
    service: postgres
```

### dokku_service_link

Links and unlinks a given service to an application

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app<br /><sup>*required*</sup>||The name of the app|
|name<br /><sup>*required*</sup>||The name of the service|
|service<br /><sup>*required*</sup>||The type of service to link|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the service link|

#### Example

```yaml
- name: redis:link default hello-world
  dokku_service_link:
    app: hello-world
    name: default
    service: redis

- name: postgres:link default hello-world
  dokku_service_link:
    app: hello-world
    name: default
    service: postgres

- name: redis:unlink default hello-world
  dokku_service_link:
    app: hello-world
    name: default
    service: redis
    state: absent
```

### dokku_storage

Manage storage for dokku applications

#### Parameters

|Parameter|Choices/Defaults|Comments|
|---------|----------------|--------|
|app||The name of the app|
|create_host_dir|*Default:* False|Whether to create the host directory or not|
|group|*Default:* 32767|A group or gid that should own the created folder|
|mounts|*Default:* []|A list of mounts to create, colon (:) delimited, in the format: `host_dir:container_dir`|
|state|*Choices:* <ul><li>**present** (default)</li><li>absent</li></ul>|The state of the service link|
|user|*Default:* 32767|A user or uid that should own the created folder|

#### Example

```yaml
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
```

## Example Playbooks

### Installing Dokku

```yaml
---
- hosts: all
  roles:
    - dokku_bot.ansible_dokku
```

### Installing Plugins

```yaml
---
- hosts: all
  roles:
    - dokku_bot.ansible_dokku
  vars:
    dokku_plugins:
      - name: clone
        url: https://github.com/crisward/dokku-clone.git
      - name: postgres
        url: https://github.com/dokku/dokku-postgres.git
```

### Deploying a simple word inflector

```yaml
---
- hosts: all
  roles:
    - dokku_bot.ansible_dokku
  tasks:
    - name: dokku apps:create inflector
      dokku_app:
        app: inflector

    - name: dokku clone inflector
      dokku_clone:
        app: inflector
        repository: https://github.com/cakephp/inflector.cakephp.org
```

### Setting up a Small VPS with a Dokku App

```yaml
---
- hosts: all
  roles:
    - dokku_bot.ansible_dokku
    - geerlingguy.swap
  vars:
    # If you are running dokku on a small VPS, you'll most likely
    # need some swap to ensure you don't run out of RAM during deploys
    swap_file_size_mb: '2048'
    dokku_version: 0.19.13
    dokku_users:
      - name: yourname
        username: yourname
        ssh_key: "{{lookup('file', '~/.ssh/id_rsa.pub')}}"
    dokku_plugins:
      - name: clone
        url: https://github.com/crisward/dokku-clone.git
      - name: letsencrypt
        url: https://github.com/dokku/dokku-letsencrypt.git
  tasks:
    - name: create app
      dokku_app:
        # change this name in your template!
        app: &appname appname
    - name: environment configuration
      dokku_config:
        app: *appname
        config:
          # specify a email for dokku-letsencrypt
          DOKKU_LETSENCRYPT_EMAIL: email@example.com
          # specify port so `domains` can setup the port mapping properly
          PORT: "5000"
    - name: git clone
      # note you'll need to add a deployment key to the GH repo if it's private!
      dokku_clone:
        app: *appname
        repository: git@github.com:heroku/python-getting-started.git
    - name: add domain
      dokku_domains:
        app: *appname
        domains:
          - example.com
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT License

See LICENSE.md for further details.
