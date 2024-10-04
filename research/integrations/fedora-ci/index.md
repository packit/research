---
title: Packit as Fedora dist-git CI
authors: mfocko
---

Related links:

- [Epic](https://github.com/packit/packit-service/issues/2453)
- [Research issue](https://github.com/packit/packit-service/issues/2462)

## Current Fedora CI

1. Koji scratch build
1. Installability
1. tmt (if plans are present)

### Zuul as a parallel CI

1. Builts SRPM
1. Submits Koji scratch build
1. Runs RPM linter
1. Runs RPM inspect
1. Tests install
1. Runs tmt

## Possible implementation

### SRPM build

Ideally kept identical. Packit should not be involved in any way that can affect
the results of the SRPM build, i.e., just run `fedpkg srpm` and be done with it.

This can be done within the sandbox as we do for non-scratch builds. However it
might need some tweaking as Packit has specific worfklow.

:::note Questions from review

> This is a very interesting point -- do we want to be consistent as much as
> possible with Packit's upstream implementation or be close to the real Fedora
> builds.
>
> I agree the suggested approach `fedpkg srpm` makes more sense from the user
> perspective since this results in the production-like result.

With respect to downstream, I would be definitely voting for avoiding adjusting
the SRPM creation. Adjusting the SRPM creation in any way enables the chance of
inconsistencies, i.e., I have green CI, but once I merge it doesn't build. I
don't think many maintainers would like that :D

> How do we want to handle sources? (Do we want to continue with the current
> trend of requiring sources in the lookaside cache?)

I'm not really sure, but if we go deep into the possible improvements then it's
quite possible that most of this initiative will not be achievable :)

:::

### Koji scratch build

We are already submitting scratch builds for merged PRs, if configured. This
would just extend the functionality to the non-merged PRs (with need to provide
the SRPM).

:::note Review

And we have scratch build functionality for upstream PRs available as well if
this is anyhow relevant.

:::

### RPM linting, inspect and installability test

There are premade tmt plans that we can run.

:::note Question

Should these be run in parallel or sequentially and fail on first?

Follow-up question from review:

> Are some of these somehow dependent?

From the excerpt here (linting, installability, tests), it feels like linting
should not be a hard blocker. I've seen the installability tests fail (even if
tests passed) just because of the network flakes and such, so…

In the sense of saving the resources, it definitely makes sense to make _full_
_test suite_ dependent on the _installability_, but if it's flakey, it's just
annoying.

:::

#### Installability test

Installability test run by Fedora CI triggers Testing Farm and uses the
following tmt plan: https://github.com/fedora-ci/installability-pipeline

Installability test run by Zuul CI is done in the Zuul itself.

### Testing Farm

Different form of request than for upstream jobs.

```json
{
  "id": "2fdee1a0-0746-45ad-ad0c-d3ec8833630b",
  "user_id": "c4af7afe-b95e-4cf1-b989-9c458f0eecf0",
  "token_id": "c4af7afe-b95e-4cf1-b989-9c458f0eecf0",
  "test": {
    "fmf": {
      "url": "https://src.fedoraproject.org/forks/packit-stg/rpms/packit",
      "ref": "0d4dfcfcc2a708f06c65b80404cc022e7bf6bead",
      "merge_sha": null,
      "path": ".",
      "name": null,
      "settings": null,
      "plan_filter": null,
      "test_name": null,
      "test_filter": null
    },
    "script": null,
    "sti": null
  },
  "state": "complete",
  "environments_requested": [
    {
      "arch": "x86_64",
      "os": {
        "compose": "CentOS-Stream-9"
      },
      "pool": null,
      "variables": {
        "KOJI_TASK_ID": "123014869"
      },
      "secrets": null,
      "artifacts": [
        {
          "id": "123014869",
          "type": "fedora-koji-build",
          "packages": null,
          "install": true,
          "order": 50
        }
      ],
      "settings": null,
      "tmt": {
        "context": {
          "arch": "x86_64",
          "distro": "centos-stream-9",
          "initiator": "fedora-ci",
          "trigger": "commit"
        },
        "environment": null
      },
      "hardware": null,
      "kickstart": null
    }
  ],
  "notes": [
    {
      "level": "info",
      "message": "tf-tmt/dispatch-1725615078-80d05f05"
    }
  ],
  "result": {
    "summary": null,
    "overall": "passed",
    "xunit": "…",
    "xunit_url": "https://artifacts.dev.testing-farm.io/2fdee1a0-0746-45ad-ad0c-d3ec8833630b/results.xml"
  },
  "run": {
    "console": null,
    "stages": null,
    "artifacts": "https://artifacts.dev.testing-farm.io/2fdee1a0-0746-45ad-ad0c-d3ec8833630b"
  },
  "settings": null,
  "user": {
    "webpage": null
  },
  "queued_time": 6.892783,
  "run_time": 1207.608357,
  "created": "2024-09-06T09:31:17.471815",
  "updated": "2024-09-06T09:31:17.471844"
}
```

