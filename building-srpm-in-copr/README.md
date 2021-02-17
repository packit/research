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
- we could create a CLI command in Packit which would clone the repo in the version we want (particular branch, commit sha), run 1. and 2. step from current process,
  move the needed files into `resultdir`
- we need to get the required info into the script:
  - git ref
  - project url for cloning the repo and additional arguments to clone the version we want
- the script could look like this, `packit` would be the build dependency
  (+ packages needed for running the user-defined actions?):

```bash
#!bin/sh

packit prepare-sources --project_url={PROJECT_URL} --upstream-ref={UPSTREAM_REF}

```

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
