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

Several approaches for how users express intent, which can also be combined.

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

### Jira Automation manual trigger with user input form

Jira Cloud Automation supports manual triggers from issues
(the lightning bolt / Actions menu on an issue). When configured with "Prompt for input when
this rule is triggered", a [custom form pops up](https://community.atlassian.com/forums/Automation-articles/Request-input-from-users-when-a-Manual-rule-is-triggered/ba-p/2333587)
before the rule runs.

Supported input field types: short text, paragraph, dropdown, number, checkbox.
Values are referenced in actions via `{{userInputs.variableName}}`.

Example: a "Backport" rule could prompt for "Upstream Fix URL" (short text) and "Target Branch"
(dropdown), then POST these to the event router.

Access can be restricted to specific [permission groups](https://support.atlassian.com/cloud-automation/docs/jira-automation-triggers/#Manual)
("Groups that can run trigger"). Individual fields can be marked as required. Cancelling the
form doesn't count towards monthly automation execution limits.

### Custom Jira fields

Users fill in dedicated Jira fields (e.g., "Upstream Fix URL", "Target Branch") and the system
reads parameters directly from issue fields.

Not explored in depth — seems to have worse UX: users need to know which fields to set, fields
clutter the issue form, and different workflows may need different fields. The `/ymir` CLI
approach is more self-documenting (triage pastes the command with all required flags).

### Comparison

|                | Labels  | `/ymir` CLI            | Manual trigger form    | Natural language  | Custom fields    |
| -------------- | ------- | ---------------------- | ---------------------- | ----------------- | ---------------- |
| **Parameters** | No      | Yes                    | Yes (form fields)      | Yes               | Yes              |
| **Parsing**    | Trivial | Deterministic          | Deterministic          | LLM-dependent     | Deterministic    |
| **UX**         | Simple  | Copy-paste from triage | Click + fill form      | Intuitive         | Must know fields |
| **Pollable**   | Yes     | No (needs label combo) | N/A (automation posts) | No                | Yes              |
| **Auth**       | N/A     | Needs group check      | Built-in group filter  | Needs group check | N/A              |

**CLI vs manual trigger forms**: Manual trigger forms are UI-centric — good for standalone use,
but triage can't paste a one-click follow-up action. With CLI, triage pastes a pre-filled
command that the user copy-pastes to trigger backport/rebase. Both can coexist.

**To decide**: Which to start with — `/ymir` CLI or manual trigger forms (or both).
We should aim for consistency and simple UX.

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

**Comment-based polling** (comment-only, no labels):

If users `@mention` a Ymir service account or post a `/ymir` command in a comment, we could filter it with e.g., `comment ~ "YMIR_ACCOUNT_ID"` or `comment ~ "/ymir"`. This removes the need
for a trigger label but adds complexity:

- No atomic "mark as processed" — with labels, we could remove the label after processing.
  With comments, we must track processed comment IDs in Redis (edits to already-processed
  comments should be ignored — user posts a new comment to correct)
- Result set grows over time, needs time-based filtering (e.g., `AND updated >= -1d`)
  — but `updated` catches any issue update, not just new @Ymir mentions, producing
  false positives that still require comment-by-comment inspection
- API cost scales with active issues: each poll does 1 search + N comment fetches, rate limiting?

**Implementation**:

- Labels + comments: change JQL, build `/ymir` parser, add polling loop, fetch comments for labeled issues
- Comment-based polling: same, plus comment ID tracking in Redis, time-based JQL filtering

| Pro                   | Con                                                       |
| --------------------- | --------------------------------------------------------- |
| No new infrastructure | 30-60s latency                                            |
| All in code           | Labels + comments: two-step UX (comment + label)          |
|                       | Comment-based: complex dedup (no atomic "mark processed") |

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
to detect events and POST to an external endpoint. Two sub-options for user input:

**C1: Comment-triggered rules** (pairs with `/ymir` CLI commands)

- Rule: "Work item commented" + condition `comment contains /ymir` → "Send web request"
- User posts `/ymir backport --upstream-fix <URL> --branch <branch>` as a comment
- Triage agent can paste the pre-filled command for copy-paste triggering

**C2: Manual trigger with input form** (Jira-native UI)

- Rule: "Manual trigger from work item" with "Prompt for input" enabled
- User clicks Actions → "Ymir Backport" on the issue, fills in a form (upstream fix URL,
  target branch), and submits → rule POSTs to event router
- Access restricted via "Groups that can run trigger" (built-in auth)
- No comment syntax to learn — fully guided UI

Both can coexist: e.g., manual trigger forms for new users, `/ymir` commands for power users
or automation. The event router receives the same payload shape either way.

It seems like other teams/automations utilise this too, e.g. Watson automation.

**Permissions**: **Project admins** can create automation rules for their projects. No global admin needed — more accessible/simpler to configure than webhooks.

**Implementation**:

- New `event_router/` service (simpler — payloads pre-filtered by Jira)
- Configure automation rules in Jira Cloud UI (project admin can do this)
- Set up HTTPS endpoint
- For C1: build `/ymir` command parser
- For C2: configure input forms in Jira Automation rule UI

| Pro                                     | Con                    |
| --------------------------------------- | ---------------------- |
| Project admins can set up               | Not version-controlled |
| Pre-filtered events                     | HTTPS endpoint needed  |
| More reliable than webhooks             |                        |
| C2: built-in auth + guided input forms  | C2: form config in UI  |
| C1: triage can paste pre-filled command | C1: syntax to learn    |

---

### Options Summary

|                         | Polling (labels)   | Polling (comments)                | Webhooks           | Automation         |
| ----------------------- | ------------------ | --------------------------------- | ------------------ | ------------------ |
| **Jira permissions**    | API access         | API access                        | Global admin       | Project admin      |
| **Comments standalone** | No                 | Yes                               | Yes                | Yes                |
| **Latency**             | 30-60s             | 30-60s                            | Sub-second         | Seconds            |
| **Dedup complexity**    | Low (remove label) | High (track comment IDs)          | Low (event-driven) | Low (event-driven) |
| **Infrastructure**      | None new           | None new                          | HTTPS endpoint     | HTTPS endpoint     |
| **New code**            | Extend fetcher     | Extend fetcher + comment tracking | Event router       | Event router       |

---

## Security Considerations

- **Unauthorized triggering**: External users with Jira access could post `/ymir` commands or put labels.
  With CLI (C1): event router must check comment author's group membership via Jira API.
  With manual trigger forms (C2): built-in "Groups that can run trigger" handles this natively
  in Jira — no custom auth code needed.

- **Prompt injection via `--instructions`**: Malicious instructions could manipulate the LLM agent.
  Mitigations: input length limits, system prompt hardening, group membership check.
  With manual trigger forms (C2), input fields have defined types (short text, dropdown) which
  limits the attack surface compared to free-form comments.

---

## Implementation Tasks

The following changes are needed regardless of triggering option and user input method.
With manual trigger forms (C2), the command parser is replaced by form payload handling.

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

**Deployment**:

- New container in OpenShift, Service + Route
- Route must be publicly reachable for Jira Cloud — requires external namespace and route config
- Auth: shared secret token in a custom HTTP header, configured in the Jira Automation rule and validated by the event router. Combined with Jira-side "Groups that can run
  trigger" restriction.
- WAF could be placed in front of the route as well
- More details: https://source.redhat.com/departments/strategy_and_operations/it/datacenter_infrastructure/itcloudservices/itocp/itocp_wiki/tenant_onboarding_and_administration~23#application-ingress

### Other changes

- **Rename jotnar → ymir**: labels, constants, JQL defaults, compose service names, Jira migration
- **Jira issue fetcher**: based on the decision, add polling loop (currently one-shot), extend JQL for trigger labels
- **Branch-specific queue routing**: move `get_*_queue_for_branch` logic from triage to event router

---

## Summary of Trade-offs

_To be agreed on with the team._

**Comment-based polling**:

- Simpler to start with, no new service
- Extend existing fetcher — no new infra or HTTPS endpoint
- Example JQL: `comment ~ "YMIR_ACCOUNT_ID" AND updated >= -1d AND project = RHEL`
- Deduplication is the main challenge, see in the related sections
- Result set grows — even with time filtering, issues re-appear if they get any update. Each poll must re-check comments on returned issues.
- Latency: 30-60s
- Rate limits: each poll fetches issues, then comments per issue — API cost scales with
  number of active issues mentioning @Ymir or /ymir (based on the format we decide)

**Automation Rules** (new event router service):

- Event-driven — no dedup needed (each trigger fires once)
- Lower latency (seconds)
- Requires HTTPS endpoint (trivial on OpenShift with Routes, blocker otherwise)
- Project admins can configure rules
- C1 (comment-triggered) + C2 (manual trigger form) both work through same event router
- Not version-controlled (rules live in Jira UI)

**User input**: `/ymir` CLI (C1) is more flexible — triage can paste pre-filled commands,
easy to script. Manual trigger forms (C2) have lower barrier — no syntax, built-in auth.
Both can coexist and use the same event router.

### Agreements

- **Triggering**: Event-driven (Automation Rules + event router service), with polling retained as fallback
- **User input**: Manual trigger forms with optional fields + natural language fallback
  (form fields left empty → agent extracts parameters from free-text using LLM)
- **Event router**: New lightweight service, shared secret auth, external route
- **Jira Automation rules**: One rule per workflow (triage, backport, rebase) with
  manual trigger from work item
- **Agent changes**: Decouple triage from downstream routing, backport/rebase accept
  direct input from event router. Auto-chain kept in code but disabled by default.
- **Labels**: Keep for status tracking (in-progress/completed/failed)
- **Fix Version/Severity**: Keep but make optional, or wait for feedback from early adopters
