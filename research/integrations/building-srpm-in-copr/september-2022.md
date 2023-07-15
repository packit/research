---
title: Statistics as of September '22
authors: mfocko
---

Building of SRPMs in Copr has been merged on service' side on January 25th '22.

## tl;dr

- 232k SRPMs built since 25th January.
- 119k of them built in Copr.
- 3.14% of SRPMs built in Copr failed.
- 3x more projects not using Copr for SRPM builds.

## Count all SRPM builds since SRPM build in Copr was merged

```sql
SELECT COUNT(*) FROM srpm_builds INNER JOIN pipelines ON srpm_builds.id=srpm_build_id INNER JOIN job_triggers ON job_trigger_id=job_triggers.id WHERE datetime >= '2022-01-25';
```

```
 count
--------
 232672
```

## Count all SRPM builds done in Copr

```sql
SELECT COUNT(*) FROM srpm_builds INNER JOIN pipelines ON srpm_builds.id=srpm_build_id INNER JOIN job_triggers ON job_trigger_id=job_triggers.id WHERE datetime >= '2022-01-25' AND srpm_builds.copr_build_id <> '';
```

```
 count
--------
 119457
```

Overall we get 51.34% of SRPM builds done in Copr.

## Inspect the usage of SRPM builds in Copr by the trigger

```sql
SELECT COUNT(*) FROM srpm_builds INNER JOIN pipelines ON srpm_builds.id=srpm_build_id INNER JOIN job_triggers ON job_trigger_id=job_triggers.id where srpm_builds.copr_build_id <> '' AND type='‹type goes here›';
```

| Trigger type   | Count  | Percentage |
| -------------- | ------ | ---------- |
| `pull_request` | 110190 | 92.24      |
| `branch_push`  | 8805   | 7.37       |
| `release`      | 402    | 0.34       |

## Failed SRPM builds in Copr

```sql
SELECT COUNT(*) FROM srpm_builds INNER JOIN pipelines ON srpm_builds.id=srpm_build_id INNER JOIN job_triggers ON job_trigger_id=job_triggers.id where srpm_builds.copr_build_id <> '' AND status='failure';
```

```
 count
-------
  3758
```

Overall 3.14% of SRPM builds done in Copr are failed.

## Projects using Copr

### Pull requests

```
      namespace
----------------------
 jkonecny12
 sdaps
 nmstate
 rhinstaller
 LenkaSeg
 cockpit-project
 ansible-community
 StephenCoady
 evverx
 osbuild
 systemd
 TomasTomecek
 martinpitt
 oamg
 storaged-project
 fedora-infra
 systemd-ci-incubator
 avocado-framework
 mfocko
 packit
 redhat-performance
(21 rows)
```

### Branch pushes

```
   namespace
---------------
 jkonecny12
 majamassarini
 mfocko
 oamg
 osbuild
 packit
 rhinstaller
(7 rows)
```

### Releases

```
    namespace
-----------------
 cockpit-project
 fedora-infra
 martinpitt
 osbuild
 packit
 StephenCoady
(6 rows)
```

## Projects »not« using Copr

### Pull requests

```
        namespace
-------------------------
 rear
 t0xic0der
 Madeyro
 jkonecny12
 sdaps
 kdudka
 nmstate
 matusmarhefka
 facebook
 containers
 facebookincubator
 ComplianceAsCode
 rhinstaller
 LenkaSeg
 dmnks
 fedora-sysv
 sgallagher
 antonvoznia
 OpenSCAP
 ondrejbudai
 cockpit-project
 csutils
 ansible-community
 phracek
 abrt
 fedora-iot
 rpm-software-management
 StykMartin
 vex21
 evverx
 redhat-plumbers
 osbuild
 majamassarini
 pcahyna
 systemd
 TomasTomecek
 flexmock
 martinpitt
 facebookexperimental
 httpie
 bus1
 oamg
 rebase-helper
 fedora-infra
 storaged-project
 SecurityCentral
 user-cont
 xsuchy
 avocado-framework
 dbus-fuzzer
 sosreport
 varlink
 r0x0d
 beaker-project
 psss
 sopos
 candlepin
 teemtee
 packit
 restraint-harness
 containerbuildsystem
 beakerlib
 Commonjava
 redhat-performance
 dracutdevs
 osandov
 cronie-crond
 fedora-modularity
(68 rows)
```

