---
title: Packit as Fedora dist-git CI
authors: mfocko
---

Related links:

- [Epic](https://github.com/packit/packit-service/issues/2453)
- [Research issue](https://github.com/packit/packit-service/issues/2462)

## Current Fedora CI

1. Koji scratch build
1. Installability
1. tmt (if plans are present)

### Zuul as a parallel CI

1. Builts SRPM
1. Submits Koji scratch build
1. Runs RPM linter
1. Runs RPM inspect
1. Tests install
1. Runs tmt

## Possible implementation

### SRPM build

Ideally kept identical. Packit should not be involved in any way that can affect
the results of the SRPM build, i.e., just run `fedpkg srpm` and be done with it.

This can be done within the sandbox as we do for non-scratch builds. However it
might need some tweaking as Packit has specific worfklow.

### Koji scratch build

We are already submitting scratch builds for merged PRs, if configured. This
would just extend the functionality to the non-merged PRs (with need to provide
the SRPM).

### RPM linting, inspect and installability test

There are premade tmt plans that we can run.

:::note Question

Should these be run in parallel or sequentially and fail on first?

:::

### Testing Farm

Different form of request than for upstream jobs.

```json
{
  "id": "2fdee1a0-0746-45ad-ad0c-d3ec8833630b",
  "user_id": "c4af7afe-b95e-4cf1-b989-9c458f0eecf0",
  "token_id": "c4af7afe-b95e-4cf1-b989-9c458f0eecf0",
  "test": {
    "fmf": {
      "url": "https://src.fedoraproject.org/forks/packit-stg/rpms/packit",
      "ref": "0d4dfcfcc2a708f06c65b80404cc022e7bf6bead",
      "merge_sha": null,
      "path": ".",
      "name": null,
      "settings": null,
      "plan_filter": null,
      "test_name": null,
      "test_filter": null
    },
    "script": null,
    "sti": null
  },
  "state": "complete",
  "environments_requested": [
    {
      "arch": "x86_64",
      "os": {
        "compose": "CentOS-Stream-9"
      },
      "pool": null,
      "variables": {
        "KOJI_TASK_ID": "123014869"
      },
      "secrets": null,
      "artifacts": [
        {
          "id": "123014869",
          "type": "fedora-koji-build",
          "packages": null,
          "install": true,
          "order": 50
        }
      ],
      "settings": null,
      "tmt": {
        "context": {
          "arch": "x86_64",
          "distro": "centos-stream-9",
          "initiator": "fedora-ci",
          "trigger": "commit"
        },
        "environment": null
      },
      "hardware": null,
      "kickstart": null
    }
  ],
  "notes": [
    {
      "level": "info",
      "message": "tf-tmt/dispatch-1725615078-80d05f05"
    }
  ],
  "result": {
    "summary": null,
    "overall": "passed",
    "xunit": "…",
    "xunit_url": "https://artifacts.dev.testing-farm.io/2fdee1a0-0746-45ad-ad0c-d3ec8833630b/results.xml"
  },
  "run": {
    "console": null,
    "stages": null,
    "artifacts": "https://artifacts.dev.testing-farm.io/2fdee1a0-0746-45ad-ad0c-d3ec8833630b"
  },
  "settings": null,
  "user": {
    "webpage": null
  },
  "queued_time": 6.892783,
  "run_time": 1207.608357,
  "created": "2024-09-06T09:31:17.471815",
  "updated": "2024-09-06T09:31:17.471844"
}
```

Most notable differences:

- RPMs are provided from Koji scratch build (following Fedora CI, which is
  easier than self-hosting)
- chroot is defined by the branch rather than config

## Technical issues / questions

### Load balancing

### SRPM build

For Zuul is run via `fedpkg srpm`. Then it's provided for the Koji build.

Packit should not interefere with the way the SRPM gets built.

### Propagating Koji build

### RPM for Testing Farm

Zuul provides its own (self-hosted) repository. Fedora CI just refers to the
scratch build.

Self-hosting the repository is not preferred, following the Fedora CI approach
might be the best.

### STI tests

Older format of tests that can be run via Zuul. Based on the TF API, Testing Farm
supports it too. Requesting STI tests from the Testing Farm should be possible,
detection of their presence lies on Packit.

## User perspective

### Fedora

### Fedora SIGs

### CentOS SIGs

## Difficulties depending on the forge

### Pagure

Mainly reliability, it would require retries. Together with normal Packit CI
workflows, considerable overhead.

### GitLab

#### Upstream vs downstream

### Forgejo

#### ogr
