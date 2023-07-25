---
title: `commit_sha` refactor follow-up
authors: mmassari
---

# `commit_sha` refactor follow-up

Database refactoring from PR https://github.com/packit/packit-service/pull/2070 related with issue https://github.com/packit/packit-service/issues/1328 has:

- renamed `JobTriggerModel` in `ProjectEventModel`
- removed the `commit_sha` field from `CoprBuildTargetModel`, `KojiBuildTargetModel`, `SRPMBuildModel`, `TFTTestRunGroupModel`, `VMImageBuildTargetModel` and moved it into the `ProjectEventModel`

#### These are some of the thoughts that came to my mind after having worked on this:

I always thought that a `JobTriggerModel` was an "event" able to trigger jobs in packit-service.
But we were not using the `JobTriggerModel` like an event: two different pushes to the same pull request are two different pull request events but we were not saving two different rows in the `JobTriggerModel`. For this reason I would say that we were not dealing with events but just with "project objects" like pull requests, releases or issues.
I can say that the `JobTriggerModel` was the base table of polymorphic entities: the "project objects" entities (pull request, branch push, release, issue).

I have added the `commit_sha` to the `ProjectEventModel` (ex `JobTriggerModel`) and **now this is really an event table and I lose the base table for the polymorphic project object entities**!

I see the relation between the ex `JobTriggerModel` and `PullRequestModel/GitBranchModel/[...]` as the relation between `Employee` and `Engineer/Manager`; I can not add a row in employee without adding a row in engineer or manager. Now I am adding many new rows in the `ProjectEventModel`, one row for every new push with a new commit_sha, but I am not adding new rows to the project objects tables. Now this table is really a "project event" table and no more the base table for the "project objects".

I think this refactoring could be further improved for the following reasons:

1. The `ProjectEventModel` table now keeps track of events but just for those events that have a `commit_sha`. For the issue's events, as an example, since there is no way to differentiate them we will end up having always just one event for the same issue (even though many comments have been created). _To have issue events in the table we need to save some other kind of information like the comment id._

   Same thing for the release events generated with a `NewHotnessEvent`, where I can't get the `commit_sha` from the project, unless I refactorize completely this [method](https://github.com/packit/packit-service/blob/34aa347efe8f06810134590244d514a67392ea5b/packit_service/worker/events/event.py#L148) (here we need to use the specialized event classes and not the generic one).

   A way to use the project event could be to collect in one view all related jobs triggered by the same event or a history of the events per project with their related jobs but we can not really do this, right now, since the above problems.

2. We can not properly model an `hardly` use case: for a `MergeRequestGitlabEvent` we are dealing in hardly with a source_git `PullRequestModel` object and a dist_git `PullRequestModel` db object. They have different `commit_sha` (because they are placed in two different git projects) but the event which triggered this job is just one. So it seems to me that we need a `n-m` relationship between events and related project objects.

   The event by itself should not be forcibly related with a project object but, as a result, it will make packit-service work on one or more project objects.

Probably a db re-design improvement could be something similar to the following:

```
events (EventModel)
    id (PK)
    type (event type?)

project_objects (ProjectObjectModel)
    id (PK)
    type (pull_request, branch_push, release, issue)

commit_sha (CommitSHAModel)
    id (PK)
    event_id (FK to EventModel)
    project_object_id (FK to ProjectObjectModel)
    commit_sha

comment (CommentModel)
    id (PK)
    event_id (FK to EventModel)
    project_object_id (FK to ProjectObjectModel)
    comment_id

pull_requests (PullRequestModel)
    id (PK) (FK to ProjectObjectModel)
    project_id (FK to GitProjectModel)
    pr_id

git_branches (GitBranchModel)
    id (PK) (FK to ProjectObjectModel)
    project_id (FK to GitProjectModel)
    issue_id

issues (IssueModel)
    id (PK) (FK to ProjectObjectModel)
    project_id (FK to GitProjectModel)
    name
```
