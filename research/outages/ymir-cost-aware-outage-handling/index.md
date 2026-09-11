---
title: Ymir infrastructure outage handling and LLM cost control
authors: lbarczio
---

# Ymir infrastructure outage handling and LLM cost control

## Summary

Ymir retries at several levels: HTTP/tools, model calls, agent steps, and
complete workflows. During an external outage this can spend many LLM calls on
work that cannot succeed.

The proposed outcome is to:

1. capture failure facts where external calls are made;
2. classify clear cases with code, without an LLM;
3. pause new work for the affected dependency;
4. replay queued work with bounded budgets and safe Redis operations.

The MCP gateway is internal to the OpenShift namespace. It is not an external
dependency, although connection and identity failures should be logged.

## What is currently costing retries

| Area             | Current behavior                                                                           | Action needed                                                       |
| ---------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| HTTP             | HTTP 503 is retried three times.                                                           | Preserve status and operation for classification.                   |
| Copr             | Every `CoprException` is retried three times.                                              | Distinguish service failure from invalid request/build failure.     |
| Git/dist-git     | Some stderr patterns retry three times; other operations do not.                           | Classify reads, pushes, and unknown push results separately.        |
| Jira             | Critical label writes retry three times; other writes have no HTTP retry layer.            | Avoid blind retries of writes.                                      |
| Model/agent      | LiteLLM: three provider retries; Ymir: five retries per step and 25 total.                 | Stop new model work when dependency is paused.                      |
| Ordinary queues  | `MAX_RETRIES=3` can rerun a complete workflow.                                             | Do not let outage failures enter generic workflow retry.            |
| Reproducer       | Package opt-in, 30-minute delay, lock-blocked lists, `MAX_RETRIES=3` to `ERROR_LIST`.      | Use as the first pilot; make delayed promotion safe before scaling. |
| MR consolidation | Atomic Hash claim, `MAX_BUILD_ATTEMPTS=3`; failed returned state reaches `complete_job()`. | Add delayed release and side-effect reconciliation separately.      |

Some external calls bypass MCP entirely (direct HTTP, Git subprocesses,
Koji/Brew clients). The same classification must work for both paths.

### CronJobs that feed work into queues

CronJobs run outside agent pods and don't use LLM calls, so outage cost
is wasted job time, not model spend.

| CronJob                                                     | Schedule              | External deps                          |
| ----------------------------------------------------------- | --------------------- | -------------------------------------- |
| `jira-issue-fetcher` / `-todo`                              | Every 15 / 5 min      | Jira                                   |
| `sweep-dependency` / `pr-pending` / `y-stream` / `no-patch` | 6h / 8h / 12h / daily | Jira; `pr-pending` also GitLab, GitHub |
| `mr-cleanup`                                                | Daily                 | GitLab                                 |

The fetcher already has backpressure: `QUEUE_DEPTH_THRESHOLD` stops
pushing when the triage queue is deep enough. During an outage, if
agents are paused and queues aren't draining, the fetcher naturally
stops adding more work. This complements the proposed gate — no
additional fetcher changes needed.

The main risk is the **sweep jobs** — a partial failure (Jira errors for
some issues but not others) could leave inconsistent label state. The
sweeps currently use a synchronous `requests` client that should be
refactored to a shared location, and would benefit from
`classify_failure()`.

## Proposed policy

### Failure facts and classification

