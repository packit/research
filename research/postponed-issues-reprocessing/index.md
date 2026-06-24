# Postponed CVE Issues Reprocessing Plan

## Overview

When Ymir triages a CVE issue, the result may be that the issue is not actionable yet — it gets postponed. This document describes the mechanism for periodically reprocessing postponed issues once blocking conditions are resolved.

## Core Mechanism

### Design Rationale

Jira labels are used as the primary tracking mechanism because they provide efficient JQL queries, require no Jira admin approval, and are already familiar to the team/users. Alternative solutions considered include custom Jira fields (higher API load, requires admin setup), external PostgreSQL database (durable but adds operational complexity), and label swapping for audit trail (fragile, relies on undocumented Jira behavior). The chosen approach uses labels for state, Redis for sweep optimization, and brief comments for human-readable context, balancing simplicity with scalability.

### Labels as Primary Signal

Each postponement reason has a corresponding label:

- `ymir_postponed_dependency` — waiting for a dependency CVE to be fixed
- `ymir_postponed_y_stream` — waiting for Z-stream errata to ship
- `ymir_postponed_no_patch` — no upstream patch found yet
- `ymir_postponed_pr_pending` — patch identified but not yet merged

**Properties:**

- Labels are mutually exclusive (only one postponement reason per issue at a time)
- Labels enable efficient JQL queries for sweep scripts
- Labels are visible in Jira UI for quick status checks

### Brief Comments for Context

Add minimal comment with blocker reference when postponing:

| Category   | Comment Format                                                                                  |
| ---------- | ----------------------------------------------------------------------------------------------- |
| Dependency | `Postponed: dependency CVE not yet fixed\nBlocker: RHEL-54321`                                  |
| Y-stream   | `Postponed: Y-stream - waiting for Z-stream errata\nErrata: RHSA-2026:12345`                    |
| PR pending | `Postponed: waiting for upstream patch to merge\nhttps://github.com/upstream/package/pull/1234` |
| No patch   | `Postponed: no upstream patch available yet`                                                    |

**Update policy:** Only update when postponement reason changes, not on rechecks.

### Postponement State Transitions

Issues can change postponement reasons:

**Example flow:**

1. Initial triage: no patch available → `ymir_postponed_no_patch`
2. Sweep finds patch (not merged) → remove `ymir_postponed_no_patch`, add `ymir_postponed_pr_pending`, update comment with PR URL
3. Sweep finds PR merged → remove `ymir_postponed_pr_pending`, push to triage queue

**Transition logic:**

- Remove old postponement label
- Add new postponement label (if still blocked)
- Update comment with new context
- Reset backoff tracking (if using Redis in Phase 2)

## Sweep Types and Timing

### 1. Dependency CVE Sweep

**What it checks:** Whether the blocking dependency issue now has "Fixed in build" set

**Method:** Jira API field lookup on the blocker issue

**Blocker identification:**

- **Basic (Phase 1):** Parse blocker issue key from comment
- **Optional enhancement:** Use Jira issue links for more robust tracking
  - Option A: Custom "Ymir Dependency" link type (requires Jira admin, enables reverse lookup and event-driven triggers)
  - Option B: Built-in "Blocks" link filtered by `ymir_postponed_dependency` label
  - Benefit: Machine-queryable, robust to comment edits, enables webhook triggers (Phase 3, task 19)

**Base frequency (Phase 1):** Every 6 hours, checks all postponed dependency issues

**Backoff policy (Phase 2):**
| Sweep attempts | Interval |
|----------------|----------|
| 1-3 attempts | 2 hours |
| 4-8 attempts | 6 hours |
| 9-15 attempts | 12 hours |
| 16+ attempts | 24 hours |

**Rationale:** Cheap operation, but dependencies may take days/weeks to fix. Aggressive backoff (Phase 2) prevents wasteful checks on long-blocked issues.

**Action on unblock:** Remove postponement label, push to triage queue with context about which dependency was fixed.

---

### 2. Y-stream CVE Sweep

**What it checks:** Whether the Z-stream errata has shipped

**Method:** Errata Tool API status check

**Base frequency (Phase 1):** Every 12 hours

**Backoff policy (Phase 2):**
| Sweep attempts | Interval |
|----------------|----------|
| 1-4 attempts | 6 hours |
| 5-10 attempts | 12 hours |
| 11+ attempts | 24 hours |

**Rationale:** Z-stream errata ship on a predictable but slow cadence. Backoff (Phase 2) moderates checks for long-pending errata.

**Action on unblock:** Remove postponement label, push to triage queue.

---

### 3. PR Pending Sweep

**What it checks:** Whether the identified upstream PR/commit has been merged

**Method:** GitHub/GitLab API state check

**Base frequency (Phase 1):** Every 8 hours

