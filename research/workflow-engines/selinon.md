---
title: Selinon
authors: lbarcziova
---

- docs: https://selinon.readthedocs.io

> This tool is an implementation above Celery that enables you to define flows and dependencies in flows, schedule tasks based on results of Celery workers, their success or any external events.
>
> The main advantage of using Selinon over these are facts, that you can use it in fully distributed systems and for example let Kubernetes or OpenShift do the workload (and much more, such as recursive flows, sub-flows support, selective task runs, …), define task flows that are not strictly DAG (not strictly directed acyclic graph, but directed graph instead), let system compute which tasks should be run in dependency graph and other features.

- migration from raw Celery: https://selinon.readthedocs.io/en/latest/celery.html
- YAML-based config file - here the tasks, flows and storages are defined, e.g.:

```yaml
flow-definitions:
  - &flow1_def
    name: "flow1"
    queue: "flow1_v1"
    propagate_node_args: true
    edges:
      - from:
        to: "Task4"
      - from: "Task4"
        to: "Task5"

  - <<: *flow1_def
    name: "flow1_sla"
    queue: "flow1_sla_v1"
    # node_args_from_first and edges configuration will be taken from flow1
```

- no UI
- doesn't support dynamic pipeline generation in runtime, doesn't look like this would fit what we need
