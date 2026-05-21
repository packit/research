# MR Consolidation Strategy

## Overview: Two Consolidation Scenarios

This research addresses two distinct MR consolidation scenarios for Ymir agents:

### Scenario 1: Incremental Multi-Issue Consolidation (Manual)

**Problem**: Multiple separate CVE/bug issues for the same package+fixVersion arrive at different times, each creating separate MRs that could be consolidated.

**Example**:

- RHEL-1000: CVE-2024-1234 in openssl-9.8.0
- RHEL-2000: CVE-2024-5678 in openssl-9.8.0
- RHEL-3000: CVE-2024-9012 in openssl-9.8.0

Each has a different upstream patch, but maintainer wants single consolidated MR.

**Solution**: Manual incremental consolidation using `ymir_consolidate_base` and `ymir_consolidate_next` labels to stack MRs sequentially.

### Scenario 2: Multi-CVE Single-Patch Consolidation (Automatic)

**Problem**: A single upstream patch addresses multiple CVEs at once, but each CVE has a separate downstream Jira issue. Without consolidation, the agent would create duplicate backport MRs for the same patch.

**Example**:

- Upstream commit fixes CVE-2024-1234, CVE-2024-5678, CVE-2024-9012 in one patch
- Downstream has RHEL-1000, RHEL-2000, RHEL-3000 (one per CVE)
- Agent triggered on RHEL-1000 should detect RHEL-2000 and RHEL-3000 are siblings

**Solution**: Automatic triage-time detection that parses upstream commit message, finds related downstream issues, and consolidates into single MR with `Resolves: RHEL-1000, RHEL-2000, RHEL-3000`.

---

## Scenario 1: Incremental Multi-Issue Consolidation

### Key Requirements

1. **Unblocking**: If a MR is not doable by our agents (for any reason), we need a way to skip it without being blocked
2. **Flexibility**: Users can easily change their mind and decide for a different approach
3. **Urgency**: This is an important topic holding us back - we should lean toward the easiest/quickest way to resolve it and iterate later

### Approaches Considered

**Incremental (Recommended)**: Modify backport agent to stack MRs incrementally using `consolidate_base` and `consolidate_next` labels.

**Triage-Time (Plan A)**: Consolidate issues at triage time, similar to existing rebuild consolidation pattern.

**Batch Consolidation (Plan C)**: Build separate consolidation agent that rebases all marked MRs at once into single MR.

**Dynamic Stacking (Plan B)**: Automatically detect existing MRs and stack new patches on shared branch.

**Parent Issue (Plan E)**: Create parent Jira issue to orchestrate and track consolidation with maintainer approval.

**Hybrid (Plan D)**: Combine multiple approaches with per-package configuration policy.

### Comparison Table

| Approach                      | Effort    | Flexibility         | Unblocking    | Composable | Best For         | Complexity |
| ----------------------------- | --------- | ------------------- | ------------- | ---------- | ---------------- | ---------- |
| **Incremental (RECOMMENDED)** | **Low**   | ✅ High             | ✅ Easy skip  | ✅ Yes     | **2-4 issues**   | **Low**    |
| Triage-Time (Plan A)          | Low       | ❌ Locked at triage | ⚠️ Limited    | ❌ No      | Same-time issues | Low        |
| Batch Consolidation (Plan C)  | Medium    | ❌ All-or-nothing   | ❌ Blocks all | ❌ No      | 5+ issues        | High       |
| Dynamic Stacking (Plan B)     | High      | ⚠️ Medium           | ⚠️ Medium     | ❌ No      | Automatic        | Very High  |
| Parent Issue (Plan E)         | High      | ✅ High             | ✅ Good       | ⚠️ Partial | With approval    | Medium     |
| Hybrid (Plan D)               | Very High | ✅ Configurable     | ✅ Good       | ⚠️ Partial | All scenarios    | Very High  |

**Key Insights**:

- Incremental consolidation is **composable** - can add orchestrator later (Phase 2: Low effort) for automated batch-like experience. Total effort remains Low-Medium for full automation, but phased deployment reduces risk.
- Supports **cross-type consolidation** - backport and rebuild issues for the same package+fixVersion can be consolidated into a single MR.

### Recommended Solution: Incremental Consolidation

**Use two Jira labels to enable step-by-step consolidation:**

- **`consolidate_base`** - Marks the current "base" issue (whose MR branch others build on)
- **`consolidate_next`** - Marks the next issue to consolidate on top of base

