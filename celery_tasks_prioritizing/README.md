# Prioritizing of the Celery tasks

## Current state

- 2 workers in prod, 1 worker in staging, no priority
- in each worker we do:

`celery --app="${APP}" worker --loglevel=${LOGLEVEL} --concurrency=1 --prefetch-multiplier=1`

## What do we want to achieve

- process the tasks depending on their priority and duration

- high-prio:
  - actionable events to users such as results with logs, final events
  - informations with high value - i.e. first status report
- low-prio:
  - intermediate results

| high-prio                      | low-prio                         |
| ------------------------------ | -------------------------------- |
| process_message                | run_copr_build_start_handler     |
| run_copr_build_handler         | run_copr_build_end_handler       |
| run_testing_farm_handler       | run_koji_build_report_handler    |
| run_propose_downstream_handler | run_testing_farm_results_handler |
| run_koji_build_handler         | run_installation_handler         |
| run_pagure_pr_label_handler    | babysit_copr_build               |
|                                | run_distgit_commit_handler       |

- long-running
  - tasks that build the SRPM: run_koji_build_handler, run_copr_build_handler
- short-running:
  - other tasks

## How to do it

- from [FAQ](https://docs.celeryproject.org/en/master/faq.html#does-celery-support-task-priorities):

  - Redis transport emulates priority support
  - prioritize work by routing high priority tasks to different workers, this usually works better than per message priorities

- also from [docs](https://docs.celeryproject.org/en/stable/userguide/optimizing.html#prefetch-limits)
  - if you have a combination of long- and short-running tasks, the best option is to use two worker nodes that are
    configured separately, and route the tasks according to the run-time

### Task priority

- docs are not so clear:

  - [priority](https://docs.celeryproject.org/en/latest/reference/celery.app.task.html?highlight=celery.app.task#celery.app.task.Task.priority)
    attribute of the `Task` - default task priority
  - [priority](https://docs.celeryproject.org/en/stable/reference/celery.app.task.html?highlight=priority#celery.app.task.Task.apply_async)
    argument in `apply_async` method: The task priority, a number between 0 and 9 (defaults to the `priority` attribute of Task)

  - [priority](https://docs.celeryproject.org/en/latest/userguide/calling.html#advanced-options) defined in Advanced
    options of task calling - number between 0 and 255, where 255 is the highest priority, Redis (priority reversed, 0 is highest)

#### [Redis message priorities](https://docs.celeryproject.org/en/latest/userguide/routing.html#redis-message-priorities)

- there are 10 (0-9) priority levels
- ```
  app.conf.broker_transport_options = {
    'queue_order_strategy': 'priority',
    }
  ```
- creating `n` lists for each queue - by default 10 priority levels are consolidated to 4 levels
  - e.g. queue named `celery` will be split into 4 queues:
    ` ['celery0', 'celery3', 'celery6', 'celery9']`
  - for more levels - `priority_steps` transport option

### [Routing tasks](https://docs.celeryproject.org/en/latest/userguide/routing.html)

- next to having the default queue/s have one either for low-prio or high-prio tasks
- a worker instance can consume from any number of queues
- specify what queues to consume from in worker with `-Q`:
  - `celery -A proj worker -l INFO -Q foo,bar,baz`
- the destination for a task is decided by the following:
  - routing arguments:
    `task.apply_async(queue="queue_name")`
  - attributes defined on the Task itself:
    - `@task(queue="queue_name")` in task decorator
    - class based task:
    ```
      class MyTask(Task):
            queue = "queue_name"
    ```
  - in confuguration (also default queue priority in the route can be set):
  ```
  task_routes = {
  'myapp.tasks.compress_video': {
      'queue': 'video',
      'routing_key': 'video.compress',
      'priority': 10,
      },
  }
  ```
- `task_create_missing_queues` (by default should be True) - a named queue that’s not already defined in `task_queues`
  will be created automatically

## Plan

- start with creating a new queue
- route the long-running tasks into different queue than short-running
- discuss how should workers consume these queues (e.g. 1 worker consumes queue for short-running and 1 worker for both queues)
- later, we can play also with the priority attribute
