---
title: Data stores
authors: jpopelka
---

## Why

At the moment (Nov 19) we use Redis as a Celery backend (i.e. for storing results of Celery tasks) as well as a data store where we track copr builds, github app installations and whitelist of users.
Redis is in-memory DB, i.e. the more data we store the more memory we use.
Because memory is (unlike disk) quite expensive we want to move to a DB which stores the data on disk.
The task here is to decide between SQL or NoSQL and then between our own deployment or a database in a cloud.

## SQL

SQL stores data in a structured way of interconnected tables.
The question here is whether we actually need structured tables to do some crazy queries.
Big plus here is that Celery supports [SQLAlchemy](https://www.sqlalchemy.org) as a [built-in backend](https://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#keeping-results) and the same applies to [Flask](https://github.com/pallets/flask-sqlalchemy).
From the databases which SQLAlchemy supports I'd select SQLite and Postgresql (see also [this](https://tableplus.com/blog/2018/08/sqlite-vs-postgresql-which-database-to-use-and-why.html) and [this](https://www.digitalocean.com/community/tutorials/sqlite-vs-mysql-vs-postgresql-a-comparison-of-relational-database-management-systems)):

### SQLite

#### Pros

Ultra-lightweight in setup, administration, and required resource. Very fast.

#### Cons

Because SQLite is a serverless database, it doesn’t provide direct network access to its data. An application (as I understand it) just stores data in a file by using a SQLite library. If more containers (in our case service and more workers) need to access the db, they probably need to have the file on a shared (RWX) volume.

### Postgresql

#### Pros

[JSON data type](http://www.postgresqltutorial.com/postgresql-json) is a big plus, because we already have our data serialized as jsons so we can just store them that way and then do all kinds of queries over them.

#### Cons

[Overkill](https://www.digitalocean.com/community/tutorials/sqlite-vs-mysql-vs-postgresql-a-comparison-of-relational-database-management-systems#when-not-to-use-postgresql)

## NoSQL

Example of a NoSQL ([Document-oriented](https://www.digitalocean.com/community/tutorials/a-comparison-of-nosql-database-management-systems-and-models#document-oriented-databases)) database is [MongoDB](https://www.mongodb.com/what-is-mongodb).

### Pros

Stores data in flexible, JSON-like documents, meaning fields can vary from document to document and data structure can be changed over time. It also [supports queries](https://www.tutorialspoint.com/mongodb/mongodb_query_document.htm) and indexing.

### Cons

Using MongoDB as a Celery backend is not that straightforward, but there are options: [[1]](http://docs.celeryproject.org/en/latest/_modules/celery/backends/mongodb.html), [[2]](https://stackoverflow.com/questions/15740755/working-example-of-celery-with-mongo-db), [[3]](https://stackoverflow.com/questions/53017827/example-celery-v4-2-with-mongodb-results-backend)

## DBaaS

Deploy ourselves or [cloud-native](https://en.wikipedia.org/wiki/Cloud_database)? That's the question.

### Deploy in OpenShift

There are publicly available container images for both [Postgresql](https://docs.openshift.com/container-platform/3.11/using_images/db_images/postgresql.html) and [MongoDB](https://docs.openshift.com/container-platform/3.11/using_images/db_images/mongodb.html).

### AWS

#### Postgresql

- [Amazon RDS for PostgreSQL](https://aws.amazon.com/rds/postgresql)
- [PostgreSQL on Amazon RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)

#### MongoDB

Even that one can use MongoDB in AWS (see [[1]](https://docs.aws.amazon.com/quickstart/latest/mongodb/welcome.html), [[2]](https://aws.amazon.com/quickstart/architecture/mongodb)), Amazon seems to be pushing their MongoDB compatible [DocumentDB](https://aws.amazon.com/documentdb) (see also [Docs/Developer Guide](https://docs.aws.amazon.com/documentdb/latest/developerguide)).
Given that we don't need full MongoDB compatibility, the DocumentDB seems to be the preferred one. (and the winner of today's battle)