**How it works:**

1. RHEL-1000 → normal backport → MR1 created
2. Mark RHEL-1000 with `consolidate_base`
3. Mark RHEL-2000 with `consolidate_next`
4. Backport agent forks from MR1's branch (not c9s), applies patch
5. MR2 created (contains both patches), MR1 closed, base label moves to RHEL-2000
6. Repeat: mark RHEL-3000 with `consolidate_next`, it builds on MR2
7. Final MR contains all consolidated patches

**Cross-type consolidation (backport + rebuild):**

When a backport also resolves a rebuild issue (same package+fixVersion), they can be consolidated:

1. RHEL-1000 (backport) → MR1 created with backported patch
2. RHEL-2000 (rebuild) exists for same package+fixVersion
3. Mark RHEL-1000 with `consolidate_base`
4. Mark RHEL-2000 with `consolidate_next`
5. Rebuild agent runs on RHEL-2000, forks from MR1's branch
6. Applies rebuild changes on top of backport
7. MR2 created (contains both backport patch AND rebuild), MR1 closed
8. Single MR resolves both RHEL-1000 and RHEL-2000

**Note**: The backport typically includes the fix that would necessitate the rebuild, so the consolidated MR contains both the patch and any additional rebuild-specific changes (spec file updates, changelog, etc.).

**Why this wins:**

- ✅ **Low Effort**: Modifies existing backport agent, no new infrastructure
- ✅ **Flexible**: Skip conflicting issues, reorder, partial consolidation
- ✅ **Cross-type consolidation**: Supports backport + rebuild in single MR
- ✅ **Unblocking**: Conflicts don't break everything - just skip that issue
- ✅ **Composable**: Can add orchestrator later for automation (see Evolution Path below)
- ✅ **Low Risk**: Reuses battle-tested backport agent code
- ✅ **Low Complexity**: No complex git rebasing logic to build

**Accepted tradeoffs (for MVP - minimum viable product):**

- Sequential/manual process (maintainer triggers each issue)
- Multiple CI runs (one per issue)
- Some closed MRs (intermediate consolidations)

All acceptable for 2-4 issue consolidations (most common case) and easily automated later in Phase 2.

---

## Recommended Approach Details

### Evolution Path: Composable Architecture

**MVP (Minimum Viable Product)**: The simplest implementation that delivers core value and allows learning from real usage. For this project, Phase 1 is the MVP - it enables manual consolidation with minimal changes, proving the approach works before investing in automation.

The incremental approach has clean separation of concerns, enabling phased deployment:

```
Phase 1: Manual Incremental (MVP - Low Effort)
  ├─ Modify backport agent to support consolidate_base/consolidate_next
  ├─ Maintainer manually applies labels
  └─ Proves consolidation works, gathers data

Phase 2: Add Orchestrator (Optional - Low Effort)
  ├─ Option A: Simple label-based (consolidate_batch)
  │   └─ Auto-applies labels in sequence
  │
  └─ Option B: Parent Jira issue (suggested in PACKIT-4998)
      ├─ Creates PACKIT parent ticket for orchestration
      ├─ Maintainer can review/approve before MR creation
      ├─ Better visibility and control for complex consolidations
      └─ Supports custom ordering, add/remove issues, special instructions
```

**Total: Low-Medium effort for fully automated solution, deployed in low-risk phases**

**Phase 2 decision based on data:**

- Simple consolidations (2-3 issues): Option A sufficient
- Complex consolidations (5+ issues, need control): Option B provides more value

### Phase 1 Implementation Plan (Low Effort)

#### 1. Modify Backport and Rebuild Agents

**Location**: `ymir/agents/backport.py` and `ymir/agents/rebuild.py`

**Key changes (apply to both agents):**

1. **Detect consolidation mode**: Check for `consolidate_next` label
2. **Find base branch**: If triggered, search for issue with `consolidate_base` label (same package+fixVersion)
3. **Fork from base**: Use base MR's branch instead of target branch (c9s/c8s)
4. **Validate base MR**: Must be opened, branch must exist
5. **Post-consolidation cleanup**:
   - Close old base MR
   - Move `consolidate_base` label from old → new issue
   - Remove `consolidate_next` label
   - Update new MR description to list all consolidated issues

**Cross-type consolidation**: This enables backport + rebuild consolidation. Example: backport MR exists for RHEL-1000, rebuild needed for RHEL-2000 (same package+fixVersion) → mark backport as `consolidate_base`, rebuild as `consolidate_next` → rebuild agent forks from backport branch → single MR resolves both issues.

