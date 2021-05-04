# Ideas about splitting the source-git work and upstream work

Some ideas, possibilities, pros and cons of moving out the source-git related work.

## What does the source-git workflow mean?

Must have:

- If user creates a merge-request on the source-git repository:
  - Create a matching merge-request to the dist-git repository.
  - Sync the CI results from the dist-git merge-request to the source-git merge-request.
- If the dist-git is updated, update the source-git repository by opening a PR.
- User is able to convert source-git change to the dist-git change locally via CLI.

Should have:

- If the source-git merge-request is updated, update the dist-git merge-request.
- If the source-git merge-request is closed, close the dist-git merge-request.

Could have:

- User is able to re-trigger the dist-git CI from the source-git merge-request.
- User is able to re-create the dist-git MR from the source-git merge-request.

## Key questions:

1. Should we start developing a new service or modify the existing packit-service to be able to deploy only with a gitlab-endpoint?
2. How to link merge requests in the src namespace to the ones in the rpms namespace using the GitLab API? This should be bidirectional.
3. Check the GitLab API to learn more about working with merge-trains and pipelines, in order to support the UX for merging source-git MRs (see the doc linked bellow).
4. How are CI results going to be displayed in dist-git MRs? We wan't to know this so that we can think about ways to take those results and display them for contributors on the source-git MRs.

## Split

We have multiple options:

### 0. no split

- No extra cost of two deployments and two codebases.
- New jobs will be implemented as new handlers.
- We don't have support for multiple identities for one forge.
  - Not hard to do but requires some work.
- Fedora-source-git friendly: easy combination of events (different for Fedora and Stream)
  and handlers (=implementation, can be shared).

### 1. same codebase, new deployment

- No extra cost of maintenance of two codebases.
- New jobs are implemented as new handlers.
- Different identities can be used in one git forge (=gitlab.com).
- Resources can be tweaked separately.
- Fedora-source-git friendly: easy combination of events (different for Fedora and Stream)
  and handlers (=implementation, can be shared).

### 2. separate workers

- New jobs are implemented as new handlers in a separate repository.
- The centos-stream related code is in one place, based-on the packit-service code.
- We can use same or a separate deployment.
  (Fedora-source-git can be separated or with Stream.)

### 3. split the packit-service repo and build upstream/centos-stream workers

- One repo with the scheduler.
  Two repositories with the worker(=handlers) definition: one for the upstream, one for the stream.
- Requires more work.
- Can lead to a cleaner architecture. Something we were discussing for some time.
  - The centos-stream related code is in one place,
    upstream code is in one place and
    the shared code is in one place.
- Another dependency in the chain.
  - It's sometimes hard to work on the functionality that goes across multiple git projects.
- We can use same or a separate deployment.
  (Fedora-source-git can be separated or with Stream.)

### 4. fork and improve

- The benefits of the current service code can be preserved.
- The non-relevant/bad code can be removed.
- More time needed for development.
- Improvements relevant for both are hard to sync.
- More time needed for maintenance.

### 5. separate project from scratch

- The new service can be more lightweight and efficient.
- We can iterate on the prototype more quickly.
- We can get rid of the old bad staff in the packit-service.
- We can go through the same pain we've already gone through.
- We need to maintain two separate projects. (We need more people or reduce the productivity.)
- We are not motivated to improve the current projects.
- To share the code between the upstream and source project, we need to create some shared libraries.
  - Can lead to 3. and/or having another project on our dependency chain.

## Linking of the merge-requests

We have two goals:

1. User can easily find the related merge request on the web UI. (In both ways.)
2. We can get the related merge request from the service.

