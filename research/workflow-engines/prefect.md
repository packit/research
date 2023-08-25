---
title: Prefect
authors: lbarcziova
---

- docs: https://docs.prefect.io/2.11.5/

  > Prefect is a workflow orchestration tool empowering developers to build, observe, and react to data pipelines.

- provides UI for monitoring flows and tasks, and it also allows you to build custom dashboards: ![UI](https://docs.prefect.io/2.11.5/img/ui/dashboard-cloud.png)
- workflows are defined as directed flows, where tasks can be arbitrary Python functions or objects
- provides strong support for dynamic workflows
- more advanced error handling, including retries, retries with backoff, and more fine-grained control over how errors are managed
- compared to Airflow it is less mature, more light-weight
- example of flow:

```python
@task
def get_letters(word: str) -> int:
    # call Python libs, shell out to bash
    return list(word)

@task
def display(letter: str):
    # or talk to Cloud services, or whatever else
    print(f"My letter: '{letter}'")

with Flow("myflow") as flow:
    word = Parameter("word")
    letters = get_letters(word)
    display.map(letters)

```

## Deployment

- architecture overview: https://docs.prefect.io/2.11.5/concepts/deployments/#deployments-overview
- worker types: https://docs.prefect.io/2.11.5/concepts/work-pools/#worker-types
- task runners: https://docs.prefect.io/2.11.5/concepts/task-runners/
  - enable using specific executors of tasks for concurrent, parallel or distributed execution
  - DaskTaskRunner - parallel task runner, distributed scheduler
- hosting: https://docs.prefect.io/2.11.5/guides/host/