```python
def determine_base_branch(issue: JiraIssue, target_branch: str) -> tuple[str, bool]:
    """Determine which branch to fork from for backport."""
    if 'consolidate_next' not in issue.labels:
        return (target_branch, False)  # Normal flow

    base_issue = find_consolidation_base(issue.package, issue.fix_version)
    if not base_issue:
        raise ConsolidationError("No consolidate_base found. Mark one issue first.")

    base_mr = find_mr_for_issue(base_issue.key)
    validate_base_mr(base_mr)  # Check opened, branch exists

    return (base_mr.source_branch, True)  # Consolidation mode
```

#### 2. Error Handling

- No base found → clear error, suggest marking base first
- Multiple bases found → error, ask to remove duplicate
- Base MR closed/merged → error, cannot consolidate
- Patch conflict → existing conflict handling works, don't close base MR
- Add warning label to base MR: "DO-NOT-MERGE-CONSOLIDATION-IN-PROGRESS"

#### 3. Testing & Documentation

- Update CLAUDE.md with workflow guide
- Maintainer documentation

**Total Phase 1 Effort: Low**

### Phase 2: Orchestrator (Optional, Low Effort)

**When to build**: If data shows manual process is tedious (many 5+ issue consolidations)

#### Two Orchestrator Approaches

**Option A: Simple Label-Based (Lower Effort)**

New label: `consolidate_batch` - triggers orchestrator to auto-consolidate all related issues

```python
def orchestrate_consolidation(trigger_issue: JiraIssue):
    """Auto-consolidate all issues with same package+fixVersion."""
    candidates = find_issues(trigger_issue.package, trigger_issue.fix_version)
    candidates.sort(key=lambda i: i.key)  # Deterministic order

    # Apply consolidate_base and consolidate_next sequentially
    for issue in candidates[1:]:
        add_label(issue, 'consolidate_next')
        wait_for_backport_completion(issue)
```

**Option B: Parent Jira Issue (Suggested in PACKIT-4998 - More Powerful)**

Create a parent PACKIT ticket to orchestrate and track consolidation:

```
Project: PACKIT
Type: "CVE Consolidation"
Title: "Consolidate fixes for {package} {fixVersion}"
Links: All RHEL issues to be consolidated
```

**Why Parent Issue Approach is Better (per PACKIT-4998 discussion):**

1. **Pre-MR Maintainer Control**: Maintainer can review and approve the consolidation plan BEFORE any MR is created
   - See which issues will be consolidated together
   - Add/remove issues if triage missed something
   - Specify order of patches (comment: "apply RHEL-1000 before RHEL-2000")
   - Add special handling instructions

2. **Clear Audit Trail**: Single place to track entire consolidation lifecycle
   - Pending approval
   - Consolidation in progress
   - Which issues succeeded/failed
   - Final MR link
   - Build status

3. **Better Communication Channel**: Maintainer can influence agent behavior
   - Comment specific requirements: "Skip RHEL-X if conflicts"
   - Request retry after fixing upstream issue
   - Provide context that helps agent make better decisions

4. **Flexible Approval Workflow**:
   - Maintainer sets label/field/comment to approve: "ymir_approved"
   - If no reply in X days: auto-proceed (avoid blocking)
   - Can decline: remove issues or close parent ticket

5. **Future Extension Point**: Parent issue becomes interface for advanced features
   - Custom patch ordering
   - Conditional consolidation rules
   - Integration with sprint planning
   - Batch operations across multiple packages

**Implementation:**

```python
def create_consolidation_parent(issues: list[JiraIssue]) -> JiraIssue:
    """Create parent PACKIT issue for consolidation orchestration."""
    parent = jira.create_issue(
        project="PACKIT",
        issuetype="CVE Consolidation",
        summary=f"Consolidate {len(issues)} fixes for {package} {fix_version}",
        description=f"""
# Consolidation Plan

Ymir detected {len(issues)} related issues:
{'\n'.join(f'- {i.key}: {i.summary}' for i in issues)}

**Maintainer Actions:**
- Review the list above
- Add/remove issues by linking/unlinking
- Add comments for special handling (order, skip on conflict, etc.)
- Approve by setting label: ymir_approved
- Or wait {timeout} days for auto-approval

Ymir will then consolidate these into a single MR incrementally.
        """
    )

    # Link all child issues
    for issue in issues:
        jira.create_link("Consolidates", parent.key, issue.key)

    # Notify maintainer
    mention_maintainer(parent)

    return parent

def orchestrate_via_parent_issue(parent: JiraIssue):
    """Run consolidation based on parent issue."""
    # Wait for approval or timeout
    if not wait_for_approval(parent, timeout_days=3):
        comment(parent, "Auto-proceeding after timeout")

    # Get linked issues (may have changed since creation)
    issues = get_linked_issues(parent)

    # Check for ordering instructions in comments
    order = parse_ordering_instructions(parent) or sort_by_key(issues)

    # Run incremental consolidation
    for i, issue in enumerate(order):
        if i == 0:
            add_label(issue, 'consolidate_base')
        else:
            add_label(issue, 'consolidate_next')
            result = wait_for_backport_completion(issue)
            update_parent_status(parent, issue, result)
```