**Backoff policy (Phase 2):**
| Sweep attempts | Interval |
|----------------|----------|
| 1-5 attempts | 4 hours |
| 6-12 attempts | 8 hours |
| 13-20 attempts | 24 hours |
| 21+ attempts | 48 hours |

**Rationale:** PRs merge at human pace. Backoff (Phase 2) reduces checks for stalled PRs.

**Action on unblock:** Remove postponement label, push to triage queue with PR URL as context.

---

### 4. No Patch Available Sweep

**What it checks:** Whether a new upstream patch is now available

**Method:** Re-run triage agent (expensive operation)

**Base frequency (Phase 1):** Daily (24 hours)

**Backoff policy (Phase 2):**
| Sweep attempts | Interval |
|----------------|-----------|
| 1-3 attempts | 24 hours |
| 4-7 attempts | 3 days |
| 8-14 attempts | 7 days |
| 15+ attempts | 14 days |

**Rationale:** Full triage re-run consumes LLM tokens. Aggressive backoff (Phase 2) essential for cost control.

**Action on finding patch:**

- If patch is merged: remove postponement label, push to triage queue
- If patch exists but not merged: transition to `ymir_postponed_pr_pending`, add PR URL comment

---

## Backoff Optimization with Redis (Optional - Phase 2)

**Why backoff is needed:** Without backoff, all postponed issues are checked on every sweep, even if recently verified as still blocked. This wastes API calls and agent tokens, especially for issues blocked for weeks.

**Redis tracking schema:**

- `attempt_count:{issue.key}` - number of sweep checks
- `last_check:{issue.key}` - timestamp of last check
- `first_postponed:{issue.key}` - timestamp when first postponed

**How backoff works:** Before checking an issue, calculate required interval based on `attempt_count` (see backoff tables per sweep type). Skip check if `now() - last_check < interval`.

**Redis as cache, not source of truth:**

- Jira labels/comments remain authoritative for postponement state
- Redis only optimizes sweep frequency
- Cache miss defaults to `attempt_count=0` (triggers immediate check)

**Recovery from Redis data loss:**

- All postponed issues checked immediately (5-10x temporary spike)
- Backoff state rebuilds naturally over ~12 hours
- No data loss - labels/comments preserved in Jira
- Temporary performance degradation acceptable vs ongoing Jira changelog parsing overhead

### Alternative: Custom Jira Fields for Backoff Tracking

Instead of Redis, use custom Jira fields to track sweep attempts and backoff.

**Custom fields:**

- `ymir_last_recheck` (DateTime) - last sweep timestamp
- `ymir_recheck_count` (Number) - attempt count

**Comparison:**

| Aspect          | Redis (Recommended)                | Custom Field                   |
| --------------- | ---------------------------------- | ------------------------------ |
| Data durability | Lost on restart, 12h recovery      | Always persisted               |
| Jira API load   | Low (updates only on state change) | High (updates every sweep)     |
| Setup           | None (Redis already available)     | Requires Jira admin            |
| Visibility      | Not in Jira UI                     | Visible in Jira, JQL support   |
| Performance     | Fast                               | Slower at scale (1000+ issues) |

**Recommendation:** Use Redis - already available, lower API load, acceptable recovery.

## Example Issue Lifecycle

**Phase 1 behavior (no backoff):**

```
Day 1, 10:00 - Initial triage
└─> Result: Dependency on golang not yet fixed
    Action: + ymir_postponed_dependency
    Comment: "Postponed: dependency CVE not yet fixed\nBlocker: RHEL-54321"

Day 1, 16:00 - Dependency sweep (every 6h)
└─> Check RHEL-54321: still no "Fixed in build"
    No action

Day 1, 22:00 - Dependency sweep
└─> Check RHEL-54321: still no "Fixed in build"
    No action

Day 2, 04:00 - Dependency sweep
└─> Check RHEL-54321: "Fixed in build" is set!
    Action: - ymir_postponed_dependency, push to triage_queue
    Comment: "Dependency RHEL-54321 now fixed, retriaging"
```

**Phase 2 behavior (with backoff):**

```
Day 1, 10:00 - Initial triage
└─> Redis: first_postponed=now, attempt_count=0
    Action: + ymir_postponed_dependency
    Comment: "Postponed: dependency CVE not yet fixed\nBlocker: RHEL-54321"

Day 1, 12:00 - Dependency sweep #1
└─> Check RHEL-54321: still no "Fixed in build"
    Redis: attempt_count=1, last_check=now

Day 1, 14:00 - Dependency sweep #2
└─> Check RHEL-54321: still no "Fixed in build"
    Redis: attempt_count=2, last_check=now

Day 1, 16:00 - Dependency sweep #3
└─> Check RHEL-54321: still no "Fixed in build"
    Redis: attempt_count=3, last_check=now

Day 1, 22:00 - Dependency sweep #4 (backoff now 6h, skipped - only 6h elapsed)
└─> Skip: last_check too recent

Day 2, 04:00 - Dependency sweep #5 (10h elapsed, check now)
└─> Check RHEL-54321: "Fixed in build" is set!
    Action: - ymir_postponed_dependency, Redis delete keys, push to triage_queue
    Comment: "Dependency RHEL-54321 now fixed, retriaging"
```

