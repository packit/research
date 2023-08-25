---
title: Celery Canvas
authors: lbarcziova
---

- docs: https://docs.celeryq.dev/en/stable/userguide/canvas.html
- provides capabilities to build simple workflows
- it is possible to define e.g. serial execution, in parallel, in group

## Chains

- tasks can be linked together: the linked task is called when the task returns successfully
- example:

```python
from celery import chain
from task import task_a, task_b, task_c

work_flow = chain(task_a(arg1, arg2), task_b(result, arg4, arg5), task_c(arg6, arg7))

# another way

s = task_a.s(arg1, arg2)
s.link(task_b.s(arg4, arg5))

# another way using pipes
work_flow = task_a(arg1, arg2) | task_b(result, arg4) | task_c(arg5, arg6)

```

- we would only write code on top of existing one, for handling the dependant tasks, no need
  for deployment changes
- post describing the capabilities in detail: https://dev.to/akarshan/the-curious-case-of-celery-work-flows-39f7