**Why This is Still Low Effort:**

- Reuses Phase 1 incremental consolidation (all git logic done)
- Just adds Jira issue creation and orchestration logic
- Parent issue is optional enhancement - Phase 1 works without it

**Tradeoff vs Label Approach:**

- **More Jira complexity** (against Desktop team preference from PACKIT-4998)
- **More maintainer value** (control, visibility, communication)
- **Better for complex scenarios** (5+ issues, special requirements)

**Recommendation**: Start with Phase 1, then decide:

- If most consolidations are simple (2-3 issues): Add Option A (label-based)
- If complex consolidations are common (5+ issues, need control): Add Option B (parent issue)

---

## Appendix: Alternative Approaches

### Plan A: Triage-Time Consolidation

**Approach**: Consolidate at triage time (like existing rebuild consolidation)

The triage agent would find backport siblings (same package+fixVersion) and pack them into a single consolidated task. The backport agent would then apply all patches in one run and create a single MR. This mirrors the existing `find_rebuild_siblings()` pattern.

**Pros**: All data upfront, single CI run, follows established pattern
**Cons**: Only consolidates issues triaged together, later CVEs create separate MRs

**Effort**: Low
**Rejected because**:

- No flexibility to consolidate issues arriving at different times (locked in at triage)
- Cannot skip problematic issues after triage (all-or-nothing per triage batch)
- Compared to incremental: less flexible, no post-triage consolidation, no way to adjust after seeing conflicts

### Plan B: Dynamic MR Stacking

**Approach**: Auto-detect existing MRs and stack new patches on shared branch

Each backport run checks if an open MR already exists for the package+branch, and if found, stacks new patches on top of it automatically. Uses shared branch naming (`ymir-{PACKAGE}-{BRANCH}` instead of `ymir-{ISSUE}`). No explicit labels needed - consolidation happens automatically.

**Pros**: Automatic, handles CVEs over time
**Cons**: Very complex, risky (could break working MRs), hard to attribute failures

**Effort**: High
**Rejected because**:

- Too complex, too risky for value gained
- Not composable (fully automatic, no manual mode for MVP/learning phase)
- Risk of breaking MRs already in review or with CI running
- Compared to incremental: much higher complexity (High vs Low), no control over consolidation, harder to debug failures, higher risk to existing workflow

### Plan C: Batch Consolidation (Maintainer-Driven)

**Approach**: Build separate consolidation agent that rebases all MRs at once

Create a new consolidation agent that finds all open MRs marked for consolidation (same package+branch), fetches their patches, rebases them together onto the target branch, and creates a single consolidated MR. Triggered by maintainer action (label or comment). All candidate MRs are processed in one batch operation.

**Pros**: Clean final result (1 MR), faster for large batches
**Cons**: Monolithic, all-or-nothing, can't skip mid-batch

**Effort**: Medium
**Rejected because**:

- Not composable (cannot decompose into manual MVP + automation phases)
- All-or-nothing failure mode (single conflict breaks entire consolidation)
- Higher effort than incremental for MVP (Medium vs Low)
- Compared to incremental: monolithic architecture, cannot skip problematic issues, no phased deployment, requires building complex git rebasing logic from scratch vs reusing existing backport agent

### Plan D: Hybrid with Per-Package Config

**Approach**: Combine Plan A + C with per-package policy configuration

Implement both triage-time (Plan A) and batch consolidation (Plan C) approaches, then allow per-package configuration to choose behavior: `"auto"` for triage-time, `"manual"` for batch, or `"separate"` for no consolidation. Configuration stored in `rhel-config.json` and checked by triage agent. Allows teams to opt-in gradually based on their workflow needs.

