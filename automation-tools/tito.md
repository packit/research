# TITO

- Tito is a tool for managing RPM based projects using git for their source code repository.
- [ :computer: github.com/dgoodwin/tito](https://github.com/dgoodwin/tito)
- ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tito.svg), [![PyPI](https://img.shields.io/pypi/v/tito.svg)](https://pypi.org/project/tito/), [ :package: fedora packages](https://src.fedoraproject.org/rpms/tito)

:heavy_plus_sign:
- [custom builders/taggers/releasers](https://github.com/dgoodwin/tito#custom-builders--taggers--releasers)
  - releasers: `man 8 releasers.conf`
- `--ofline` and `--dry-run` mode
- multiple packages in one repository

:heavy_minus_sign:
- PythonAPI not specified and documented:
  - [[issue] Provide/document a Python API](https://github.com/dgoodwin/tito/issues/165)
  - README.md:
   > Also, there are no guarantees that tito will not change in future releases, meaning that your custom implementations may occasionally need to be updated.

---

## Usecases

### [Tagging](https://github.com/dgoodwin/tito#tagging-packages)

Tag new releases with incremented RPM version or release.

1. bump the version/release in spec file
2. auto-generate spec file changelog based on git history since last tag
3. commit changes
4. git tag

### [Building](https://github.com/dgoodwin/tito#custom-builders--taggers--releasers)

- Create reliable tar.gz files with consistent checksums from any tag.
- Build source and binary rpms off any tag.

  ```
  $ tito build --help
  Usage: tito build [options]

  Options:
    --tgz                 Build .tar.gz
    --srpm                Build srpm
    --rpm                 Build rpm
    :
  ```


- Build source and binary "test" rpms off most recently committed code.
  ```
  tito build --test
  ```
- Build multiple source rpms with appropriate disttags for submission to the Koji build system.


- Build packages off an "upstream" git repository, where modifications in the "downstream" git repository will be applied as a patch in the source rpm. ([UpstreamBuilder](https://github.com/dgoodwin/tito/blob/0942baa1217ad31cd5c4cbb8750de3db15410672/src/tito/builder/main.py#L701))
- Manage all of the above for a git repository with many disjoint packages within it.

### Releases

- multiple release implementations
- blog posts by msuchy:
  - [How to build in Copr](http://miroslav.suchy.cz/blog/archives/2013/12/29/how_to_build_in_copr/)
  - [How to create new release of RPM package in 5 seconds](http://miroslav.suchy.cz/blog/archives/2013/12/17/how_to_create_new_release_of_rpm_package_in_5_seconds/)
