---
title: Definitions of SLOs and SLIs for Packit
authors:
  - jpopelka
  - ttomecek
  - lbarczio
---

If you are not familiar with SLOs and SLIs, please check [the parent](../error-budgets) first.

## How do others do it?

The CKI team has a pretty comprehensive set of
[SLOs](https://cki-project.org/docs/hacking/rfcs/cki-004-slo/#created-slos-based-on-the-feedback).
Instead of taking the same route, let's start small and slowly add more and
more objectives and indicators over time.

Testing Farm team has [Service level
expectations](https://docs.google.com/document/d/1iHK3v_tCK4w-F82ZvUEO3xHcNv78tkR31w3oF-zpi1Q/edit#heading=h.26gd46u8e15q)
and a pretty slick
[dashboard](http://grafana-latest-osci-infra.cloud.privileged.psi.redhat.com/d/VXwH27XMk/rhel-infrastructure-and-service-health?orgId=1).

## Packit SLOs

SLOs are based on [discussions with our stakeholders](users-expectations.md).

Let's define job statuses first to get a clear understanding of these objectives:

- successful run: a job finished and everything is awesome
- failure: the job finished and wasn't successful: the PR needs to be fixed
- error: infrastructure problems prevented the job to complete

### SLO1: Changes to GitHub PRs receive a status update within 15 seconds in 99% of cases

It can be frustrating (for us and our users) when we push changes to our PRs
while no statuses are being set. Let's make a deadline for packit to set these.

### SLO2: 98% of builds have status set to success or failure within 12 hours

The most core functionality is to run COPR builds for PRs. We want to be sure
those builds either pass or fail and no error interrupts the build process.

The problem is that some builds take minutes and some hours so it's hard to
design this objective in a generic way for everyone.

### SLO3: 95% of test runs have status set to success or failure within 12 hours

Similar as builds but since Testing Farm is outside of our control, let's lower
the percentage.

## Packit SLIs

If we want to track our SLOs, we need to start measuring different aspects of our workflow.

- Number of builds queued

- Number of tests queued

- Number of builds started

- Number of test runs started

- Number of builds finished

- Number of test runs finished

- Time it took to go for a build from queued to finish

- Time it took to go for a test from queued to finish

- Number of unfinished builds that are in progress for more than 12 hours

- Number of unfinished test runs that are in progress for more than 12 hours

- Number of PRs handled by packit with no commit status from packit for more than 15s

- Time it takes packit to set the initial status

### Note on the implementation

All the other teams use prometheus + grafana combo so this will be our choice
as well.

[Histograms and
summaries](https://prometheus.io/docs/concepts/metric_types/#histogram) are
used in prometheus to measure durations. One can then use these values for
[aggregation operations](https://prometheus.io/docs/practices/histograms/) such
as averages, sums, max, min, above or below a certain value.

## Ideas

- It would be awesome to know if our GitHub app correctly accepts all webhook
  events but [sadly there is no API to get the
  list](https://docs.github.com/en/rest/reference/apps#webhooks), though
  [GitHub has plans for this
  functionality](https://github.com/github/roadmap/issues/125).
