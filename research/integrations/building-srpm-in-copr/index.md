---
title: Building SRPMs in Copr
authors:
  - lbarczio
  - mfocko
---

Copr provides an option to use their [custom source method](https://docs.pagure.org/copr.copr/custom_source_method.html)
to create sources for SRPM.

## How to use the custom source method to create sources

- required script in any scripting language and chroot where the script is executed (defaults to `fedora-latest-x86_64`)
- output of the script: specfile, optionally any other file needed to successfully build a source RPM from that spec file (tarballs, patches)
- script is executed under non-privileged user -> packages needed for running script should be specified as a list of (srpm)build-dependencies
- optional parameters:
  - builddeps: list of packages
  - resultdir: dir with output files (defaults to current working directory)
- cannot be run separately without creating a copr build
  (we cannot use it for koji builds)
- in `python-copr` we would call this method (currently we use `create_from_file`):

```python
    def create_from_custom(self, ownername, projectname, script, script_chroot=None,
                           script_builddeps=None, script_resultdir=None, buildopts=None,
                           project_dirname=None):
        """
        Create a build from custom script.

        :param str ownername:
        :param str projectname:
        :param script: script to execute to generate sources
        :param script_chroot: [optional] what chroot to use to generate
            sources (defaults to fedora-latest-x86_64)
        :param script_builddeps: [optional] list of script's dependencies
        :param script_resultdir: [optional] where script generates results
            (relative to cwd)
        :param str project_dirname:
        :return: Munch
        """
```

- logs from building the SRPM stored in separate file, [example](https://download.copr.fedorainfracloud.org/results/lbarczio/ogr-test-custom/srpm-builds/01967579/builder-live.log.gz)

- current process for creating SRPM in Packit:
  - `create_srpm` method of `PackitAPI` class, `PackitAPI` has the info about package config,
    local project, user config
  - `create_srpm` calls these methods of `Upstream` class:
    1. `run_action(actions=ActionName.post_upstream_clone)`
       - run user-defined action for what to do after cloning of the upstream repo
    2. `prepare_upstream_for_srpm_creation(upstream_ref=upstream_ref)`
       - upstream_ref: git ref to upstream commit
       - determine version, create an archive or download upstream and create patches for sourcegit,
         fix/update the specfile to use the right archive, download the remote sources, user-defined actions
         used also here, e.g. `ActionName.create_archive`
    3. `create_srpm(srpm_path=output_file, srpm_dir=srpm_dir)`
       - run `rpmbuild` command
- we need to group the functionality of cloning the particular repo version, running 1. and 2. step from current process,
  move the needed files into `resultdir` -> dedicated CLI command/method - this will be used in the script
- we need to get the required info into the script:
  - info about project version
    - git ref
    - pr_id
    - repo name + namespace / url
  - job config
  - do we need anything from service config? we have the secrets there, so we can't pass the whole service config

#### How did I test the functionality

I used our `packit srpm` command for testing:

```python
script = """
#!/bin/sh

resultdir=$PWD

git clone https://github.com/packit/ogr ogr
cd ogr
packit -d srpm

tarball=$(echo fedora/ogr-*.tar.gz)
mv fedora/python-ogr.spec "$resultdir"
mv "$tarball" "$resultdir"
"""
```

and then called:

```python
copr_client.build_proxy.create_from_custom(ownername="lbarczio", projectname="ogr-test-custom", script=script,
                           script_builddeps=["git", "packit", "python3-wheel", "python3-pip", "python3-setuptools",
                            "python3-setuptools_scm", "python3-setuptools_scm_git_archive"])
```

### Plan how to build SRPMs in Copr in Packit Service

- create CLI command or only Packit API method for preparing sources (would mostly use existing functionality, described above)
- implement creation of the script (Python/bash - Python would be easier for handling with configs)
  - script will be created dynamically each time
  - pass the needed arguments and use the method/command
- implement using the script for creating SRPMS for Copr builds
  - use copr API to submit SRPM build:
    - `copr_client.build_proxy.create_from_custom(ownername=owner, projectname=project, script=script, script_builddeps=["git", "packit", ...])`
    - find out what exactly will be the `builddeps` for SRPM creation (check which I needed to include when testing earlier)
      - currently, we have some builddeps hardcoded in workers added on demand of some of our users,
        those need to be included
      - in future, we could implement mechanism for specifying builddeps for the action itself
        - those would be included dynamically
  - make sure we receive messages about SRPM state in fedmsg (we already have some processing in Packit Service,
    check whether the format is up to date
    [here](https://github.com/packit/packit-service/blob/950b865018b843be2addc68d0606491fca57343c/packit_service/worker/handlers/copr.py#L189)
    and [here](https://github.com/packit/packit-service/blob/950b865018b843be2addc68d0606491fca57343c/packit_service/worker/handlers/copr.py#L268))
  - create new handlers for SRPM state change / extend the CoprBuildStartHandler/CoprBuildEndHandler
    - report the SRPM state to user (checks/statuses)
    - create/update SRPM model in our DB
    - provide the link with SRPM logs
- for Koji builds, still use the old way for now
