---
title: Improve Packit Service event processing
authors: lbarczio
---

## Problematic parts of the process

- setting GH statuses is the slowest part of the short running tasks

  - this shows mainly in projects with a lot of targets configured):

  ```
  [2022-04-12 21:44:01,874: DEBUG/ForkPoolWorker-1] Status reporter will report for GithubProject(namespace="osbuild", repo="osbuild"), commit=937afa51b19f5c78b552e77694d80845e69f2a84, pr=1003
  [2022-04-12 21:44:01,874: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:centos-stream-9-x86_64': SRPM build is in progress...
  [2022-04-12 21:44:02,553: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-36-ppc64le': SRPM build is in progress...
  [2022-04-12 21:44:02,900: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-34-ppc64le': SRPM build is in progress...
  [2022-04-12 21:44:03,255: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:centos-stream-8-x86_64': SRPM build is in progress...
  [2022-04-12 21:44:03,631: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-35-ppc64le': SRPM build is in progress...
  [2022-04-12 21:44:03,977: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:epel-8-aarch64': SRPM build is in progress...
  [2022-04-12 21:44:04,371: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-36-aarch64': SRPM build is in progress...
  [2022-04-12 21:44:04,698: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-36-s390x': SRPM build is in progress...
  [2022-04-12 21:44:05,064: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-34-aarch64': SRPM build is in progress...
  [2022-04-12 21:44:05,431: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-35-x86_64': SRPM build is in progress...
  [2022-04-12 21:44:06,107: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:centos-stream-8-aarch64': SRPM build is in progress...
  [2022-04-12 21:44:06,445: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-34-x86_64': SRPM build is in progress...
  [2022-04-12 21:44:06,794: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-rawhide-ppc64le': SRPM build is in progress...
  [2022-04-12 21:44:07,169: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-35-s390x': SRPM build is in progress...
  [2022-04-12 21:44:07,538: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-rawhide-x86_64': SRPM build is in progress...
  [2022-04-12 21:44:07,870: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-35-aarch64': SRPM build is in progress...
  [2022-04-12 21:44:08,215: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-36-x86_64': SRPM build is in progress...
  [2022-04-12 21:44:08,541: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:centos-stream-9-aarch64': SRPM build is in progress...
  [2022-04-12 21:44:08,893: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-34-s390x': SRPM build is in progress...
  [2022-04-12 21:44:09,227: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:epel-8-x86_64': SRPM build is in progress...
  [2022-04-12 21:44:09,576: DEBUG/ForkPoolWorker-1] Setting Github status check 'in_progress' for check 'rpm-build:fedora-rawhide-aarch64': SRPM build is in progress...
  ```

  - we probably can't fasten the process of creating check runs
  - overall, the scaling of short-running worker should help with this

- processing event when there is no config file
  - finding out there is no config file takes few seconds (on average around 2, but this depends probably on the repo size,
    I have seen also a log with 4 seconds duration)
  - we support more file formats/names (packit.yaml, packit.json, .packit.yaml, ...)
    - [.]packit.json should be removed if noone uses it
- the target expansion is also done more times during one processing, we could improve it (using properties and setting build/test targets only once),
  but the process takes milliseconds, so this is not problematic from a time perspective

## Suggestions for improvements

#### Can we uninstall a repo? - Not receive events, after some period of time when we didn’t produce any meaningful work.

- the documentation provides info on how to list installations, get a specific installation, delete, suspend it
  (when a GitHub App is suspended, the app's access to the GitHub API or webhook events is blocked for that account)
  https://docs.github.com/en/rest/reference/apps
- we could have a periodic job which would check the installations and if an installed repo does not contain a config file
  after some time limit (e.g. a month after installation), uninstall it
  - if the app is installed on a namespace - at least one repo with a config file?

#### Add higher prio to tasks from repos who are active users

- in service we could get the repo name and check it in DB and accordingly route the tasks to different queues
  (as we do currently for long and short running tasks)
- the info about "active" users would be updated in the worker tasks
  - do we want to have it only binary? for this we could proceed similarly as with short/long running queues
    1. run at least one job for the repo
    2. no jobs run
  - or something more granular - this would require utilization of Celery `priority`:
    - suggestions:
      1. avoid overloading service by one project. (Decrease priority if we have at least X jobs already running for this namespace/project/PR.)
      2. historically active users. (Increase priority if a project has at least X jobs during the last week/month/...)
      3. decrease priority for some triggers -- e.g. Decrease priority if the trigger is push/release.
      4. increase/decrease priority for some projects -- e.g. set it in the service-config. (Test projects can have lower priority, some privileged projects higher.)
- what [Celery docs](https://docs.celeryq.dev/en/master/faq.html#does-celery-support-task-priorities) tells about priorities:

  ```
  Does Celery support task priorities?

  Answer: Yes, RabbitMQ supports priorities since version 3.5.0, and the Redis transport emulates priority support.

  You can also prioritize work by routing high priority tasks to different workers.
  In the real world this usually works better than per message priorities. You can use this in combination with rate limiting,
  and per message priorities to achieve a responsive system.
  ```

- the priority can be set when calling `task.apply_async()`

#### Prefiltering in fedmsg

- we already do prefiltering - e.g.checking Packit user for Copr builds
- can we do something more here?

#### Recording metrics about tasks

- we should first start recording more tasks-related metrics to get more insights
  - task duration
  - the rate of tasks processing repos without a config file
  - ?

## TODOs:

1. more metrics
2. drop `[.]packit.json` from config file names we support

then depending on the metrics some optional: 3. periodical uninstalling of unactive repos 4. higher priority for tasks handling active projects
