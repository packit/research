---
title: Source-git in Zuul
authors: csomh
---

# Source-git in Zuul

## Zuul YAML programming 101

Some docs: https://gitlab.com/redhat/centos-stream/ci-cd/ci-cd-docs/-/blob/main/assemblies/assembly_test-merge-requests.adoc

Repositories to clone and grep through:

- https://gitlab.com/redhat/centos-stream/ci-cd/zuul/jobs-config
- https://gitlab.com/redhat/centos-stream/ci-cd/zuul/jobs
- https://pagure.io/zuul-distro-jobs/tree/master

Matrix channel to reach Zuul maintainers: https://app.element.io/#/room/#sf-ops:matrix.org
Mainly ask fbo (Fabian).

CentOS Stream Zuul jobs:

- [Enable Zuul for selected repositories and apply job templates](https://gitlab.com/redhat/centos-stream/ci-cd/zuul/jobs-config/-/blob/master/zuul.d/projects.yaml)
- [Job template definitions](https://gitlab.com/redhat/centos-stream/ci-cd/zuul/jobs/-/blob/master/zuul.d/templates.yaml)
- [Job definitions](https://gitlab.com/redhat/centos-stream/ci-cd/zuul/jobs/-/blob/master/zuul.d/jobs.yaml)
- [An actual role](https://pagure.io/zuul-distro-jobs/blob/master/f/roles/rpminspect/tasks/main.yaml)

## High level work items to define a Zuul job for source-git

This is a rough proposal after reading through the links above. More tasks
might surface after things are checked in more detail.

In the context of Zuul in CentOS Stream a build is actually a [mock-build
job]. This one starts with executing the [centpkg-fetch-sources] role, which
executes `centpkg sources` in the dist-git repository.

So, in order to be able to build and test MRs from a source-git repository:

Have something like a `source-git-mock-build` playbook (executed as part of a
`source-git-build` project-template), which would execute a
`source-git-srpm-build` role (to be implemented; should set an `srpm` fact
with the path of the SRPM) and a `mock-build` role.

It'll need a check to figure out how this `source-git-build` template needs to
pass on the artifact produced to the playbook/roles executed by the `test`
project-template.

Once the above is ready, enable zuul on
`redhat/centos-stream/src/<selected_repositories>`.

Testing this might not be so straightforward, as most probably changes will
need to be merged before giving them a try. A separate namespace should be
used to test on, for example `gitlab.com/packit-service/src`, with some
source-git repositories forked into it.

Tip: In order to check what an actual Zuul pipeline is doing, check one of the
[open MRs in centos-stream/rpms] and navigate to the logs of a Zuul pipeline
run.

[mock-build job]: https://gitlab.com/redhat/centos-stream/ci-cd/zuul/jobs/-/blob/master/zuul.d/jobs.yaml#L2
[centpkg-fetch-sources]: https://pagure.io/zuul-distro-jobs/blob/master/f/roles/centpkg-fetch-sources/tasks/main.yaml
[centos-stream/rpms]: https://gitlab.com/groups/redhat/centos-stream/rpms/-/merge_requests