**Pros**: Very flexible, teams choose what works
**Cons**: Most complex, maintains two paths

**Effort**: Very High
**Rejected because**:

- Premature optimization (builds multiple approaches before validating any)
- Requires maintaining two separate consolidation code paths
- Very High effort (7-10 days) vs Low for incremental
- Compared to incremental: extremely high complexity, requires upfront decisions without data, no phased learning, builds infrastructure for uncertain use cases vs incremental's learn-as-you-go approach

### Plan E: Parent Issue Orchestration

**Approach**: Create parent Jira issue to group and coordinate consolidation

Triage agent creates a PACKIT parent ticket linking all related CVE issues for consolidation. Maintainer reviews the parent issue, can add/remove linked issues, specify patch ordering via comments, and approves via label or auto-proceeds after timeout. The orchestrator then runs incremental consolidation based on the approved plan. Provides pre-MR visibility and control.

**Pros**: Clear audit trail, maintainer approval workflow, pre-MR control
**Cons**: More Jira complexity (against Desktop team preference), adds latency

**Effort**: High
**Status**: Not rejected - incorporated as **Phase 2 Option B** (see "Phase 2: Orchestrator" section above).

**Why not MVP (compared to incremental Phase 1)**:

- Higher effort upfront (High vs Low for Phase 1)
- Adds Jira complexity before validating core consolidation workflow
- Requires building orchestration + parent issue infrastructure before proving incremental consolidation works
- Incremental approach enables learning consolidation patterns first, then adding orchestration layer in Phase 2 based on real data

**Value as Phase 2**: After Phase 1 proves incremental consolidation works, parent issue approach provides superior maintainer control and visibility per PACKIT-4998 discussion. Particularly useful for complex consolidations (5+ issues) where pre-MR review and approval workflow adds significant value.

---

## Current State

**Existing consolidation**:

- ✅ Rebuild consolidation exists at triage time (`find_rebuild_siblings()`)
- ✅ Branch naming: `ymir-{JIRA_ISSUE}`
- ✅ MR reuse logic exists (handles 409 conflicts)

**Not implemented**:

- ❌ Backport consolidation (single or multi-issue)
- ❌ Cross-type consolidation (backport + rebuild in one MR)

**What this solution enables**:

- ✅ Incremental consolidation for backports (Phase 1)
- ✅ Cross-type consolidation: backport + rebuild in single MR (Phase 1)
- ✅ Automated orchestration (Phase 2, optional)

**Key Feedback from PACKIT-4998**:

- **Parent issue approach**: Suggested with maintainer approval before MR creation. Benefits: pre-MR control, ability to adjust issues/ordering, clear audit trail, communication channel for special instructions.
- **Desktop Team**: Prefer minimal Jira ops, maintainer-driven consolidation on explicit action (labeling). Complex to do automatically due to sprint-based CVE batching.

---

## Next Steps

1. ✅ Confirm label names: `ymir_consolidate_base`, `ymir_consolidate_next`, `ymir_consolidate_batch` (Phase 2)
2. Start Phase 1 implementation (Low effort)
3. Decide on Phase 2 orchestrator based on data

---

# Scenario 2: Multi-CVE Single-Patch Consolidation

## Problem Statement

When a single upstream patch addresses multiple CVEs (common in security fixes), each CVE has a separate downstream Jira issue.

