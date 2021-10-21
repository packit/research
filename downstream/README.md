# Automation of the downstream part of the workflow

In this document, I would like to take a look at the downstream part of the Fedora workflow and how we can automate it, namely:

- from upstream to dist-git (already implemented, but still needs to be revisited)
- builds in Koji
- creating updates in Bodhi

For each step, I would like to cover the following structure:

- User perspective
  - How to enable?
  - How to trigger?
  - How to enhance the workflow?
  - What this should do?
- Implementation
  - How we can get the event?
  - How to implement it?
  - How to communicate with the user?

_The user perspective is described as a goal, the already implemented parts are explicitly marked as already done._

## From upstream to dist-git

### User perspective

As a maintainer, I would like to get a pull-request in distgit when the new upstream git-tag is created. Specifically:

- Version in specfile is updated and there is a new changelog entry.
- New version of source is saved in lookaside cache and the spec-file uses that new version.
- Some files can be directly synced to dist-git.

#### How to enable?

- I can install the Packit GitHub application and configure the `propose-downstream` job. (already possible)
- I can do this without the upstream's permission:
  - Send a pull-request to a repository containing the list of repositories to sync.
- I can configure this in dist-git.
  - I can use packit config to enable this.

#### How to trigger?

As a maintainer, I expect this to be done when there is a new upstream release. Also, I have a way to trigger this manually when I need and I have a way to re-create the PRs when there is a problem.

Specifically, triggering works like this:

- New upstream release can trigger the workflow. (already implemented)
- New commit to the branch can trigger the workflow. (needs to be enabled)
- Adding `/propose-downstream` comment to any upstream issue. (already implemented)
- Creating a new issue with some syntax.

Updating the already created PRs:

- Dist-git PR is closed and the workflow is retriggered (e.g. `/propose-downstream` comment). (already implemented)
- Comment to the dist-git PR to re-create the PR.
- Be able to push to the PR created by Packit.
  - Needs support in Pagure.

When reacting to comment, we now add :+1: to the comment so the user knows we have accepted the event.

#### How to enhance the workflow?

As a maintainer, I can influence the following:

- Which branch is updated.
- How the new changelog entry looks like.
- What files are synced to dist-git.
- Some command that is run to change the state of the dist-git.

When there is a packit config available, we can use it. If not, the configuration is not possible.

#### What this should done?

1. Find the source for the new release and upload it to the lookaside cache if it is not already there.
2. Update the version in specfile
3. Create the new changelog entry. There are multiple options for this:

