# What's in packit's production database?

## How-to?

Here is how you can get a production database shell, please use it wisely!

Find the name of the postgres pod on the production OpenShift namesapce:

    $ oc get pods | grep postgres
    postgres-12-1-t4l5k                 1/1       Running     0          80d

Open a database console:

    $ oc rsh postgres-12-1-t4l5k psql
    psql (12.5)
    Type "help" for help.

Connect to the packit database:

    postgres=# \c packit
    You are now connected to database "packit" as user "postgres".

List tables in the database:

    packit=# \dt
                          List of relations
     Schema |             Name             | Type  |    Owner
    --------+------------------------------+-------+-------------
     public | alembic_version              | table | packit-boss
     public | allowlist                    | table | packit-boss
     public | bugzillas                    | table | packit-boss
     public | build_triggers               | table | packit-boss
     public | celery_taskmeta              | table | packit-boss
     public | celery_tasksetmeta           | table | packit-boss
     public | copr_builds                  | table | packit-boss
     public | git_branches                 | table | packit-boss
     public | git_projects                 | table | packit-boss
     public | github_installations         | table | packit-boss
     public | koji_builds                  | table | packit-boss
     public | project_authentication_issue | table | packit-boss
     public | project_issues               | table | packit-boss
     public | project_releases             | table | packit-boss
     public | pull_requests                | table | packit-boss
     public | runs                         | table | packit-boss
     public | srpm_builds                  | table | packit-boss
     public | tft_test_runs                | table | packit-boss
    (18 rows)

## Review tables

So let's start reviewing how many entries there are in the tables:

    packit=# SELECT schemaname,relname,n_live_tup
      FROM pg_stat_user_tables
      ORDER BY n_live_tup DESC;
     schemaname |           relname            | n_live_tup
    ------------+------------------------------+------------
     public     | celery_taskmeta              |     135670
     public     | runs                         |     111345
     public     | copr_builds                  |     108398
     public     | srpm_builds                  |      32558
     public     | tft_test_runs                |      29114
     public     | pull_requests                |      22377
     public     | git_branches                 |      16780
     public     | build_triggers               |      10411
     public     | project_issues               |       5363
     public     | git_projects                 |       4960
     public     | project_releases             |        585
     public     | koji_builds                  |        254
     public     | allowlist                    |        186
     public     | github_installations         |        154
     public     | project_authentication_issue |          2
     public     | alembic_version              |          1
     public     | bugzillas                    |          0
     public     | celery_tasksetmeta           |          0
    (18 rows)

`celery_taskmeta` has 135k entries, what's in there?

    packit=# select * from celery_taskmeta limit 1;
       id    |               task_id                | status  |    result    |         date_done          | traceback | name | args | kwargs | worker | retries | queue
    ---------+--------------------------------------+---------+--------------+----------------------------+-----------+------+------+--------+--------+---------+-------
     1249908 | d56ac427-0fbc-4d84-bae8-9a6cc045a11d | SUCCESS | \x80055d942e | 2021-08-07 04:01:27.184676 |           |      |      |        |        |         |
    (1 row)

Celery results! And some seems to be pretty beefy:

    packit=# SELECT pg_size_pretty( pg_total_relation_size('celery_taskmeta') );
     pg_size_pretty
    ----------------
     155 MB
    (1 row)

The other two tables are smaller:

    packit=# SELECT pg_size_pretty( pg_total_relation_size('runs') );
     pg_size_pretty
    ----------------
     9264 kB
    (1 row)


    packit=# SELECT pg_size_pretty( pg_total_relation_size('copr_builds') );
     pg_size_pretty
    ----------------
     45 MB
    (1 row)

Though srpm build logs take up a lot of space:

    packit=# SELECT pg_size_pretty( pg_total_relation_size('srpm_builds') );
     pg_size_pretty
    ----------------
     239 MB
    (1 row)

### Useless entries

Let's see if we have some "useless" entries in the database.

    packit=# select count(*) from runs where test_run_id is null and koji_build_id is null and copr_build_id is null and srpm_build_id is null;
     count
    -------
         0
    (1 row)


    packit=# select count(*) from copr_builds where build_id is null;
     count
    -------
         0
    (1 row)

### Checking validaty of links

This section involves Copr only since that's where all our database links
point. Copr has a fairly [aggressive garbage collection
policy](https://docs.pagure.org/copr.copr/user_documentation.html#how-long-do-you-keep-the-builds).

| Type            | Removed after |
| --------------- | ------------- |
| SRPM files      | 2 weeks       |
| Failed builds   | 2 weeks       |
| Old packages[1] | 2 weeks       |
| Fresh builds[2] | Never         |

[1] - These builds are superseded by newer submissions.

[2] - Our Copr projects for pull-request builds are set to be removed after 60 days.

## Future work

- Do not store task results in the database. We are not using them for
  anything. Even [celery's
  documentation](https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html#keeping-results)
  says it's an optional thing to do:

        If you want to keep track of the tasks’ states, Celery needs to store or
        send the states somewhere. There are several built-in result backends to
        choose from: SQLAlchemy/Django ORM, MongoDB, Memcached, Redis, RPC
        (RabbitMQ/AMQP), and – or you can define your own.

- We should implement a DB cleanup mechanism based on the findings above. One
  thing to keep in mind is that with dashboard and metrics, it make sense to keep
  old data for statistical purpose, except for the SRPM builds logs which take up
  a lot of space.

- We are not doing
  [vacuum](https://www.postgresql.org/docs/current/sql-vacuum.html)
  periodically which is a best practice to conserve space.
