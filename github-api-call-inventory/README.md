# GitHub API Call Rate Limits

## Inventory of GitHub API calls made during a pipeline run

See [this Jupyter Notebook](./github-api-call-inventory.ipynb).

## Collecting metrics on GitHub API calls

We want to count the number of GitHub API calls, so that we can produce an
indicator about the average API calls per pipeline run. Such an indicator
could help us notice if code changes result in an increase in the API calls
made, and so making it more likely that the call rate limits are reached in
certain orgs.

Packit and Packit-Service interact with GitHub through ogr, which in turn
relies on PyGithub.

### Approach 1: Patch PyGithub to inject a metric object

The first thing, that was explored is if PyGithub could be patched in some way
in order to enable Prometheus metrics collection. This would be possible, by
patching [Requester] to accept a Prometheus metric object and use it. This
then could be used to pass down a metrics collector object (for example a
Counter) from PackitAPI through ogr to PyGithub.

Going through the whole flow:

In packit-service GithubProjects are obtained with
`ServiceConfig.get_project()`. This method (implemented in
`packit.config.config.Config`) will need to be updated to take a
`github_call_counter` object and pass it down to `ogr.get_project()`.

Here `ogr.factory.get_project()` would pass it down to `GithubService` which
then would pass it down to `GithubProject`, which then would pass it down to
the PyGithub `Github` object, so that it can be used as [a new property of the
`Requester`], in order to be able to pass it to the connection, and
incremented every time [a response is received].

Patching PyGithub could be done while building the service and the worker
images. The patches could be also submitted upstream, to get some feedback on
the approach and maybe incorporate them in PyGithub.

### Approach 2: Use a proxy

An another solution that _might_ work is to update the hosts files in the
service and worker images and route all connections to GitHub through an
[NGINX proxy pod], and then use [NGINX Prometheus Exporter] to expose some
[HTTP metrics], which then could be interpreted as metrics on GitHub API
calls. Exposing these metrics—so that they can be scraped—would require
setting up a new route, something like `github-calls.packit.dev`. I did not
try this approach, so some more time should be spent on this, to figure out if
it would indeed work.

[requester]: https://github.com/PyGithub/PyGithub/blob/master/github/Requester.py
[nginx proxy pod]: https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/
[nginx prometheus exporter]: https://github.com/nginxinc/nginx-prometheus-exporter
[http metrics]: https://github.com/nginxinc/nginx-prometheus-exporter#http
[a new property of the `requester`]: https://github.com/PyGithub/PyGithub/blob/e414c3227bb15819b443b4474f1aded433011bda/github/MainClass.py#L122
[connection]: https://github.com/PyGithub/PyGithub/blob/e414c3227bb15819b443b4474f1aded433011bda/github/Requester.py#L668
[a response is received]: https://github.com/PyGithub/PyGithub/blob/e414c3227bb15819b443b4474f1aded433011bda/github/Requester.py#L129
