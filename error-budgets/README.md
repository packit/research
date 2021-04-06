# Error Budgets

## Next steps for Packit

1. Identify stakeholders who can help us to define our SLO

   - Project which are the most frequent users of the service.
   - Prominent users:
     - [rhinstaller/anaconda](https://github.com/rhinstaller/anaconda)
     - [nmstate/nmstate](https://github.com/nmstate/nmstate)
     - [systemd/systemd](https://github.com/systemd/systemd)
     - [oamg/convert2rhel](https://github.com/oamg/convert2rhel)
     - [psss/tmt](https://github.com/psss/tmt)
     - [avocado-framework/avocado](https://github.com/avocado-framework/avocado)
     - [rpm-software-management/dnf](https://github.com/rpm-software-management/dnf)
     - [fedora-modularity/libmodulemd](https://github.com/fedora-modularity/libmodulemd)
     - [containerbuildsystem/atomic-reactor](https://github.com/containerbuildsystem/atomic-reactor)
     - [OpenSCAP/oval-graph](https://github.com/OpenSCAP/oval-graph)
     - [rpm-software-management/libdnf](https://github.com/rpm-software-management/libdnf)
     - [containerbuildsystem/osbs-client](https://github.com/containerbuildsystem/osbs-client)
     - [psss/fmf](https://github.com/psss/fmf)
     - [abrt/retrace-server](https://github.com/abrt/retrace-server)
     - [cockpit-project/cockpit-podman](https://github.com/cockpit-project/cockpit-podman)
     - [storaged-project/blivet](https://github.com/storaged-project/blivet)
     - [OpenSCAP/OVAL-visualization-as-graph](https://github.com/OpenSCAP/OVAL-visualization-as-graph)

2. Discuss and document their expectations. At a minimum in terms of
   (questions are provided as an example):

   - latency
     - How fast should builds/tests start? (First feedback from the service
       that something is happening.)
     - How fast should job results become available?
   - throughput
     - How many builds/tests/jobs should the service handle?
   - error rate
     - How many if the jobs can fail due to causes not related to the
       build/test?
   - availability
     - What percentage of PRs/branches should be handled by the service?
   - durability
     - How long should job results stay available?

   Look at the [CKI SLOs].

   Collected expectations are in a [separate document](users-expectations.md).

3. Figure out which of the expectations identified in the previous step can be
   measured with an indicator. What are these indicators (SLIs)? What are the
   SLOs?
   - We might want to check whether the SLOs make sense to the stakeholders.
4. Capture/produce the indicators (metrics/monitoring)
5. Track indicators to know how we are doing against our targets (SLOs). This
   means setting up monitoring dashboards and alerts, and making sure we have
   the process in place to become aware and take action (if needed) in case
   objectives are in danger to be missed.

## TL;DR: Notes and background

### Defining the "Error Budget" Cookbook

[The Cookbook] gathers best practices and necessary steps to define an error
budget, capturing the know-how from teams who already did this work.

### Principles

- Embracing Risk
- Service Level Objectives
- Eliminating Toil
- Monitoring
- Automation
- Release Engineering
- Simplicity

### Embracing Risk

[Chapter from the Google SRE book].

Building extremely reliable services turns out to be very expensive and
difficult. Focusing on this could limit the teams ability to deliver new
features. And many times, it doesn't even make sense: user experience might be
dominated by other, less reliable components. A user using a 99% reliable
network connection, won't be able to tell the difference between 99.99% and
99.999% reliability of a service.

Due to this, focus should rather be given on finding the optimum balance
between service uptime and availability and spending time on developing new
features.

##### Managing Risk

"Unreliable systems can quickly erode users' confidence".

Balance between developing features that diminish failures as opposed to
develop features that are directly visible or usable by end users.

"strive to make the service reliable enough, but not more reliable than it
needs to be"

"an objective metric to represent the property of a system we want to optimize"

A target helps with assessing current performance and track improvements and
degradations.

- time-based availability → uptime ([availability table]) - This might not be
  relevant in all the cases, though. For example, Google being a globally
  distributed service, it's up to some degree all the time at some part of the
  Globe.
- aggregate availability → request success rate - not all requests are equal,
  but from an user point of view calculating with and overall success rate is
  usually a good approximation.

Quarterly availability targets, tracked on a weekly or even daily basis.

##### Risk Tolerance of Services

It's OK to have a lower availability target in order to give space for quicker
innovation.

Background error rate of ISPs: 0.01%–1% according to the book.

##### Target level of availability

Different groups of users might have antithetical availability and performance
expectations for the same service, depending on their usage scenario.

To resolve this conflict, the infrastructure (deployment) of the service can
be partitioned, each partition serving users with some specific set of
requirements. This approach will also allow externalizing the difference in
cost for different levels of services, which in turn can motivate users to
choose the level of service with the lowest cost that still meets their needs.

### Motivation for Error Budgets

Inherent tension between development teams (aiming for product velocity) and
SRE (aiming for reliability).

There is also a tension in how a service is understood, devs know more about
development, SRE knows more about operation.

Typical areas of tension:

- software fault tolerance
- testing
- push (release) frequency
- canary duration and size

Proving the optimal balance is difficult, and can be driven by politics and
become a function of negotiating skills.

> "Hope is not a strategy"

Instead there should be an objective metric that can guide negotiations in a
reproducible way.

##### Forming an Error Budget

Based on the service level objective (SLO).

Defines a clear, objective metric that determines how unreliable a service is
allowed to be within a quarter.

1. Product Management defines the SLO, which sets an expectation for the
   uptime.
2. Monitoring system (neutral third party) measures the uptime.
3. The previous two define the "budget" of how much "unreliability" is left in
   the quarter.
4. As long as there is error budget remaining, releases can be pushed.

##### Benefits

Discussions/decisions around release velocity can be driven by the error
budget.

External factors that reduce the SLO are also eat into the error budget (infra
instability) - shared responsibility for uptime.

Helps to highlight the cost of reliability targets, in terms of both
inflexibility and slow innovation.

### Service Level Objectives

[SLO Chapter]

Understand which behaviours matter for the service, and who to measure and
evaluate those behaviours.

Service level indicators (SLIs), objectives (SLOs), and agreements (SLAs).

##### Indicators

- request latency - how long does it take to return a response to a request
- error rate
- system throughput
- availability - 99.95% = "three and a half nines" availability

Ideally, an SLI directly measures a service level of interest, but sometimes
only a proxy is available.

##### Objectives

- a target value or range of values for a service level that is measured by an
  SLI.
  - SLI ≤ target
  - lower bound ≤ SLI ≤ upper bound
- sharing SLOs with users helps setting expectations and avoid over- or
  under-reliance.
- Intentionally taking a service to outage in order to not to exceed it's
  service level objective.

##### Agreements

Explicit or implicit contract with the users that includes consequences of
meeting or missing the SLOs they contain: "what happens if the SLOs aren't
met?"

SRE don't get involved in constructing SLAs (that's a business and product
function), however they are helping to avoid triggering the consequences of
missed SLOs and define SLIs.

##### What Do You and Your Users Care About?

Not every metric from a monitoring system needs to become an SLI.

An understanding of user expectations should drive selecting a few indicators.

Services can be usually categorised as:

- User-facing serving systems
  - availability - Could we respond to the request?
  - latency - How long did it take to respond?
  - throughput - How many requests could we handle?
- Storage systems
  - latency - How long does it take to read/write data?
  - availability - Can data be accessed on demand?
  - durability - Is the data still there when it's needed? (aka data
    integrity)
- Big data systems (ex: data processing pipelines)
  - throughput - How much data is being processed?
  - end-to-end latency - How long does it take the data to progress from
    ingestions to completion?
- All systems should care about **correctness** - but this is often a
  property of the data in the system rather than the infrastructure, and so
  it's usually not an SRE responsibility to meet.

Where does Packit-as-a-Service fit in the above categorisation?

##### Collecting Indicators

- server side monitoring (for example, with Prometheus)
- periodic log analysis
- client-side collection

##### Aggregation

Needs to be done with care as it might hide issues in the tails.

Better to think about indicators in terms of **distribution** than averages:
"99% of requests receive a response within 200ms" vs "requests on average
receive a response within 200ms".

Don't assume data is normally distributed without first verifying it.

##### Standardize Indicators

Standardize common definitions:

- aggregation intervals: "averaged over 1 minute"
- aggregation regions: "all the tasks in the cluster"
- measurement frequency: "every 10 seconds"
- which requests are included: "HTTP GETs from black-box monitoring jobs"
- how the data is acquired: "throughout our monitoring, measured at the server"

### Objectives in Practice

- Start by thinking and/or finding out what users care about. - Often this is
  difficult or impossible to measure, so some approximation is needed.

##### Defining Objectives

SLOs should specify how they are measured and the conditions under which they
are valid.

It's unrealistic and undesirable to insist that SLOs will be met 100% of the
time - this can reduce the rate of innovation and deployment and require
costly solutions.

An error budget is just an SLO for meeting other SLOs.

##### Choosing targets

- Don't pick a target based on current performance
- Keep it simple - complicate aggregations are more difficult to reason about.
- Avoid absolutes - things like: scale "infinitely"
- Have as few SLOs as possible - if an SLO is never part of conversations,
  better drop it. Also: not all product attributes can be turned into an SLO.
- Perfection can wait - better to start with loose targets and revisit them
  over time.

##### Control Measures

1. Monitor and measure SLIs
2. Compare SLIs to SLOs and decide whether or not action is needed
3. Figure out what needs to be done to meet the target.
4. Do it.

The SLO helps figuring out when to take action.

##### Managing Expectations

SLOs can help drive users' expectations. A few caveats:

- Keep a safety margin - internal vs advertised SLOs give room to respond to
  chronic problems.
- Don't overachieve - users react to the reality not to the promise.

[the cookbook]: https://docs.google.com/document/d/1LkTDrwLnT7Z6_Ql9rrH80ts3yNyKW0fDAXwbHm6KRIM/edit#heading=h.f3pony0nfxb
[chapter from the google sre book]: https://sre.google/sre-book/embracing-risk/
[availability table]: https://sre.google/sre-book/availability-table/#appendix_table-of-nines
[slo chapter]: https://sre.google/sre-book/service-level-objectives/
[cki slos]: https://cki-project.org/docs/hacking/rfcs/cki-004-slo/
