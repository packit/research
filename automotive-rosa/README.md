# Automotive clusters

The Automotive initiative uses [Red Hat OpenShift Service on AWS (ROSA)](https://docs.openshift.com/rosa) for their clusters.

See [this internal repo](https://gitlab.cee.redhat.com/c-team/monaco) for Infrastructure as Code definitions.

They gave us access to their test cluster - creds are in [our internal repo](https://gitlab.cee.redhat.com/user-cont/packit-service).

There's also [a recording](https://drive.google.com/file/d/1ROw7owiF47GAE1TaQ7i6fV5ZStbkdVgF) of a intro that Hubert Stefanski gave us.

For communication use `packit-auto-shared-infra` internal chat and/or google group.

## Staging packit-service @ test cluster

A new [deployment](https://github.com/packit/deployment) of staging instance of packit-service to the test cluster went flawlessly.

All microservices work OK, the only hiccup we've seen is with PostgreSQL which is working intermittently.
The readiness probe sometime fails and/or a query via SQLAlchemy ofter returns
"server closed the connection unexpectedly" even when the readiness probe is
turned off so the probe can't be the cause per se.

When one runs `watch pg_isready` in the pod's terminal, the outages are
mysteriously gone and don't show up any more even when the watch is later stopped.
The readiness probe also calls the `pg_isready` periodically via
`/usr/libexec/check-container`, but it doesn't have the same effect as
running it manually in the terminal.

(author of these letters owe you a beer six pack if you can help shed some light on this mystery)
