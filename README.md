# Research notes

This repo is used to document research performed by the packit team.

## Topics covered

- [`git notes` as a storage of our data](./git_notes)
- [Tools/libraries similar or related to the Packit](./automation-tools)
- [Zuul CI](./zuul)
- [Deprecation policy](./deprecation)
- [User stories related to our work](./user-stories/)
- [Summit 2020 demo](summit-demo/)
- [External Testing](external-testing/)
- [Monitoring Packit Service](monitoring/)
- [Packit-service deployment research](ps_deployment)
- [Distributed workers](distributed-workers) and [AWS](AWS-SQS-RDS)
- [Deploy a testing instance for Packit-as-a-Service](./deploy-packit-pr/)
- [Improving https://packit.dev/](./website-improvements/)
- [Automation for moving the stable branches](./automation-for-stable-branches)
- [Error budgets](./error-budgets/)
- [Support monorepos in source-git](./source-git-monorepos/README.md)
- [Oauth integration](./oauth)
- [Making technical decisions in our projects](./making-decisions/)
- [`packit source-git update-source-git` research](./update-source-git/)
- [Fedora Spec Files analysis](./fedora-spec-files/)
- [Verifying the sync status of source-git and dist-git repos](source-git-sync-status/README.md)

## Organization of this repository

### How to add new findings?

1. Please create a new directory in this repository.
2. Create a README.md document in that directory.
3. Make sure your README.md contains a clear description of what the outcome is
   from your research topic: ideally propose what the next steps should be.
   It's completely fine to tell that the technology is not interesting to us
   and there are no further actions.
4. Add everything related to your topic in the directory.
5. Open a pull request.
