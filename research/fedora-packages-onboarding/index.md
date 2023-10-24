---
title: Fedora package candidates for onboarding to downstream automation
authors: lbarcziova
---

The directory contains a script `get-maintainers.py` which goes through all fedora spec files
and runs some checks on them (see the details in script).
It exports a list of top n (by default 20) maintainers with the biggest number of packages that fit the
conditions.

## Usage

1. Change the directory

```
$ cd research/fedora-packages-onboarding
```

2. Download the specfiles and extract

```
$ curl -LO https://src.fedoraproject.org/repo/rpm-specs-latest.tar.xz
$ tar -xvf rpm-specs-latest.tar.xz
```

3. Run the script

```
$ ./get-maintainers.py
```

or with specifying number of maintainers

```
$ ./get-maintainers.py 30
```

4. List of the maintainers will be exported to `maintainers.json`
