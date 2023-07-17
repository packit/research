---
title: Triggering testing farm tests with builds from other PRs (projects)
authors: lbarczio
---

Use case: having 2 builds for different PRs, being able to trigger TF tests using both builds with a Packit
command comment in one PR

## Architecture notes

`Copr allows interlinking Copr projects so that TF could just install proper packages and Copr would enable the whole dependency chain`

- it is possible to specify `runtime_dependencies` in Copr: https://pagure.io/copr/copr/pull-request/2245#
  (should be released soon) - list of external repositories that will be automatically enabled together with this project repository
- we would need to have a dynamic way of specifying these `runtime_dependencies`
- since we want concrete packages to be installed in TF (we pass the build ID and NVRs), this wouldn't be enough
  - if users build all the PRs in one Copr repo (e.g.
    [leapp](https://github.com/oamg/leapp/blob/351cfe75ce1a7e10d7e565d9fa0bdc946a9af66d/.packit.yaml#L9) and
    [leapp-repository](https://github.com/oamg/leapp-repository/blob/8b228941d34b3fcf4322353806fdcafa9fbba550/.packit.yaml#L26) build their PRs in one common Copr repo)
    we cannot enforce with this solution what should be installed during tests (build ID, NVRs).

## Possible implementation

### Requirements

The requirement would be to have enabled Packit Copr build job on both repositories where the PRs are happening.
Then, the testing farm test job could be triggered by comment specifying the other pull request ID
and we would rely on builds being already done by Packit.

### Implementation

We should have everything needed in our database and be able to get Copr build ID and package NVRs via having the other PR ID from there:
`PullRequestModel.get_or_create(pr_id=xy, namespace=xy, repo_name=xy, project_url=xy).get_copr_builds()`
and determine the latest build comparing one of the stored times (task_accepted, build_submitted).

With having the Copr build ID and package NVRs of the other PR Copr build, we could just pass these
into the Testing farm payload.

Process:

1. Try to get the PR specified in the comment from the DB - if not able to find, report this to user
2. Get the latest Copr build for the PR from the DB - if no Copr build, report this to user
3. Append artifact including the ID of the Copr build and NVRs to the payload for Testing Farm
4. Trigger the tests
5. When reporting the status, make sure it is done on the "main" PR (probably corresponding to the
   first one build in the artifacts)

#### Another option

There is also an option to get the needed info via Copr API, but in that case, we would need to know
the name of the Copr project where the build from another PR is. We could require the build to be in
the default-named Copr repo (this way we could easily construct the default name of the repo for other PR
and work with that repo via API - get the latest build ID, NVRs). Allowing non-default Copr project would mean
we would need to obtain the package config from the repo where the other PR is created so that we
can work with the correct Copr project.

### Models

Currently, each pipeline model can be linked to one Copr build model (and also one SRPM model) and one TF model at most.
Options:

1. Do not store the information about the other PR build. Consequences => the other PR build would not
   be displayed in the dashboard, we would lose this information.
2. Do not modify the PipelineModel, store this as 2 pipelines and store the relationship of the pipelines.
3. Modification of PipelineModel probably does not make sense since we have to store not only the copr build, but also
   the connected SRPM build.

### Retriggering

How can a testing farm job be retriggered:

1. via comment - we would require each time to explicitly pass the PR related attributes
2. via Github check - we would trigger the tests only with the build from the current PR

### Syntax of the command

Do we want to support specifying also Git forge?

- from the implementation point, this should not be a problem (the data should be stored in the same way)
- we can behave similarly as for the default Copr project naming schema: implicitly Github PRs

suggestions:

1. `/packit test --pr-id 123 --repository repo --namespace namespace (--forge github.com)`

2. `/packit test namespace/repo#123`

- this looks like a preferred format

3. `/packit test github.com/namespace/repo#123`

4. `/packit test github.com/namespace/repo#pr:123`
