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
