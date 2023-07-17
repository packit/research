---
title: Reporting
authors: jpopelka
---

We want to efficiently report to our users that we have an outage, so they are aware of it and
then know when the outage is over. The main audience is people outside Red Hat.

Currently, when we know ahead there's gonna be an outage, we just write to IRC.
Can we use some existing service/portal for this?

## [One Portal](https://one.redhat.com)

#### From docs & FAQ

- "One Portal is an integrated website consisting of frameworks and modules to support various initiatives across PnT DevOps team and fill the gaps such as infrastructure accessibility, service duplications, lack of a standard platform for service hosting and data integration, inefficient resource management, limited real time metrics unavailability, cross-team collaboration and scattered documentation."
- "One Portal will be One Stop Shop solution to manage, maintain and monitor workflow & service related information across PnT. One portal will increase cross-team collaboration and visibility of PnT services within and outside PnT."
- "Objective is to increase the flow of information between systems sooner, faster, cheaper keeping clarity and transparency."

#### Pros

If we need only the outage reporting, then it should work, yes.
As a member of a team you can easily create an outage and a notification will be shown to
all subscribers of your tool/service.

#### Cons

- One Portal does not seem to be accessible outside Red Hat VPN.
- I've been not able to create a new Service because "One Portal is PnT DevOps portal and focused on DevOps initiatives at this moment hence you dont have access to create or modify tools & services."
- The notifications seem to be only on the website. There's no way to sent them for example to an e-mail.

## [One Platform](https://beta.one.redhat.com)

In a 'few months' time-frame, the One Portal will be 'upgraded' to One Platform, which should be more scalable.
Currently the One Platform runs [here](https://beta.one.redhat.com) and is continuously updated so you may find it broken, which was my case when I tried it.

(jpopelka, Sep/Oct 2020)