[PR #775](https://github.com/packit/ai-workflows/pull/775) adds
`tool_error_context()` to the gateway-side tools (Copr, GitLab, lookaside,
Jira, dist-git, Testing Farm). It captures service, operation, and exception
type as `ToolErrorWithContext.additional_context`.

For **local tools** (same process), the full `ToolErrorWithContext`
survives to `_runner.py`'s `tool_call.error`. For **MCP tools**
(cross-process), `additional_context` is lost — but BeeAI's
`MCPTool._run()` already reads `result.meta.error_context` if present.
The gateway just needs to populate
`CallToolResult(meta={"error_context": {...}})` and the structured dict
flows through.

In both cases, the top-level retry handler (e.g. `triage_agent.py`'s
`retry()`) only sees a generic `ErrorData` from the workflow exception,
not per-tool errors. Classification therefore needs to happen at the
tool-call level in `_runner.py`, not in the retry closure.

What remains is:

- populating `meta.error_context` on the gateway side (small change to
  `tool_error_context()` or the tool base class);
- adding equivalent capture for direct (non-MCP) calls: Koji/Brew
  clients, direct HTTP, Git subprocesses in agent pods;
- building the classifier and gate on top.

The observation structure could look like:

```python
FailureObservation(
    dependency="jira", operation="edit_jira_labels",
    exception_type="ClientResponseError", status_code=503,
)
```

Redact credentials; keep full errors in logs linked to task/correlation IDs.

Implement a pure `classify_failure(observation)` function returning
`transient`, `permanent`, `logic`, or `unknown`, plus `reconcile_first` for
ambiguous writes.

| Dependency          | Transient candidates                                                                                      | Do not retry automatically                                             |
| ------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Jira                | Timeout/connection, 429, selected 5xx; writes need reconciliation if the connection dropped after sending | 400/401/403/404, invalid field/transition, missing issue               |
| GitLab/dist-git     | Network/TLS/DNS/early EOF, 429/5xx reads                                                                  | Auth, invalid ref, rejected push; unknown push needs reconciliation    |
| Copr                | Network/timeout, 429, 5xx                                                                                 | Invalid project/chroot, auth, malformed request, content build failure |
| Koji/Brew/lookaside | Network/timeout, client 5xx                                                                               | Missing build/source, checksum, auth/configuration                     |
| Testing Farm        | Provisioning/network failure after submission                                                             | Test failure or invalid request; no health reservation probe           |
| Errata              | Network/timeout, 5xx                                                                                      | Auth, missing erratum; used by collector cronjob, not agents           |
| Model provider      | 429/temporary provider failure                                                                            | Do not use a model call as a health check                              |

Unknown is the default when facts are missing or contradictory. It does not
automatically create a replay.

Deterministic rules are the default. LLM classification is an open
option only for ambiguous build output, bounded, tested offline first.
Existing `is_infra_error`/`retryable_error` fields are compatibility
inputs only.

### Pause and replay limits

The worker checks a shared `OutageGate` before `mcp_tools()`, agent creation, or
an LLM call:

```python
if await outage_gate.is_paused(task.dependencies):
    await schedule_delayed(task)
    return
await run_workflow(task)
```

Initial values for discussion:

| Limit                                   | Meaning                                                                                     |                          Starting value |
| --------------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------: |
| LLM calls while dependency is paused    | How many new agent/model runs to allow for tasks needing a paused service                   |                                       0 |
| Replays per outage episode              | After the service recovers, how many times to re-run a task that failed during this episode |                                       1 |
| Outage episodes per task                | How many separate outage windows a single task can survive before giving up                 |                                       3 |
| Maximum total postponement              | Wall-clock time from first outage-caused delay to final give-up                             |                                 2 hours |
| Reproducer delay                        | How long to wait before retrying a reproducer task (Testing Farm is slow/expensive)         |                              30 minutes |
| Provider retries during provider outage | LLM provider-specific retries after a provider 429/failure is detected                      |                                       0 |
| After all limits exhausted              | What happens when a task hits the ceiling                                                   | One `ERROR_LIST` entry; stop automation |

An **outage episode** starts when the gate pauses a dependency. It ends when
a recovery probe or real task succeeds. If the same dependency fails again
after recovery, that counts as a new episode. Independent dependencies have
independent episodes.

Unknown failures fail closed. Operators use
`openshift/scripts/requeue_error.py` to move a specific error back to its
original queue after fixing the cause.

The gate only prevents _new_ work from starting. A workflow already running
will still use its remaining retries. Stopping active workflows mid-run is
deferred until we measure how much the pre-workflow gate saves.

## Implementation plan

### Phase 0 — wire up MCP error context

BeeAI already reads `result.meta.error_context` on the client side; the
gateway just doesn't populate it yet.

1. In `tool_error_context()` or the tool base class, populate
   `CallToolResult(meta={"error_context": additional_context})`.
2. Write a test that triggers errors (Jira 503, Copr 400, timeout,
   unknown Git push result) through the real MCP path and asserts the
   structured dict arrives at `tool_call.error.context`.
3. Save redacted examples as test fixtures.

No production retry behavior changes in this phase.

### Phase 1 — fix per-call retries based on error type

This is the most immediate win. Today every error gets the same treatment.
For example, the triage retry closure (`triage_agent.py:1493`):

```python
# Current: every error is treated the same
async def retry(task, error):
    task.attempts += 1
    if task.attempts < max_retries:
        await redis.lpush(retry_queue, task.model_dump_json())  # immediate requeue
    else:
        # ... error labels, ERROR_LIST
```

With classification:

```python
async def retry(task, error):
    classification = classify_failure(error)
    if classification == “permanent”:
        # Jira 400, auth error, invalid ref — won't fix itself
        await push_to_error_list(task, error)
        return
    task.attempts += 1
    if classification == “transient” and task.attempts < max_retries:
        await schedule_delayed(task, delay=backoff(task.attempts))
    else:
        await push_to_error_list(task, error)
```

The same pattern applies to all four agent retry closures. Steps:

1. Write a shared `classify_failure()` function using the table in
   “Failure facts and classification” above.
2. For MCP tools, build on the `tool_error_context()` from #775. For
   direct calls (Koji/Brew, direct HTTP, Git subprocesses), add
   equivalent adapters that build a `FailureObservation`.
3. Change retry behavior per classification:
   - **Transient** (503, timeout, connection reset): retry with backoff.
   - **Permanent** (400, 403, 404, invalid request): stop immediately,
     don't waste retries.
   - **Unknown**: don't retry automatically; send to `ERROR_LIST`.
4. Log the classification to Sentry as structured context on the event.

Start with one or two services (e.g. Jira and GitLab) and expand.
Run in shadow mode first (log the classification but don't change retry
behavior) until false positives are understood.

### Phase 2 — add the pre-workflow gate

Once per-call retries are sensible, add the shared gate to prevent
starting new LLM workflows when a service is down:

1. Add the `OutageGate` backed by Redis, checking before agent creation.
2. Pilot on the reproducer (it already has delayed retry and is opt-in).
   Preserve its package-enable check and lock-blocked behavior.
3. Add a global kill switch and a per-workflow enable flag.
4. Optional: per-dependency flags, configurable limits, Slack
   notification when a dependency is paused.

### Phase 3 — make delayed replay safe

Make the delayed queue work reliably with multiple replicas:

1. In `ymir/common/delayed_queue.py`, replace the
   `ZRANGEBYSCORE → LPUSH → ZREM` sequence with a single Lua script that
   atomically removes one due item and pushes it to the target queue.
   Test with two pollers and process crashes.
2. Include source queue, task ID, episode, and counters in delayed
   records.

### Phase 4 — MR consolidation support

MR consolidation has a different queue model (Redis Hash) and side
effects. Core change: don't silently discard a failed job via
`complete_job()` — add a delayed-retry path. Concurrency fixes
(check-and-set in `submit_merge_job()`, side-effect reconciliation)
are separate improvements that happen to be useful here.

### Phase 5 — measure and tune

Roll out gradually: shadow mode → reproducer → one ordinary workflow →
MR consolidation.

Check that:

- a paused dependency causes zero new LLM calls;
- delayed work is promoted exactly once under competing pollers;
- permanent/unknown failures don't create automatic replays;
- the ceiling creates one `ERROR_LIST` entry and stops;
- the kill switch restores current behavior.

## Open decisions

- Are the proposed limits (1 replay, 3 episodes, 2-hour ceiling) right, or
  should we commit to them as tunable defaults and adjust after Phase 5?

## Decided

- No LLM-based classification in the first iteration. If needed later, it
  must run offline/shadow first and not trigger unlimited retries.
- No manual "mark service as down" mechanism initially — the gate pauses
  dependencies automatically based on failure count, and a kill switch
  (env var or Redis key) disables the gate entirely if it misbehaves.
- Local tools preserve `ToolErrorWithContext.additional_context` fully.
  MCP tools lose it, but BeeAI already supports `result.meta.error_context`
  — the gateway just needs to populate it (Phase 0). Classification
  happens at the tool-call level in `_runner.py`, not the retry closure.

## Related but separate

- A Ymir status view is a communication follow-up (can take inspiration from
  [`status.packit.dev`](https://status.packit.dev/)); it should stay reachable
  during an OpenShift outage.
- Stopping active workflows mid-run is deferred (see note above).