## Metrics Collection

### Jira Dashboards

Built-in Jira dashboards can track postponement state using labels and JQL filters.

**Recommended gadgets:**

- **Pie Chart** - Postponement reasons distribution (filter: `labels IN (ymir_postponed_*)`, group by labels)
- **Created vs Resolved** - Backlog trend over last 30 days
- **Filter Results** - Current postponed count
- **Recently Unblocked** - Issues that became actionable (filter: `labels WAS ymir_postponed_* AND labels NOT IN (ymir_postponed_*) AND updated >= -7d`)

**What Jira dashboards show:**

- Current backlog size by category
- Historical trends (growth/shrinkage)
- Distribution by component

**What Jira dashboards cannot show:**

- Sweep effectiveness (unblock rate per sweep run)
- Time-to-unblock (how long issues stay postponed)
- Backoff behavior (attempt count distribution)

### Redis Metrics (Optional - Phase 2 only)

**Note:** Redis metrics depend on Phase 2 backoff implementation. If using Phase 1 basic sweeps only, skip this section.

**Why Redis metrics are needed:**

1. **Tune backoff timing** - If dependency sweep has 20% unblock rate, backoff intervals too aggressive
2. **Measure impact** - Know how long issues typically stay postponed before becoming actionable
3. **Identify stuck issues** - Find issues checked 20+ times that may need manual intervention
4. **Resource planning** - Track API calls and agent token usage per sweep type

**Where to publish Redis metrics:**

**Option 1: Dedicated Jira Issue**

Create: **"Ymir Reprocessing Metrics Dashboard"**

Post daily automated comments:

```
=== Metrics for 2026-06-23 ===
Backlog: 88 total (45 dependency, 12 Y-stream, 8 PR, 23 no patch)
Sweep effectiveness (last 7d): Dependency 8.5% (17/200), PR 25.0% (5/20)
Avg time-to-unblock: Dependency 48h, PR 18h
```

**Option 2: Phoenix Trace Server**

Push metrics to Phoenix for visualization and correlation with agent traces. Provides time-series graphs, advanced filtering, and integration with existing observability stack.

---

## Implementation Tasks

### Data Sources Summary

| Signal                   | Source                    | API/Method                                                       |
| ------------------------ | ------------------------- | ---------------------------------------------------------------- |
| Dependency fixed         | Jira                      | `issue.fields.customfield_fixedinbuild` on blocker issue         |
| Errata shipped           | Errata Tool               | `/api/v1/erratum/{id}` status check                              |
| PR merged                | GitHub/GitLab             | `/repos/{owner}/{repo}/pulls/{pr}` state field                   |
| Upstream patch available | Git repositories          | Re-run triage agent with date filter                             |
| Blocker reference        | Jira comment OR Jira link | Parse comment for issue key/URL, or query Jira links             |
| Postponement state       | Jira label                | Query issues with `labels IN (ymir_postponed_*)`                 |
| Sweep attempts           | Redis (Phase 2 only)      | `attempt_count:{issue.key}` and `last_check:{issue.key}`         |
| First postponed time     | Redis (Phase 2 only)      | `first_postponed:{issue.key}` (initialized when first postponed) |

### Phase 1: Basic Implementation (No backoff, no Redis)

Start with simple periodic sweeps that check all postponed issues on every run. This validates the core mechanism before adding optimization complexity.

**1. Triage agent integration**

- Update triage agent to handle postponement flow when issue is not actionable
- Add appropriate postponement label based on reason
- Write brief comment with blocker reference (issue key, errata ID, or PR URL)
- Optionally create Jira issue link for dependency CVEs (see task 1a)

**1a. Investigate Jira issue links for dependency tracking (optional)**

- Check with Jira admin if custom "Ymir Dependency" link type can be created without interfering with existing workflows
- If not feasible, continue using comment parsing
- Document chosen approach for sweep scripts to use

**1b. Label conventions**

- Define labels: `ymir_postponed_dependency`, `ymir_postponed_y_stream`, `ymir_postponed_pr_pending`, `ymir_postponed_no_patch`, `ymir_abandoned`
- Document brief comment format for each category
- Document state transition rules

**2. Sweep framework core**

