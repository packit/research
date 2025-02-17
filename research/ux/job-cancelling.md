---
title: Job cancelling
authors: mfocko
---

:::info

- [Original issue](https://github.com/packit/packit-service/issues/5)
- [Backing issue](https://github.com/packit/packit-service/issues/2694)

:::

## Motivation

Saving up resources of the external services (especially for projects running
builds / tests for an extensive matrix of _architectures × releases × distros_).

## Finding the jobs to cancel

:::warning

We also have to consider subsequent jobs, i.e., running TF after Copr build
succeeds.

:::

We should differentiate here based on the trigger / event.

:::note

In general, when pushing to branches git forges usually provide previous commit
hash, parse and provide it in the event, so that we can optimize the lookup
in the database on our side.

:::

### Triggered by commit / pull request

:::note

In both cases we should be given previous commit hash.

:::

In the most ideal scenario, we should utilize the provided previous commit, to
find the latest pipeline that might be still running.

:::note Arch discussion

Do not cancel builds/tests on commit trigger for now.

:::

#### Lookup based on the commit hash

:::note Arch discussion

Start with the cheapest approach, i.e., this one.

:::

Finding the latest pipeline that might be still running based on the commit hash
can be done by lookup through `PipelineModel` and `ProjectEventModel` (provided
via `project_event_id`) that has a commit hash attribute.

#### Alternative approach

:::note

Looks much simpler using the ORM, but boils down to the enumeration below
anyways.

:::

1. Join on `pipelines × project events`
1. Filter by event type (commit or pull request)
1. Join on `(pipelines × project events) × specific events`
1. And then find latest by
   - commit: branch
   - pull request: PR ID

### Triggered by release

tl;dr _n/a_

Doesn't make sense to consider, since there is no reasonable scenario for
_re-releasing_.

### Subsequent jobs

Given the pipelines we store, it shouldn't be hard, basically similar approach
as for cancelling the initial job, just gotta check any other fields in the same
row.

## Cancelling the jobs themselves

Given that we know what we want to cancel, it is relatively easy to execute with
the most critical services that we integrate (VM Image Builder is rather vague
in the description of what `DELETE` on a compose means and OpenScanHub has no
mention of allowing to cancel running scans).

### Copr

With build ID it's possible to easily cancel the job via the following API call
on our side:

```py
# packit/copr_helper.py
self.copr_client.build_proxy.cancel(build_id)
```

[Link to Copr docs](https://python-copr.readthedocs.io/en/latest/client_v3/proxies.html#copr.v3.proxies.build.BuildProxy.cancel)

### Testing Farm

TF has an [API endpoint](https://api.testing-farm.io/redoc#operation/delete_test_request_v0_1_requests__request_id__delete) for deleting the test requests:

```
DELETE https://api.testing-farm.io/v0.1/requests/{request_id}
```

### Koji

There are multiple API calls:

- cancelling a specific build - [`cancelBuild`](<https://koji.fedoraproject.org/koji/api#:~:text=cancelBuild(buildID%2C%20strict%3DFalse)>)
- cancelling a task - [`cancelTask`](<https://koji.fedoraproject.org/koji/api#:~:text=cancelTask(task_id%2C%20recurse%3DTrue)>)
- cancelling a “full” task - [`cancelTaskFull`](<https://koji.fedoraproject.org/koji/api#:~:text=cancelTaskFull(task_id%2C%20strict%3DTrue)>)

:::note Arch discussion

Do not consider for now, but could be beneficial for saving resources of the
Fedora Infra once we run as a _Fedora CI_.

:::

### VM Image Builder

It **appears** that it is possible to _delete_ a compose:

```yaml
/composes/{composeId}:
  delete:
    description: |
      Deletes a compose, the compose will still count towards quota.
    operationId: deleteCompose
    responses:
      "200":
        description: OK
    summary: delete a compose
  get:
    description: status of an image compose
    operationId: getComposeStatus
    responses:
      "200":
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ComposeStatus"
        description: compose status
    summary: get status of an image compose
    tags:
      - compose
  parameters:
    - description: Id of compose
      in: path
      name: composeId
      required: true
      schema:
        example: 123e4567-e89b-12d3-a456-426655440000
        format: uuid
        type: string
```

Though based on the description, as you can see, it still counts towards the
quota and there's no mention that it would cancel running image build.

### OpenScanHub

Based on a brief look through the docs, it appears that it is not possible to
cancel running scans.

## Breakdown

Suggested splitting into subtasks:

- [ ] Implement cancelling in the Packit API (knowing what needs to be
      cancelled, i.e., Copr build ID, Testing Farm request, etc.)

- [ ] Implement methods that would yield respective jobs to be cancelled, i.e.,
      after retriggering a Copr build, we should get a list of running Copr
      builds associated with the previous trigger

- [ ] Automatically cancel running jobs once an update happens, e.g., push to
      a PR, branch, or retriggering via comment.

- [ ] Improve the previous method by incorporating subsequent jobs

  - _NOTE_: this might get more complex after implementation of job dependencies

- [ ] Allow users to cancel running jobs via comment

- [ ] Allow users to cancel running jobs via custom GitHub Check _action_

  - _NOTE_: custom action can incorporate additional metadata provided by us,
    therefore cancelling this way could be pretty cheap (there would be no need
    to deduce which jobs need to be cancelled)
  - _NOTE_: there's a smallish issue of differentiating of what should be
    cancelled (could be handled by multiple custom actions), for example:
    - _Copr build for specific target_
    - _Copr build for all targets_
    - _Copr build for all targets matching an identifier_

- [ ] (optionally, low-prio) Allow this to be configurable

  - _use case_: I want to be able to test multiple Copr builds, even if they
    were triggered in a succession of pushes
  - _NOTE_: this use case could be more beneficial for running _commit_ events
    rather than PR, i.e.

    > as a maintainer I'd like to retain **all** builds
    > that were pushed to the `main`, or `stable`
