# How to decide whether to rebase or backport

## Rules

There are no hard rules, but the general consensus is that a rebase means a higher chance of ABI breakage,
and the majority of packages in RHEL have ACG level 2, meaning they have to maintain ABI compatibility
for the entire lifecycle of a major RHEL release, thus rebasing is discouraged.

## What can be automated

Final decision is always on the maintainer, the automation could:

- check past issues to see if the package is usually rebased, if the fixes are usually backported,
  or a combination of both, and suggest a way to proceed based on that
- read ACG level of a package for a given RHEL release from https://gitlab.cee.redhat.com/rcm/lifecycle-defs
  - ACG level 4 or unset means high probability that a rebase would be allowed (even if there are ABI changes)
- perform the rebase anyway, do a scratch build and provide results of abidiff check
  and output of reverse dependency tests

The automation could also cite or link the RHEL Development Guide:
https://one.redhat.com/rhel-development-guide/#_rebase_considerations

## A way to indicate how to proceed

There is a `Rebase` keyword in Jira that should be used for rebases, though I have found issues
that were resolved with a rebase but without said keyword. Either way, it could be used as a clear indication
that the maintainer has decided to proceed with a rebase.

## Alternative approach

The automation could do both rebasing and backporting as separate tasks and provide feedback for the maintainer to decide.

## Maintainer feedback

Rebasing is rare, because there is a high level of uncerntainty and a risk of changed behavior
not covered with tests and hard to spot by a human but relied on by customers. Typically rebasing is only done in Fedora
to cover the next major version of RHEL and during RHEL lifetime fixes are only backported.

It is unusual for a component to have a good (if any) upstream test suite. Often there are only regression tests
that have been written for RHEL over the time. This is again a factor that speaks against rebasing.

Usually only teams/maintainers that are upstream for their components do rebases.

### Human requirements

#### Can AI decide the type of resolution?

Yes, but we would need to define criteria for a risk-free rebase. This would involve e.g.:

- there are no ABI changes
- the amount of changed code is under risk threshold (needs to be defined)
- there is a changelog that guarantees there are only bugfixes and no new features
  (as they would have to become supported)
- new release is trusted/verifiable (to prevent supply chain attacks)

#### Is a feedback from human vital/required?

Not required if the rebase is deemed risk-free.

#### What is the type of information we want from the real human?

Version to rebase to, but that's usually specified or inferable from e.g. CVE description
(`xterm before version 370 is vulnerable to buffer overflow`).

#### Would it be welcomed to collect data for human to decide?

Yes.
