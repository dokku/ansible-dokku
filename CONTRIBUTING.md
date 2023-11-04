# Contributing


Contributions to the the Dokku open source project are highly welcome!
For general hints see the project-wide [contributing guide](https://github.com/dokku/.github/blob/master/CONTRIBUTING.md).

## Codebase overview

 * The role's directory layout follows [standard Ansible practices](https://galaxy.ansible.com/docs/contributing/creating_role.html#roles).
 * Besides the yaml-based ansible instructions, the role includes several new Ansible *modules* in the `library/` folder (e.g. `dokku_app`).
 * The `README.md` of this repository is auto-generated: do *not* edit it directly.  
   In order to update it, run `make generate`.

## Setting up a test environment

This role is tested using [molecule](https://molecule.readthedocs.io/en/latest/).
Setting up a test environment involves the following steps:

 * Install [docker](https://www.docker.com/)
 * Install [python](https://www.python.org/)
 * (optional) Create a python virtual environment
 * Run `pip install -r  requirements.txt`
 * Run `pre-commit install`
 * Run `make generate`

After this, you'll be able to test any changes made to the role using:

```
molecule test
```
This will ensure that:

  * the role adheres to coding standards (via `yamllint`, `ansible-lint`, `flake8` and `black` pre-commit hooks)
  * the role runs fine (with default parameters)
  * the role is idempotent (with default parameters)
  * any tests defined in `molecule/default/verify.yml` pass

In addition to local testing, continuous integration tests on a selection of Ubuntu and Debian versions are run on any pull request.
