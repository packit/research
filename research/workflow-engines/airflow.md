---
title: Airflow
authors: lbarcziova
---

- docs: https://airflow.apache.org/docs/apache-airflow/stable/index.html

  > Apache Airflow is a platform used to programmatically author, schedule, and monitor workflows. It allows you to define complex workflows as directed acyclic graphs (DAGs) and execute them on a scheduled basis or triggered by events.

- A DAG is the core concept in Airflow. It's a collection of tasks and their dependencies, organized as a directed acyclic graph. Example:

```python
from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

def build_task():
    pass

def test_task():
    pass

def dynamic_workflow():
    dag = DAG(
        f'dynamic_workflow',
        start_date=datetime.now(),
        schedule_interval=None,
        catchup=False,
    )

    build = PythonOperator(
        task_id=f'build',
        python_callable=build_task,
        op_args=[],
        dag=dag,
    )

    test = PythonOperator(
        task_id=f'test',
        python_callable=test_task,
        op_args=[],
        dag=dag,
    )

    # Set task dependencies
    build >> test

    return dag

dynamic_workflow()

```

- Airflow uses schedulers and executors to manage task execution. The scheduler determines when to execute tasks, while the executor defines how tasks are run. Airflow supports various executors, including SequentialExecutor, LocalExecutor, and CeleryExecutor.
- allows dynamic pipelines generation
- provides UI ![UI](https://airflow.apache.org/docs/apache-airflow/stable/_images/dags.png)
- from `Why not` in docs:
  > Airflow™ was built for finite batch workflows. While the CLI and REST API do allow triggering workflows, Airflow was not built for infinitely running event-based workflows. Airflow is not a streaming solution. However, a streaming system such as Apache Kafka is often seen working together with Apache Airflow. Kafka can be used for ingestion and processing in real-time, event data is written to a storage location, and Airflow periodically starts a workflow processing a batch of data.

## CeleryExecutor

Details: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/celery.html

- it is also possible to use Flower UI

## Deployment

- the architecture is more complex, there are multiple components: scheduler, webserver, executor, db, ..
- example of running in Docker: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html
- production deployment: https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/production-deployment.html
  - provides Docker images: https://airflow.apache.org/docs/docker-stack/index.html
  - provides Helm charts
