---
title: Temporal
authors: TomasTomecek
---

![https://docs.temporal.io/](https://temporal.io/images/logos/logo-temporal-with-copy.svg)

From the docs:

> Temporal is a scalable and reliable runtime for Reentrant Processes called Temporal Workflow Executions.
>
> A Temporal Workflow Execution is a durable, reliable, and scalable function execution. It is the main unit of execution of a Temporal Application.
>
> Each Temporal Workflow Execution has exclusive access to its local state. It executes concurrently to all other Workflow Executions, and communicates with other Workflow Executions through Signals and the environment through Activities. While a single Workflow Execution has limits on size and throughput, a Temporal Application can consist of millions to billions of Workflow Executions.

After going through the docs and
[examples](https://github.com/temporalio/samples-python/), it isn't _so_
different from celery. It definitely has more features and is far more
advanced.

Before reading further, please skim through this page: https://docs.temporal.io/application-development/features

Let's dive right into the first example.

## Polling example

https://github.com/temporalio/samples-python/blob/main/polling/

https://github.com/temporalio/samples-python/blob/4ef3a3779d1485a27ba5abd94180b7680aeeaafc/polling/infrequent/workflows.py#L10-L22

```python
@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            compose_greeting,
            ComposeGreetingInput("Hello", name),
            start_to_close_timeout=timedelta(seconds=2),
            retry_policy=RetryPolicy(
                backoff_coefficient=1.0,
                initial_interval=timedelta(seconds=60),
            ),
        )
```

There are three ways how to perform polling. To be quite honest, we already do something similar with celery.

1. [Infrequent polling](https://github.com/temporalio/samples-python/blob/main/polling/infrequent/workflows.py): retry with backoff, we already do this.
2. [Frequent polling](https://github.com/temporalio/samples-python/blob/main/polling/frequent/workflows.py): similar to 1), only the frequency is different
3. [Periodic sequence](https://github.com/temporalio/samples-python/blob/main/polling/periodic_sequence/workflows.py): similar to 2), except they poll in a child workflow

Polling and retry works similarly to celery.

## Dynamic execution

This is where we'd really need help. In Packit we always have two inputs:

1. Configuration (packit.yaml)
2. Event

And off these two we construct a chain of tasks. That would be a [Temporal Workflow](https://docs.temporal.io/workflows#workflow-execution).

With celery, creating tasks is okay, but very dynamic. We struggle with the
first part: how to efficiently get from those 2 inputs to the series of tasks.
Once we're in handlers, things are good.

### Where can temporal help?

- Signals: sending data to active workflows, [example](https://github.com/temporalio/samples-python/blob/main/hello/hello_signal.py)
- Workflows and activities: https://github.com/temporalio/samples-python/blob/main/hello/hello_parallel_activity.py

Every new event would spawn a new workflow. That would somewhat resemble our
pipeline. Celery tasks seem equivalent to activities.

Signals: I can't see how they would be useful in our workflow. We can just
update values in database if we need communication between tasks.

## [UI](https://temporal.io/blog/temporal-ui-beta)

![v2 UI](https://images.ctfassets.net/0uuz8ydxyd9p/5W5ooANY9KiGkFK1DXNPuV/ce3951c20624fe957a9dbe348dee9489/159999018-d82dfe25-394b-4332-b6e8-a4fedeceec34.png)

![v2 UI workflow](https://images.ctfassets.net/0uuz8ydxyd9p/64FDx5ZtpsBT5m4CPyoxB5/dc14fdf20e25ae1c71a65b09bffd506e/160000073-fcc79ef6-4be3-4f4a-98c8-2831007a26f6.png)

The UI looks like the biggest Temporal benefit. The introspection is just amazing.

## Deployment

It's hard to tell what is the best deployment of temporal: https://docs.temporal.io/cluster-deployment-guide#elasticsearch

[Example docker-compose with psql](https://github.com/temporalio/docker-compose/blob/main/docker-compose-postgres12.yml)

But overall looks to be more complex than celery.

## Conclusion

Temporal offers richer workflow engine over celery. It wouldn't be trivial to
port our solution from celery to temporal.

Except for the UI, I don't see a big advantage in temporal. Hunor has ideas how
we can improve processing of events. That sounds like a time better spent
rather than migrating to a new platform.
