#  DLRN

- DLRN builds and maintains yum repositories following upstream commits from a Git repo.
- [ :computer: github.com/softwarefactory-project/DLRN](https://github.com/softwarefactory-project/DLRN), [ :scroll: documentation](https://dlrn.readthedocs.io/en/latest/intro.html)
- ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dlrn.svg), [![PyPI](https://img.shields.io/pypi/v/dlrn.svg)](https://pypi.org/project/dlrn/), [ :package: fedora packages](https://src.fedoraproject.org/rpms/dlrn)

:heavy_plus_sign:
- automatic builds of packages
- generating of yum repositories
  - DLRN does not delete any generated repositories.
  - Repositories are unique. e.g. `/centos7/current/delorean.repo` can point to `/centos7/42/0c/420c638d6325d1ccf50eb5fe430c5d255dcbfb94_52cbbfe7`
- [REST API](https://dlrn.readthedocs.io/en/latest/api.html)
  - `/api/last_tested_repo`
  - `/api/repo_status`

:heavy_minus_sign:
- heavily coupled to rdopkg/OpenStack workflow (need to use [RPM Packaging for OpenStack](https://github.com/openstack/rpm-packaging))
