---
title: Packit Service deployment improvements
authors: sakalosj
---

## Motivation

- docker image related dependencies -
  packit image which is providing dependencies for packit-service image, adding unwanted complexity and delays in deployment

- dependencies on fedora rpm release -
  - for packit-service - deployment depends on rpm deployment, which can be quite long (to fix typo you have to go through whole rpm deployment process)
  - for 3rd party packages - we are facing issues when package was not released as rpm for all required OS versions

Areas to be covered:

- how we handle dependencies in code(rpm vs github)
- how we handle container image dependencies (s2i vs base_image-final_image)
- how we will handle overall flow

## Current Flow

1. new commit in master/stable branch
2. image build is automatically triggered in dockerhub. There is some delay, but it can be triggered manually
3. new image is pulled to OpenShift via OpenShift cron job and pods are rebuild:
   - prod every Sunday at 2:00
   - stg every hour

## Research

### Installation source

- github

  - pros:
    - current changes in other projects are always in place - useful especially for stg branch
  - cons:
    - Handling of dependencies is harder (we need to mix `rpm` and `PyPI` versions).

- rpm:
  - pros:
    - All dependencies are installed similarly and automatically via `rpm`.
  - cons:
    - very long deployment process

### Image build approach

- s2i: Source-to-Image (S2I) is a tool for building reproducible, Docker-formatted container images. It produces ready-to-run images by injecting application source into a container image and assembling a new image. The new image incorporates the base image (the builder) and built source and is ready to use with the docker run command. S2I supports incremental builds, which re-use previously downloaded dependencies, previously built artifacts, etc.

  - pros:
    - separating code and image development - probably advantage in bigger projects where development and devops is separated
  - cons:
    - not copying .git to image, using default paths (/opt/app/src), maybe others which can probably require our scripts rework

- normal image build (eg. `docker build ...`):
  - pros:
    - already in use in our environment
    - no need to implement additional tool
    - clean approach

| image name                         | build time  | size         |
| ---------------------------------- | ----------- | ------------ |
| ps_normal_github_base              | 4m42.531s   | 797MB        |
| ps_normal_github_final             | 0m12.925s   | 797MB        |
| ---------------------------------- | ----------- | ------------ |
| ps_normal_rpm_base                 | 5m8.026s    | 804MB        |
| ps_normal_rpm_final                | 0m15.766s   | 804MB        |
| ---------------------------------- | ----------- | ------------ |
| ps_s2i_github_base                 | 4m38.620s   | 1.12GB       |
| ps_s2i_github_final                | 0m10.715s   | 1.12GB       |
| ---------------------------------- | ----------- | ------------ |

### High level build flow strategies

#### OpenShift vs. Public service

- OpenShift:
  - pros:
    - flexible
    - no waiting in queue
  - cons:
    - additional maintenance
    - additional resources = additional costs/failures because of resource limit
- Public service:
  - pros:
    - our current approach - no radical changes required
    - simple and straightforward
    - free
  - cons:
    - dependency on external service
    - long queue time in case of service issue/high load

#### OpenShift

- Source-to-Image - (`sourceStrategy` in OC configuration) is using s2i tool for image deployment

Links:

- [s2i details](https://docs.openshift.com/container-platform/3.11/architecture/core_concepts/builds_and_image_streams.html#source-build)
- [s2i strategy options](https://docs.openshift.com/container-platform/3.11/dev_guide/builds/build_strategies.html#source-to-image-strategy-options)
- [s2i tool blog](https://www.openshift.com/blog/create-s2i-builder-image)

- Image Stream - current configuration
- Custom Build - need more details

## Conclusion

- Source-to-image (S2I) - no performance improvements, bigger image
- RPM vs github:
  - from performance perspective basically same results
  - github repos should not have issues with OS version - will make deployment easier
- splitting image to base + final, will improve build times

## Discussion output

- GitHub will be used for installing internal projects
  - Dependencies have to be installed via RPM's for security reasons
  - There are 2 sources of dependencies - spec file and setup.cfg - both have to be taken into account
- Deployment will use the same branch (master/stable) for all internal projects
