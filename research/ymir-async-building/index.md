# Ymir: Async Building — Solving the Copr Build Blocking Problem

## Problem Statement

The backport/rebase agent currently blocks the entire pod while waiting for
Copr builds to finish. Builds can take up to 3 hours, and the cherry-pick fix
loop can trigger up to 10 rebuild attempts — meaning a single task can
monopolize a pod for 30+ hours. During this time the pod is idle except for
polling Copr every 30 seconds.

## Current Architecture

### Workflow (backport agent)

```
Redis brpop (pick task)
  → change Jira status
  → fork & prepare dist-git
  → run backport agent (Claude applies patches)
  → run build agent (submit SRPM to Copr, poll until done)   ← BLOCKING
      ├─ SUCCESS → update release → commit → MR → Jira
      ├─ TIMEOUT → proceed anyway
      └─ FAILURE (decrement attempts_remaining)
            ├─ cherry-pick workflow → fix_build_error loop    ← BLOCKING (repeated)
            └─ git-am workflow → full reset & retry           ← BLOCKING (repeated)
                 (back to fork_and_prepare_dist_git — re-clones, re-patches, rebuilds)
  → post-processing (log agent, MR, labels, Jira comment)
```

### Workflow (rebase agent)

The rebase agent has the same blocking pattern. On build failure it always
does a full pipeline reset (like backport's git-am path):

```
Redis brpop (pick task)
  → fork & prepare dist-git
  → run rebase agent (Claude performs rebase)
  → run build agent (submit SRPM to Copr, poll until done)   ← BLOCKING
      ├─ SUCCESS → update release → commit → MR → Jira
      ├─ TIMEOUT → proceed anyway
      └─ FAILURE (decrement attempts_remaining)
            → full reset & retry                              ← BLOCKING (repeated)
              (back to fork_and_prepare_dist_git — re-clones, re-rebases, rebuilds)
  → post-processing (log agent, MR, labels, Jira comment)
```

Up to 10 full re-runs (`MAX_BUILD_ATTEMPTS`), no incremental fix loop.

### Where time is spent

| Phase                              | Typical duration      | Notes                           |
| ---------------------------------- | --------------------- | ------------------------------- |
| Patch application (backport agent) | 2–10 min              | LLM calls + tool use            |
| SRPM generation                    | < 1 min               |                                 |
| **Copr build polling**             | **10 min – 3 hours**  | `asyncio.sleep(30)` loop        |
| Build error analysis               | 1–2 min               | Downloads logs, LLM analysis    |
| Fix attempt (if cherry-pick)       | 5–15 min              | Fresh agent + rebuild           |
| **Full retry (if git-am)**         | **12 min – 3+ hours** | **Re-clone, re-patch, rebuild** |
| Post-processing                    | 1–3 min               |                                 |

The two failure paths use independent retry counters (`attempts_remaining` and
`incremental_fix_attempts`, both default to 10) that don't interact:

- **Backport (cherry-pick)**: up to **11 builds** (1 initial + 10 fix attempts).
- **Backport (git-am)**: up to **10 full pipeline re-runs** (re-clone,
  re-patch, rebuild each time) — worst case ~32 hours blocking a pod.
- **Rebase**: up to **10 full pipeline re-runs** (same as backport git-am
  path) — worst case ~32 hours blocking a pod.

The Copr polling (`ymir/tools/privileged/copr.py:186–229`) uses `asyncio.sleep`
which is non-blocking at the event-loop level, but the workflow is
single-task-per-pod so nothing else runs.

### Key code locations

- Copr build tool (polling loop): `ymir/tools/privileged/copr.py` — `BuildPackageTool._run()`
- Build agent: `ymir/agents/build_agent.py`
- Backport workflow state machine: `ymir/agents/backport_agent.py:1486–1509`
- Fix build error loop (cherry-pick): `ymir/agents/backport_agent.py:1195–1280`
- Git-am full retry (back to `fork_and_prepare_dist_git`): `ymir/agents/backport_agent.py:1329–1330`
- Attempt counter decrement: `ymir/agents/backport_agent.py:1316–1322`
- Reset on retry (does NOT reset `attempts_remaining`): `ymir/agents/backport_agent.py:1086–1089`
- Rebase workflow (same pattern): `ymir/agents/rebase_agent.py`
- Agent runner (memory management): `ymir/agents/reasoning_agent/_runner.py`

### Resource constraints

| Resource               | Current                            |
| ---------------------- | ---------------------------------- |
| Namespace quota        | 14Gi requests / 16Gi limits        |
| Backport agents (×2)   | 2Gi req / 5Gi limit each           |
| Rebase agents (×2)     | 512Mi req / 1Gi limit each         |
| Rebuild agents (×2)    | 512Mi req / 1Gi limit each         |
| Triage agent (×1)      | 512Mi req / 1Gi limit each         |
| Phoenix                | 256Mi req / 1Gi limit              |
| **Total allocated**    | **~6.8Gi requests / ~16Gi limits** |
| **Remaining headroom** | **~7.2Gi requests / ~0Gi limits**  |

The namespace is nearly at its limit budget. Any solution that adds pods or
increases per-pod memory needs a quota increase.

### What consumes memory in a backport pod

- **Source processing** — the dominant consumer. `rhpkg sources` downloads
  compressed sources and `rhpkg prep` unpacks them. Large packages like
  Firefox/Thunderbird have ~750MB compressed sources that expand to ~4GB
  uncompressed. Both CPU and memory spike during these operations. The SE deployment already requires `cpu: 1000m, memory: 6Gi` limits for
  backport pods (2 of each kind) just to avoid OOM kills.
- Git repos cloned to PVC (`/git-repos/{issue}/`) — disk-backed, but repo
  operations spike RSS
- BeeAI `UnconstrainedMemory` — conversation history grows with each LLM
  call and tool result, never trimmed during a run
- Multiple sub-agents created sequentially (backport, build, fix, log) — each
  holds its own conversation state until garbage collected

### Agent state and serialization

- Workflow state is a Pydantic `BaseModel` — trivially serializable via
  `model_dump_json()`.
- Agent conversation history (`UnconstrainedMemory`) can be serialized via
  `BaseMemory.to_json_safe()` and `Message.to_plain()` — all message content
  types are Pydantic models with `model_dump()`. Deserialization requires a
  small custom utility (dispatch on `role` to construct the right `Message`
  subclass), since the framework doesn't provide a `from_json()` method, but
  the constructors already accept dicts internally. BeeAI also offers
  alternative memory classes (`SlidingMemory`, `TokenMemory`,
  `SummarizeMemory`) that could help bound conversation size for long-running
  fix loops.
- Each `fix_build_error` call creates a **fresh agent** with no memory of prior
  fix attempts — context is passed entirely through the prompt template (build
  error message, upstream patches, repo path). This means conversation
  continuity across the build wait is **not required**.

## Alternative: Skip Build Verification Entirely

Instead of optimizing the build wait, eliminate it — open the MR without a
Copr build and rely on CI (GreenWave/OSCI gating) to catch failures. The
preliminary testing agent already monitors these CI results on opened MRs.

**Advantages:**

- Eliminates the blocking problem completely — no architectural changes needed
- MRs opened faster, CI runs in parallel across the dist-git infrastructure

**Challenges:**

- The cherry-pick fix loop in the backport agent uses Copr builds as
  **inline feedback** — the agent builds, reads the error, fixes, rebuilds.
  Without this, the agent can't iteratively fix build failures. The MR would
  be opened with potentially broken code.
- Someone (human or agent) would need to react to CI failures after the MR is
  opened, adding a separate feedback loop outside the current workflow.
- For the git-am and rebase workflows, skipping the build is more viable since
  their retry loop restarts from scratch anyway — the build result doesn't
  guide the fix, it just triggers a blind retry.

**Verdict:** viable for git-am/rebase workflows where the build doesn't guide
fixes. Not viable for the cherry-pick workflow without a way to close the
feedback loop post-MR (e.g. a separate agent that reacts to CI failures). Could
be offered as a configurable option per workflow type.

## Proposed Solutions

### Option A: Async Task Multiplexing (In-Process Concurrency)

Run multiple tasks concurrently within the same pod using `asyncio`.

```
Pod main loop:
  - Maintain a pool of N concurrent tasks (e.g. N=2–3)
  - When a slot opens, brpop the next task
  - Each task runs as an independent asyncio.Task
  - Build polling (asyncio.sleep) yields the event loop to other tasks
```

**Implementation sketch:**

```python
sem = asyncio.Semaphore(2)

async def process_task(payload):
    async with sem:
        task = Task.model_validate_json(payload)
        # ... existing workflow ...

active = set()
while True:
    element = await fix_await(redis.brpop([backport_queue], timeout=30))
    if element:
        _, payload = element
        t = asyncio.create_task(process_task(payload))
        active.add(t)
        t.add_done_callback(active.discard)
```

**Advantages:**

- Minimal code changes — workflows are already async
- Copr polling already uses `asyncio.sleep`, yielding the event loop — this
  includes builds triggered inside the cherry-pick fix agent's LLM session,
  since the `build_package` tool call goes through the same async polling loop
- Single pod, single process — simpler operations

**Challenges:**

- **Memory**: each concurrent task needs its own source extraction + agent
  conversation. Source processing is the dominant consumer — large packages
  (Firefox, Thunderbird) need ~4Gi just for unpacked sources. With N=2, a
  backport pod could need ~12Gi; with N=3, ~18Gi. The SE deployment already runs backport pods at 6Gi limits for single
  tasks.
- **MCP Gateway**: the MCP protocol multiplexes requests by ID over a single
  SSE session (`_response_streams` dict keyed by `RequestId`), so concurrent
  tool calls from the same pod work out of the box. The gateway tools
  (e.g. `BuildPackageTool`) are stateless. No gateway changes needed.
- **Error blast radius**: one task's crash could affect others in the same
  process.

**Memory mitigation:** eagerly clear agent conversation history after each
sub-agent completes. However, the main memory pressure comes from source
processing, not agent state — conversation history cleanup won't help with
a 4Gi Firefox source extraction.

**Verdict:** viability depends heavily on the package mix. For small packages
(N=2 feasible), this is a quick win. For large packages, even N=2 may exceed
memory limits. Doesn't fundamentally solve the problem.

### Option B: Split Build-Wait from Fix into Separate Workflow Phases

Decouple the workflow into two independently-schedulable phases.

```
Phase 1 — Patch & Submit:
  1. Fork dist-git, apply patches
  2. Generate SRPM
  3. Submit to Copr (fire and forget — just get build_id)
  4. Serialize workflow state to Redis
  5. Return to queue loop immediately

Build Monitor (UMB consumer or lightweight polling service):
  - One small pod (~256Mi)
  - Subscribes to UMB topic /topic/VirtualTopic.devel.copr (build.end)
    and matches build IDs against active tasks
  - Alternatively, polls all active Copr builds every 30s in a single loop
  - When a build completes → push result to "build_complete" queue

Phase 2 — Verify & Fix:
  1. Pop from build_complete queue
  2. Deserialize workflow state
  3. If build succeeded → post-processing (update release, MR, Jira)
  4. If build failed → run fix agent → new SRPM → submit → back to monitor
```

**Advantages:**

- Pod is never idle — always processing real work
- Memory freed between phases (no state held in RAM during builds)
- Scales naturally: one pod processes many tasks per hour
- Clean separation of concerns
- State serialization is straightforward (Pydantic models → JSON in Redis)

**Challenges:**

- Agent conversation history is lost between phases. However, the fix agent
  already creates a **fresh agent** per attempt with full context in its prompt,
  so nothing is actually lost.
- Upstream repo on PVC (`/git-repos/{issue}-upstream/`) must survive between
  phases — this already works.
- Two workflow entry points instead of one — more complex orchestration.
- Needs a new build monitor service (small but new component).

Copr does not support outgoing webhooks, but the internal Copr instance
publishes build completion events on the UMB (Unified Message Bus) under
`/topic/VirtualTopic.devel.copr` with topic `build.end`. Messages include
build ID, status (`SUCCEEDED`/failed), project, owner, and chroot. A UMB
consumer could replace polling entirely for Options B/C.

Note: this option only covers builds triggered at the **workflow step** level
(`run_build_agent`). The cherry-pick fix agent calls `build_package` as a tool
**during its LLM session** — that build still blocks inside `fix_agent.run()`.
Splitting that would require intercepting tool calls mid-agent-run, which the
BeeAI framework doesn't support. In practice this means the fix loop still
blocks, but only the fix iterations (not the initial build or the git-am/rebase
retries).

**Verdict:** addresses the main source of blocking (the initial build and
git-am/rebase retries). The cherry-pick fix loop's internal builds remain
blocking but are shorter (the fix agent only rebuilds after making targeted
changes).

### Option C: Context Switching with Externally-Stored State

When the agent reaches a build wait, serialize the **entire agent state**
(including conversation history) to external storage, release the pod, and
resume later. Redis/Valkey is the natural choice since it's already deployed
with a persistent 2Gi NFS-backed volume. S3 is another option but would
require new infrastructure. This pattern (storing chat history in external
storage during context switches) is used by other teams in their projects.

```
1. Agent runs until build_package is called
2. build_package returns immediately with build_id
3. Serialize to Redis:
   - Pydantic workflow State
   - BeeAI conversation history (all messages)
   - Git state (commit hash, branch, dirty files)
4. Push task into "waiting_for_build" sorted set in Redis
5. Pod picks up next task
6. Monitor detects build completion → push to "resume" queue
7. Pod loads state from Redis, reconstructs agent, continues
```

This is the only option that could handle the cherry-pick fix loop's internal
builds — serializing mid-agent-run when `build_package` is called as a tool,
then resuming the agent with its conversation history intact after the build
completes.

**Advantages:**

- True suspend/resume — conversation history preserved
- Pod utilization maximized, including during cherry-pick fix loop builds
- No new infrastructure — uses existing Redis/Valkey
- Validated pattern (used by other teams)

**Challenges:**

- **BeeAI agent reconstruction**: conversation history is serializable via
  `to_json_safe()`/`to_plain()` (deserialization needs a small custom
  utility). The harder part is reconstructing `ReasoningAgentRunner` state —
  beyond messages, `ReasoningAgentRunState` holds an `iteration` counter,
  `steps` list (with `Tool` instances and `ToolOutput` objects — not trivially
  serializable), and `usage`/`cost` tracking. The runner itself also holds
  retry counters (`_iteration_error_counter`, `_global_error_counter`) and
  tool call cycle detection state. Tool references, LLM config, and
  requirement evaluations are deterministic from config and can be re-created.
- **Prompt caching**: after restoring state, the LLM prompt cache will be cold
  (cache miss on the first call), increasing cost and latency for that
  request. This is a cost tradeoff, not a correctness issue — cache control
  injection points are recomputed dynamically on each LLM call based on
  message positions.
- **Complexity**: most complex option, requires deep framework-level changes.

**State size estimate:**

- Workflow State JSON: ~1–5 KB
- Agent conversation (up to 255 iterations × ~2KB per message pair): ~500 KB
- Well within Redis capacity (2Gi PVC, current usage is small queues).

The same serialization mechanism could also be used to **pass context between
agents in the end-to-end workflow** (triage → backport/rebase). Currently the
triage agent's conversation history — its reasoning about the issue, upstream
research, CVE analysis — is discarded when the task is enqueued. Only a small
structured payload (`BackportData`/`RebaseData` with package name, patch URLs,
justification) survives the handoff via `Task(metadata=state.model_dump())`.
With serialized conversation history in Redis, the downstream agent could load
the triage agent's research as additional context, potentially making better
decisions about patch application and conflict resolution.

**Verdict:** most elegant but requires work to serialize/reconstruct full agent
state. The conversation history part is solvable now; the runner state
reconstruction is the remaining gap. Worth investigating if scale demands grow
beyond what Option B handles.

### Build Monitor Service (shared component for Options B and C)

Options B and C both need a way to detect when Copr builds finish. This would
be a dedicated lightweight service (~256Mi pod) — either a UMB consumer
listening on `/topic/VirtualTopic.devel.copr` (`build.end`) or a polling loop.
The UMB approach is event-driven and near-instant.

This is not a standalone solution — the agent pod still blocks waiting for the
result without one of the options above.

## Comparison Matrix

|                             | Option A: Async Multiplexing  | Option B: Split Phases           | Option C: Redis State             |
| --------------------------- | ----------------------------- | -------------------------------- | --------------------------------- |
| **Effort**                  | Low                           | Medium                           | High                              |
| **Memory impact**           | N× current per pod            | Neutral (freed between phases)   | Neutral (state in Redis)          |
| **Pod utilization**         | Improved (N tasks)            | Optimal (never idle)             | Optimal (never idle)              |
| **New infrastructure**      | None                          | Build monitor pod (UMB consumer) | Monitor pod (uses existing Redis) |
| **Conversation continuity** | Preserved (in-memory)         | Not needed (fresh agent)         | Preserved (serialized)            |
| **Framework changes**       | None                          | Workflow refactoring             | Agent serialization layer         |
| **Quota impact**            | Need ~22Gi+ limits            | Need ~17Gi limits (+monitor)     | Need ~17Gi limits (+monitor)      |
| **Risk**                    | Memory pressure, blast radius | Orchestration complexity         | Framework coupling                |

## Recommendation

### Short-term: Option A with N=2

- Add semaphore-based task pool to the main loop
- Run 2 tasks concurrently per backport pod
- Profile actual RSS first — if well under 5Gi, this is easy
- Increase pod memory to ~8Gi if needed (requires quota bump to ~22Gi)
- Estimated effort: 1–2 days

### Medium-term: Option B (Split Phases)

- Refactor workflow into "submit" and "verify" phases
- Add lightweight Copr build monitor service
- State serialization via Pydantic `model_dump_json()` to Redis
- Conversation history intentionally not preserved — fix agent already gets
  full context through prompt templates
- Estimated effort: 1–2 weeks

### Long-term: Option C (if needed)

- Only justified if workload grows significantly
- Build serialization layer for BeeAI agents, store state in existing Redis
- Depends on framework support

## Open Questions

1. **What is the actual RSS of a backport pod during source processing?**
   Feedback from the SE deployment shows large packages (Firefox, Thunderbird)
   need ~4Gi just for source extraction, making even N=2 concurrency
   challenging. Profiling smaller packages would clarify the typical case.
2. **What's the namespace quota expansion path?** Determines feasibility of
   Option A at higher concurrency.
3. **How large are typical agent conversations?** Affects state size
   estimates and memory profiling for Option A.
