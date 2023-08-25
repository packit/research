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