Most notable differences:

- RPMs are provided from Koji scratch build (following Fedora CI, which is
  easier than self-hosting)
- chroot is defined by the branch rather than config

## Technical issues / questions

### Load balancing

Preferably it would be ideal to have separate deployment for the “dist-git only”
service as handling all Fedora packages would definitely increase traffic and
could cause issues with running as both Fedora CI and original Packit Service.

:::note Question from review

> Would this mean `dist-git CI` and the current Packit? Or, Packit upstream and
> Packit Fedora automation (including Koji, Bodhi and maybe also propose/pull)?

I've been thinking about a way to split this in some reasonable matter :D Based
on the way Packit operates, the most reasonable would be splitting the
upstream/downstream parts, i.e.,

- Packit Service (handles upstream **and** `propose-downstream` (as it is
  triggered by upstream))
- “Packit as Fedora CI” (handles downstream **and** `pull-from-upstream`)

**However** I rant somewhere about the config in the dist-git and default config
:D and this complicates things a lot :/ Maybe we could treat PRs in a special
way for the _downstream PRs_ (Koji + TF).

---

feels like whack-a-mole…

:::

#### Default config

Having a separate instance would also open up a door to a potential “default
config” which could be different to our current one (SRPM, Copr build, TF) and
more tailored to the needs of the Fedora CI.

**TODO**:

