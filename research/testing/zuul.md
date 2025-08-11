---
title: Zuul CI
authors:
  - ttomecek
  - jpopelka
---

:::caution

Outdated, see https://github.com/packit-service/packit-service-zuul

:::

[Zuul](https://zuul-ci.org/) is a CI system invented in OpenStack community.
[Softwarefactory](https://softwarefactory-project.io) (SF) is project which is hosting a bunch of services to ease
development of open source projects. Zuul is one of the services.

Zuul is a heavy Ansible user.

## On-boarding

In-order to get on-board SF, you need to do these things:

- Let Zuul know about your repo: https://softwarefactory-project.io/r/15927
  - [Docs](https://ansible.softwarefactory-project.io/docs/user/config_repo.html#config-repo)

- Install SF GitHub app: [softwarefactory-project-zuul](https://github.com/apps/softwarefactory-project-zuul)

- Create .zuul.yaml and define noop job inside to test the connection: https://github.com/packit-service/ogr/pull/120/commits/23046836e2774a1c5de6620d93d9a88b21a98751

- [Zuul SF Documentation](https://ansible.softwarefactory-project.io/docs/user/zuul_user.html)

## Assorted notes & Gotchas

- Zuul accepts a config file named .zuul.yaml: it can be in the root of your repo (or somewhere else, which is pretty confusing).

- Results: once the testing is done, there is a new comment posted in the PR with links to each job: https://github.com/packit-service/ogr/pull/120#issuecomment-511790688
  - ARA report contains GUI for the playbook run: https://softwarefactory-project.io/logs/20/120/2e2b6a2c173b8be04c33c94fd75fa2d1febbecba/check/tests/e9adb06/
  - There is also a zuul-info/ directory with Ansible vars and generated inventory file (which contains Zuul Ansible vars)

- Zuul is a fairly complex system and can feel intimidating for a beginner (I'm still scared). The core building block of Zuul is a job:
  - [Job documentation](https://zuul-ci.org/docs/zuul/user/config.html#job)
  - [Different job documentation](https://zuul-ci.org/docs/zuul/user/jobs.html#job-content)

- This is where your locally cloned repo is: `project_dir: "{{ ansible_user_dir }}/{{ zuul.project.src_dir }}"`
  - Executor: A piece of Zuul's infra where Ansible is being invoked
  - Node: a VM where our tests are running

- A list of available nodes which are available for testing: https://softwarefactory-project.io/zuul/t/local/labels

- A repo with existing jobs, playbooks and roles which OpenStack is using: https://github.com/openstack-infra/zuul-jobs/blob/master/zuul.yaml

- More useful links:
  - Existing SF jobs: https://softwarefactory-project.io/cgit/config/tree/zuul.d/_jobs-base.yaml#n58
  - Our Zuul tenant: https://softwarefactory-project.io/zuul/t/local/status
  - Zuul pipelines defined in SF: https://softwarefactory-project.io/cgit/config/tree/zuul.d/_pipelines.yaml

- You can join internal IRC channel #sf-ops for questions. [Fabien](https://github.com/morucci) is super-duper helpful.

- Good luck and have fun!
