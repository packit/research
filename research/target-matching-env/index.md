---
title: Running operations in target-matching environments
authors: lbarczio
---

For some of the operations run in our service, it would be beneficial
to run them in target-matching environment, e.g. parsing the specfile placed
in F41 branch should happen on F41. Currently, we base our images
on Fedora 41.

## Use cases

- user-configured commands (`actions` in config)
  - affected jobs: `copr_build`, `propose_downstream`, `pull_from_upstream`
  - run in on demand pods in `sandbox` (dedicated Openshift project)
- building SRPM
  - affected jobs:
    - `upstream_koji_build` - in `long-running` workers
    - `copr_build` - in Copr, we just pass the required env as an argument for the API call
- specfile parsing
  - for getting version, manipulating changelog, etc. during release syncing
  - affected jobs: `pull_from_upstream`, `propose_downstream`
  - run in `long-running` workers
- potentially new use cases if Packit runs as Fedora dist-git CI

## Possible solutions

### container-based solutions

#### dedicated workers for each Fedora version

- for building SRPM, running release syncing (=> specfile parsing)
- build separate images for each Fedora version
- use Celery for task routing; tasks requiring specific environments would be routed accordingly
- by default, tasks could run on the "main" worker (e.g. currently F41-based).
- tasks requiring target-matching environments would be refactored (e.g. release syncing for
  all branches (currently one task) will need to be split)
- suggestion from review: for better load balancing, we could consider running all the tasks except `process_message` utilising
  this routing logic, i.e. the tasks would be refactored so that one task runs for specific target and is always routed accordingly from `process_message`
- potential waste of resources
- shouldn't introduce any delays

#### sandcastle adjustments

- for running `actions`
- build separate images for each Fedora version
- adjust the code running sandcastle to dynamically pass the image reference
- for commands not specified by users, e.g. `rpmbuild`, `fedpkg`, we could also utilise
  sandcastle, without the need of deploying the pod in different project, but this would lead
  to slower execution (overhead of scheduling the pods)

### Copr resalloc

- set up a custom resalloc instance, most of the tooling would need to be implemented
- communication via SSH
- relying on external infra, might be slow

### Testing Farm reservations

- [docs](https://docs.testing-farm.io/Testing%20Farm/0.1/cli.html#reserve)
- `testing-farm reserve` to get a chosen OS
- communication via SSH
- there are already users using it in CI for provisioning systems for Ansible Molecule
- not yet a proper API, a proper supported use case in plan
- in the future a target machine could be obtained in <30s
- still relying on external infra
- could be considered for running actions

### mock

- [mock in a container](https://rpm-software-management.github.io/mock/#mock-inside-podman-fedora-toolbox-or-docker-container)
  requires privileged mode which is not possible in our current OpenShift instance

## Next steps

- with switching to F41 based image, we have unblocked users needing the latest RPM macros
- once there is more user demand for any of the use cases, we can consider the options above, depending on
  the particular use-case
  - the container-based solution with dedicated workers looks like the best fit for running the whole tasks to me
  - for the `actions`, the `sandcastle` adjustments could be enough,
    but for the future I could see using TF reservations as a complete replacement
