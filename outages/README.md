## How to manage outages

### Who is responsible for resolving outages and what should be done

- rotating role - new / incorporate to an existing one (Sentry master, community master)
- identify an outage
- inform team
- inform users
- be responsible for fixing the issue = try to fix it / ask in the team
- inform when the outage is resolved

### How to identify an outage

- Sentry
  - mostly info about new exceptions
  - currently we are informed about each new Sentry issue by mail
  - [alerts](https://docs.sentry.io/product/alerts-notifications/metric-alerts/)
    - alert rules can be set up - threshold, notification,
      [example](https://www.sentry.dev/_assets2/static/fca0872133bf0ed54631d4ba44725879/eb1d2/new-alert-rule-all.png)
    - alerting is triggered when a threshold is breached
- Prometheus can provide alerts as well - we would need to collect some metric about failed tasks and create alert rules
  for that
- analyze DB info we use in dashboard jobs - periodically check the state of the SRPM builds/ Copr builds/ tests in DB from e.g. the last hour
  - cron job to check this can be set up

### How team members are informed

- IRC - the messages are mirrored to Telegram, this should be enough

### How users are informed

- our [status page](https://dashboard.packit.dev/status) in dashboard
  - currently we have there only info about API which only checks https://prod.packit.dev/api/healthz
  - we could provide more info:
    - manually added info about current outage, have some template: what and when happened, when it will be fixed
    - history of outages
  - if Openshift is down, we cannot communicate here
- pinned issue in Github about current outage
  - link to dashboard?
- IRC - also provide links
- status page hosted some other place then the actual project, so that it's possible to communicate the status even if OpenShift is down:
  - [Cachet](https://github.com/CachetHQ/Cachet) - self-hosted status page system
  - [Statusfy](https://github.com/juliomrqz/statusfy) - Static Generated or Server Rendered, variety of hosting
    [services](https://docs.statusfy.co/guide/deploy/#github-pages)
  - [cState](https://github.com/cstate/cstate) - built with Hugo, statically generated, can be hosted for free on Github Pages
  - [Corestatus](https://github.com/jayfk/statuspage) - turns GitHub issues into a status page, hosted on GitHub
- for certain known failures of Testing Farm or Copr "neutral" status on PRs (instead of an error)
  - the checks need to be implemented ([opened issue for this](https://github.com/packit/ogr/issues/461))
  - could be configurable
  - better UX for users - PRs are not marked as failed

#### What should be included

- scope:
  - what functionality is broken
  - what/who is affected
- provide alternatives if there are some
- when can users expect a fix
- if the outage is caused by other tool/service - provide links (e.g. Copr outage, Testing farm)
