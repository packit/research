---
title: Workers scaling
authors: jpopelka
---

## What

This research is about scaling worker(s) that do short-running tasks to [improve Packit Service event processing](https://github.com/packit/research/tree/main/improve-service-processing#problematic-parts-of-the-process).

## History

Once upon a time there were more (two?) workers who were not picky and took
whatever task they find in the (only) queue.
To not waste time they always assigned more (4) tasks at a time to themselves
before starting to work on a task.
It [could then happen](https://github.com/packit/packit-service/issues/375)
that one worker processed a `copr_build_finished` event sooner than the other
worker processed a corresponding `copr_build_started` event,
and then it looked like that the copr build never finished.

For example, if you have 2 workers and a task queue like

    build1_start | build2_start | build3_start | build1_end | build2_end | build3_end

and each worker takes 4 tasks, then the first worker takes

    build1_start | build2_start | build3_start | build1_end

and the second is left with

    build2_end | build3_end

and by the time the first worker starts processing `build2_start`,
the second has already processed `build2_end` so it looks like the build2 never ended.

This [has been fixed](https://github.com/packit/packit-service/commit/5d199cfee54dafd9a5cd5dadc1086e15d78598e5)
by making sure that the workers are not so greedy and reserve only one task ahead
(`--prefetch-multiplier=1`, default is 4).

Later, we also [set up 2 Celery queues, for long and short running tasks](https://github.com/packit/packit-service/commit/617c76ef77ef37bc220b029bc49326d3841c54c0)
because that's what [Celery User Guide suggests](https://docs.celeryq.dev/en/stable/userguide/optimizing.html#optimizing-prefetch-limit).

## worker --concurrency

The same [commit](<(https://github.com/packit/packit-service/commit/5d199cfee54dafd9a5cd5dadc1086e15d78598e5)>)
that set `--prefetch-multiplier=1` also set `--concurrency=1`
(number of concurrent worker processes/threads executing tasks)
even it's probably had no effect because [the default is "number of CPUs/cores on the host"](https://docs.celeryq.dev/en/stable/userguide/configuration.html#std-setting-worker_concurrency)
and the workers have no more than one core.
We definitely don't want to change the prefetch multiplier because that might
cause [p-s#375](https://github.com/packit/packit-service/issues/375)
for no significant benefit, but having more concurrent worker threads
should hopefully be safe.

Whether it's really safe depends on how Celery
fetches messages for the worker's threads. If it waits for all threads
to finish their tasks before fetching a new batch of messages (times prefetch-multiplier)
for all threads then we might still hit [p-s#375](https://github.com/packit/packit-service/issues/375)
if we have more workers serving the short-running-tasks queue.
But if Celery fetches a new message(s) for a thread once it finishes a task
without waiting for other threads then we should be fine (as long as prefetch-multiplier=1).
I checked the [Celery source code](https://github.com/celery/celery)
but couldn't find an answer for how/when it fetches messages for the threads
(whether individually or for all at once). Someone's up for a challenge?;)
But if we had only one worker (with more threads) serving the
short-running-tasks queue then we should be fine anyway.

### Processes vs. threads aka. [Celery execution pool](https://www.distributedpython.com/2018/10/26/celery-execution-pool)

- **Processes** (`prefork` pool) -
  are good when tasks are CPU bound. The number of processes should not exceed
  the number of CPUs on host.
- **Threads** ([eventlet](https://docs.celeryq.dev/en/latest/userguide/concurrency/eventlet.html)/[gevent](https://www.gevent.org) pool) -
  when tasks are I/O or network bound. The number of greenlets (green threads) is
  unrelated to the number of CPUs on host and can go even to thousands.

### worker --autoscale

Regarding the `--concurrency` value, we even don't have to set a static number
if we use [worker --autoscale](https://docs.celeryq.dev/en/latest/userguide/workers.html#autoscaling)
which dynamically resizes the pool based on load ([number of requests](https://github.com/celery/celery/blob/aa9fd8a6c06e69c7eda2a59866c3d84622c85d20/celery/worker/autoscale.py#L85)
in the message queue, not a CPU load).

## Kubernetes/Openshift Horizontal Pod Autoscaling

- [Automatically scaling pods with the horizontal pod autoscaler ](https://docs.openshift.com/container-platform/4.10/nodes/pods/nodes-pods-autoscaling.html)
- [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale)

The horizontal pod autoscaler (HPA) can be used to specify how should K8s/Openshift
scale a StatefulSet based on metrics collected from the pods.
The supported metrics are CPU and/or memory utilization.

For example: You say that you want to have 1 to 5 workers with average CPU
utilization around 50% (of their cpu resource request). The HPA controller
then periodically checks the cpu metrics and scales the pods up/down
based on the CPU consumption.

The memory utilization of short-running workers is constant so that's off the table.
CPU utilization doesn't quite follow the load (of tasks in queue) because the tasks
are mostly network bound. For example at times when there's not much to do a
short-running worker consumes about 2 millicores, while when there's a lots of tasks
the utilization jumps between 2 and 20 millicores, so it's hard to decide on a
desired average utilization.

The ideal metric for us would be a number of outstanding tasks in a queue,
however [external metrics](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/#autoscaling-on-metrics-not-related-to-kubernetes-objects)
are not clearly described how to achieve.

We'd also need to return [readiness probes](https://github.com/packit/deployment/pull/142)
to make the HPA work.

Compared to `worker --autoscale` the HPA looks like:

- less reliable (if we used the CPU metrics)
- more work to set up (if we used custom/external metrics - queue size)
- slower - starting a pod is way slower than adding a thread
- more resource hungry - running 4 pods eats much more memory than running 1 pod with 4 threads

## Summary/Suggestion

- Default for stg & dev can stay as it is, i.e. [one worker for all tasks](https://github.com/packit/deployment/blob/cb47f9e6f806f9e340669031c7eb58df02b164f1/playbooks/deploy.yml#L40)
  with no concurrency/autoscaling/prefetching.
- For prod, we should experiment with setting `--autoscale` (or just `--concurrency`)
  together with `--pool=eventlet/gevent`. We should have only [one worker for serving
  short-running tasks](https://github.com/packit/deployment/blob/cb47f9e6f806f9e340669031c7eb58df02b164f1/vars/packit/prod_template.yml#L77)
  which would autoscale based on load and [no worker for all tasks](https://github.com/packit/deployment/blob/cb47f9e6f806f9e340669031c7eb58df02b164f1/vars/packit/prod_template.yml#L76)
  to avoid [p-s#375](https://github.com/packit/packit-service/issues/375) regression.