- [ ] Maybe have a default config configurable?
      For context, we have [default jobs](https://packit.dev/docs/guide#jobs) on
      the upstream in case there are no jobs specified. This could be leveraged
      to provide some **reasonable** defaults for Koji builds and Testing Farm
      runs on the downstream part.

### SRPM build

For Zuul is run via `fedpkg srpm`. Then it's provided for the Koji build.

Packit should not interefere with the way the SRPM gets built.

### Propagating Koji build

As of now, the sources need to be already uploaded in the lookaside cache to run
the RPM build in general (either Fedora CI or Zuul CI). Given that merges in
dist-git are handled as fast-forward, it should be possible to just tag the
build from the PR instead of rebuilding again (with the same sources and
specfile).

:::note

This is definitely a _nice-to-have_, a follow-up.

:::

**TODO**:

- [ ] Does it make sense to open a follow-up already, even if there's no PoC
      yet?

### RPM for Testing Farm

Zuul provides its own (self-hosted) repository. Fedora CI just refers to the
scratch build.

Self-hosting the repository is not preferred, following the Fedora CI approach
might be the best.

### STI tests

Older format of tests that can be run via Zuul. Based on the TF API, Testing
Farm supports it too. Requesting STI tests from the Testing Farm should be
possible, detection of their presence lies on Packit.

**TODO**:

- [ ] Should we support the STI tests?

### Side tags

Support for side tags has been requested in the original thread with the
proposal. This may be required for “packaging workflows” that are more complex,
e.g., Rust packaging (dependencies that are built as separate packages).

> As a maintainer, I should be able to specify the dependencies of my package
> that need to be verified with any proposed update.

### Upstream vs Downstream

By default, we sync the Packit config to the downstream. This can cause a
conflict when Packit runs as a Fedora CI, since the config would override any
defaults that we would've set.

Additionally, there needs to be a way to distinguish between upstream/downstream
jobs anyways, cause Testing Farm runs on the downstream install RPMs from the
Koji rather than Copr.

:::warning

It would probably be easier to run stateless as the current CI, utilizing only
defaults and ignoring any Packit config that is present.

It might be possible to “abuse” the `packit_instances` key in the config to
differentiate the normal deployments (`prod`, `stg`, `dev`) from a potential
Fedora CI deployment. OTOH together with syncing the upstream configs to
downstream, it may cause an incomprehensible mess.

:::

## User perspective

### Fedora

> As a maintainer I'd like to open a PR and have automated RPM build to verify
> that, whatever I'm submitting, can be
>
> - built,
> - installed, and
> - passes the test suite.
>
> Adding and configuring the tests in the dist-git should be my responsibility.
> I don't want the CI to be blocking, just annoying…

**TODO**:

- [ ] Packit should be able to run without any repo-specific configuration, but
      there should be a way to override, if needed.

### Fedora SIGs

AFAIK the repositories are hosted on the Fedora dist-git, therefore they should
be handled by the Fedora CI already, the experience should be similar (if not
the same) to the regular Fedora packages.

### CentOS SIGs

As there is no streamlined CI for the CentOS SIGs, adoption would allow
relatively simple integration with the Testing Farm.

## Difficulties depending on the forge

### Pagure

Mainly reliability, it would require retries. Together with normal Packit CI
workflows, considerable overhead.

### GitLab

ogr has a support for GitLab already, reporting sucks, but it's not a blocking
issue (due to the lack of upstream users, the priority of improving the UX has
been lowered).

:::warning GitLab UX

There are limitations on how Packit can improve the user experience on GitLab.

GitLab is focused on providing the best user experience when using their own
GitLab CI, external services must either just report commit statuses (unlike on
GitHub that allows Check Suites and Check Runs), or integrate into the GitLab
codebase itself.

This hinders the user experience significantly.

> Switching from Pagure to GitLab sounds effectively like getting rid of the
> stability issues while maintaining the poor UX.

:::

#### Upstream vs downstream

Difference between upstream and downstream events can be told easily by source
of the webhooks (downstream come from Fedora Messaging, upstream directly from
GitLab instances).

### Forgejo

Forgejo is an open-source git forge that seems to be a viable alternative to
both Pagure and GitLab. There is no support for the forgejo in ogr as of now,
additionally to ogr support we would need to adjust parsing of the webhooks, but
it can completely replace the Pagure (as Fedora dist-git is the only Pagure
instance used by Packit).

## Notes from the arch discussion

### Configuration

For the beginning we should just handle the packages that are configured.

:::warning

This means that we don't want to handle _all_ Fedora packages for the _PoC/MVP_.

:::

### Auto-merging / gating

During the implementation, we should keep in mind the possibility of polishing
the process to eventually allow for auto-merging with improved gating (TF is
helpful in this case a lot).

**TODO**:

- [ ] Consider this in the design.
- [ ] Should not cause any annoyance for _proven packagers_

:::note Review

There's an [RFE](https://github.com/packit/packit-service/issues/1723) for
a workflow that involves auto-landing PRs in the Fedora dist-git.

:::

## Follow-up cards

- [ ] Allow triggering of the Testing Farm with Koji build (instead of the Copr
      build)
- [ ] Try to unify _installability pipeline_ with the tmt plan for install test
      that we already have
- [ ] Packit needs to be able to deduce the build target based on the branch
      rather than config (i.e., Packit triggered by push to `f40` branch in the
      dist-git should run Testing Farm for the F40; this **can't** be deduced
      from the config)
- [ ] Allow Packit to have customizable default config (more details above)
- [ ] Allow Packit to run without any config (utilizing the previous point)
- [ ] After PoC and final decision, deploy a separate instance to handle only
      Fedora CI queue
- [ ] Allow triggering of the Testing Farm **STI** tests with Koji build (or in
      general)