### Branch pushes

```
        namespace
-------------------------
 jkonecny12
 kdudka
 thrix
 facebook
 facebookincubator
 rhinstaller
 besser82
 ondrejbudai
 csutils
 abrt
 cri-o
 rpm-software-management
 osbuild
 majamassarini
 TomasTomecek
 lachmanfrantisek
 facebookexperimental
 oamg
 python-bugzilla
 ostreedev
 psss
 teemtee
 packit
 beakerlib
 dracutdevs
 osandov
(26 rows)
```

### Releases

```
  namespace
-------------
 cri-o
 facebook
 fedora-sysv
 oamg
 packit
 t0xic0der
(6 rows)
```

## Projects not using Copr in the last 3 months

### Pull requests

```
        namespace
-------------------------
 rear
 Madeyro
 kdudka
 nmstate
 facebook
 containers
 facebookincubator
 rhinstaller
 ComplianceAsCode
 dmnks
 fedora-sysv
 sgallagher
 antonvoznia
 OpenSCAP
 ondrejbudai
 csutils
 ansible-community
 abrt
 fedora-iot
 rpm-software-management
 vex21
 evverx
 redhat-plumbers
 majamassarini
 pcahyna
 systemd
 TomasTomecek
 martinpitt
 oamg
 rebase-helper
 storaged-project
 SecurityCentral
 user-cont
 avocado-framework
 xsuchy
 dbus-fuzzer
 sosreport
 varlink
 r0x0d
 beaker-project
 psss
 sopos
 candlepin
 teemtee
 packit
 restraint-harness
 containerbuildsystem
 beakerlib
 Commonjava
 redhat-performance
 dracutdevs
 osandov
 cronie-crond
 fedora-modularity
(54 rows)
```

### Branch pushes

```
        namespace
-------------------------
 jkonecny12
 kdudka
 facebook
 facebookincubator
 rhinstaller
 csutils
 cri-o
 rpm-software-management
 lachmanfrantisek
 oamg
 ostreedev
 psss
 teemtee
 beakerlib
 osandov
(15 rows)
```

### Releases

```
  namespace
-------------
 cri-o
 facebook
 fedora-sysv
 oamg
(4 rows)
```

## Notes

### Trigger type mapping

| Trigger Type   | Table              |
| -------------- | ------------------ |
| `pull_request` | `pull_requests`    |
| `branch_push`  | `git_branches`     |
| `release`      | `project_releases` |

### Queries

To get SRPMs built in Copr:

```sql
SELECT distinct(namespace) FROM srpm_builds INNER JOIN pipelines ON srpm_builds.id=srpm_build_id INNER JOIN job_triggers ON job_trigger_id=job_triggers.id INNER JOIN ‹TABLE› ON trigger_id=‹TABLE›.id INNER JOIN git_projects ON project_id=git_projects.id WHERE srpm_builds.copr_build_id <> '' AND type='‹TRIGGER_TYPE›' AND datetime >= '2022-01-25';
```

To get SRPMs built in Sandcastle:

```sql
SELECT distinct(namespace) FROM srpm_builds INNER JOIN pipelines ON srpm_builds.id=srpm_build_id INNER JOIN job_triggers ON job_trigger_id=job_triggers.id INNER JOIN ‹TABLE› ON trigger_id=‹TABLE›.id INNER JOIN git_projects ON project_id=git_projects.id WHERE srpm_builds.copr_build_id IS NULL AND type='‹TRIGGER_TYPE›' AND datetime >= '2022-01-25';
```
