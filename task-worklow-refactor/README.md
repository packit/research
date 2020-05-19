# How to split one Celery task into multiple tasks

Let's talk about splitting the `task.process_message` into one processing task
and multiple tasks handling the specific events. The main benefit from this 
will be the possibility to use more queues (for faster/slower tasks)
 and to differentiate tasks easily (Sentry).


## Workflow
 - get webhook payload or message from message bus 
 - add aditional info which can make determining the event type easier
 (GH webhooks - X-GitHub-Event)
 - send it to Celery as `task.process_message` - this task will take care about:
    - parsing of the event into object of class Event (this class provides `project`, `package_config` properties,
     which enables us to make the checks)
    - private repository check
    - getting the handlers which handle the event
    - whitelist check
    - possibly creating records in DB (explained below)
    - (running `pre-check` here to filter out some events?)
    - sending specific task to Celery
  - handle specific tasks, which directly run the handlers
    
#### How to pass the information needed by handlers
 Handlers are currently using the information from event (with `project` and `package_config` properties, specific for each event),
  service config and job config object:
 ```python
class JobHandler(Handler):
    def __init__(
        self, config: ServiceConfig, job_config: Optional[JobConfig], event: Event
    )
```
 Possible solutions, which can be somehow combined:
 1. serialize the info about objects and pass it into `send_task`
     - this would need serializing and then again deserializing
 2. save the info about objects in DB and pass IDs of models into `send_task`
     - what models does make sense to have? possibilities:
         - project
         - package config 
         - service config
         - job config 
         - event
     
     - each subclass of class Event stores different set of info -> does it make sense to create model for each? 
     - these could be reused since in `task_results` table we store the event dict
 3. pass just the arguments which are required by the specific handler


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