---
title: Improvements
authors: mfocko
---

# Dashboard Improvements

## Main points

- Informing users about results of SRPM, Copr and Koji builds or Testing Farm
- Replace service "Build Result" webpage with dashboard
  - Deprecation of webpage in service
- Database connection for dashboard
  - Consider sensitivity of information provided (even with read-only access)
  - Consider customizing API to the needs of dashboard
- Consider possible improvements related to either of the points

## Related issues

- [Have a separate page for Testing farm](https://github.com/packit/packit-service/issues/506)
  - Seems to be at least partially fixed: https://dashboard.stg.packit.dev/results/testing-farm/5603
  - I guess we need to interlink all related jobs (SRPM, Copr and TF)
- [IDs for Copr builds in API endpoint (bug)](https://github.com/packit/packit-service/issues/982)
  - Does not affect usage of Copr build result page so far (is not used), or is the
    reason for only one chroot result being displayed?

## Current state

- [Already existing TODO list](https://github.com/packit/dashboard/blob/main/TODO.md)
- We have empty homepage
  - I can see a potential in showing some statistics, could be helpful to us
    and also to users.
  - We could list recently finished jobs or queue.
- We have implemented result pages
  - Copr builds:bug mentioned above
  - Minimal info for testing farm
- For Copr builds we link directly Copr logs on the dashboard (recent Copr builds),
  we should probably address our own result page before the Copr one.
- Navigation:
  - From each of those we can get back to the branch or the PR
  - SRPM results -> {can see logs, download SRPM if available}
  - Copr results -> {SRPM results, Copr logs, compressed build logs from Copr}
  - TF results -> dead end

## Removal of the _build result_ webpage

0. Fix Copr build bug mentioned above, so that we can see all chroots.
1. Set dashboard link for all new commit statuses.
2. Set 2-week long (conveniently matching sprint) grace period for build result
   page in service.

   _Argument_: 2 weeks is enough for populating commit statuses with links to dashboard
   and in majority of cases, old links are mainly used for debugging purposes on
   our side.

3. Remove build result page from service.

   _Alternatively_: Also redirect all requests from service to dashboard in step 1
   and keep live for longer period of time.

## Providing more information for dashboard through API

### Allowing read-only access to database

- Suspects: `data` in Copr, Koji and Testing Farm
- Otherwise there does not appear to be anything sensitive present
- Potential downsides would be:
  - Providing information through dashboard that cannot be accessed from API
  - Additional logic for the dashboard (in case we want to provide information via
    API too)
  - Testing

## Authentication against git-forge

- Could be probably generalized to OAuth in regards to expanding to GitLab
- OAuth
  - From GitHub we get code (valid for 10 minutes) that can be used to get access
    token
  - GitLab appears to work in similar way, there are more options though
  - For our case we should be fine with one-time codes that would be used client-side

### Possible use-cases

- Retriggering

  We could allow retriggering and be sure that user triggering the build again is
  authorized to do so (spam/DoS protection)

  Cost on our side:
  Requires changes in service codebase and also we would need to make sure that
  retriggering cannot be used outside of the dashboard
  - Auth in API `dashboard <=> service`
  - we could probably restrict IP address of sender to cluster on service side?

- Personalization of homepage view, e.g. all projects I have _write access_ to or
  all my open PRs (regardless of write access)

## Additional improvements

- _Badge_ for README with direct link to project's overview page in dashboard ;)
- _Any other suggestions are welcome_
  (we could open an issue for this to collect feedback)

### Overviews

It would be nice to provide overviews:

- _Pipeline/Run_: Currently there is no way to track pipeline/run of Packit on a
  specific trigger (push, release, PR), it would be nice to have an overview page
  on which we could track the whole pipeline from SRPM through Copr to Testing Farm
  and seeing all results (just success/fail) at that one page (with linking to the
  pipeline overview from each of the result pages).
- _Project_: Open PRs with latest status (or release, branch push), recently
  closed PRs (allowing to switch to results page or the PR/release/branch itself)
- _Namespace_: Similar but with projects, e.g. by recently updated project, showing
  status for default branch for example

### Notifications

We could provide browser notifications for recently finished/failed builds:

- For currently open namespace/repository overview
- For user's open PRs and all projects with write access, when authenticated
- For currently open pipeline (SRPM -> Copr -> TF)

## Timeline for changes

1. **Switch to dashboard and deprecate build-results.**

   In the current state dashboard provides definitely more information compared
   to currently used build results page, so in my opinion there are no blockers
   for a switch.

   Regarding the Copr build bug mentioned above: It appears to not show statuses
   (success/failure) for each of the chroots, just the one. And it appears to be
   same for the service-side page.

   Regarding Testing Farm: Currently we link directly to TF page, there is result
   page currently present on dashboard, which might seem to be better option.

2. **Improve the UX for results on dashboard.**
   - Start with pipeline overview.

     With a goal of achieving easy navigability at dashboard after being redirected
     to specific result page from git-forge or even looking up the pipeline itself
     from the dashboard.

   - Homepage with statistics, current queue, recent runs.

     That would also make the service look more live at first sight.

3. **Overviews for project and namespaces.**
4. Authentication and implementing related features (retriggering, custom views).
5. Any additional improvements (from _Packit badge_ through notifications to anything else).
