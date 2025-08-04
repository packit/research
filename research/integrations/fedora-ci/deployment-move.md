---
title: Decoupling Fedora CI deployment from Packit Service
authors: lbarcziova
---

Related links:

- [issue](https://github.com/packit/packit-service/issues/2737)

This research describes requirements and plan to decouple Fedora CI-specific worker functionality from
the [Packit Service repository](https://github.com/packit/packit-service) and deploy it as a separate, independent service.
This will improve maintainability, scalability, and make the deployment within Fedora infrastructure easier.

## Code

- create the new repo (`https://github.com/packit/fedora-ci`?) structure, something like this:

```
fedora-ci/
├── fedora_ci/
│   ├── handlers/      # Fedora CI handlers
│   ├── helpers/       # Helper classes like FedoraCIHelper
│   ├── checker/       # Checker classes
│   ├── jobs.py        # Job processing logic
│   └── tasks.py       # Celery tasks
├── tests/

```

- code migration:
  - identify and move all Fedora CI-related worker functionality from packit-service to the new repository; this concerns jobs that do not depend on a repo having Packit configuration in the repository
  - set up tests and CI
  - create files needed for deployment: `run_worker.sh`, Containerfile, docker-compose file, etc.
- remove the moved code from the `packit-service` repo
  (this should be done after the code from new repo is deployed)
- needed changes:
  - once there is separate dashboard page, change the URL paths in the code

### Implementation changes during the transition period

- changes only to the new repo, without deploying
  - this would mean for few weeks the changes wouldn't take effect in the old deployment,
    and might cause some bugs landing when the new deployment happens which might be harder to investigate (if there are a lot of new changes)
  - old deployment might continue to run with known bugs
- changes to both repos
  - this involves duplicated work, and might be prone to errors (e.g. forgetting to apply a change to one repo)
  - first changing the code in old repo, and then applying the same to the new one
- importing the code from new repo

  - cleaner transition
  - requires more initial effort and might be more complex to set up
  - how to implement:
    - git submodule - directly link the new repository as a subdirectory in the old one
    - open to other suggestions
  - this might be not possible to do easily, as it could cause circular imports, as fedora-ci code will need to import events from packit-service

- in any case, we could try to minimize the new features and focus only on bug fixing during this time

## DB and API

- schema same, empty tables
- do we want to migrate the data from the current deployment?
- API at e.g. `prod.fedora-ci.packit.dev/api`

## Dashboard

- keeping one instance or having 2
  - 1 instance: we can use [`Context selector`](https://www.patternfly.org/components/menus/context-selector/design-guidelines) like OpenShift does
    - using different backends
    - we agreed we prefer this solution
  - 2 instances:
    - implementation wise this would require more changes
- to consider: this might be also required to be deployed in Fedora infra
  - dashboard deployment is quite straightforward, shouldn't be an issue

## Identity

- we probably want a new identity (or 2, both for stg and prod) on `src.fedoraproject.org` to be set up
- current Fedora CI user (`releng-bot`) is in these groups:
  - cvsadmin
  - fedora-contributor
  - fedorabugs
  - packager
  - relenggroup

## Openshift

### Ansible playbook, roles, Openshift object definitions

- [Fedora infra ansible repo](https://pagure.io/fedora-infra/ansible)
- copy and adjust the existing [deployment playbook](https://github.com/packit/deployment/blob/main/playbooks/deploy.yml) and related files
- mimic existing Fedora infrastructure playbooks, such as https://pagure.io/fedora-infra/ansible/blob/main/f/playbooks/openshift-apps/openscanhub.yml, and remove any unneeded tasks specific to Packit Service
- copy and adjust the Openshift object definitions, also remove Packit Service specific values (e.g. MPP specific)
- logs collection in Fedora infra?

### Configuration

- create Packit service config (specific server name etc.), variable file templates

### Secrets

- all the secrets should be new (different from Packit Service)
  - certificates
  - identity related files: token, SSH keys, keytab
  - Fedora messaging
  - Testing Farm
  - Flower
  - postgres
  - Sentry
  - ?

# To discuss

- repo naming
  - fedora-ci-worker
- identity
  - new one
- do we want both stg and prod? new code deployment strategy? weekly prod updates?
  - yes, for the beginning stick with weekly updates, this might need to be adjusted later on
- existing data migration
  - let's not do this and rather spend time on other tasks
- how to handle code changes while being in the process of the decoupling
  - try to minimize changes, urgent fixes contribute to both repos

# Follow-up work (to be adjusted based on discussion)

- code migration as described above:
  - functionality and tests
  - CI setup
  - deployment related files
- configuration and secrets generation
- integrate our deployment into https://pagure.io/fedora-infra/ansible/blob/main/f/playbooks
- dashboard changes
- reverse dependency tests run in packit-service repo to make sure changes there do not break the Fedora CI
