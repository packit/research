---
title: Automation for moving the stable branches
authors: lbarczio
---

Every Friday we move the stable branches of our repositories so that new `prod` images are rebuilt
for Packit Service. There are still more and more repositories which
we need to move the stable branches for and this work is repetitive and can be done automatically.

Repositories which we currently need for Packit Service:

- packit
- packit-service
- packit-service-fedmsg
- packit-service-centosmsg
- sandcastle
- dashboard
- tokman

- ogr (at the moment we have only master branch for it,
  but we planned to create a stable branch for it as well)

Dependencies (order of moving):

- [packit -> packit-service](https://github.com/packit/packit-service/blob/a1ba5988ce2a2409b4f52f05324587303b52e676/files/install-deps-worker.yaml#L50)
- [ogr -> packit-service](https://github.com/packit/packit-service/blob/a1ba5988ce2a2409b4f52f05324587303b52e676/files/install-deps-worker.yaml#L52)

AC:

- have a mechanism to determine whether stage works fine (the decision would need to be approved by human)
  and move the stable branches to appropriate commit hashes

## Solution

- create a script which runs the validation of stage and afterwards moving the branches (in one / 2 different scripts)
- run the script manually/automatically(job)
- what to do when validation for stage fails
  - running automatically - notify us - how: e.g.message in Sentry
  - running manually - output failure
- specific commit-hashes can be defined (so that not the latest commit-hash is used), e.g.:
  `python3 ./move-branches.py --packit-service=1787687aba71`
  would move packit-service to the `1787687aba71` and others to the latest commit in `master`

### Determine whether stage works

Staging app uses images built from master branches, therefore if stage works
as expected, we should be okay to move all stable branches to the latest commits.
For this we could use:

- since the validation script runs on our `hello-world` repository, where the staging instance is enabled,
  we have the information about results of builds and tests triggered in the morning by the validation script,
  we can somehow check the results for stage (e.g. Github flags for stage)
- check new unresolved sentry issues from stage
- final decision done by us

### Move the stable branches

For moving the stable branches we can use e.g. Github API.
For each repo:

- check whether `master` and `stable` are even, if yes, do nothing
- know the commit-hash we want to update the stable branch to
  - default, when stage works: get last commit-hash from `master`
  - specified by us
- update the stable branch by this commit-hash
- if running automatically, we need to use an account with appropriate permissions

## Possible plan

1. Create a script for moving the stable branches, run it manually (stage validation done by us).
2. Implement some sort of validation of the stage which would need to be approved by us.
3. (optional) Deploy periodic job which would run both.
