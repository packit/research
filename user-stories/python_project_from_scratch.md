# propose new python package to fedora
It is intented for complely newbies what would like to incorporate ``python``
package from scatch finally to fedora from Packit project perspective

## Prerequsities
 * You have python project on [github server](https://github.com/)

## Workflow to enable COPR builds of your packages

### Create python package
Create ``setup.py`` or with ``setup.cfg`` to configure packaging informations for your package

 * directly via [setup.py](https://packaging.python.org/tutorials/packaging-projects/#creating-setup-py)
 * With [setuptools](https://setuptools.readthedocs.io/en/latest/setuptools.html) support, it is more elegant solution, allows to write information via config instead of direct ``python`` code. 

### Decide and setup versioning schema
How your project creates new releases, choose your scheme, eg ``0.1.0``.
It depends on previous steps, if you have hardcoded version in setup.py, or used mechanism like git tags
 * create git tag ``git tag 0.1.0``,  then python setup will use this as version
 * push the tag to origin ``git push origin 0.1.0``
 * use [tito](https://github.com/dgoodwin/tito) project to increase versions  

### Upload package release to PYPI
 * If you are not already registered, please register to [PYPI server](https://pypi.org/account/register/)
 * build the package ``python3 setup.py sdist``
 * install twine: ``sudo dnf install python3-twine`` (It is tool what could be used to upload package to PYPI)
 * Upload release: ``twine upload dist/your_package_name-0.1.0.tar.gz``

### Create Specfile
 * Install tool to convert your setup.py to specfile ``sudo dnf install pyp2rpm``
 * Create specfile: ``pyp2rpm requre > python-your_project_name.spec``

### Enable packit-service github app
Enable it for your organization or for selected projects. Documentation available at [packit.dev](https://packit.dev/packit-as-a-service/)

### Create .packit.yaml with copr build enabled
comprehensive documenatation available at [packit.dev](https://packit.dev/docs/configuration/)
create file ``.packit.yaml`` with proper content and add it to git.

 * generic part example:
  ```yaml
specfile_path: python-your_project_name.spec
synced_files:
  - python-your_project_name.spec
  - .packit.yaml
# package project name what correspond to package name in setup.py
upstream_package_name: your_project_name
# name what you used as name in specfile (for python packages it starts with python-)
downstream_package_name: python-your_project_name
```
 * copr build enablement part of config - It enables copr builds for stable fedora releases (In shortcut without rawhide)
  ```yaml
jobs:
- job: copr_build
  trigger: pull_request
  metadata:
    targets:
     - fedora-stable
```

Then create pull request containing this ``.packit.yaml`` file.
Packit service found it and try to do copr builds for you to prove that fedora packaging is fine.

## Increase version and push it to git/PYPI already
It is important to get to consistent state. Previous steps are important do to in this sequence, because it is important for specfile creation.


## Troubleshooting
 * If the package cannot be build - try to build SRPM package locally
 * If there is issue with build it could be caused by version what were pushed to production. create another tag, or increase version and push the changes to git PR and PYPI


## Workflow to add your package to fedora

### Became Fedora package maintaner
if you are not already fedora packager, you have to become to be. It takes a while. [instructions](https://fedoraproject.org/wiki/Join_the_package_collection_maintainers)

### Contribute new package to fedora
Follow [instruction](https://fedoraproject.org/wiki/New_package_process_for_existing_contributors).
It is also little bit complex process to incorporate some package to fedora.

###  
 

