# Monitoring Packit Service

## Prometheus & Grafana

Requires implementing the `/metrics` end-point.

Areas to be monitored

- resources used in the namespaces and clusters
  - number of processes/threads
    - in API
    - in workers
  - memory
  - CPU
  - storage
  - PostgreSQL metrics
  - Redis/Celery metrics (?)
    - tasks waiting in the queue
- Actions taken by Packit Service and its components
  Some of the questions we could answer:
  - How many times do we call the GitHub/Pagure/GitLab API?
  - How many messages do we process from the Fedora and CentOS message
    queues?
  - Any other thing that is interesting information for us, but it's not
    stored in the database.

### How do we instrument our services and code?

In Packit Service API the `/metrics` endpoint [can be exported] using Flask's
application dispatching mechanism.

Then code would need to be [instrumented].

For monitoring Celery tasks, the most fitting solution seems to be [to export
to a Pushgateway]. For this to work, a [Prometherus Pushgateway] needs to be
deployed in the Packit Service cluster where workers are running, to collect the
metrics from the workers and provide the `/metrics` endpoint for Prometheus.

### How could we try it out?

1. As a POC we could pick one of the API end-points, instrument it, point the
   internal Prometheus instance to scrape the data, and create a dashboard
   visualizing that data.
2. We might want to consider a second POC to instrument a part of our Celery
   tasks, to try out the Pushgateway solution. This needs [Prometheus
   Pushgateway] to be set up and configured for scraping.
3. Monitor some resources.

### How to monitor the Openshift objects?

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

## Dashboard

The Dashboard would offer a view in the data Packit Service stores about jobs,
builds, etc. In short it would be a view on the database.

One of the reasons we would like to keep this option, despite also wanting to
use Prometheus, is that the data in the DB will have high cardinality (Packit
Service will be enabled on many projects), and the time series database used
by Prometheus is not built to support high-cardinality use-cases.

With the dashboard we will be able to drill down into statistics about
individual projects, PRs, builds. See [#43].

[can be exported]: https://github.com/prometheus/client_python#flask
[#43]: https://github.com/packit-service/research/pull/43
[to export to a pushgateway]: https://github.com/prometheus/client_python#exporting-to-a-pushgateway
[federation]: https://prometheus.io/docs/prometheus/latest/federation/
[instrumented]: https://github.com/prometheus/client_python#instrumenting
[prometherus pushgateway]: https://github.com/prometheus/pushgateway
