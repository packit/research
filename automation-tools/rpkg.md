# RPKG


- base library for fedpkg provides common functionality for dist-git setups
- [ :computer: pagure.io/rpkg](https://pagure.io/rpkg), [ :scroll: documentation](https://docs.pagure.org/rpkg)
- ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rpkg.svg), [![PyPI](https://img.shields.io/pypi/v/rpkg.svg)](https://pypi.org/project/rpkg/), [ :package: fedora packages](https://src.fedoraproject.org/rpms/rpkg)

:heavy_plus_sign:
- [CLI deffinition](https://docs.pagure.org/rpkg/cli.html#) for tools build on top of the rpkg
- [Python API](https://docs.pagure.org/rpkg/api.html), some examples:
  - [cli](https://docs.pagure.org/rpkg/api.html#cli)
  - [commands](https://docs.pagure.org/rpkg/api.html#commands)
    - `add_tag(tagname, force=False, message=None, file=None)`
    - `build(skip_tag=False, scratch=False, background=False, url=None, chain=None, arches=None, sets=False, nvr_check=True, fail_fast=False)`
    - `container_build_koji(target_override=False, opts={}, kojiconfig=None, kojiprofile=None, build_client=None, koji_task_watcher=None, nowait=False, flatpak=False)`
    - `copr_build(project, srpm_name, nowait, config_file)`
    - `import_srpm(srpm)`
    - `koji_upload(file, path, callback=None)`
    - `patch(suffix, rediff=False)`
    - `prep(arch=None, builddir=None, buildrootdir=None)`
    - `switch_branch(branch, fetch=True)`, ...
  - [lookaside cache](https://docs.pagure.org/rpkg/api.html#lookaside)
    - `download(name, filename, hash, outfile, hashtype=None, **kwargs)`
    - `remote_file_exists(name, filename, hash)`
    - `upload(name, filepath, hash)`, ...
  - [sources](https://docs.pagure.org/rpkg/api.html#sources)
  - [gitignore](https://docs.pagure.org/rpkg/api.html#gitignore)

:heavy_minus_sign:
- .


### Requirements:

- mock: for local mockbuild.
- rpm-build: for local RPM build, which provides the command line rpm.
- rpmlint: check SPEC.
- copr-cli: for building package in Fedora Copr.
- module-build-service: for building modules.
