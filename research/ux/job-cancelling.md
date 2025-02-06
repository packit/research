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

:::note

When pushing to branches git forges usually provide previous commit hash, parse
and provide it in the event, so that we can optimize the lookup in the database
on our side.

:::

_TODO_

### Subsequent jobs

_TODO_

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

_TODO_
