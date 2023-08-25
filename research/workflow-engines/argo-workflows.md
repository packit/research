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

- provides UI
- workflows can be run using `Argo CLI` or directly `kubectl`
- complex architecture: https://github.com/argoproj/argo-workflows/blob/master/docs/architecture.md
- doesn't look like a fit for us