**Example** (per antbob's comment):

- Upstream commit fixes CVE-2024-1234, CVE-2024-5678, CVE-2024-9012 in one patch
- Downstream has separate issues: RHEL-1000, RHEL-2000, RHEL-3000
- Agent should detect relationship and create single MR resolving all three

### Critical Requirements for Downstream Automation

ALL consolidated issues must:

1. **Transition to "In Progress"** - Each issue must be transitioned when work begins (required by downstream automation)
2. **Link to MR** - Each issue must have a comment indicating it's part of the consolidated backport with MR link

## Recommended Solution: Triage-Time Auto-Detection

### Why This Approach

**1. Symmetric to Existing Rebuild Consolidation**

Existing `find_rebuild_siblings()` in `ymir/agents/rebuild_consolidation.py` already implements triage-time consolidation for dependency rebuilds. This solution **mirrors that exact pattern**:

| Aspect          | Rebuild Consolidation                     | Multi-CVE Backport (Symmetric)                |
| --------------- | ----------------------------------------- | --------------------------------------------- |
| **When**        | During triage, after `resolution=REBUILD` | During triage, after `resolution=BACKPORT`    |
| **Detection**   | JQL search for dependency rebuilds        | Parse upstream commit, search for CVE matches |
| **Validation**  | LLM verifies dependency rebuild           | Check CVE eligibility                         |
| **Storage**     | `RebuildData.consolidated_issues`         | `BackportData.consolidated_issues`            |
| **MR Creation** | Single MR with all `Resolves:`            | Single MR with all `Resolves:`                |

**2. Early Detection = Optimal Resources**

Triage-time consolidation:

- Detects siblings **before** backport runs
- Creates **one MR** with all issues
- Runs **one CI pipeline**
- No duplicate MRs to close

**3. High Accuracy with Low Complexity**

Upstream commit messages reliably list CVEs (security documentation requirements). Simple regex parsing (`CVE-\d{4}-\d{4,}`) provides high accuracy.

**4. Fully Automatic**

Unlike incremental consolidation (requires manual labels), multi-CVE consolidation is automatic:

1. Maintainer triages primary issue
2. Agent detects multi-CVE patch and finds siblings
3. Agent creates consolidated MR
4. All issues updated automatically

**5. Composable with Incremental Consolidation**

The two approaches complement each other:

- **Scenario 1**: Different patches at different times (manual stacking)
- **Scenario 2**: Same patch with multiple CVEs (auto-detection)

Can be combined: Multi-CVE creates RHEL-1000+2000+3000 MR, then RHEL-4000 added later via `ymir_consolidate_next`

---

## Implementation Plan (Low Effort)

### 1. Extend Data Models

**File**: `ymir/common/models.py`

Add to `BackportData` (symmetry with `RebuildData`):

- `consolidated_issues: list[ConsolidatedIssue]`
- `consolidation_summary: str | None`

### 2. Create Multi-CVE Detection Module

**New file**: `ymir/agents/backport_consolidation.py` (mirrors `rebuild_consolidation.py`)

**Key functions**:

- `extract_upstream_references(commit_message)` - Parse CVE IDs and Jira keys from commit
- `build_multi_cve_sibling_jql(...)` - Build JQL to find downstream issues matching upstream CVEs
- `find_multi_cve_siblings(...)` - Main function, returns `(consolidated_issues, summary)`, validates eligibility

### 3. Integrate into Triage Agent

**File**: `ymir/agents/triage_agent.py`

**Changes**:

- Add workflow step `consolidate_backport_siblings` (parallel to `consolidate_rebuild_siblings`)
- Route to consolidation after `resolution=BACKPORT`
- Fetch upstream commit message from patch URL
- Store results in `backport_data.consolidated_issues`

### 4. Update Backport Agent

**File**: `ymir/agents/backport_agent.py`

**Changes**:

- Read `consolidated_issues` from BackportData
- Build commit message with all issues: `Resolves: RHEL-1000, RHEL-2000, RHEL-3000`
- Update MR description with consolidation summary
- **Transition ALL issues to "In Progress"**: Loop through all consolidated issues and transition each to "In Progress" (required by downstream automation)
- **Comment on ALL issues**: Comment on each consolidated issue with MR link and consolidation explanation (not just primary issue)
- Label all issues (primary + consolidated) with `ymir_triaged_backport`

**Note**: Current backport agent only transitions/comments on primary issue.

### 5. Testing & Documentation

**Testing**:

- Unit tests: Commit message parsing, JQL construction, mock detection workflow
- E2E tests: Full triage → detection → backport flow
- Integration tests: Real multi-CVE commits from OpenSSL, glibc

**Documentation**:

- Update CLAUDE.md with auto-detection behavior
- Document relationship with incremental consolidation
- Maintainer guide for when consolidation happens

---

## Comparison: Two Consolidation Scenarios

| Aspect         | Scenario 1: Incremental            | Scenario 2: Multi-CVE             |
| -------------- | ---------------------------------- | --------------------------------- |
| **Use Case**   | Different patches, different times | Same patch, multiple CVEs         |
| **Trigger**    | Manual labels                      | Automatic triage-time             |
| **Detection**  | User marks base/next               | Parse upstream commit             |
| **MR Count**   | Multiple sequential                | Single upfront                    |
| **Pattern**    | Sequential stacking                | Mirrors `find_rebuild_siblings()` |
| **Effort**     | Low                                | Low                               |
| **Composable** | Yes                                | Yes                               |

**Both scenarios are needed** - they solve different problems and work together.
