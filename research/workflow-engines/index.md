---
title: Workflow engines
authors: lbarcziova
---

- this research aims to describe workflow engines that could improve the state of the service, in particular
  how the logic around job dependencies could be eased by usage of these

- you can find separate files describing tools that were proposed to be researched more:

  - [Airflow](airflow.md)
  - [Argo workflows](argo-workflows.md)
  - [Temporal](temporal.md)
  - [Selinon](selinon.md)
  - [Prefect](prefect.md)
  - [(Celery Canvas)](celery-canvas.md)

- besides that, I found some great articles and resources overviewing some of these:
  - overview and comparison of Argo, Airflow and Prefect: https://neptune.ai/blog/argo-vs-airflow-vs-prefect-differences
  - Prefect vs Celery: https://github.com/PrefectHQ/prefect/issues/1689
  - multiple 1 to 1 comparisons of some of the mentioned tools: https://www.datarevenue.com/en-blog/airflow-vs-luigi-vs-argo-vs-mlflow-vs-kubeflow
- how are job dependencies managed in other services?
  - explicit dependencies/steps
  - mostly own implementation of the logic:
    - https://github.com/harness/drone/blob/e63b8f9326969220df73b9d74349405eb86c1073/operator/manager/teardown.go#L278
    - https://github.com/buildbot/buildbot/blob/90c1ce112443449b34527a2f6124b7b2ec78de2f/master/buildbot/process/build.py#L550C9-L550C22
    - https://github.com/gocd/gocd/blob/d46db3f41f08cfcbe2cc8bc5b2c8c846baa6a978/server/src/main/java/com/thoughtworks/go/server/domain/PipelineConfigDependencyGraph.java#L77C49-L77C49

## Conclusion, next steps

- the logic behind mapping the event + configuration to the tasks and their dependencies
  needs to be done on our side, the tools can help with the orchestration of the dependencies
  after we define them
- without much changed needed, we could try utilising Celery Canvas to help us with
  scheduling tasks based on the dependencies we specify
- other tools mostly provide support for more complex usecases, but from the ones that were listed,
  I can see Airflow/Prefect could fit into what we do in Packit - the downside of using these
  is more complex deployment than we have now
- as for Airflow/Prefect, Airflow is a more stable tool that has great documentation, provides variety of
  features and a lot of people already handled the problems we would need to handle; Prefect might be on the other hand more light-weight
  - I definitely suggest reading the previously mentioned [comparison blogpost](https://neptune.ai/blog/argo-vs-airflow-vs-prefect-differences)
- some of the tools offer features for waiting for an external event (such as message on a messaging bus), we could
  utilise these (e.g. Airflow's Sensors)
- some of the solutions could help us get rid of sandcastle (KubernetesExecutor in Airflow)
