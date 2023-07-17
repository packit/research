---
title: Counting patches in specfiles
authors: csomh
---

Ways to count the number of patches in the packages in a distribution.

## Fedora Rawhide

Download and unpack the specfile archive for the packages currently in
Rawhide:

```
$ curl -LO https://src.fedoraproject.org/repo/rpm-specs-latest.tar.xz
$ tar -xvf rpm-specs-latest.tar.xz
```

Count the number of of specfiles with a given number of patches:

```
$ grep -crE '^Patch[0-9]*:' rpm-specs/ | grep --only-matching -E '[0-9]+$' | sort -g | uniq -c
```

The command above tells how many specfiles there are with 0, 1, 2, ...
patches.

## CentOS Stream

Use `download-stream.py` and specify the stream from which specfiles should be
downloaded. This uses GitLab.com API, so you'll need to specify the token
either by using the GITLAB_TOKEN environment variable or by providing the
'--gitlab-token' option.

```
$ ./download-stream.py c8s
```

After the specfiles are downloaded, use the `rg` command above, to produce a
statistic on the result.

## RHEL

Use `download-rhel.py` to download spec-files for a given RHEL version.

The following will attempt to download specfiles from the `rhel-8.7.0` branch
and save them in the `rhel-8` directory.

```
$ ./download-rhel.py rhel-8.7.0 rhel-8
```

When multiple branches are specified, the specfile will be downloaded from the
branch which is first found in a repository:

```
$ ./download-rhel.py rhel-9.0.0 rhel-9.1.0 rhel-9.2.0 rhel-9
```

## A Deeper Look

To have a better understanding of this data, one could produce CSV files with
"package" and "patches" columns, and load this data with pandas for further
inspection.

```
$ grep -crE '^Patch[0-9]*:' rhel-9/  | sed -e 's/:/,/' -e 's/^rhel-9\///' -e 's/\.spec,/,/' > rhel-9.csv
```

Then in Python:

```python
import pandas as pd

rhel_9 = pd.read_csv("rhel-9.csv", names=["package", "patches"], index_col=0)
c9s = pd.read_csv("c9s.csv", names=["package", "patches"], index_col=0)

# Get packages with more than 10 patches
p_rhel_9 = set(rhel_9[rhel_9["patches"] >= 10].index)
p_c9s = set(c9s[c9s["patches"] >= 10].index)

# Packages which have more than 10 patches both in c9s and rhel-9
print(p_rhel_9 & p_c9s)
```
