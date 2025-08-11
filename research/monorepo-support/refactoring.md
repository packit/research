---
title: Code refactoring
authors: mmassari
---

## CLI

With the monorepo support, multiple _dist-git repositories_ can be mapped to a single _upstream monorepo_.

Three different ways to modify our `CLI` existing code to support mapping _one upstream repo_ with _multiple dist-git repos_ have been researched.

1. **`get_packit_api` to return multiple `PackitAPI` objects**: https://github.com/packit/packit/pull/1838.
2. **deal with the _package configs_ outside of `get_packit_api`**: https://github.com/packit/packit/pull/1840.
3. **change `PackitAPI`**: _not done._

Solution 3 has not been followed since a lot of code changes would have been required: to accomplish a _koji build_ (as in the linked PR) we need to create new objects inside the `PackitAPI` which would bind togheter, as an examples, this attributes:

- https://github.com/packit/packit/blob/edfbde6e77552293e3c8888460b68f6726d5f115/packit/utils/changelog_helper.py#L52
- https://github.com/packit/packit/blob/edfbde6e77552293e3c8888460b68f6726d5f115/packit/cli/builds/koji_build.py#L92

and after having created this new objects inside `PackitAPI` we should change this existing lines of code and many others in the `CLI` commands.

We decided to follow one of solution 1 or 2 which have a much narrow code impact, try them out, and if they will not work we can discuss solution 3 later.

Solution 1 has two downsides:

- it binds together `PackitAPI` and `PackageConfig` management inside the method `get_packit_api`: with the monorepo support, the effort to manage the `PackageConfig` will increase a lot, for this reason probably it is better to move its management in a new class/method.
- it returns a collection where before there was just a single object, so it has a broader impact on our code with respect of solution 2

Solution 2) has just one downsides:

- it uses a decorator which is not always easy to debug/understand.

Probably the best solution is the second one.

### What is missing

`PackageConfig` management has to be improved. The `CommonPackageConfig` used by solution 1 and 2 is not complete. As an example it does not have the `jobs` details on it.

We should probably enrich the `MultiplePackages` object with new functionalities and probably create a new package config class. Something like a `PackageConfigView` that would mean, let me say, a _package config viewed through the eyes of a single package in it_.

## Packit Service

The handlers in `packit-service` are using the `JobConfig` class to access most of the job data and the `JobConfig` objects, passed to an handler, are taken from the `self.event.package_config.jobs` call [here](https://github.com/packit/packit-service/blob/451f24b9ff08803e852f6245e6b3806c2767b10e/packit_service/worker/jobs.py#L555) and are used [here](https://github.com/packit/packit-service/blob/451f24b9ff08803e852f6245e6b3806c2767b10e/packit_service/worker/jobs.py#L400).

I see two possible solutions to support monorepos.

1. For a `JobConfig` referencing multiple packages create as many `JobConfigView`, [here a draft example](https://github.com/majamassarini/packit/blob/multiple_distgit_external_package_config/packit/config/job_config.py#L108-L143), as the packages **but do not group them together**

   Substitute the `self.event.package_config.jobs` calls like in this [commit](https://github.com/majamassarini/packit-service/commit/10d012bfddef815ad03781c2e3907998e20d8c7f). Where the `package_config.get_job_views` method looks like [this](https://github.com/majamassarini/packit/blob/multiple_distgit_external_package_config/packit/config/package_config.py#L157-L172).

   The above solution resolves a test like [this](https://github.com/majamassarini/packit-service/blob/multiple_distgit_packit_api/tests/unit/test_jobs.py#L3134-L3234).
   - **PROS**: we don't need to touch much more code than this. Our handlers are designed to work with one `JobConfig` and they will keep doing that, working in the same way with a `JobConfigView` (or just pick another name for it) and a `JobConfig`.

   - **CONS**: if, for supporting monorepos, we need to deal with multiple packages in the same handler. Then we need to group together the `JobConfigView`s, like in the `package_config.get_grouped_job_views` method [here](https://github.com/majamassarini/packit/blob/multiple_distgit_external_package_config/packit/config/package_config.py#L174-L196). And we should **add a new way to match jobs and handlers** in `steve_job.process_jobs` method.
     Create new `steve_job.get_handlers_for_event` and `steve_job.get_config_for_handler_kls` methods that instead of calling the `steve_job.get_jobs_matching_event` will call a new method named something like `steve_job.get_grouped_jobs_matching_event`.
     And the `steve_job.process_jobs` at the end will create both the old handlers taking just one `JobConfig` or `JobConfigView` and also the **brand new handlers** taking a list of `JobConfigView`s.

2. For a `JobConfig` referencing multiple packages create as many `JobConfigView`, [here a draft example](https://github.com/majamassarini/packit/blob/multiple_distgit_external_package_config/packit/config/job_config.py#L108-L143), as the packages and **group them together**

   Substitute the `self.event.package_config.jobs` with a call like the `package_config.get_grouped_job_views` [here](https://github.com/majamassarini/packit/blob/multiple_distgit_external_package_config/packit/config/package_config.py#L174-L196).
   Modify `steve_job.process_jobs`, `steve_job.get_handlers_for_event`, `steve_job.get_config_for_handler_kls` methods to work with the new data structure returned by the `package_config.get_grouped_job_views`.

   At the end the `steve_job.process_jobs` will create only handlers taking a list of `JobConfig` or `JobConfigView` and for this reason we will modify all our handlers to loop over all the given configs.
   - **PROS**: one single way to _match jobs and handlers_

   - **CONS**: we are suggesting that all the handlers should be able to handle multiple configs, but this is probably not true.

Personally I prefer solution 1. I see it as more simple and explicit. We probably could/should re-think the job/handler matching code from the point of view of a monorepo. I feel like it is worth doing that when we have a clear understanding of what we need in a handler capable of supporting multiple packages.
