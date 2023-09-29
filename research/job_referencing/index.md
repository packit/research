---
title: Job referencing
authors:
  - mmassari
sidebar_position: 1
---

# Job referencing

## Already implemented use cases

The following dependencies use cases are not exposed to the user.
This are implementation details useful as a starting point for thinking about user defined dependencies.

### COPR build depends on SRMP build

[Here](https://github.com/packit/packit-service/blob/16236087fb8071c83b3802464f3af504f4fb933e/packit_service/worker/handlers/copr.py#L136-L203) we build both the SRPM and the COPR packages (and the COPR package depends on the SRPM one).
We don't need any special data to be saved in the database, we just check for the existance of the SRPM build.
This code is triggered by a `CoprBuildStartEvent` event, this event is sent by COPR both for the SRPM package build and for the COPR package build, in this way we run twice the code and we can deal with the dependency.

### Tests depends on COPR builds

[Here](https://github.com/packit/packit-service/blob/16236087fb8071c83b3802464f3af504f4fb933e/packit_service/worker/handlers/testing_farm.py#L202-L241) we check that a COPR build exist for every target we should run a test for.
If not build is found we run a `CoprBuldHandler` instance.
For every `CoprBuildEndEvent` the `CoprBuildEndHandler` is able to run again the `TestingFarmHandler` if needed.
No special data is stored in the database, the COPR build is searched using: project name, commit sha, copr build owner and target.

## New use cases

### Tests depends on specified COPR builds

Since it is possible to add identifiers for jobs, we allow defining multiple Copr build jobs and multiple TF jobs. In that case, Packit Service doesn't know what Copr build job to use for the particular TF job.

For this purpose, we could introduce a new field for job configs which would allow the referencing, for example:

```yaml
- job: copr_build
identifier: "build1"
trigger: pull_request
actions: ...
- job: copr_build
identifier: "build2"
trigger: pull_request
actions: ...
- job: tests
identifier: "tests2"
trigger: pull_request
build_identifier: "build1"
- job: tests
identifier: "tests2"
trigger: pull_request
build_identifier: "build2"
```

#### The easiest solution I see

I don't think we need anything more in the database to be able to retrieve the copr build id. We need the data given in the `copr_build` job matching the specified `build_identifier` name in the `tests` job, plus all the data we are already using in the search like the `commit_sha`.
We need to add the `build_identifier` key in config.
We need to modify [this code](https://github.com/packit/packit-service/blob/16236087fb8071c83b3802464f3af504f4fb933e/packit_service/worker/handlers/testing_farm.py#L202-L241) in a way that it is able to retrieve the proper `build_id`.

#### `build_identifier` key name or?

Another suggestion was to use `after` as a name for the key. I like it but our implementation, if made as specified above, will not be generic. For this reason I would rather prefer `after_build` or `build_identifier` to mark the fact that in the test job we are waiting for a build job.

### Monorepo: Package dependencies

The following is the [RFE](https://github.com/packit/packit/issues/1903) by LecrisUT

```
packages:
A:
depends:
- B
- name: C
rebuild: true
B: ...
C: ...
```

at first I would simplify it like:

```
packages:
A:
depends:
- B
- C
B: ...
C: ...
```

I would always rebuild everything for every package but we can enhance the code and if a package has no changes in the given `commit_sha` and it does not depend on changed packages, we can simply copy lines from the previous database pipeline, filling the database as if the jobs were run.

#### The easiest solution I see following what we are already doing for copr builds and tests

We should [create tasks](https://github.com/packit/packit-service/blob/16236087fb8071c83b3802464f3af504f4fb933e/packit_service/worker/jobs.py#L464-L497) only for those packages that do not depend on other packages.
When running, as an example, the COPR build for the latest dependent package in the list (C in our example), at the end of the handler we can create the COPR build tasks for package A (if any).
This can be done for all the kinds of job we directly start at [this lines](https://github.com/packit/packit-service/blob/16236087fb8071c83b3802464f3af504f4fb933e/packit_service/worker/jobs.py#L464-L497).

We can change `bodhi` jobs in a way that they will do nothing, apart from starting new `bodhi` tasks for other packages, unless they belong to a package not required by another package. Ideally only package A, in this example, should do a `bodhi` update if I am not wrong. Or at least we should be able to skip doing something in this job during the chain of dependencies.

I think we don't need changes in the database schema to be able to implement this solution.
We need to add the `depends` or `depends_on` key to the schema. I slightly prefer the `depends` key, but not strong opinions on that.

### Request new feature: support side tag for multi package update

This is the [RFE](https://github.com/packit/packit/issues/1870).

I am not really sure I am getting the point here. But they are talking about a multi-package feature and for this reason I assume they need to use the monorepo syntax (otherwise we have no way to reference the packages).
If they can and want to use the monorepo syntax then I think that the package dependencies solution for the monorepos would solve their problems too. Or am I wrong?

## Drawbacks

I see just a drawback in the previous solutions, the code is getting more and more complex to read (I mean to grasp the execution order) and test.
I think `Celery` was well suited for tasks which didn't depend on each other, now that dependencies are growing quickly I feel it is like a limit. I would like to be able to have communication between tasks and suspend the execution without exiting.
I think that a code using `asyncio`, as an example, could be more readable and testable.

Let's take as an example the simple dependency we have between COPR builds and SRPM builds

[This code](https://github.com/packit/packit-service/blob/16236087fb8071c83b3802464f3af504f4fb933e/packit_service/worker/handlers/copr.py#L136-L203) is performing both builds. But it is not straightforward to know that this code is called twice, because there are two `CoprBuildStartEvent`(s) sent by the COPR server. The execution flow is not obvious and not easily testable, even though this is a really simple example.

I would like to be able to write something similar using `asyncio`.
As far as I can understand it [temporalio](https://docs.temporal.io) would give us this flexibility. For this reason I wrote down some _python pseudo code_ using `temporalio`. I don't really know it so I can be missing something.

```python
from temporalio.client import Client

client = await Client.connect("localhost:7233")

# Run a worker for the workflow
async with Worker(
  client,
  task_queue="project-sha-event-queue",
  workflows=[COPRBuildHandler],
  activities=[submit_build_srpm,
              submit_build_copr,
              update_ux]
  ):

  # While the worker is running, use the client to start the workflow.
  # Note, in many production setups, the client would be in a completely
  # separate process from the worker.
  result = await client.execute_workflow(
    COPRBuildHandler.run,
    id="copr-build-for-project-and-sha",
    task_queue="project-sha-event-copr-build-queue",
    execution_timeout=timedelta(minutes=60)
```

```python
from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

@activity.defn
async def submit_build_srpm():
  ...

@activity.defn
async def submit_build_copr():
  ...

@activity.defn
async def update_ux():
  ...

class COPRBuildHandler:

  def __init__(self) -> None:
    self._srpm_builded = False
    self._copr_builded = False

  @reacts_to(event=CoprBuildEndEvent)
  @workflow.signal
  def submit_srpm_build_ended():
    if event.chroot == COPR_SRPM_CHROOT:
      self._srpm_builded = True

  @reacts_to(event=CoprBuildEndEvent)
  @workflow.signal
  def submit_copr_build_ended():
    if event.chroot != COPR_SRPM_CHROOT:
      self._copr_builded = True

  @workflow.run
  async def run(self):

    srpm_activity_handle = workflow.start_activity(
      submit_build_srpm,
      start_to_close_timeout=timedelta(seconds=1),
      ...
      )
    await workflow.wait_condition(lambda: self._srpm_builded)

    update_ux_handle = workflow.start_activity(
      update_ux,
      start_to_close_timeout=timedelta(seconds=1),
      ...
      )

    build_copr_handle = workflow.start_activity(
      build_copr,
      start_to_close_timeout=timedelta(seconds=1),
      ...
      )
    await workflow.wait_condition(lambda: self._copr_builded)

    update_ux_handle = workflow.start_activity(
      update_ux,
      start_to_close_timeout=timedelta(seconds=1),
      ...
      )
```

As far as I understand from the `temporalio` documentation, the framework is in charge of putting this `CoprBuildHandler workflow` in a sleeping queue while it is waiting for a signal and waking up it later. So we don't need to exit the workflow and the order of the activities is well visible in the `workflow` code.

There is another small improvement I see using a solution like this one instead of doing what we are already doing.
I don't think that the `CoprBuildEndHandler` should deal with the `TestingFarmHandler` and viceversa, this is dangerous, and the more dependencies we will introduce the more we will need this dangerous cross referencing.

Something above them should be able to orchestrate and know the jobs, and I think a `workflow` is exactly what we are missing here.

## Conclusion

From my point of view we have two possible ways to implement job referencing:

1.  We can keep doing what we are already doing: use Celery and spawn different tasks when we need them.

    PRO: this is the quickest solution

    CON: it does not scale well, every new reference makes our code less readable/testeable and makes managing errors harder

2.  Introduce a workflow engine with support for tasks communication

    PRO: it should make our code more readable/testeable and we should be able to better manage error handling

    CON: it will take us far more time

An hybrid solution could be: go with solution 1 and implement just those job referencing we believe are actually/really needed.
If we realize we would need other job referencing in future, we want to make job referencing more generic or we want the user to be able to build his own workflow then we need to start studying a workflow manager (like temporal) and planning a change in our core code base to go with solution 2. We will need to adjust the code and all the **configuration keys**, used with solution 1, when we will decide to go with solution 2.
