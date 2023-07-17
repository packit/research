---
title: Cloud databases
authors: jpopelka
---

In [Distributed workers](/research/deployment/distributed-workers) we realized we need a cloud database
in order to be able to have workers in a private cloud (PSI).

Since we already have AWS account (log in with your kerberos credentials
[here](https://auth.redhat.com/auth/realms/EmployeeIDP/protocol/saml/clients/itaws))
we decided to use RDS PostgreSQL as database and SQS as Celery broker.

## Simple Queue Service - [SQS](https://console.aws.amazon.com/sqs/home)

At the moment we use only one Celery queue (default, named `celery`) per packit service deployment.
With `redis` instance (separate one per deployment) as a broker,
each deployment has its separate `celery` queue.
But with SQS the deployments (`prod` and `stg`) can't both use `celery` queue, so we use
`packit-$DEPLOYMENT-` prefix in order to have `packit-prod-celery` and `packit-stg-celery` queues.
They are Standard type (best-effort ordering). FIFO would probably be better
since it's not OK when for example 'build finished' event is processed before 'build started',
but FIFO queue costs more and Celery uses by default Standard type so let's start with it.
The queues can be accessed (send to, receive from) only by our packit user.
Other than that (and proper Tags) they're configured with default values.

## [RDS](https://console.aws.amazon.com/rds/home)

For `stg` (there's no DB for `prod` atm) we have a `db.t3.micro` (cheapest/slowest)
class PostgreSQL (11.x) DB in `default` VPC with `public-all` security group.
For `prod` db we might investigate restricting it so that it could be accessed
only from Openshift cluster(s) we use.
To import data from our local `postgres` instance to RDS:

```
oc rsh postgres-1-r2vnd pg_dump -v -U <user> -d <db name> -f /tmp/packit.dump
oc rsync postgres-1-r2vnd:/tmp/packit.dump ./
psql -f packit.dump --host packit-stg.abcxyz.region.rds.amazonaws.com --username <user> --password --dbname <db name>
```

## Status

At the moment of writing this only `stg` uses `SQS` & `RDS`,
`prod` still runs its own `redis` & `postgres`.
So far `stg` seems to be running OK with it and `redis` & `postgres` turned off.
The downside we've noticed is that dashboard is several times slower
(due to the DB instance class we use).
Also we
[can't use readiness and liveness probes for workers](https://github.com/packit/deployment/pull/135).

I also temporarily deployed one packit worker in our cyborg-stage project @ PSI.
I proved that it was accepting tasks from AWS SQS and tore it down again.
I saw no backend related error so I believe it was able to connect to AWS RDS PostgreSQL as well.
To make it build (S)RPMS I'd need a separate sandbox project there which I don't have atm.

(jpopelka, September 2020)
