---
title: Migration from Flask to FastAPI
authors: lbarcziova
---

Currently, we use [Flask](https://flask.palletsprojects.com/en/stable/) for our API ([code](https://github.com/packit/packit-service/tree/main/packit_service/service/api)).
We have been considering a potential migration to FastAPI due to its benefits over Flask (detailed below), which would also be a chance to refactor our API (and maybe also DB) code.
This research aims to evaluate these benefits and outline the key aspects of a possible migration.

## [FastAPI](https://fastapi.tiangolo.com/)

### Advantages

- automatic documentation: OpenAPI, Swagger
- data validation, type hints: Python’s type annotations and [Pydantic](https://docs.pydantic.dev/latest/) for data validation
- built-in support for dependency injection, which is useful for managing database
  sessions, authentication, and configuration
- websocket and background task support - can be helpful for real-time updates or long-running processes (for usages stats?)
- good ecosystem, community
- async support
- performance
- filtering, searching, pagination should be more easier to do

### Disadvantages (from our architecture discussion)

- frequent updates, maintenance overhead
- Pydantic v2 Rust dependency: Pydantic v2 requires a Rust toolchain, which can be difficult to manage
  on LTS-based distributions. Since we use Fedora-based images in OpenShift and can also pin dependencies,
  this is unlikely to be a major blocker.

### Considerations

- migration cost: refactoring, creating the models for documentation, rewriting of endpoints
- benefits:
  - we could get rid of non-used endpoints
  - we could refactor/improve the functionality
  - documentation of endpoints => easier dashboard development
- alternatives:
  - Sanic, Tornado, Falcon - lacking the functionalities such as validation, autodocumentation
  - Django - too heavy
  - none offer significant advantages over FastAPI/Flask

## Migration requirements

### Rewriting endpoints

- convert Flask routes to FastAPI - replace Flask routes (`@app.route`) with FastAPI routes (`@app.get()`).
- update request parsing, query params
- response handling
  - Pydantic models are recommended for response validation (raw dictionary responses can be returned also)
- revisit error handling, utilise built-in support

### Implementing models

- this is not strictly required (for the GET requests) but significantly improves the migration's value and is highly recommended.
- it would be also our primary reason for migration:
  - could be fixed in Flask, but the effort would be similar to a full migration
  - previous attempt to document the endpoints with Flask:
    - https://github.com/packit/packit-service/pull/2089/files
    - the biggest issues: lot of duplication and additional code, change in serialization

#### Using Pydantic with our existing models

- retain current SQLAlchemy models for database interactions and add separate Pydantic schemas
  to handle API validation, serialization, and documentation
- support for integration with ORMs: https://docs.pydantic.dev/latest/concepts/models/#arbitrary-class-instances

```python
from pydantic import BaseModel, ConfigDict

class UserSchema(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)
```

- advantages:
  - lower risk of breaking something: wouldn't need to touch the DB layer
  - separation: DB layer decoupled from the API layer - control on what gets exposed via the API without altering the persistence logic
  - flexibility: schema can be updated independently
- disadvantages:
  - duplication
  - manual mapping

#### Migrating to [SQLModel](https://sqlmodel.tiangolo.com/)

- a single model that serves both as database model and your API schema
- advantages:
  - no duplication
  - automatically validated and documented endpoints
  - cleaner codebase
- disadvantages:
  - higher migration overhead: rewriting models, increased risk
  - less mature: it is newer than the established combination of SQLAlchemy + Pydantic

```python
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    email: str

```

## Migration approach

### Gradual rewrite

- keep existing Flask endpoints and introduce FastAPI under e.g. `/api/v1/`
- migrate endpoints gradually (e.g., file by file) to FastAPI
- update code to use the new endpoints
- once all critical endpoints are migrated, remove Flask entirely

- smaller risk of breaking something
- work could be paralelised

### Rewrite all at once

- requires rewriting all endpoints and models at once
- higher risk of introducing breaking changes

## Migration example

### Before

```python
koji_builds_ns = Namespace("koji-builds", description="Production builds")

@koji_builds_ns.route("")
class KojiBuildsList(Resource):
    @koji_builds_ns.expect(pagination_arguments)
    @koji_builds_ns.response(HTTPStatus.PARTIAL_CONTENT, "Koji builds list follows")
    def get(self):
        """List all Koji builds."""
        scratch = (
            request.args.get("scratch").lower() == "true" if "scratch" in request.args else None
        )
        first, last = indices()
        result = []

        for build in KojiBuildTargetModel.get_range(first, last, scratch):
            build_dict = {
                "packit_id": build.id,
                "task_id": build.task_id,
                "scratch": build.scratch,
                "status": build.status,
                "build_submitted_time": optional_timestamp(build.build_submitted_time),
                "chroot": build.target,
                "web_url": build.web_url,
                # from old data, sometimes build_logs_url is same and sometimes different to web_url
                "build_logs_urls": build.build_logs_urls,
                "pr_id": build.get_pr_id(),
                "branch_name": build.get_branch_name(),
                "release": build.get_release_tag(),
            }

            if project := build.get_project():
                build_dict["project_url"] = project.project_url
                build_dict["repo_namespace"] = project.namespace
                build_dict["repo_name"] = project.repo_name

            result.append(build_dict)

        resp = response_maker(
            result,
            status=HTTPStatus.PARTIAL_CONTENT,
        )
        resp.headers["Content-Range"] = f"koji-builds {first + 1}-{last}/*"
        return resp
```

### After (using Pydantic)

```python
from fastapi import APIRouter, Query, Request, Response, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from http import HTTPStatus

router = APIRouter(prefix="/koji-builds", tags=["Production builds"])

# Pydantic models
class ProjectModel(BaseModel):
    project_url: str
    repo_namespace: str
    repo_name: str


class KojiBuildModel(BaseModel):
    packit_id: int
    task_id: int
    scratch: bool
    status: str
    build_submitted_time: Optional[str]
    chroot: str
    web_url: str
    build_logs_urls: List[str]
    pr_id: Optional[int]
    branch_name: Optional[str]
    release: Optional[str]
    project: Optional[ProjectModel] = None


@router.get("", response_model=List[KojiBuildModel], status_code=HTTPStatus.PARTIAL_CONTENT)
def get_koji_builds(
    request: Request,
    response: Response,
    scratch: Optional[bool] = Query(None, description="Filter by scratch builds"),
    first: int = Query(0, description="Pagination start index"),
    last: int = Query(10, description="Pagination end index"),
):
    """List all Koji builds."""
    result = []

    for build in KojiBuildTargetModel.get_range(first, last, scratch):
        build_data = KojiBuildModel(
            packit_id=build.id,
            task_id=build.task_id,
            scratch=build.scratch,
            status=build.status,
            build_submitted_time=optional_timestamp(build.build_submitted_time),
            chroot=build.target,
            web_url=build.web_url,
            build_logs_urls=build.build_logs_urls,
            pr_id=build.get_pr_id(),
            branch_name=build.get_branch_name(),
            release=build.get_release_tag(),
            project=(
                ProjectModel(
                    project_url=build.get_project().project_url,
                    repo_namespace=build.get_project().namespace,
                    repo_name=build.get_project().repo_name,
                )
                if build.get_project()
                else None
            ),
        )

        result.append(build_data.model_dump())

    response.headers["Content-Range"] = f"koji-builds {first + 1}-{last}/*"
    return result


```

### Useful links

- https://testdriven.io/blog/moving-from-flask-to-fastapi/
- https://amitness.com/posts/fastapi-vs-flask#data-validation
