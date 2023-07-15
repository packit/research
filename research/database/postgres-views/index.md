---
title: Postgres views
authors: mmassari
---

## Why this research

While working on [this card](https://github.com/packit/packit-service/issues/1328) I thought that a `sql view` could have been usefull to speed up queries and simplify the code.
I took as a reference the code for the [usage statistics](https://github.com/packit/packit-service/blob/01cbaf4fc3eb1898a1bb9d73a638d218b7a9c8d0/packit_service/models.py#L812-L869).
My goal was to avoid duplicating a field (as requested by step 3 in [this card](https://github.com/packit/packit-service/issues/1328)), speeding up the query and make the code more simple using `sql views`.
Implicitly I was working also on [this card](https://github.com/packit/packit-service/issues/1986).

## Materialized views

My first thought was that `materialized views` could improve queries' performance.

To create a `materialized view` -> **4097.513 ms**.

```sql
CREATE MATERIALIZED VIEW copr_target_builds_for_pull_requests AS
    SELECT git_projects.project_url, git_projects.repo_name, copr_build_targets.build_id, pipelines.datetime
    FROM git_projects
    JOIN pull_requests ON git_projects.id = pull_requests.project_id
    JOIN job_triggers ON job_triggers.trigger_id = pull_requests.id
    JOIN pipelines ON pipelines.job_trigger_id = job_triggers.id
    JOIN copr_build_groups ON copr_build_groups.id = pipelines.copr_build_group_id
    JOIN copr_build_targets ON copr_build_targets.copr_build_group_id = copr_build_groups.id
    ORDER BY git_projects.project_url, git_projects.instance_url;
```

---

To refresh the `materialized view` -> **5526.618 ms**

```
SELECT * FROM copr_target_builds_for_pull_requests;
```

---

To query the `materialized view` -> **904.686 ms**

```
SELECT * FROM copr_target_builds_for_pull_requests;
```

---

To create a `normal view` -> **25.266 ms**

```sql
CREATE VIEW copr_target_builds_for_pull_requests AS
    SELECT git_projects.project_url, git_projects.repo_name, copr_build_targets.build_id, pipelines.datetime
    FROM git_projects
    JOIN pull_requests ON git_projects.id = pull_requests.project_id
    JOIN job_triggers ON job_triggers.trigger_id = pull_requests.id
    JOIN pipelines ON pipelines.job_trigger_id = job_triggers.id
    JOIN copr_build_groups ON copr_build_groups.id = pipelines.copr_build_group_id
    JOIN copr_build_targets ON copr_build_targets.copr_build_group_id = copr_build_groups.id
    ORDER BY git_projects.project_url, git_projects.instance_url;
```

---

To query the `normal view` -> **2616.131 ms**

```
SELECT * FROM copr_target_builds_for_pull_requests;
```

---

Since we have to refresh a `materialized view`, like this, every time we use it (the data it contains change too often) sadly **there is no improvement**.

## Normal views

Normal views, _once created, are easy to work with_ but I can not really say that they save us time.

To get the usage statistics page from the service api (https://service.localhost/api/) it tooks me **4 seconds**

```logs
service             | [Fri May 19 12:57:34.145012 2023] [wsgi:error] [pid 6:tid 39] [remote 10.89.0.4:39636] 2023-05-19 12:57:34,144 INFO sqlalchemy.engine.Engine [cached since 1.482e+04s ago] {'type_1': 'issue'}
service             | 10.89.0.4 - - [19/May/2023:12:57:30 +0000] "GET /api/usage HTTP/1.1" 200 120160
```

To get all the data we need with a single query (saved as a view named `jobs_count`) it tooks me **3277.724 ms**.

We can move the complexity below at sql level and simplify our code, this is all.

The views are not really supported in sqlalchemy, there are two projects that implement them somehow (`sqlalchemy-utils` and `sqlalchemy-views`) but this are "young projects" I would not count on them for the `packit-service` code.

There is a page in the sqlalchemy documentation that shows how to implement support for views in a [tricky way](https://github.com/sqlalchemy/sqlalchemy/wiki/Views).

_But in neither of this cases alembic will be supported_.

I think that the most effective way to use `views`, at the moment, is just create them in a migration (with pure sql) and simply map them in our sqlalchemy models.
In this way we can not create or delete them through sqlalchemy but we can easily query them as normal tables. I have tried this and seems to be working.

I have created some views that can remove the loops inside the code for the [usage statistics](https://github.com/packit/packit-service/blob/01cbaf4fc3eb1898a1bb9d73a638d218b7a9c8d0/packit_service/models.py#L812-L869).
If we want to move the complexity from the python code to the sql level this can be useful.
However we agreed that _we prefer to read more complex python code than more complex sql code_.

```sql
CREATE VIEW projects_for_triggers AS
SELECT temporary.project_url, temporary.instance_url, temporary.trigger_id, job_triggers.id AS job_trigger_id, job_triggers.type FROM
	(SELECT git_projects.project_url, git_projects.instance_url, pull_requests.id AS trigger_id FROM git_projects
		JOIN pull_requests ON git_projects.id = pull_requests.project_id UNION
		(SELECT git_projects.project_url, git_projects.instance_url, git_branches.id AS trigger_id FROM git_projects
			JOIN git_branches ON git_projects.id = git_branches.project_id UNION
			(SELECT git_projects.project_url, git_projects.instance_url, project_releases.id AS trigger_id FROM git_projects
				JOIN project_releases ON git_projects.id = project_releases.project_id UNION
					(SELECT git_projects.project_url, git_projects.instance_url, project_issues.id AS trigger_id FROM git_projects
						JOIN project_issues ON git_projects.id = project_issues.project_id)))) temporary
	JOIN job_triggers ON job_triggers.trigger_id = temporary.trigger_id;

EXPLAIN ANALYZE [...] -> 17ms
```

```
                           project_url                           |      instance_url      | trigger_id | job_trigger_id |     type
-----------------------------------------------------------------+------------------------+------------+----------------+--------------
 https://github.com/cockpit-project/cockpit                      | github.com             |      48233 |          27750 | pull_request
 https://github.com/RedHat-SP-Security/keylime-tests             | github.com             |      51015 |          30088 | pull_request
 https://github.com/cockpit-project/cockpit                      | github.com             |      53514 |          32279 | pull_request
 https://github.com/systemd/systemd                              | github.com             |      49850 |          29120 | pull_request
 https://github.com/systemd/systemd                              | github.com             |      49745 |          29029 | pull_request
 https://github.com/systemd/systemd                              | github.com             |      57009 |          35291 | pull_request
 https://github.com/systemd/systemd                              | github.com             |      56241 |          34633 | pull_request
 https://github.com/storaged-project/blivet                      | github.com             |      58353 |          36386 | pull_request
 https://github.com/ComplianceAsCode/content                     | github.com             |      56362 |          34737 | pull_request
 https://github.com/cockpit-project/cockpit                      | github.com             |      62372 |          40035 | pull_request
 https://github.com/fedora-infra/fedora-messaging                | github.com             |       1372 |          27932 | release
...
```

```sql
CREATE VIEW triggers_count AS
SELECT DISTINCT projects_for_triggers.project_url, projects_for_triggers.type, COUNT(projects_for_triggers.trigger_id) OVER (PARTITION BY projects_for_triggers.project_url, projects_for_triggers.type) FROM projects_for_triggers WHERE projects_for_triggers.instance_url != 'src.fedoraproject.org' GROUP BY projects_for_triggers.project_url, projects_for_triggers.type, projects_for_triggers.trigger_id ORDER BY projects_for_triggers.type, COUNT(projects_for_triggers.trigger_id) OVER (PARTITION BY projects_for_triggers.project_url, projects_for_triggers.type) DESC;

EXPLAIN ANALYZE [...] -> 55ms
```

```
                           project_url                           |     type     | count
-----------------------------------------------------------------+--------------+-------
 https://github.com/systemd/systemd                              | pull_request |  3055
 https://github.com/ComplianceAsCode/content                     | pull_request |  1499
 https://github.com/cockpit-project/cockpit                      | pull_request |  1067
 https://github.com/osbuild/osbuild-composer                     | pull_request |   757
 https://github.com/teemtee/tmt                                  | pull_request |   605
 https://github.com/rhinstaller/anaconda                         | pull_request |   568
 https://github.com/packit/hello-world                           | pull_request |   452
 https://github.com/ansible/ansible-lint                         | pull_request |   447
 https://github.com/nmstate/nmstate                              | pull_request |   438
 https://github.com/keylime/keylime                              | pull_request |   317
 https://github.com/cockpit-project/cockpit-machines             | pull_request |   305
 https://github.com/fedora-infra/noggin                          | pull_request |   295
 https://github.com/oamg/convert2rhel                            | pull_request |   290
 https://github.com/cockpit-project/cockpit-podman               | pull_request |   287
...
```

```sql
CREATE VIEW pipelines_for_projects AS
SELECT projects_for_triggers.project_url, projects_for_triggers.instance_url, projects_for_triggers.type, pipelines.datetime, pipelines.srpm_build_id, pipelines.sync_release_run_id, pipelines.vm_image_build_id, pipelines.test_run_group_id, pipelines.copr_build_group_id, pipelines.koji_build_group_id FROM projects_for_triggers JOIN pipelines ON projects_for_triggers.job_trigger_id = pipelines.job_trigger_id;

CREATE VIEW jobs_for_projects AS
SELECT pipelines_for_projects.project_url, pipelines_for_projects.instance_url, pipelines_for_projects.type AS trigger_type, pipelines_for_projects.datetime, srpm_builds.build_submitted_time AS submitted_time, srpm_builds.id AS job_id, 'srpm_build' AS job_type FROM pipelines_for_projects
	JOIN srpm_builds ON pipelines_for_projects.srpm_build_id = srpm_builds.id
	UNION (SELECT pipelines_for_projects.project_url, pipelines_for_projects.instance_url, pipelines_for_projects.type AS trigger_type, pipelines_for_projects.datetime, sync_release_runs.submitted_time, sync_release_runs.id AS job_id, 'sync_release_run' AS job_type  FROM pipelines_for_projects
		JOIN sync_release_runs ON pipelines_for_projects.sync_release_run_id = sync_release_runs.id
		UNION (SELECT pipelines_for_projects.project_url, pipelines_for_projects.instance_url, pipelines_for_projects.type AS trigger_type, pipelines_for_projects.datetime, koji_build_groups.submitted_time, koji_build_groups.id AS job_id, 'koji_build' AS job_type  FROM pipelines_for_projects
			JOIN koji_build_groups ON pipelines_for_projects.koji_build_group_id = koji_build_groups.id
			UNION (SELECT pipelines_for_projects.project_url, pipelines_for_projects.instance_url, pipelines_for_projects.type AS trigger_type, pipelines_for_projects.datetime, copr_build_groups.submitted_time, copr_build_groups.id AS job_id, 'copr_build' AS job_type  FROM pipelines_for_projects
				JOIN copr_build_groups ON pipelines_for_projects.copr_build_group_id = copr_build_groups.id
				UNION (SELECT pipelines_for_projects.project_url, pipelines_for_projects.instance_url, pipelines_for_projects.type AS trigger_type, pipelines_for_projects.datetime, tft_test_run_groups.submitted_time, tft_test_run_groups.id AS job_id, 'test_run' AS job_type  FROM pipelines_for_projects
					JOIN tft_test_run_groups ON pipelines_for_projects.test_run_group_id = tft_test_run_groups.id
					UNION (SELECT pipelines_for_projects.project_url, pipelines_for_projects.instance_url, pipelines_for_projects.type AS trigger_type, pipelines_for_projects.datetime, vm_image_build_targets.build_submitted_time AS submitted_time, vm_image_build_targets.id AS job_id, 'vm_image_build' AS job_type  FROM pipelines_for_projects
						JOIN vm_image_build_targets ON pipelines_for_projects.vm_image_build_id = vm_image_build_targets.id)))));

EXPLAIN ANALYZE [...] -> 2337.092 ms
```

```
                           project_url                           |      instance_url      | trigger_type |          datetime          |       submitted_time       | job_id |     job_type
-----------------------------------------------------------------+------------------------+--------------+----------------------------+----------------------------+--------+------------------
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-09-19 07:42:57.065564 | 2022-09-19 07:42:57.060558 |  88793 | srpm_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-09-19 07:42:57.065564 | 2023-02-14 02:27:54.598528 |   2876 | copr_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-09-19 07:43:31.062927 | 2022-09-19 07:42:57.060558 |  88793 | srpm_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-09-19 07:43:31.062927 | 2023-02-14 02:27:54.598528 |   2876 | copr_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-09-19 07:43:31.690265 | 2022-09-19 07:42:57.060558 |  88793 | srpm_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-09-19 07:43:31.690265 | 2023-02-14 02:27:54.598528 |   2876 | copr_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-09-19 07:43:32.33272  | 2022-09-19 07:42:57.060558 |  88793 | srpm_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-09-19 07:43:32.33272  | 2023-02-14 02:27:54.598528 |   2876 | copr_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-11-29 20:36:10.322812 | 2022-11-29 20:36:10.3174   | 101186 | srpm_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-11-29 20:36:10.322812 | 2023-02-14 02:55:59.35493  |  96222 | copr_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-11-29 20:36:45.713206 | 2022-11-29 20:36:10.3174   | 101186 | srpm_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-11-29 20:36:45.713206 | 2023-02-14 02:55:59.35493  |  96222 | copr_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-11-29 20:36:46.305243 | 2022-11-29 20:36:10.3174   | 101186 | srpm_build
 https://github.com/abrt/abrt-java-connector                     | github.com             | pull_request | 2022-11-29 20:36:46.305243 | 2023-02-14 02:55:59.35493  |  96222 | copr_build
...
```

```sql
CREATE VIEW jobs_count AS
SELECT DISTINCT jobs_for_projects.project_url, jobs_for_projects.trigger_type, jobs_for_projects.job_type, COUNT(jobs_for_projects.job_id) OVER (PARTITION BY jobs_for_projects.project_url, jobs_for_projects.trigger_type, jobs_for_projects.job_type) FROM jobs_for_projects WHERE jobs_for_projects.instance_url != 'src.fedoraproject.org' GROUP BY jobs_for_projects.project_url, jobs_for_projects.trigger_type, jobs_for_projects.job_type, jobs_for_projects.job_id ORDER BY jobs_for_projects.trigger_type, jobs_for_projects.job_type, COUNT(jobs_for_projects.job_id) OVER (PARTITION BY jobs_for_projects.project_url, jobs_for_projects.trigger_type, jobs_for_projects.job_type) DESC;

EXPLAIN ANALYZE [...] -> 3277.724 ms
```

```
                           project_url                           | trigger_type |     job_type     | count
-----------------------------------------------------------------+--------------+------------------+-------
 https://github.com/systemd/systemd                              | pull_request | copr_build       |  9523
 https://github.com/teemtee/tmt                                  | pull_request | copr_build       |  6099
 https://github.com/packit/hello-world                           | pull_request | copr_build       |  5129
 https://github.com/osbuild/osbuild-composer                     | pull_request | copr_build       |  4322
 https://github.com/cockpit-project/cockpit                      | pull_request | copr_build       |  4133
 https://github.com/ComplianceAsCode/content                     | pull_request | copr_build       |  3948
 https://github.com/oamg/convert2rhel                            | pull_request | copr_build       |  2591
 https://github.com/nmstate/nmstate                              | pull_request | copr_build       |  1539
 https://github.com/rhinstaller/anaconda                         | pull_request | copr_build       |  1454
 https://github.com/cockpit-project/cockpit-machines             | pull_request | copr_build       |  1266
 https://github.com/ansible/ansible-lint                         | pull_request | copr_build       |  1247
 https://github.com/oamg/leapp-repository                        | pull_request | copr_build       |  1185
...
```

```sql
CREATE VIEW job_triggers_commit_sha AS
SELECT job_triggers.id, job_triggers.type, srpm_builds.commit_sha FROM pipelines
        JOIN job_triggers ON pipelines.job_trigger_id = job_triggers.id
	JOIN srpm_builds ON pipelines.srpm_build_id = srpm_builds.id
	UNION (SELECT job_triggers.id, job_triggers.type, koji_build_targets.commit_sha FROM pipelines
		JOIN job_triggers ON pipelines.job_trigger_id = job_triggers.id
		JOIN koji_build_groups ON pipelines.koji_build_group_id = koji_build_groups.id
		JOIN koji_build_targets ON koji_build_groups.id = koji_build_targets.koji_build_group_id
		UNION (SELECT job_triggers.id, job_triggers.type, copr_build_targets.commit_sha FROM pipelines
			JOIN job_triggers ON pipelines.job_trigger_id = job_triggers.id
			JOIN copr_build_groups ON pipelines.copr_build_group_id = copr_build_groups.id
			JOIN copr_build_targets ON copr_build_groups.id = copr_build_targets.copr_build_group_id
			UNION (SELECT job_triggers.id, job_triggers.type, tft_test_run_targets.commit_sha FROM pipelines
				JOIN job_triggers ON pipelines.job_trigger_id = job_triggers.id
				JOIN tft_test_run_groups ON pipelines.test_run_group_id = tft_test_run_groups.id
				JOIN tft_test_run_targets ON tft_test_run_groups.id = tft_test_run_targets.tft_test_run_group_id
				UNION (SELECT job_triggers.id, job_triggers.type, vm_image_build_targets.commit_sha FROM pipelines
					JOIN job_triggers ON pipelines.job_trigger_id = job_triggers.id
					JOIN vm_image_build_targets ON pipelines.vm_image_build_id = vm_image_build_targets.id))));

EXPLAIN ANALYZE [...] -> 3369.211 ms
```

```
  id   |     type     |                commit_sha
-------+--------------+------------------------------------------
  4641 | pull_request | 3854797abbbf445a8190b46f6471bff0bfcac8fb
  5887 | branch_push  | 01462368e03f0e9705a6ee6ca146dc666e13ac27
  5887 | branch_push  | 035759ba734efcd08b1d23666d29efe963e909e7
  5887 | branch_push  | 060b82ccd5739c87494453110886a1663409886f
  5887 | branch_push  | 0f9759f0bd1fc237558db8b3cf2037016a292de7
  5887 | branch_push  | 1099056a5a04ab0e12278cf910f655bd3cc7835c
  5887 | branch_push  | 1374cc11cdcf08080bf16aaef704ec010eafbcb7
  5887 | branch_push  | 1b5611cd822602c265ab73c2f8f5246a721e4b9d
  5887 | branch_push  | 213c789c5ec496e4471dbdb7279d9d7d61b4ed44
  5887 | branch_push  | 281a5acbdbc8358405bc75e72f568cb7fd7a8a84
  5887 | branch_push  | 2e316980c3a00156fa7d3ac313dc53304e1dcf95
  5887 | branch_push  | 33fd64ac44b22c4da8a40cea7c817d8b8178f4ec
  5887 | branch_push  | 3c699c5077f6803ca8054350c51cb5d2fc7436e1
  5887 | branch_push  | 3cf8b476ecf9482ba1dc5fa24155ea8be9dab141
 ...
```
