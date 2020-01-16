# New python package to Fedora
A guide for complete newbies about what it takes to incorporate a python package to fedora from Packit project perspective.

## Prerequsities
 * You have python project on [Github](https://github.com).

### Create python package
Create `setup.py` or `setup.cfg` with a package metadata.
`setup.{py|cfg}` is the build script for [setuptools](https://setuptools.readthedocs.io/en/latest/setuptools.html).

### Decide and setup versioning schema
You can either manually set version in `setup.py` or let [setuptools-scm](https://pypi.org/project/setuptools-scm) do that for you.

Choose your scheme, eg `0.1.0`.
It depends on previous steps, if you have hardcoded version in `setup.py`, or used mechanism like git tags
 * Create git tag `git tag 0.1.0`,  then python setup will use this as version
 * Push the tag to origin `git push origin 0.1.0`
 * Use [tito](https://github.com/dgoodwin/tito) project to increase versions

### Upload package release to PYPI
 * If you are not already registered, register to [PYPI server](https://pypi.org/account/register/)
 * Build the package `python3 setup.py sdist`
 * Install twine: `sudo dnf install python3-twine`
 * Upload release: `twine upload dist/your_package_name-0.1.0.tar.gz`

## Workflow to enable COPR builds of your packages

### Create Specfile
 * Install [pyp2rpm](https://pypi.org/project/pyp2rpm/) to convert your `setup.py` to a specfile: `sudo dnf install pyp2rpm`
 * Create specfile: `pyp2rpm requre > python-your_project_name.spec`

### Install Packit-as-a-Service GitHub App
See [documentation](https://packit.dev/packit-as-a-service).

### Create .packit.yaml with copr build enabled
Comprehensive documentation is available at [packit.dev](https://packit.dev/docs/configuration).
Create file `.packit.yaml` with proper content and add it to git.

 * generic part example:
  ```yaml
specfile_path: python-your_project_name.spec
# package project name what correspond to package name in setup.py
upstream_package_name: your_project_name
# name what you used as name in specfile (for python packages it starts with python-)
downstream_package_name: python-your_project_name
```
 * copr build enablement part of config - It enables copr builds for stable (without rawhide) fedora releases.
  ```yaml
jobs:
- job: copr_build
  trigger: pull_request
  metadata:
    targets:
     - fedora-stable
```

Then create pull request containing this `.packit.yaml` file.
Packit service should try to do Copr builds for you to prove that Fedora RPM packages build fine.

### Increase version and push it to git/PYPI already
It is important to get to consistent state. Previous steps are important do to in this sequence, because it is important for specfile creation.


### Troubleshooting
 * If the package cannot be build - try to build SRPM package locally
 * If there is issue with build it could be caused by version what were pushed to production. create another tag, or increase version and push the changes to git PR and PYPI


## Workflow to add your package to Fedora

### Became Fedora package maintainer
If you are not already Fedora packager, you have to [become one](https://fedoraproject.org/wiki/Join_the_package_collection_maintainers).

### Contribute new package to Fedora
Follow [instruction](https://fedoraproject.org/wiki/New_package_process_for_existing_contributors).
It is quite complex process to incorporate some package to Fedora.

###  
 