- We can set the dependent merge-requests across multiple projects
  (e.g. https://gitlab.com/lachmanfrantisek/kernel-ark/-/merge_requests/1)
  - The API is not implemented: https://gitlab.com/gitlab-org/gitlab/-/issues/12551
- Mentioning the other merge-request is always a possibility.
  (Mapping would be problematic.)
- For the purpose of the service, we can save the pairs to the database.

Some related GitLab issues:

- [Rearchitect MR widget mergeability logic](https://gitlab.com/gitlab-org/gitlab/-/issues/300042)
- [Rearchitect / Refactor MR Widget [Discovery]](https://gitlab.com/gitlab-org/gitlab/-/issues/324381)

## Merge trains

Allow merging multiple MRs in one target branch safely:

- We put MRs to the queue.
- For each MR, we run pipeline on the code containing this MR and all before.
- Pipelines are run in parallel to safe time.

Conclusion:

- This feature is something like zuul's gating pipeline with auto-rebase done in parallel.
- It's not meant for cross-project MRs => not useful for us.

Sources:

- https://docs.gitlab.com/ee/ci/merge_request_pipelines/pipelines_for_merged_results/merge_trains/
- https://about.gitlab.com/blog/2020/12/14/merge-trains-explained/
- https://about.gitlab.com/blog/2020/01/30/all-aboard-merge-trains/

## Multi-project pipelines

- https://docs.gitlab.com/ee/ci/multi_project_pipelines.html
- Pipeline to trigger a pipeline in a different project
  (e.g. generate documentation in a different repo once code change is merged).

Conclusion:

- Don't give us much benefits. (We need to work with dynamic reference on the second repository.)

## Parent-child pipelines

- https://docs.gitlab.com/ee/ci/parent_child_pipelines.html
- Pipeline can trigger a set of concurrently running child pipelines within the same project.
  - Child jobs are not dependant on the state of non-related jobs on parent pipeline.
  - Configuration can be split into multiple smaller easy-to-understand parts.
  - Avoids name collisions. (Comparing to pure `import`.)

## Pipelines API

Looks like pipelines need to be defined beforehand. We can manipulate only defined ones.

- REST API: https://docs.gitlab.com/ee/api/pipelines.html
- Python API: https://python-gitlab.readthedocs.io/en/stable/gl_objects/pipelines_and_jobs.html

> Pipelines for merge requests are configured.
> A detached pipeline runs in the context of the merge request, and not against the merged result.
> Learn more in the documentation for Pipelines for Merged Results.

To support this we can define the pipelines, wait for and get the result from Packit API.
(Goes against the current Packit workflow.)

We can also have a custom gitlab runner running our implementation in our infrastructure.

- Results are shown as pipelines.
- Completely independent to our celery-base workflow.
- A funny example: https://about.gitlab.com/blog/2018/06/29/introducing-auto-breakfast-from-gitlab/

Potentially, we can use `only: - external` when defining the pipeline and combine it with the commit statuse:

- https://gitlab.com/gitlab-org/gitlab/-/issues/20907#note_300399873
- But I can't make this approach work.

Some related GitLab issues:

- [EPIC: Customer custom MR widgets/Checks](https://gitlab.com/groups/gitlab-org/-/epics/5701)
  - [Introduce Checks API](https://gitlab.com/gitlab-org/gitlab/-/issues/22187)
  - [Provide an API for generic section in the Merge Request widget](https://gitlab.com/gitlab-org/gitlab/-/issues/7669)
  - [Redesign external commit status](https://gitlab.com/gitlab-org/gitlab/-/issues/23759)
  - [Markdown CI View / MR Widget](https://gitlab.com/gitlab-org/gitlab/-/issues/23282)
- [Show arbitrary build results (closed)](https://gitlab.com/gitlab-org/gitlab/-/issues/15018)
- [Custom merge widget blocks](https://gitlab.com/gitlab-org/gitlab/-/issues/22985)

## Commit status

- Converted to `external` jobs of `detached` pipeline.
- Only one stage (=column) is possible in the pipeline chart: https://gitlab.com/gitlab-org/gitlab/-/issues/19177
- https://docs.gitlab.com/ee/api/commits.html#commit-status
- Python API: https://python-gitlab.readthedocs.io/en/stable/gl_objects/commits.html#commit-status
- OGR: https://packit.github.io/ogr/services/gitlab/flag.html

## CI results

- Currently, the CI results are shown as pipelines.
- Example: https://gitlab.com/redhat/centos-stream/rpms/hdparm/-/merge_requests/1/pipelines
- There is a Python API for pipelines: https://python-gitlab.readthedocs.io/en/stable/gl_objects/pipelines_and_jobs.html
  - (No OGR support yet: https://github.com/packit/ogr/issues/420)

## Answers to Key questions

1. Should we start developing a new service or modify the existing packit-service to be able to deploy only with a gitlab-endpoint?
   - If we want to have a clean architecture, we can use version 3 with separate deployments. Version 2 can be done as a middle step.
2. How to link merge requests in the src namespace to the ones in the rpms namespace using the GitLab API? This should be bidirectional.
   - There is only a GUI to do that. We can use comments via API.
3. Check the GitLab API to learn more about working with merge-trains and pipelines, in order to support the UX for merging source-git MRs (see the doc linked bellow).
   - Looks like we can't use any GitLab structure to make this automatic, but can provide the UX independently.
   - We can define pipelines or use commit statuses (=detached pipelines).
4. How are CI results going to be displayed in dist-git MRs? We wan't to know this so that we can think about ways to take those results and display them for contributors on the source-git MRs.
   - Displayed as pipelines.
