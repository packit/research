---
title: Ymir Staging Environment Strategies
authors: mmassari
---

This research addresses [PACKIT-5014](https://redhat.atlassian.net/browse/PACKIT-5014) and evaluates staging/testing approaches for Ymir (Jotnar v2) to catch errors before production deployment.

## Context

Ymir needs pre-production validation to catch deployment issues, infrastructure problems, and integration failures before they hit production. Two complementary approaches address different validation needs:

1. **Full Staging Environment** - persistent production-like deployment for integration testing with real external services
2. **CI with Testing Farm** - automated deployment validation on each PR using temporary OpenShift Local clusters

---

## Approach 1: Full Staging Environment

A persistent production-like deployment with real external service integration.

**Reference Implementation:** SE team has deployed [Jotnar Stage](https://gitlab.cee.redhat.com/abobrov/jotnar-se) with [detailed documentation](https://redhat.atlassian.net/wiki/spaces/SustainingEngineering/pages/427100260/Jotnar+Stage+Deployment).

### What It Is

Complete Ymir deployment (11 Deployments, 2 CronJobs) on dedicated infrastructure with:

- Dedicated `ymir-staging` bot credentials
- Staging Jira instance (`stage-redhat.atlassian.net`)
- Agents run with `STAGE_INSTANCE=true` environment variable - processes issues fully, creates branches in dist-git, adds Jira comments, but skips MR creation
- All comments added to staging Jira only (nothing touches production Jira)

### Best For

- Multi-team collaboration
- Release candidate validation

### Trade-offs

- ✅ **Real integration** - catches issues with actual Jira API interactions
- ✅ **Always available** - persistent environment for team access
- ✅ **Production parity** - same agent code, just different configuration
- ❌ **High cost** - requires 24/7 cluster resources
- ❌ **Maintenance** - ConfigMaps, Secrets, PVCs to manage

---

## Approach 2: CI with Testing Farm + OpenShift Local

Automated deployment validation on every PR using ephemeral OpenShift clusters. Can also be used for on-demand manual testing.

### What It Is

[Testing Farm](https://docs.testing-farm.io/) provisions temporary VMs (20 CPUs, 48GB RAM, 150GB disk) that:

1. Install OpenShift Local (CRC) in the VM
2. Deploy all Ymir components
3. Validate deployment health and service endpoints
4. Clean up automatically when done

**Important:** Ymir CI must use **internal Testing Farm Red Hat Ranch** (not public testing-farm.io) to access internal Red Hat services like dist-git, internal Jira, Kerberos authentication, and internal GitLab.

Triggered via Packit-as-a-Service on every PR. Same infrastructure can provision VMs for manual testing.

### How It Works

**Automated CI:**

1. PR opened → Testing Farm provisions CentOS Stream 10 VM
2. VM installs CRC, starts OpenShift cluster
3. Deployment scripts create secrets, deploy Ymir with `STAGE_INSTANCE=true`
4. Clone test issue from production Jira to staging Jira
5. Agents process issue through full workflow (triage → backport → rebase → rebuild)
6. Agents create branches in dist-git and add comments to staging Jira (but skip MR creation)
7. Validation agent checks Jira comments, traces, and dist-git branches for correctness
8. Results published to PR, VM torn down

**Manual Testing (same infrastructure):**

1. Developer runs `tmt run --interactive` to provision Testing Farm VM
2. SSH to VM, manually test changes (push issues to queues, watch agents, modify deployments)
3. Keep VM alive as long as needed or let tmt clean up

### Best For

- **Automated:** Full workflow validation on every PR before merge
- **Manual:** On-demand production-like testing without local hardware constraints

### Trade-offs

- ✅ **Automated quality gate** - every PR validated before merge
- ✅ **Full workflow validation** - tests actual agent processing, Jira integration, dist-git operations (except MR creation)
- ✅ **No permanent infrastructure** - ephemeral VMs only when needed
- ✅ **Production-like** - real OpenShift 4.x APIs via CRC
- ✅ **Reusable for manual testing** - same infrastructure for CI and developer testing
- ✅ **No local hardware needed** - Testing Farm provides VMs with sufficient resources
- ❌ **Slower feedback** - VM provisioning + CRC startup adds 5-10 minutes (can be improved with custom Testing Farm images, see [Build custom images for Testing Farm](https://fedoramagazine.org/build-custom-images-for-testing-farm/))
- ❌ **Requires test automation** - needs validation agent creation to verify correctness

### Dual-Use Infrastructure

The same Testing Farm setup serves both automated CI and manual developer testing:

**For CI:** PR opened → VM provisions → CRC starts → Ymir deploys → validation runs → results to PR → VM tears down

**For Manual Testing:** Developer runs `tmt run --interactive` → SSH to VM → manually test changes (push issues to queues, watch agents, update deployments) → cleanup when done

This eliminates the need for separate local development tooling while providing production-like OpenShift environment on demand.

---

## Comparison: Real Staging vs CI on PR

Both approaches address different validation needs:

| Aspect             | Real Staging Environment                                                | CI with Testing Farm                                                    |
| ------------------ | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Purpose**        | Integration testing with real services                                  | Full workflow validation on every PR                                    |
| **When**           | Release candidates, before production                                   | Every PR + on-demand manual testing                                     |
| **Infrastructure** | Persistent dedicated cluster                                            | Ephemeral VMs (CI or manual)                                            |
| **What It Tests**  | Full workflow except MR creation (creates branches, adds Jira comments) | Full workflow except MR creation (creates branches, adds Jira comments) |
| **Credentials**    | Staging-specific or reuse production initially                          | Can reuse production credentials initially (no user-facing changes)     |
| **Cost**           | High - 24/7 cluster resources                                           | Low - VMs only when needed (~15-20 min per PR)                          |
| **Feeding**        | Requires CronJob or manual issue cloning                                | Automatic - each test clones fresh issue                                |
| **Best For**       | Continuous testing, team collaboration                                  | Pre-merge checks, developer testing                                     |

**Note on Credentials:**

Both staging instance and CI can reuse **production Ymir credentials** initially, since they do not make any user-facing changes. This avoids credential management overhead and speeds up initial setup.

**Required credentials:**

- **Staging Jira token (write)** - NEW - for creating/updating issues in `stage-redhat.atlassian.net`
- **Production Jira token (read-only)** - reuse from production - for cloning issues
- **GitLab token (optional, read-only API access)** - reuse from production - for repository metadata queries (git operations use Kerberos)
- **Kerberos keytab** - reuse from production - for git clone/push via dist-git
- **GCP Vertex key** - reuse from production - for AI operations
- **Testing Farm token** - reuse from production - for CI infrastructure (only needed for CI approach)

**For local manual testing:** Users must provide these credentials when running CI plans locally via tmt.

### Recommended Strategy

**Use both approaches as complementary layers:**

1. **Testing Farm for deployment validation** (automated + manual)
   - Every PR automatically validates deployment succeeds
   - Developers provision Testing Farm VMs on-demand for manual testing
   - Catches deployment issues, infrastructure problems, manifest errors

2. **Staging environment for integration testing** (when needed)
   - Release candidates test against real Jira before production
   - Team validates full workflows with actual external service interactions
   - Persistent environment for continuous testing

This dual-layer strategy provides automated safety on every PR while maintaining confidence that real integrations work before production deployment.

---

## The Feeding Problem

**CRITICAL LIMITATION:** Both staging approaches require continuous feeding with realistic test issues.

**jira_prod_to_stage Cloner:**

SE team has implemented a [jira_prod_to_stage cloner](https://gitlab.cee.redhat.com/abobrov/jotnar-se/-/tree/feature/jira-prod-to-stage-cloner) tool that:

- Clones issues from production Jira to staging Jira
- Adds `[CLONED]` prefix to issue title for identification
- Preserves issue structure, fields, and complexity for realistic testing
- Can be extended to automatically add `jotnar-stage` label (so jira-issue-fetcher picks it up without manual intervention)

**Feeding Solutions (all use the cloner above):**

1. **Manual cloning (current SE approach)**
   - Clone CVEs from production to staging Jira on demand
   - ❌ Requires manual intervention for each test
   - ✅ Full control over what gets tested

2. **Automated feeding via CronJob**
   - Daily CronJob runs cloner to fetch recent production issues
   - ✅ Fully automated, no manual work
   - ✅ Continuous stream of realistic test data
   - ❌ May clone irrelevant issues

3. **CI-based feeding (Testing Farm approach)**
   - Testing Farm VM runs cloner during setup for each test
   - ✅ Fully automated
   - ✅ Clean slate for every test
   - ❌ Slower (VM provisioning + cloning overhead)

### Automated Test Workflow

This workflow can be implemented as **CI tests** (Testing Farm) or **CronJob** (staging instance) for continuous validation.

1. **Pick top issue** from production batch query (`project = RHEL AND labels = jotnar ORDER BY created DESC LIMIT 1`)
2. **Clone** to staging using [jira_prod_to_stage cloner](https://gitlab.cee.redhat.com/abobrov/jotnar-se/-/tree/feature/jira-prod-to-stage-cloner)
3. **Trigger processing** (jira-issue-fetcher uses different query for staging: `labels = jotnar-stage`)
4. **Validation agent** verifies workflow correctness from Jira comments and traces
5. **Report** pass/fail (exit code for CI, notification for CronJob)

---

## Automated Testing Strategy

Both staging approaches need to test with realistic issue data without affecting production systems.

### The Challenge

- Can't create test issues in production Jira
- Can't open MRs in production dist-git
- Can't reuse processed issues (agents detect "already fixed")
- Need realistic testing with actual issue complexity

### The Solution

**Use issues in staging Jira → process through staging Ymir → stop before MR creation → validate with regression detection agent**

```
Staging Jira Issues → Staging Ymir → Stop Before Push → Regression Agent → Pass/Fail
```

**Staging Jira:** [https://stage-redhat.atlassian.net/](https://stage-redhat.atlassian.net/)

Staging Jira contains old production data (>2 weeks stale), making it unsuitable for testing current Ymir workflows without fresh issues. Use SE's [jira_prod_to_stage cloner](https://gitlab.cee.redhat.com/abobrov/jotnar-se/-/tree/feature/jira-prod-to-stage-cloner) to clone recent production issues to staging Jira, creating realistic test data without affecting production.

### How It Works

1. **Clone issue** from production Jira to staging using [jira_prod_to_stage cloner](https://gitlab.cee.redhat.com/abobrov/jotnar-se/-/tree/feature/jira-prod-to-stage-cloner)
2. **Fetch issue** from staging Jira
3. **Process through full workflow** (triage → backport → rebase → rebuild) with `STAGE_INSTANCE=true`
4. **Agents create branches in dist-git and add comments to staging Jira** (MR creation skipped via `STAGE_INSTANCE=true`)
5. **Validation agent** (to be implemented) analyzes results:
   - Verifies correct Jira comments added by agents
   - Checks agent traces and execution logs
   - Validates dist-git branches contain expected changes
   - Reports pass/fail with detailed diagnostics

### Benefits

- ✅ **Real issue complexity** without production pollution
- ✅ **Repeatable** - staging Jira maintained separately
- ✅ **Automated validation** - catches regressions
- ✅ **Safe in CI** - no risk to production
- ✅ **Works in both** staging environment and Testing Farm

---

## User-Triggered Testing

**Use Case:** Users want to test their rules against real issues.

### Option 1: Testing on Staging Instance

Requires staging instance with clone CronJob configured.

**Setup:**

- CronJob in staging instance monitors production Jira for `ymir_clone_to_stage` label
- When detected, runs [jira_prod_to_stage cloner](https://gitlab.cee.redhat.com/abobrov/jotnar-se/-/tree/feature/jira-prod-to-stage-cloner)

**Workflow:**

1. User adds **`ymir_clone_to_stage`** label to production Jira issue
2. Clone CronJob detects label, clones issue to staging Jira with `[CLONED]` prefix, and adds **`jotnar-stage`** label to cloned issue
3. Staging instance jira-issue-fetcher picks up issue and processes it
4. Analyze results in staging Jira comments and Phoenix traces
5. Clean up: remove `ymir_clone_to_stage` label, close cloned staging issue

**Benefits:**

- ✅ Uses persistent staging environment
- ✅ No need to provision VM per test
- ❌ Requires staging instance with clone CronJob setup

### Option 2: Testing with CI/Testing Farm

Uses same tmt plan as CI, but with issue key passed as parameter.

**Workflow:**

1. User runs tmt with issue key parameter:
   ```bash
   tmt run --environment YMIR_TEST_ISSUE=RHEL-12345 plan --name ymir-manual-test/remote
   ```
2. Testing Farm provisions VM
3. VM clones specified issue from production to staging using [jira_prod_to_stage cloner](https://gitlab.cee.redhat.com/abobrov/jotnar-se/-/tree/feature/jira-prod-to-stage-cloner)
4. Deploys Ymir to CRC
5. Processes cloned issue
6. User SSH to VM to analyze traces and logs
7. VM cleaned up when done

**Benefits:**

- ✅ No persistent infrastructure needed
- ✅ Reuses same Testing Farm setup as CI
- ✅ Clean environment per test
- ❌ Slower (VM provisioning overhead)

**Implementation Note:** Not implemented in current proof of concept. The tmt plan would need to accept `YMIR_TEST_ISSUE` environment variable and run jira_prod_to_stage cloner before deploying Ymir. Users manually verify agent behavior via staging Jira comments, Phoenix traces, and SSH access to the VM.

---

## Implementation Recommendations

Both approaches have similar implementation complexity. Key decision factors:

**CI with Testing Farm** - Lower cost (ephemeral VMs), automatic test feeding, but dist-git access from Testing Farm VMs not yet verified.

**Staging Instance** - Known infrastructure (SE reference implementation), proven dist-git/Kerberos setup, but higher cost (24/7 resources) and requires separate feeding mechanism.

**Common Requirements:** Both need validation agent for correctness checking, issue cloning integration (jira_prod_to_stage cloner), and staging Jira configuration.

**Proof of Concept:** The `testing-farm-automation` branch demonstrates Testing Farm VM provisioning and Ymir deployment to CRC, but lacks validation agent, issue cloning integration, and internal Testing Farm testing.

**Suggested Strategy:** Start with **CI with Testing Farm** for lower initial cost and automatic test feeding. Gather metrics (test success/failure rates, validation results) to evaluate if staging instance is needed for complementary validation coverage. Key unknown to verify first: dist-git access from internal Testing Farm Red Hat Ranch VMs.

---

## References

- [PACKIT-5014: SPIKE: staging Ymir environment](https://redhat.atlassian.net/browse/PACKIT-5014)
- [Testing Farm Documentation](https://docs.testing-farm.io/)
- [packit/deployment Repository](https://github.com/packit/deployment) - Reference implementation
- [tmt (Test Management Tool)](https://tmt.readthedocs.io/)
- [OpenShift Local (CRC) Documentation](https://developers.redhat.com/products/openshift-local/overview)
