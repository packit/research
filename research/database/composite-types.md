---
title: Usage of composite type to store the pipelines
authors: lbarczio
---

[Composite column types](https://docs.sqlalchemy.org/en/14/orm/composites.html):
Sets of columns can be associated with a single user-defined datatype, which in modern use is normally a Python dataclass. The ORM provides a single attribute which represents the group of columns using the class you provide.

Examples how can this be done:

1. sqlalchemy_utils [CompositeType](https://sqlalchemy-utils.readthedocs.io/en/latest/data_types.html?highlight=CompositeType#module-sqlalchemy_utils.types.pg_composite):
   a custom SQLAlchemy type designed to work with PostgreSQL's composite types:

```python
class MyCompositeType(CompositeType):
    attribute1 = Column(Integer)
    attribute2 = Column(String)

class MyModel(Base):
    __tablename__ = 'my_table'

    id = Column(Integer, primary_key=True)
    my_composite = Column(MyCompositeType)

```

2. [`sqlalchemy.orm.composite()`](https://docs.sqlalchemy.org/en/14/orm/composites.html#sqlalchemy.orm.composite): allows to define composite types as a Python class:

```python

class MyCompositeType(object):
    def __init__(self, attribute1, attribute2):
        self.attribute1 = attribute1
        self.attribute2 = attribute2

class MyModel(Base):
    __tablename__ = 'my_table'

    id = Column(Integer, primary_key=True)
    composite = composite(MyCompositeType, Column('attribute1', Integer), Column('attribute2', Integer))
```

3. subclassing custom class by [`sqlalchemy.types.TypeDecorator`](https://docs.sqlalchemy.org/en/14/core/custom_types.html#sqlalchemy.types.TypeDecorator) and implementing the necessary conversion methods

```python

@dataclass
class MyCompositeType:
    attribute1: int
    attribute2: int

class MyCompositeTypeDecorator(TypeDecorator):
    impl = SQLInteger

    def process_bind_param(self, value, dialect):
        if value is not None:
            return f"{value.attribute1},{value.attribute2}"

    def process_result_value(self, value, dialect):
        if value is not None:
            attribute1, attribute2 = map(int, value.split(","))
            return MyCompositeType(attribute1, attribute2)

class MyModel(Base):
    __tablename__ = 'my_table'

    id = Column(Integer, primary_key=True)
    composite = Column(MyCompositeTypeDecorator())

```

For simplification, let's work with a pipeline model that has only SRPM, Copr build and test.

## Current pipeline model

Pipeline model in current fashion:

```python
class PipelineModel(Base):
    __tablename__ = "pipelines"
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, default=datetime.utcnow)

    job_trigger_id = Column(Integer, ForeignKey("job_triggers.id"))
    job_trigger = relationship("JobTriggerModel", back_populates="runs")

    srpm_build_id = Column(Integer, ForeignKey("srpm_builds.id"), index=True)
    srpm_build = relationship("SRPMBuildModel", back_populates="runs")
    copr_build_group_id = Column(
        Integer, ForeignKey("copr_build_groups.id"), index=True
    )
    copr_build_group = relationship("CoprBuildGroupModel", back_populates="runs")
    test_run_group_id = Column(
        Integer, ForeignKey("tft_test_run_groups.id"), index=True
    )
    test_run_group = relationship("TFTTestRunGroupModel", back_populates="runs")

```

- has the foreign keys to other tables to reference steps of the pipeline (groups), the group then references particular
  targets, therefore when getting the whole pipeline, join on multiple tables has to happen
- with the composite types we would like to solve the current need of doing multiple joins to get the data about
  one pipeline

## 1.option

How could the model look like when using composite type on target level:

- storing the data for the particular target directly in pipeline
- this would be a step back since we already did the grouping refactoring

### Issues

#### 1. querying concrete steps of the pipeline

Examples of when this happens:

- when updating Copr build status in DB, we get the corresponding builds via the build ID from Copr (index)
- when updating TF run status in DB, we get the corresponding test run via the TF pipeline ID (index)
- babysit tasks - they get all the pending Copr builds / Test runs
- when triggering `/packit test` - we get the latest Copr build model with corresponding commit SHA

#### 2. data duplication

- updating SRPM build would require getting all pipelines and updating the data everywhere

##### Average number of Copr builds using the same SRPM build

```
packit=# SELECT AVG(copr_build_target_count) FROM (
    SELECT COUNT(DISTINCT copr_build_targets.id) AS copr_build_target_count
    FROM pipelines
    JOIN copr_build_targets ON pipelines.copr_build_group_id = copr_build_targets.copr_build_group_id
    GROUP BY pipelines.srpm_build_id
) AS copr_targets_count;
        avg
--------------------
 6.4208079446515274
(1 row)
```

- similar situation for Copr builds <> TF runs, since the relationship can be 1:n

##### Average number of tests using the same Copr build

```
packit=# SELECT AVG(test_run_count) AS average_test_runs FROM (
    SELECT copr_id, COUNT(DISTINCT tft_id) AS test_run_count
    FROM tf_copr_build_association_table
    GROUP BY copr_id
) AS tf_counts;
 average_test_runs
--------------------
 1.2618628164375168
(1 row)
```

## 2.option

How could the model look like when using composite type on group level:

- "groups" stored together in one pipeline
- mapping build -> TF needed

### Issues

#### 1. querying concrete steps of the pipeline

- same as in the previous case.

#### 2. more complicated manipulation with the data in general

#### 3. race conditions

- e.g. updating 2 Copr builds of the same pipeline at the same time

#### 4. more complicated implementation
