---
title: Ymir triggering rearchitecture
authors: lbarcziova
---

## Context

Currently, `jira_issue_fetcher` polls Jira for issues assigned to the jotnar user, pushes them
to a Redis `triage_queue`, and the triage agent automatically routes to backport/rebase queues.
We want to decouple the workflows so each can be triggered independently via user actions in Jira,
with support for user-provided input (upstream fix, branch, etc.).

## User Input Options

Four approaches for how users express intent, which can also be combined.

### Labels

Users add a label (e.g., `ymir-triage`, `ymir-backport`) to the Jira issue.

- Simple, no syntax to learn
- Cannot carry parameters — only signals intent (no branch, URL, instructions)
- Sufficient for triage (no input needed) but not for backport/rebase
- Can be combined with comments: label triggers the workflow, a comment or Jira fields
  provide the parameters

### `/ymir` CLI-style commands (in Jira comments)

```
/ymir backport --upstream-fix <URL> --branch <target-branch> [--instructions "..."]
/ymir rebase --version <upstream-version> --branch <target-branch> [--instructions "..."]
/ymir triage
```

Triage agent would paste the pre-filled command in its output for copy-paste triggering.

### Natural language comments

Users write free-form text like _"@ymir-agent please backport commit abc123 to rhel-9.6.0"_ and the system
uses an LLM to extract intent and parameters.

### Custom Jira fields

Users fill in dedicated Jira fields (e.g., "Upstream Fix URL", "Target Branch") and the system
reads parameters directly from issue fields.

Not explored in depth — seems to have worse UX: users need to know which fields to set, fields
clutter the issue form, and different workflows may need different fields. The `/ymir` CLI
approach is more self-documenting (triage pastes the command with all required flags).

### Comparison

|                | Labels  | `/ymir` CLI            | Natural language | Custom fields    |
| -------------- | ------- | ---------------------- | ---------------- | ---------------- |
| **Parameters** | No      | Yes                    | Yes              | Yes              |
| **Parsing**    | Trivial | Deterministic          | LLM-dependent    | Deterministic    |
| **UX**         | Simple  | Copy-paste from triage | Intuitive        | Must know fields |
| **Pollable**   | Yes     | No (needs label combo) | No               | Yes              |

**Recommendation, to agree on**: Start with `/ymir` CLI commands for backport/rebase (where parameters are needed).
Labels could be used for triage (no input needed) or as a simpler alternative trigger if parameters
are stored in Jira fields. But we should aim for consistency, simple UX.

---

## Triggering Options

### Option A: Polling

Extend `jira_issue_fetcher` to poll Jira periodically for trigger labels.

**Labels only** (for triage or workflows without parameters):
JQL supports `labels = "ymir-triage"` etc. Poll every 30-60s.

**Labels + comments** (for backport/rebase with parameters):
Label triggers the workflow; a `/ymir` command in a comment provides parameters.

- Poll for trigger labels via JQL
- Once a labeled issue is found, fetch its comments and parse the `/ymir` command
- Comment fetching is scoped to labeled issues only — avoids scanning all issues

Note: Polling for comments standalone (without labels) is not feasible — there's no
JQL filter for comment content, so it would require fetching and inspecting comments
on every issue.

**Implementation**:

- Change JQL to filter by trigger labels
- Build `/ymir` command parser
- Add polling loop (currently one-shot)
- Fetch comments only for labeled issues

| Pro                   | Con                           |
| --------------------- | ----------------------------- |
| No new infrastructure | 30-60s latency                |
| All in code           | Two-step UX (comment + label) |

---

### Option B: Jira Cloud Webhooks

