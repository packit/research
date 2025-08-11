---
title: Metrics
authors: lbarczio
---

## Requests coming to / of the API

- [Prometheus Flask exporter](https://github.com/rycus86/prometheus_flask_exporter)
  - metrics are configured via decorators, e.g. `@metrics.counter(..)`:
  ```python
  @app.route('/<item_type>')
  @metrics.do_not_track()
  @metrics.counter('invocation_by_type', 'Number of invocations by type',
           labels={'item_type': lambda: request.view_args['type']})
  def by_type(item_type):
      pass  # only the counter is collected, not the default metrics
  ```

  - the metrics are by default exposed on the same Flask application on the /metrics endpoint,
    this can be adjusted
  - counters count invocations, other types (histogram, gauge, summary) collect metrics based on the
    duration of those invocations
  - labels can be defined (also using attributes of the request or the response)

## Celery metrics

- Celery needs to be configured to send events to the broker which the exporter will collect (via config/CLI)

- [danihodovic exporter](https://github.com/danihodovic/celery-exporter)
  - [metrics](https://github.com/danihodovic/celery-exporter#metrics):
    - celery_task_sent_total
    - celery_task_received_total
    - celery_task_started_total
    - celery_task_succeeded_total
    - celery_task_failed_total
    - celery_task_rejected_total
    - celery_task_revoked_total
    - celery_task_retried_total
    - celery_worker_up
    - celery_worker_tasks_active
    - celery_task_runtime_bucket
  - [running the exporter](https://github.com/danihodovic/celery-exporter#running-the-exporter) - available via container image
  - active project
- [OvalMoney exporter](https://github.com/OvalMoney/celery-exporter)
  - metrics:
    - celery_workers - number of workers
    - celery_tasks_total - number of tasks per state (labels name, state, queue and namespace):
  ```
   celery_tasks_total{name="my_app.tasks.fetch_some_data",namespace="celery",queue="celery",state="RECEIVED"} 3.0
   celery_tasks_total{name="my_app.tasks.fetch_some_data",namespace="celery",queue="celery",state="PENDING"} 0.0
   celery_tasks_total{name="my_app.tasks.fetch_some_data",namespace="celery",queue="celery",state="STARTED"} 1.0
   celery_tasks_total{name="my_app.tasks.fetch_some_data",namespace="celery",queue="celery",state="RETRY"} 2.0
   celery_tasks_total{name="my_app.tasks.fetch_some_data",namespace="celery",queue="celery",state="FAILURE"} 1.0
   celery_tasks_total{name="my_app.tasks.fetch_some_data",namespace="celery",queue="celery",state="REVOKED"} 0.0
   celery_tasks_total{name="my_app.tasks.fetch_some_data",namespace="celery",queue="celery",state="SUCCESS"} 7.0
  ```

  - celery_tasks_runtime_seconds
  - celery_tasks_latency_seconds - time until tasks are picked up by a worker - this can be helpful for us and is
    not included in the first exporter metrics
  - otherwise similar to the previous one, available via container image
  - not that active project

## Httpd metrics

- [Apache exporter for Prometheus](https://github.com/Lusitaniae/apache_exporter)
  - metrics:
    - current total apache accesses (\*),
    - Apache scoreboard statuses
    - Current total kbytes sent (\*)
    - CPU Load (\*)
    - Could the apache server be reached
    - Current uptime in seconds (\*)
    - Apache worker statuses
    - Apache server version
    - Total duration of all registered requests
    - `*` are only available if ExtendedStatus is On in webserver config
  - how to [using Docker](https://github.com/Lusitaniae/apache_exporter#using-docker)

## Openshift metrics

- builtin Monitoring view in clusters we use currently - this should use some of the tools below

- previous research:
  1. [`kube-state-metrics`](https://github.com/kubernetes/kube-state-metrics)
     - converts Kubernetes objects to metrics consumable by Prometheus
     - not focused on the health of the individual Kubernetes components, but rather on the health of the various objects inside, such as deployments, nodes and pods
     - metrics are exported on the HTTP endpoint `/metrics` on the listening port, designed to be consumed either by
       Prometheus itself or by a scraper that is compatible with scraping a Prometheus client endpoint
     - deleted objects are no longer visible on the `/metrics` endpoint
     - examples of exposed metrics (more [here](https://github.com/kubernetes/kube-state-metrics/tree/master/docs)):
       - kube_pod_container_resource_requests
       - kube_pod_container_status_restarts_total
       - kube_pod_status_phase
     - in limited-privileges environment where you don't have cluster-reader role:
       - create a serviceaccount
       - give it view privileges on specific namespaces (using roleBinding)
       - specify a set of namespaces (using the --namespaces option) and
         a set of kubernetes objects (using the --resources) that your serviceaccount
         has access to in the kube-state-metrics deployment configuration
     - example deployment configuration files in their Github repo [here](https://github.com/kubernetes/kube-state-metrics/blob/master/examples)
     - can be configured in the args section of the deployment configuration using
       [CLI args](https://github.com/kubernetes/kube-state-metrics/blob/master/docs/cli-arguments.md#command-line-arguments)

  2. [Node exporter](https://github.com/prometheus/node_exporter)
     - Prometheus exporter for hardware and OS metrics exposed by \*NIX kernels
     - runs on a host, provides details on I/O, memory, disk and CPU pressure
     - can be configured as a side-car container, [described](https://access.redhat.com/solutions/4406661)
     - various [collectors](https://github.com/prometheus/node_exporter#collectors) which can be configured
       - cpu - exposes CPU statistics
       - diskstats - disk I/O statistics
       - filesystem - filesystem statistics (disk space used)
       - loadavg - load average
       - meminfo - memory statistics
       - netdev - network interface statistics (bytes transferred)
     - from the example metrics:
       - rate(node_cpu_seconds_total{mode="system"}[1m]) - the average amount of CPU time spent in system mode, per second, over the last minute (in seconds)
       - node_filesystem_avail_bytes - the filesystem space available to non-root users (in bytes)
       - rate(node_network_receive_bytes_total[1m]) - the average network traffic received, per second, over the last minute (in bytes)

  3. [cAdvisor](https://github.com/google/cadvisor)
     - usage and performance characteristics of running containers
     - CPU usage, memory usage, and network receive/transmit of running containers
     - embedded into the kubelet, kubelet scraped to get container metrics, store the data in Prometheus
     - by default, metrics are served under the `/metrics` HTTP endpoint
     - jobs in Prometheus to scrape the relevant cAdvisor processes at that metrics endpoint
     - example metrics (more [here](https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md#prometheus-container-metrics)):
       - container_cpu_usage_seconds_total - cumulative cpu time consumed
       - container_memory_usage_bytes - current memory usage, including all memory regardless of when it was accessed
       - container_network_receive_bytes_total - cumulative count of bytes received
       - container_processes - number of processes running inside the container
  4. [`kubernetes_sd_config`](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#kubernetes_sd_config)
     - in the Prometheus configuration allow Prometheus to retrieve scrape targets from Kubernetes REST API and stay synchronized with the cluster state.
     - role types that can be configured to discover targets:
       - `node` - discovers one target per cluster node with the address defaulting to the Kubelet's HTTP port
       - `pod` - discovers all pods and exposes their containers as targets
       - `service` - discovers a target for each service port for each service
       - `endpoints` - discovers targets from listed endpoints of a service
     - need to grant the prometheus service account access to the project defined to discover in `namespaces`
     - example:

     ```
         scrape_configs:
         - job_name: 'pods'

           kubernetes_sd_configs:
           - role: pod
             namespaces:
               names:
               - prometheus
               - application

           relabel_configs:
           - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
             action: keep
             regex: true
     ```

     - to discover targets from another cluster - pass the `api_server` URL, TLS certificate or bearer token files for Prometheus to authenticate:

     ```
      # The API server addresses. If left empty, Prometheus is assumed to run inside
      # of the cluster and will discover API servers automatically and use the pod's
      # CA certificate and bearer token file at /var/run/secrets/kubernetes.io/serviceaccount/.
      [ api_server: <host> ]
     ```

  5. [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)
     - creates, configures, and manages Prometheus monitoring instances
     - to simplify and automate the configuration of a Prometheus based monitoring stack for Kubernetes clusters
     - generates monitoring target configurations based on familiar Kubernetes label queries
     - can be installed into a specific OpenShift project - needed `cluster-admin` role
     - community supported
  6. [Metrics Server](https://github.com/kubernetes-sigs/metrics-server) - resource metrics from Kubelets,
     not meant to be used to forward metrics to monitoring solutions, or as a source of monitoring solution metrics