- Changelog contains some generic text like `New upstream version X.Y.Z`
- Changelog is generated from the git history.
- Changelog is copied from the upstream (GitHub) release.
- Changelog is generated using a custom command. (Some environment variables can be provided what can be used when the syntax of the first option can't be used.)

![](./img/downstream-pr.png)
![](./img/downstream-pr-specfile-change.png)

### Implementation

#### How we can get the event?

If a user installs Packit GitHub application, we can get the event via webhook from GitHub.

https://github.com/packit/packit-service/blob/6d8764fb7dc59450a29e2ea8557b21c6f6f81748/packit_service/worker/events/github.py#L41:

```python
class ReleaseEvent(AddReleaseDbTrigger, AbstractGithubEvent):
```

https://github.com/packit/packit-service/blob/6d8764fb7dc59450a29e2ea8557b21c6f6f81748/packit_service/worker/handlers/distgit.py#L101-L107

```python
@configured_as(job_type=JobType.propose_downstream)
@run_for_comment(command="propose-downstream")
@run_for_comment(command="propose-update")  # deprecated
@reacts_to(event=ReleaseEvent)
@reacts_to(event=IssueCommentEvent)
@reacts_to(event=IssueCommentGitlabEvent)
class ProposeDownstreamHandler(JobHandler):
```

If a user does not have Packit installed for an upstream project, we can react to the fedora-messaging messages created by Upstream Release Monitoring. (Package can be added on https://release-monitoring.org/ .)

#### How to implement it?

We already have this implemented, but we can add support for branch push as a second trigger. (packit/packit-service#1284)

#### How to communicate with the user?

The main part for improvement is providing feedback during the process:

- Here is an EPIC issue for this in upstream: https://github.com/packit/packit-service/issues/1082
- Provide a dashboard view for the `propose-downstream` job. (https://github.com/packit/packit-service/issues/1292, https://github.com/packit/dashboard/issues/155)
- Live logs (https://github.com/packit/packit-service/issues/1080) or letting the user know in place where the job was triggered (https://github.com/packit/packit-service/issues/1293).
  - When reacting to the comment, we can put a comment with the details (link to the PRs).
  - When reacting to the release/commit, we can use commit status (check runs) to show some details.
- When things go bad, there should be some feedback to the user.
  - Also warnings should be accessible.
  - This is also true when retriggering the job when the dist-git PRs have already been created. In such a scenario, the current service silently ends. (One needs to close those PRs to regenerate them.)

## Koji builds

Here is a related issue for this: https://github.com/packit/packit-service/issues/55

### User perspective

When there is a new commit in dist-git, I want a new build for it to be triggered. Optionally, I can set that I want to trigger scratch build instead of the production one or set other arguments when triggering the build (e.g. side-tag).

#### How to enable?

Options:

- I can send a pull-request to a repository containing the list of repositories to build. (The same thing Zuul does.)
- I can add a packit config to the distgit repository and configure the job (can be combined with the previous version so we can filter the projects before checking config presence).
- A service authenticated by FAS where I can enable the build and, ideally, configure the process.

Also, the [`packit` FAS user](https://accounts.fedoraproject.org/user/packit/) needs to be added as a maintainer to the project. We can try getting the permission to run builds on any package, but that can add some requirements to the service (like running inside Fedora infrastructure, TODO: check it).

#### How to trigger?

The build is triggered once there is a new commit in dist-git.

Optionally, I can retrigger the action by a commit comment on dist-git.

#### How to enhance the workflow?

In the usual case, no enhancement is needed. If we need one, we can use packit config to provide this extra info.

#### What this should done?

Clone the dist-git repository and trigger a new Koji build for the new commit.

### Implementation

#### How we can get the event?

The information about new commits is sent to fedora-messaging. We already have a listener for it.

#### How to implement it?

- Make sure we react to these fedora-messaging messages.
- Check that this project wants to do the build.
- Optionally, get the extra arguments from the packit config. (No-config scenario is currently not supported.)
- Trigger the build using the already implemented method of the packit's Python API (in packit/packit project, not the web API).

There are (at least) 3 ways how to do this:

1. New `job_type` and new handler can be created to implement the core functionality.

- Needs a new name for a job that needs to be different to `production_build`, but looks like the easiest solution.

2. Reuse the existing handler for the `production-build` and act differently when running on a downstream project (submit the build in koji from dist-git, not by using an SRPM).

- User needs to differentiate job config between downstream and upstream build => New config option can be created, but needs to be resolved in job (makes the parsing complicated) or in the job (too late, we've already send a "Task accepted" status to the user).

3. Add a new trigger type for `production-build` and act differently (submit the build in koji from dist-git, not by using an SRPM).

- With the current database schema, commit (=`GitBranchModel`) implies one config trigger (`JobConfigTriggerType.commit` in this case).

#### How to communicate with the user?

- When the build is triggered, affected users are notified via standard Fedora notifications.
- When there is a problem, we can comment on the commit.
- Optionally, when the commit comes from the PR, we can comment to that PR.

## Bodhi updates

Here is a related issue for this: https://github.com/packit/packit-service/issues/74

### User perspective

When there is a new successful production build, I want a new Bodhi update to be created for me. If the commit contains info Bugzilla that is being closed by this, the Bugzilla is linked to this update

#### How to enable?

Options:

- I can send a pull-request to a repository containing the list of repositories to build. (The same thing Zuul does.)
- I can add a packit config to the distgit repository and configure the job (can be combined with the previous version so we can filter the projects before checking config presence).
- A service authenticated by FAS where I can enable the build and, ideally, configure the process.

#### How to trigger?

When the new version of the package is successfully built, the update can be created using this build.

TODO: We need to find a way to trigger the process manually. (In the worst case, we have a CLI.)

#### How to enhance the workflow?

In the usual case, no enhancement is needed. If we need one, we can use packit config to provide this extra info.

#### What this should done?

Create a new Bodhi update using the finished build.

### Implementation

#### How we can get the event?

The information about successful builds is announced on fedora-messaging and we already listen for this because of the upstream Koji builds.

#### How to implement it?

- Make sure we listen to the relevant events.
- New handler can be created to implement the core functionality:
  - Check that this project wants to do the build. (New job type and new trigger type.)
  - Optionally, get the extra arguments from the packit config. (No-config scenario is currently not supported.)
  - Create the update using the already implemented method of the packit's Python API (in packit/packit project, not the web API).

#### How to communicate with the user?

Once the update is done, a user gets the info via usual Fedora messaging.

TODO: If we have some problem with the creation, we need to find a good method to communicate with the user.

## Generic implementation issues

### To split or not to split (the service)

There is an occurring question if the new functionality/job will be incorporated into the existing service, done as a separate deployment or done from scratch. Let's put down some benefits and problems.

1. New functionality added to the existing service

   - The new functionality is added as a new handler (=a separate class).
   - If we need to react to a new event, the parsing needs to be implemented.
   - The mapping between event and handler is done by decorating the handler and explicitly setting the event we react on.
   - The main benefits are the ease of implementation, reusing most of the work we already have and being able to quickly test the new functionality.
   - Adding new functionality can lead to a more tightly coupled design or can force us to make the current architecture more modular and generic (which requires extra work).
   - Since we have one database, we can show some overall status and combine information from upstream part and downstream part (including the propose-downstream job that is somewhere in the middle).

2. New functionality as another deployment

   - It's more a version of the previous one.
   - Benefits are independence, being able to have different identities and limits.
   - The main downside is a duplicated afford needed to maintain the service and to run the shared part (task scheduler, listeners, API service).
   - This approach has been chosen for our centos-stream service, how has it gone? (Jirka has mentioned something like: it was fine, no big issues)
   - If there will be a requirement to run the service inside Fedora infrastructure, this will be an option to reuse the current code and also satisfy that.

3. New instance
   - Nice opportunity for doing it right. (Or at least in a better way.)
   - There is a higher risk of issues before the service is ready.
   - The time for the implementation is higher.
   - Once done, we have two separate services and code-bases we need to maintain.

My personal opinion:

- We can't work on multiple different code-bases in parallel. => We need to implement it inside our current codebase. => We need to count with extra time to improve the current design when adding new features.
- The first version can be done in a few sprints, the third in months. (Some MVP is really easy to do in the first version.)
- I don't want to choose the current service just because of some personal feelings. For me, it's more about a chance to make the current service better (also from the architectural point of view).

## Plan

1. Start with the packit config as a way to enable the workflow. (Allows quicker implementation, but still an easy way how to test this.)
2. Implement the Koji builds for new dist-git commits.
3. Implement the Bodhi updates for new Koji builds.
4. Allow users to test our workflow.
5. Provide a better way how to enable this without packit config in dist-git.