- Define `SweepStrategy` base class with methods: `get_blocked_issues()`, `is_unblocked(issue)`, `on_unblock(issue)`, `on_transition(issue, new_category)`
- Implement shared logic: error handling, comment management
- Single cron job that runs all strategies in sequence
- Logging per strategy
- Error handling: log and skip issues with malformed comments, deleted blockers, or API failures

**3. Implement DependencySweep strategy**

- Query ALL issues with `ymir_postponed_dependency` label (no backoff yet)
- Parse blocker issue key from comment (or query Jira links if task 1a implemented)
- Check `customfield_fixedinbuild` on blocker issue
- Handle errors: blocker deleted/moved (log warning, keep postponed), API failures (retry next sweep)
- If unblocked: remove label, push to triage queue with context
- If still blocked: no action (will be rechecked next sweep)

**4. Implement YStreamSweep strategy**

- Query ALL issues with `ymir_postponed_y_stream` label
- Parse errata ID from comment, check Errata Tool API
- If unblocked: remove label, push to triage queue
- If still blocked: no action

**5. Implement PRPendingSweep strategy**

- Query ALL issues with `ymir_postponed_pr_pending` label
- Parse PR URL, check GitHub/GitLab API
- If merged: remove label, push to triage queue
- If still blocked: no action

**6. Implement NoPatchSweep strategy**

- Query ALL issues with `ymir_postponed_no_patch` label
- Re-run triage agent
- If patch found and merged: remove label, push to triage queue
- If patch found but not merged: transition to `ymir_postponed_pr_pending`
- If still no patch: no action

**7. Basic cron schedule**

- Dependency sweep: every 6 hours
- Y-stream sweep: every 12 hours
- PR pending sweep: every 8 hours
- No patch sweep: daily

**8. Jira dashboard**

- Create dashboard with pie chart, created vs resolved, filter results
- Add JQL filters for postponed issues and recently unblocked

### Phase 2: Backoff Strategy (Add Redis optimization)

After basic sweeps are working, add backoff to reduce unnecessary checks on long-blocked issues.

**9. Redis tracking schema**

- Define Redis key patterns: `attempt_count:{issue.key}`, `last_check:{issue.key}`, `first_postponed:{issue.key}`
- Initialize keys when issue first postponed
- Clean up keys when issue unblocked

**10. Backoff calculation logic**

- Implement `get_backoff_interval(category, attempt_count)` function using tables from "Sweep Types and Timing"
- Implement `should_check(last_check, interval)` function
- Unit tests for backoff boundaries

**11. Update triage agent**

- Initialize Redis keys when postponing: `first_postponed`, `attempt_count=0`

**12. Update sweep framework core**

- Add backoff checking before processing each issue
- Add Redis updates: increment `attempt_count`, update `last_check`

**13. Update all sweep strategies (3-6)**

- Add Redis tracking on each check (increment attempt_count, update last_check)
- Delete Redis keys on unblock
- Reset `attempt_count` to 0 on state transition (keep `first_postponed`)

**14. Sweep execution tracking**

- Track per-sweep: issues checked, unblocked, skipped (backoff)
- Store in Redis: `sweep_history` list with last 1000 runs
- Track time-to-unblock using `first_postponed`

**15. Metrics dashboard**

- Daily metrics summary: backlog counts, unblock rates, time-to-unblock
- Post to dedicated Jira issue OR push to Phoenix trace server
- Required for backoff efficiency analysis (task 16)

**16. Backoff efficiency analysis**

- Analyze relationship between backoff timing and unblock rate
- Identify if intervals are too aggressive or too conservative
- Adjust backoff tables based on observed data from task 15

### Phase 3: Follow-up Improvements (After observing sweep behavior)

**17. Automatic abandonment threshold**

- Implement after observing data to validate thresholds are appropriate
- Transition issues to "abandoned" status after: `check_count > 30 OR days_postponed > 180`
- Remove postponement label, add `ymir_abandoned` label
- Optional: close issue with resolution "Won't Fix" or keep open with label
- Prevents infinite rechecking of permanently blocked issues
- Add manual override mechanism (remove `ymir_abandoned` label to re-enable sweeps)

**18. Optimize no-patch triage re-runs (if needed)**

- Only after evidence shows frequent re-runs with low success rate
- Only after backoff factors adjusted based on metrics
- Potential optimizations:
  - Agent focuses only on recent commits (date-filtered)
  - Skip components known to have slow patch cycles
  - Lower-cost model for initial patch detection, full model only if promising

**19. Event-driven triggers**

- **Prerequisites:** Requires task 1a (Jira links) to be most effective, but can work with comment parsing
- Create webhook endpoint to receive Jira events
- Configure Jira Automation rule: "When 'Fixed in build' set on any issue" → POST to webhook
- Webhook handler: query Jira links (if available) or search comments for blocker references
- Push dependent issues to high-priority triage queue immediately
- Reduces latency for dependency CVEs from hours to minutes
