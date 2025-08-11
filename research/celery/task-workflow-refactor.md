---
title: How to split one Celery task into multiple tasks
authors: lbarczio
---

Let's talk about splitting the `task.process_message` into one processing task
and multiple tasks handling the specific events. The main benefit from this
will be the possibility to use more queues (for faster/slower tasks)
and to differentiate tasks easily (Sentry).

## Workflow 1

- get webhook payload or message from message bus
- add aditional info which can make determining the event type easier
  (GH webhooks - X-GitHub-Event)
- send it to Celery as `task.process_message` - this task will take care about:
  - parsing of the event into object of class Event (this class provides `project`,
    `package_config` properties, which enables us to make the checks)
  - private repository check
  - getting the handlers which handle the event
  - whitelist check
  - possibly creating records in DB (explained below)
  - (running `pre-check` here to filter out some events?)
  - sending specific task to Celery
- handle specific tasks, which directly run the handlers

#### How to pass the information needed by handlers (already discussed)

Handlers are currently using the information from event (with `project` and
`package_config` properties, specific for each event), service config and job config object:

```python
class JobHandler(Handler):
   def __init__(
       self, config: ServiceConfig, job_config: Optional[JobConfig], event: Event
   )
```

Possible solutions, which can be somehow combined:

1.  serialize the info about objects and pass it into `send_task`
    - this would need serializing and then again deserializing
2.  save the info about objects in DB and pass IDs of models into `send_task`
    - what models does make sense to have? possibilities:
      - project
      - package config
      - service config
      - job config
      - event

    - each subclass of class Event stores different set of info -> does it make sense
      to create model for each?
    - these could be reused since in `task_results` table we store the event dict

3.  pass just the arguments which are required by the specific handler

### What needs to be done

- create functions for serializing and deserializing the objects needed by each handler:
  - service config
  - package config
  - job config
  - project
- for each event create method which serializes and deserializes event specific data
- after doing the checks and getting the handlers pass arguments to `send_task` for each handler
  instead of running it:

```python
    # serialize objects
    serialized_config = self.config.serialize()
    ...

    handler = handler_kls(...)
    if handler.pre_check():
        celery_app.send_task(
            name=handler.task_name,
            kwargs={"config": serialized_config,
                    "job_config": serialized_job_config,
                    "package_config": serialized_package_config,
                    "project": serialized_project,
                    "specific_info": info_dict}
        )
```

- create task for each handler -> create functions handling tasks:

```python
@celery_app.task(name="task.run_copr_build_start_handler")
def process_message(self, ...):
   # get objects from serialized data
   ...

   handler = CoprBuildStartHandler(...)
   handler.run_n_clean()


```

- change the code in handlers to handle changed attributes correctly
  (have project, config, job config, package config and specific data in separate attributes ,
  not everthing in original event object)

### How the transition could be done in smaller steps

- implement the helper functions
  - serializing and deserializing common data (configs)
  - serializing event-specific data
- change the code in handlers without using Event class,
  so that the project and configs are separate attributes
  as well as event-specific info is deserialized into attributes
- when the changed handler code works, implement the division of 1 task into more tasks
  (described above - create functions for processing each task)

## Workflow 2

- get webhook payload or message from message bus
- add aditional info which can make determining the event type easier
  (GH webhooks - X-GitHub-Event)
- send it to Celery as `task.parse_message` - this task will take care about:
  - parsing of the info needed for the event object (doing event specific pre-check?)
- send event specific task to Celery with all arguments needed to create object of specific event
- event specific tasks will take care about:
  - private repository check
  - getting the handlers which handle the event
  - whitelist check
  - run the handlers

### What needs to be done

- in each specific parser function send task to Celery:

```python
def parse_pr_event(event):
    ...
    commit_sha = nested_get(event, "pull_request", "head", "sha")
    https_url = event["repository"]["html_url"]

    celery_app.send_task(
        name="task.process_pr_event",
        kwargs={"action": PullRequestAction[action],
                "pr_id": pr_id,
                "base_repo_namespace": base_repo_namespace,
                "base_repo_name": base_repo_name,
                "base_ref": base_ref,
                "target_repo_namespace": target_repo_namespace,
                "target_repo_name": target_repo_name,
                "https_url": https_url,
                "commit_sha": commit_sha,
                "user_login":user_login}
    )
```

- create task for each event -> create functions handling the event specific tasks,
  which create event object and do the things written above

```python
@celery_app.task(name="task.process_pull_request_GH_event")
def process_message(self, ...):
   event = PullRequestGHEvent(...)
   event.process()
# process method would contain code moved from process_message(),
# the checks and running jobs



```

#### Which tasks do we want to have?

- task x job (what has to be done in general, independently on the trigger and git forge):
  - propose_downstream
  - build/copr_build
  - sync_from_downstream
  - production_build
  - add_to_whitelist
  - tests
  - report_test_results
  - pull_request_action
  - copr_build_finished
  - copr_build_started
- task x handler (which handler handles the task)
  - ReleaseCoprBuildHandler
  - PullRequestCoprBuildHandler
  - PushCoprBuildHandler
  - GitHubPullRequestCommentCoprBuildHandler
  - CoprBuildStartHandler
  - CoprBuildEndHandler
  - GithubAppInstallationHandler
  - GitHubPullRequestCommentTestingFarmHandler
  - GithubTestingFarmHandler
  - TestingFarmResultsHandler
  - GitHubIssueCommentProposeUpdateHandler
  - ProposeDownstreamHandler
  - ReleaseGithubKojiBuildHandler
  - PullRequestGithubKojiBuildHandler
  - PushGithubKojiBuildHandler
  - NewDistGitCommitHandler
  - PagurePullRequestCommentCoprBuildHandler
- task x event (what event triggered the task)
  - InstallationEvent
  - CoprBuildEvent
  - KojiBuildEvent
  - TestingFarmResultEvent
  - ReleaseEvent
  - PushGithubGHEvent
  - PullRequestGHEvent
  - PullRequestCommentGHEvent
  - IssueCommentEvent
  - PushPagureEvent
  - PullRequestCommentPagureEvent
  - PullRequestPagureEvent
