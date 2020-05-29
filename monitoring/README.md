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
[to export to a Pushgateway]: https://github.com/prometheus/client_python#exporting-to-a-pushgateway
[Federation]: https://prometheus.io/docs/prometheus/latest/federation/
[instrumented]: https://github.com/prometheus/client_python#instrumenting
[Prometherus Pushgateway]: https://github.com/prometheus/pushgateway