Register [Jira Cloud webhooks](https://developer.atlassian.com/cloud/jira/platform/webhooks/)
for `comment_created` and `issue_updated` events. A new event router service receives the
POST payloads, parses `/ymir` commands or label changes, and routes to Redis queues.

**Permissions**: Seems to require **Administer Jira** global permission to create webhooks — not
available to project admins. Might require coordination with Jira administrators. TODO: get more info if needed

**Implementation**:

- New `event_router/` service: HTTP endpoint, webhook payload parsing, command parser, queue routing
- Register webhooks in Jira Cloud (requires global admin)
- Set up publicly-reachable HTTPS endpoint
- Deduplication in Redis
- Remove routing logic from triage agent, replace with `/ymir` command in output

| Pro                        | Con                        |
| -------------------------- | -------------------------- |
| Real-time (sub-second)     | Requires global Jira admin |
| No API quota for detection | Best-effort delivery       |
|                            | HTTPS endpoint needed      |

---

### Option C: Jira Automation Rules

Use Jira's built-in [Automation](https://www.atlassian.com/software/jira/guides/automation/overview#board-vs-project)
to detect comment/label events and POST to an external endpoint.

Rule examples:

- Rule: "Work item commented" + condition `comment contains /ymir` → "Send web request"
- Rule: "Field value changed" (Labels) + condition matches `ymir-*` → "Send web request"

It seems like other teams/automations utilise this too, e.g. Watson automation.

**Permissions**: **Project admins** can create automation rules for their projects. No global admin needed — more accessible/simpler to configure than webhooks.

**Implementation**:

- New `event_router/` service (simpler — payloads pre-filtered by Jira)
- Configure automation rules in Jira Cloud UI (project admin can do this)
- Set up HTTPS endpoint
- Build `/ymir` command parser

| Pro                         | Con                    |
| --------------------------- | ---------------------- |
| Project admins can set up   | Not version-controlled |
| Pre-filtered events         | HTTPS endpoint needed  |
| More reliable than webhooks |                        |

---

### Options Summary

|                         | Polling        | Webhooks       | Automation     |
| ----------------------- | -------------- | -------------- | -------------- |
| **Jira permissions**    | API access     | Global admin   | Project admin  |
| **Comments standalone** | No             | Yes            | Yes            |
| **Latency**             | 30-60s         | Sub-second     | Seconds        |
| **Infrastructure**      | None new       | HTTPS endpoint | HTTPS endpoint |
| **New code**            | Extend fetcher | Event router   | Event router   |

---

## Security Considerations

- **Unauthorized triggering**: External users with Jira access could post `/ymir` commands or put labels.
  Mitigation: check comment author's Jira group membership before processing. For labels might be more complicated.

- **Prompt injection via `--instructions`**: Malicious instructions could manipulate the LLM agent.
  Mitigations: input length limits, system prompt hardening, group membership check.

---

## Implementation Tasks

_This section assumes `/ymir` CLI commands as the user input method. Some tasks differ if
using labels-only or custom fields._

The following changes are needed regardless of triggering option (polling vs automation).

### Triage agent: decouple from downstream routing

The default behavior should change: triage posts a Jira comment with a pre-filled `/ymir`
command instead of automatically routing to downstream queues. The auto-chain code
could be kept but disabled by default — it can be useful for local/standalone
runs or potentially re-enabled in the future.

The triage LLM also currently sets Jira fields (Fix Version, Severity) via `set_jira_fields`
— needs decision on whether to keep this behavior.

### Backport/rebase agents: new input schemas

Currently both agents depend on triage state (`triage_state["triage_result"]["data"]`). With
independent triggering, most input comes directly from the `/ymir` command:

- `upstream_patches` / `version` → from `--upstream-fix` / `--version` flag
- `dist_git_branch` → from `--branch` flag (no longer mapped from `fix_version` by triage)
- `jira_issue` → from the Jira issue where the command was posted
- `package` → derivable from the Jira issue's component field (event router fetches it)
- `cve_id` → probably derivable from the Jira issue's fields

### Labels

Labels are currently used for two distinct purposes:

1. **Deduplication/state tracking** — the fetcher checks for `jotnar_*` labels to skip
   already-processed issues and detects `jotnar_retry_needed` for re-triggering
2. **Status visibility** — users can see at a glance what state an issue is in

Needs decision on whether to keep, simplify, or replace.

### Event router service (new, for automation/webhooks)

A lightweight HTTP service that receives POST requests from Jira and routes to Redis queues.

**Components**:

- HTTP endpoint (e.g., FastAPI) to receive Jira automation/webhook payloads
- `/ymir` command parser — extract action, flags, and parameters from comment text
- Author validation — check Jira group membership before processing
- Queue routing — push to appropriate Redis queue based on action and branch
- Acknowledgment — post a Jira comment confirming the command was received
- Deduplication — track processed commands to avoid re-processing on retries

**Deployment**: New container in OpenShift/compose, Service + Route (same pattern as Phoenix),
environment config for Redis connection and Jira credentials.

### Other changes

- **Rename jotnar → ymir**: labels, constants, JQL defaults, compose service names, Jira migration
- **Jira issue fetcher**: based on the decision, add polling loop (currently one-shot), extend JQL for trigger labels
- **Branch-specific queue routing**: move `get_*_queue_for_branch` logic from triage to event router

---

## Preliminary Recommendation

_To be agreed on with the team._

**Triggering**: Automation seems simpler than webhooks (project admins can configure, no global
admin needed) and likely sufficient. Both require a new **event router service** — an HTTP
server that receives POST requests from Jira, parses the input, validates the author, and
pushes to the appropriate Redis queue. This would run alongside existing agents and reuse the
queue infrastructure.

Webhooks not yet explored in depth — revisit if Automation proves insufficient.

**Polling as fallback**: Even with automation as primary trigger, polling can remain for missed
events or retries via a `ymir-retry` label.

**User input**: `/ymir` CLI commands seem like a good fit for parameterized workflows (backport,
rebase) — deterministic parsing, triage can paste pre-filled commands. For triage itself,
either labels or `/ymir triage` could work. Need to decide on consistency vs simplicity.

### To decide

- [ ] User input method: `/ymir` CLI, labels, or combination?
- [ ] Triggering mechanism: Automation (alternatively webhooks, look into that more) or start with polling?
- [ ] Keep labels for status tracking (in-progress/completed/failed)?
- [ ] Should triage still set Fix Version/Severity, or leave to user?
- [ ] Keep triage auto-chain in code (disabled by default, not breaking SE)?
