# Packit Operator

I spent my learning day researching [kubernetes operators](https://www.redhat.com/en/topics/containers/what-is-a-kubernetes-operator). I was hoping to
finish the PoC but given the current world news, I wasn't able to focus.
Hence only this write-up.

## What are k8s operators?

[Also here is a nice overview](https://kopf.readthedocs.io/en/stable/concepts/).

Kubernetes operators are pods that run code in a response to kubernetes events.
They are a mechanism to react to (nut just) events coming from the cluster.
This makes it easy to script deployment steps, scaling, configuration content,
calling external APIs directly from the cluster where your app runs.

We can write python code which would operate **all** of Packit's deployments.

## What is the use case for us?

Since our current deployment is simple, we could knock it up a notch with a
custom operator.

We could alternatively use Tekton, ArgoCD, Ansible Tower.

### Benefits of operators

- Write code in an actual programming language (not yaml or bash) to automate
  and customize deployment steps.
- Cannot be closer to the cluster.
- Operators have custom service accounts and precise [RBAC](https://en.wikipedia.org/wiki/Role-based_access_control).
- [CRDs](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) are the way to store data.
- Mature at this point.
- Support for go, java, python, ansible...

### Negatives

- Complete vendor-lockin to k8s.
- Event processing: do we need a celery for that?
- GitHub events: polling or getting GH webhooks?
- Validation: how to test an operator?

## PoC

Since our present deployment automation is implemented by two simple [CronJobs](https://github.com/packit/deployment/tree/main/cron-jobs/import-images), we can turn it into an operator.

But before doing so, we could start a PoC operator which would comment on PRs:

1. once they are deployed to stg
2. and when they make it to prod

This way we wouldn't need to check when a change makes it to stg and our users
would know when a certain PR makes it to prod. It's also an isolated use case
to our deployment (read-only, trigger some code when workers are updated) so
there is minimal risk it would disrupt our service.

## Implementation

If we are brave enough, we can try the official [Operator SDK
framework](https://sdk.operatorframework.io/) and write in go. Although I'm
worried that introducing a new programming language into our stack would be
expensive.

The SDK also supports
[Ansible](https://sdk.operatorframework.io/docs/building-operators/ansible/quickstart/).
Since we deploy with Ansible already, seems like a go to option.

Finally, there is a python operator framework: [kopf](https://kopf.readthedocs.io/). (last commit 2 months ago, recent PRs have no feedback :/ )

## Future

If the PoC is successful and the operator works reliably, we can continue:

- Move the functionality of the cron jobs into the operator
- Run actual Ansible deployments (premise: new secrets solution is implemented)
- A solid development experience for the operator
- Metrics and logs are available, especially when something breaks
- M0ar fancy deployment features! (e.g. deploy from a PR comment, scale workers during peak etc.)
