---
title: Build reverse dependencies in Packit
authors: mmassari
---

Already existing solutions:

- [Koschei service](https://github.com/fedora-infra/koschei)
- [Mass Prebuild CLI](https://gitlab.com/fedora/packager-tools/mass-prebuild)
- [mini mass rebuild](https://github.com/hroncok/mini-mass-rebuild)
- [copr-autorebuilder](https://pagure.io/copr-autorebuilder/tree/master)
- [copr-rebuild-tools](https://github.com/fedora-copr/copr-rebuild-tools/tree/main)

The first two in the above list are specifically designed for resolving reverse dependencies and this research will focus on them.

## Koschei

[Koschei](https://apps.fedoraproject.org/koschei) is a **continuous integration service** for RPM packages that tracks package dependency changes in Fedora Rawhide and rebuilds packages whose dependencies change too much.

**Koschei depends on Koji**. New Koji builds "trigger" Koschei and Koschei rebuilds reverse dependencies as Koji scratch builds.
**Koji scratch builds do not trigger Koshei** at the moment.
This means that Koschei can be used as a CI service only after a _downstream release synchronization_ but **our users would like to check changes before making a downstream release synchronization.**

If we want to use Koshei as an upstream CI service (or even downstream but without the need of a downstream release synchronization) we need to **make it react to scratch builds**.

The Koschei project is not much lively, at least upstream; different reported issues are not being answered or worked on. For this reason I fear integrating new features in the Koschei production service could take a long time.

If we want to use Koschei we could also think about **fork the project** and create our own instance inside the Packit cluster. This approach could give us two advantages:

- Shorter time to production and our changes can always be taken back by the original project at some point.
- We can re-enable COPR as a backend for Koschei builds. Accordingly to [this thread](https://pagure.io/fedora-ci/general/issue/45) Koschei has had a COPR backend for a while, but it has been removed (because COPR is a third party service not supported by the Fedora Infrastructure). Enabling COPR as a backend will allow the service to work even for those upstream projects which are not completely integrated in Fedora (if needed).

What are the **PROs** I see in re-using Koshei:

- We could benefit from an already well known somehow "standardized" user interface (the Koschei frontend).
- We shouldn't need to be able to calculate reverse dependencies in Packit and submit builds from Packit if we will reuse (the Koschei backend).

What are the **CONs** I see in re-using Koshei:

- As far as I can understand it, the guy who wrote Koshei does not work anymore in Red Hat. We can not ask him for any help dealing with the Koschei code.
- We could face unknown problems.

## Mass Prebuild

This is a CLI tool that resolves reverse dependencies and rebuild them all. It can work with both Koji and COPR.
Even if it is a CLI tool we can not easily integrate it in packit-service because of two main design choices:

- the tool interacts with a database
- the tool keeps a session and can interact with the user

The above design choices make the command line tool and also the code behind it not reusable as it is.

## Build our own solution

We will need:

1. a way to resolve reverse dependencies

   - we can follow the [Koschei way](https://github.com/fedora-infra/koschei/blob/master/koschei/backend/depsolve.py) which uses `hawkey` from `libdnf`
   - or we can follow the [Mass prebuild way](https://gitlab.com/fedora/packager-tools/mass-prebuild/-/blob/main/mass_prebuild/utils/whatrequires.py?ref_type=heads): given a package or a set of packages, namely "main packages", the mass pre-builder will calculate the list of its direct reverse dependencies: packages that explicitly mark one of the main packages in their "BuildRequires" field. As far as I can understand it, this is a **less deep** and thus **less complete** approach compared with the Koschei solution.
   - we can **avoid calculating dependencies** and let the user specify them in a static way.

2. a way to schedule builds in Koji or COPR (or both).

   We are quite good at submitting builds in both services but we are not good at dealing with dependencies.

   - **if we don't need to interact with the rebuild process** we can depend upon:

     - the [COPR build batches](https://docs.pagure.org/copr.copr/user_documentation.html#build-batches) feature that allows you to define the order of your builds in advance.

     ```
           $ copr build <project> --no-wait <first.src.rpm>
           Created builds: 101010
           $ copr build <project> --no-wait <second.src.rpm> --after-build-id 101010
           Created builds: 101020
           $ copr build <project> --no-wait <third.src.rpm> --with-build-id 101020
           Created builds: 101030
     ```

     - or/and the [Koji chained builds](https://docs.fedoraproject.org/en-US/package-maintainers/Using_the_Koji_Build_System/#chained_builds)

     ```
           fedpkg chain-build --target=side-tag-name libwidget libaselib : libgizmo :
     ```

   - but we should be aware that **the mass prebuild tool is designed in a way that lets you interact with every single step of the long rebuild process**. I don't know exactly why, but if I got it correctly, this process is error prone and the user may like to be able to continue it from a point of failure or may like to resubmit a failed build. I think it is worth discussing with the mass pre build developer why he has chosen to go this way.

     If we want the user to be able to interact with every step in this long process we should probably be capable of dealing with **job dependencies**.

3. Besides a quick check status in the PR we should need also a new (dashboard) view with the summary status of all the reverse dependencies builds (probably something like our actual pipeline view).

**PROs**:

- If we don't need to deal with **job dependencies** probably this is the solution with **less unknowns**. More easily planned.

**CONs**:

- Both designing a good dashboard view and dealing with job dependencies could be not that easy.
