---
title: Argo Workflows
authors: lbarcziova
---

- docs: https://argoproj.github.io/argo-workflows/

  > Argo Workflows is an open source container-native workflow engine for orchestrating parallel jobs on Kubernetes. Argo Workflows is implemented as a Kubernetes CRD (Custom Resource Definition).
  >
  > - Define workflows where each step in the workflow is a container.
  > - Model multi-step workflows as a sequence of tasks or capture the dependencies between tasks using a directed acyclic graph (DAG).
  > - Easily run compute intensive jobs for machine learning or data processing in a fraction of the time using Argo Workflows on Kubernetes.

- example of multi-step workflow config:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: steps-
spec:
  entrypoint: hello-hello-hello

  # This spec contains two templates: hello-hello-hello and whalesay
  templates:
    - name: hello-hello-hello
      # Instead of just running a container
      # This template has a sequence of steps
      steps:
        - - name: hello1 # hello1 is run before the following steps
            template: whalesay
            arguments:
              parameters:
                - name: message
                  value: "hello1"
        - - name: hello2a # double dash => run after previous step
            template: whalesay
            arguments:
              parameters:
                - name: message
                  value: "hello2a"
          - name: hello2b # single dash => run in parallel with previous step
            template: whalesay
            arguments:
              parameters:
                - name: message
                  value: "hello2b"

    # This is the same template as from the previous example
    - name: whalesay
      inputs:
        parameters:
          - name: message
      container:
        image: docker/whalesay
        command: [cowsay]
        args: ["{{inputs.parameters.message}}"]
```

> it can be specified which Role (i.e. which permissions) the ServiceAccount that Argo uses by binding a
> Role to a ServiceAccount using a RoleBinding (by default, ServiceAccount from the namespace from which it is run, which will almost always have insufficient privileges by default)

> All pods in a workflow run with the service account specified in workflow.spec.serviceAccountName, or if omitted, the default service account of the workflow's namespace.

- provides UI
- workflows can be run using `Argo CLI` or directly `kubectl`
- provides an API and client libraries:
  - for Python there is an auto-generated one without good documentation: https://github.com/argoproj/argo-workflows/tree/master/sdks/python
  - example:

```python
# imports

manifest = IoArgoprojWorkflowV1alpha1Workflow(
    metadata=ObjectMeta(generate_name='hello-world-'),
    spec=IoArgoprojWorkflowV1alpha1WorkflowSpec(
        entrypoint='whalesay',
        templates=[
            IoArgoprojWorkflowV1alpha1Template(
                name='whalesay',
                container=Container(
                    image='docker/whalesay:latest', command=['cowsay'], args=['hello world']))]))

api_client = argo_workflows.ApiClient(configuration)
api_instance = workflow_service_api.WorkflowServiceApi(api_client)

if __name__ == '__main__':
    api_response = api_instance.create_workflow(
        namespace='argo',
        body=IoArgoprojWorkflowV1alpha1WorkflowCreateRequest(workflow=manifest),
        _check_return_type=False)
    pprint(api_response)
```

- complex architecture: https://github.com/argoproj/argo-workflows/blob/master/docs/architecture.md
- doesn't look like a fit for us - not that flexible definition of tasks that we would need
