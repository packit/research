# Specfile parsing service

## 1. Problem: RPM parsing in specfile library can execute arbitrary code

### RPM usage in the specfile library

All `rpm.*` calls in the specfile library (`import rpm` in 4 files):

| RPM call                       | Where                    | Executes arbitrary code?                                    | In parse pipeline?              |
| ------------------------------ | ------------------------ | ----------------------------------------------------------- | ------------------------------- |
| `rpm.spec(filename, flags)`    | `SpecParser._do_parse()` | **Yes** — `%(...)`, `%{lua:...}`, `%include`, `%{load:...}` | Yes                             |
| `rpm.expandMacro(expression)`  | `Macros.expand()`        | **Yes** — `%(...)`, `%{lua:...}` in expressions             | Yes                             |
| `rpm.addMacro(name, body)`     | `Macros.define()`        | No — stores string for later expansion                      | Yes (setup before `rpm.spec()`) |
| `rpm.delMacro(name)`           | `Macros.remove()`        | No                                                          | Yes (cleanup)                   |
| `rpm.reloadConfig()`           | `Macros.reinit()`        | No — reads config files                                     | Yes (reset before parse)        |
| `rpm.labelCompare(evr1, evr2)` | `utils.py` `EVR._cmp()`  | No — pure version comparison                                | **No**                          |
| `rpm.error`                    | Exception handling       | No                                                          | Yes                             |

All dangerous RPM calls (`rpm.spec()` and `rpm.expandMacro()`) flow through two points: `Specfile._parse()` and `Specfile.expand()`. When accessed through a `Specfile` instance — which is always the case in packit — all RPM-dependent code flows through these two methods: `tags.py`, `sourcelist.py`, `conditions.py`, `sections.py`, and `value_parser.py` all use a `context.expand()` pattern that delegates to `Specfile.expand()` when a `Specfile` context exists.

`Macros.expand()` is also called directly in a few places:

- **`spec_parser.py`** (~4 calls in `_do_parse()`) — runs inside `SpecParser.parse()` which would execute on the parser service side, not on workers (see section 2)
- **`changelog.py`** (1 call: `Macros.expand("%packager")`) — reads a system-level RPM config macro for author detection; packit passes `author` explicitly to `add_changelog_entry()`, so this path isn't hit
- **`tags.py`, `sourcelist.py`, `conditions.py`, `value_parser.py`** — each has a `Macros.expand()` fallback for standalone usage without a `Specfile` context; packit always uses these through `Specfile`, so the fallback is never reached

`rpm.labelCompare()` is a pure version comparison function (no code execution, no I/O) — it can stay as-is on workers.

### Current infrastructure

- **Workers**: StatefulSet — 5 short-running (16 greenlets each) + 4 long-running (1 process each)
- **Existing services**: `packit-service` API, Dashboard, Flower, Pushgateway, Redis Commander — all Deployments with Services in the same namespace
- **No security hardening** on workers: no securityContext, no NetworkPolicy, secrets mounted

### Concurrent parse load

**Only long-running workers parse specfiles.** Short-running workers (Copr builds, Testing Farm, status reporting) and Fedora CI jobs (koji scratch builds, TF requests) don't use the specfile library at all.

| Long-running task                       | RPM parses per task |
| --------------------------------------- | ------------------- |
| Propose downstream / Pull from upstream | ~4-10               |
| Upstream/Downstream Koji build          | ~2-4                |
| Bodhi update                            | ~1-2                |
| Sync from downstream                    | ~2-4                |

**Maximum concurrent parse requests: 4** (4 long-running worker pods × 1 process each).

## 2. Integration: pluggable `ParsingBackend` in specfile library

### The constraint

- **packit-as-a-service** (workers): must use the remote parser service for security
- **packit CLI** (local usage): must continue using specfile + librpm directly
- The same `packit` codebase serves both

**Where to put the abstraction — considered approaches:**

| Approach                                                     | Pros                                                                                                                                             | Cons                                                                                                                                                               |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Backend protocol in specfile library**                     | Intercepts at 2 internal methods (`_parse`, `expand`), transparent to all callers, benefits all specfile users, minimal packit changes (2 lines) | Specfile library used on both sides (service uses it with `LocalParsingBackend` to know what to expand)                                                            |
| **Wrapper/proxy in packit-service**                          | Specfile library unchanged                                                                                                                       | See detailed analysis below                                                                                                                                        |
| **Service wraps RPM directly** (no specfile on service side) | Clean separation — service is a thin RPM sandbox                                                                                                 | Service doesn't know which expressions to pre-expand (would need client to enumerate them), or every expansion becomes a network round-trip (~20-30 per operation) |

**Wrapper/proxy in packit/packit-service**

`Specfile.__init__()` calls currently `_parse()` → `rpm.spec()` immediately. So the wrapper options are:

- **Full proxy class** (replace `Specfile` entirely): packit uses 20+ methods/properties across 9 files, each needs proxying. Context managers (`sources()`, `patches()`) yield mutable objects. Write operations (`update_version()`) mix text manipulation with `expand()` internally. Breaks when specfile adds new properties.
- **Subclass overriding `_parse()`/`expand()`** or **monkey-patching** these methods at import time: both end up intercepting at the same two points as the backend protocol — just without a clean contract, and with coupling to specfile's private API. Additionally, `Specfile` objects are created inside packit code which is shared between CLI and service — a subclass would need packit to know which class to instantiate.

The rest of this document assumes the backend protocol in specfile library approach. If we decide on a different solution, the API design (section 3) and deployment (section 5) sections could still apply.

### How it could work

The backend protocol has two methods — `parse()` and `expand()` — matching the two unsafe RPM entry points. The specfile library's `Specfile._parse()` and `Specfile.expand()` delegate to the active backend instead of calling RPM directly.

**`LocalParsingBackend`** (default): calls `SpecParser.parse()` → `rpm.spec()` and `Macros.expand()` → `rpm.expandMacro()`. Same behavior as today.

**`RemoteParsingBackend`**: sends spec content to the parser service. The service uses the specfile library with `LocalParsingBackend` internally — it creates a `Specfile`, iterates tags/sources, and returns all expanded values. The remote backend caches these; subsequent `expand()` calls are cache hits. Cache misses (from `update_value()` ad-hoc expansions) fall through to a `/expand` HTTP call.

The backend works at the `SpecParser`/`Macros` level, not the `Specfile` level, because `Specfile.__init__()` calls `self._backend.parse()` — having the backend create a `Specfile` internally would be infinite recursion.

**Write operations** (`update_version()`, `update_tag()`, `add_changelog_entry()`) also work through this mechanism — they internally call `expand()`, which delegates to the backend. After a write modifies the spec text, the next `expand()` detects the content changed (hash comparison), triggers a new `/parse` to get fresh expanded values, and repopulates the cache. Subsequent expansions within the same operation are cache hits again. So a write operation costs 1 additional `/parse` call for the new content, plus potentially a few `/expand` calls for ad-hoc expressions.

### Configuration

```python
# In packit-service worker startup
if url := os.getenv("SPECFILE_PARSER_URL"):
    Specfile._backend = RemoteParsingBackend(url)
# Otherwise: default LocalParsingBackend (CLI, local dev)
```

**Rollback**: Unset `SPECFILE_PARSER_URL` → falls back to `LocalParsingBackend` → same behavior as before.

## 3. API design

### Framework

| Framework   | Pros                                                                                          | Cons                                                                                 |
| ----------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **FastAPI** | Built-in Pydantic validation/serialization, auto-generated OpenAPI docs, modern Python typing | New dependency for the team, async features unused (if we run sync gunicorn workers) |
| **Flask**   | Team already uses it (packit-service API), mature, simple                                     | Manual request validation/serialization, more boilerplate for typed endpoints        |

### Endpoint design

**`POST /parse`** — parse spec, return all expanded values

The service creates a `Specfile(content=...)` internally, iterates over tags and sources, and returns all expanded values. No expression list needed from the client — the service knows what to expand because it runs the specfile library.

The response should include **all expressions** expanded during the request — not just tag values and source locations but also `%if`/`%ifarch` condition expressions. Analysis of Fedora specfiles shows 46% (10,977/23,654) use conditionals, averaging ~4 `%if` lines per spec. Without pre-caching conditions, each would be a separate `/expand` round-trip. The simplest approach: the service captures every `expand()` call made during the `/parse` and returns them all.

```json
Request:
{
    "content": "Name: example\nVersion: %{ver}\n...",
    "macros": [["ver", "1.0"]],
    "force_parse": true,
    "sanitize": true
}

Response:
{
    "tainted": false,
    "expanded": {
        "%{ver}": "1.0",
        "https://example.com/%{name}-%{version}.tar.gz": "https://example.com/example-1.0.tar.gz",
        ...
    },
    "expanded_no_dist": {
        "1%{?dist}": "1"
    }
}
```

The `expanded` dict maps raw expressions (tag values, source locations) to their expanded forms. `expanded_no_dist` contains values expanded with `extra_macros=[("dist", "")]` — needed for `expanded_release` and `add_changelog_entry()` EVR.

**`POST /expand`** — expand arbitrary expressions (for cache misses)

For cases where the client needs to expand expressions not covered by `/parse` (e.g., `update_value()` internally calls `expand("%{?macro_name:1}")` to check if macros are defined). Stateless — re-parses internally (hash-cached on the service side).

```json
Request:
{
    "content": "...",
    "macros": [...],
    "force_parse": true,
    "sanitize": true,
    "expressions": [
        {"expression": "%{?prerel:1}"},
        {"expression": "%{?commit:1}"}
    ]
}

Response:
{
    "expanded": {"%{?prerel:1}": "", "%{?commit:1}": "1"}
}
```

**`GET /health`** — liveness/readiness probe

### Serialization

**JSON** - native for both FastAPI and Flask, human-readable for debugging.

**Stateless** (over session-based). Each request carries complete spec content. A session-based approach (parse once, expand many) would avoid re-parsing but adds server-side state management and sticky routing. Not justified — parsing is fast, and the specfile library's hash-based cache avoids redundant re-parses even across requests within the same gunicorn worker.

### HTTP round-trips per operation

| Operation                                | `/parse` calls | `/expand` calls | Notes                                                                      |
| ---------------------------------------- | -------------- | --------------- | -------------------------------------------------------------------------- |
| Read `expanded_version`/`release`/`name` | 1              | 0               | All tag values pre-cached by `/parse`                                      |
| `determine_new_distgit_release()`        | 1-2            | 0               | 1 `/parse` per specfile (upstream + distgit)                               |
| `set_specfile_content()`                 | 1-2            | 0-1             | Re-parse after text modifications; `update_value()` may cause cache misses |
| `download_remote_sources()`              | 0              | 0               | Source locations pre-cached by initial `/parse`                            |
| `add_changelog_entry()`                  | 0              | 0               | EVR values pre-cached (both with and without dist)                         |
| **Total per propose-downstream**         | **~3-4**       | **0-1**         | `/expand` only if `update_value()` hits cache miss                         |

## 4. Thread safety — why process-only isolation

RPM uses extensive global state. Concurrent parsing within a single process has **4 high-severity hazards**:

| Hazard                         | Global state                                                                                                     | Severity |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------- | -------- |
| `os.environ` modification      | `_sanitize_environment` sets/restores `LANG`, `LC_ALL` — `setenv()` is not thread-safe in glibc                  | HIGH     |
| RPM macro context interleaving | `Macros.reinit()` → define macros → `rpm.spec()` is not atomic; another thread can call `reinit()` between steps | HIGH     |
| `SpecParser._last_parse_hash`  | Class variable shared across instances; race conditions can return wrong/stale data                              | HIGH     |
| RPM Lua tables                 | Global storage initialized/destroyed with `rpm.spec` instances; concurrent create/delete causes crashes          | HIGH     |
| stderr fd redirection          | `os.dup2()` on fd 2 is process-wide                                                                              | MEDIUM   |

**Solution: `gunicorn --workers 8 --threads 1 --timeout 30`** — each gunicorn worker is a separate OS process with its own RPM state, env vars, and file descriptors. Alternatives considered:

- Threads with a per-process `threading.Lock()` to serialize RPM operations — same throughput with more overhead and complexity
- `gunicorn + gthread` / `uvicorn (ASGI)` — both introduce threads with the same safety issues
- `uvicorn standalone` — no process management, no worker timeout for hung RPM/Lua calls

**Lua timeout**: RPM's Lua interpreter has no timeout. A malicious `%{lua: while true do end}` hangs indefinitely. gunicorn's `--timeout 30` kills and auto-respawns hung workers.

## 5. Security & deployment

### Container isolation

| Setting                        | Value                   | Reason                              |
| ------------------------------ | ----------------------- | ----------------------------------- |
| `automountServiceAccountToken` | `false`                 | No K8s API access                   |
| `readOnlyRootFilesystem`       | `true`                  | Prevent filesystem modifications    |
| `runAsNonRoot`                 | `true`                  | Standard hardening                  |
| `allowPrivilegeEscalation`     | `false`                 | Standard hardening                  |
| Secrets                        | None                    | Parser has no external dependencies |
| Network egress                 | Denied (NetworkPolicy)  | Parser makes no outbound calls      |
| Network ingress                | Workers only, port 8080 | Minimal attack surface              |
| tmpfs at `/tmp`                | 256Mi                   | For temp files during parsing       |

The specfile library needs writable dirs for `tempfile` (spec content, stderr capture) and dummy source files during `force_parse`. The tmpfs mount at `/tmp` satisfies this.

### Isolation level

An attacker achieving RCE in the parser container gets: no secrets (none mounted), no network (egress denied), no K8s API (`automountServiceAccountToken: false`), no writable filesystem (read-only + tmpfs only), no access to other pods' secrets (K8s mounts secrets per-pod, not per-namespace).

| Isolation level                       | Security gain                                           | Operational cost               | Verdict     |
| ------------------------------------- | ------------------------------------------------------- | ------------------------------ | ----------- |
| Same-namespace Deployment + hardening | Strong (no secrets, no network, no K8s API)             | Minimal                        | Sufficient  |
| Separate namespace                    | ~0 (all properties already per-pod)                     | Moderate (cross-ns networking) | Unnecessary |
| Separate VM                           | Marginal (kernel isolation, but nothing to escalate to) | High                           | Overkill    |

### Deployment

Same-namespace Deployment + ClusterIP Service. Workers call `http://specfile-parser:8080`.

- **Shared service** (not sidecar) — simpler, fewer resources, matches existing patterns
- **1 replica to start** — we could scale later as needed
- **8 gunicorn workers** — max 4 concurrent parse requests (4 long-running worker pods), so 8 provides 2× headroom. We can adjust as needed.

```yaml
kind: Deployment
metadata:
  name: specfile-parser
spec:
  replicas: 1
  template:
    spec:
      automountServiceAccountToken: false
      containers:
        - name: parser
          image: quay.io/packit/specfile-parser:{{ deployment }}
          ports:
            - containerPort: 8080
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            runAsNonRoot: true
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: "1"
              memory: 512Mi
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir:
            medium: Memory
            sizeLimit: 256Mi
```

### NetworkPolicy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: specfile-parser-isolation
spec:
  podSelector:
    matchLabels:
      component: specfile-parser
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              component: packit-worker
      ports:
        - port: 8080
  egress: [] # deny all
```

## 6. `%include` / `%{load:...}` handling

The specfile library already handles missing includes via `force_parse=True`: first parse fails → collects include/load paths → creates dummy source files → re-parses → marks result as `tainted=True`.

TODO: look if this is sufficient based on the analysis of Fedora specfiles.

## 7. Open topics

- [ ] Agree on high-level architecture
- [ ] Look into %load/%include more
- [ ] Profile actual CPU/memory of specfile parsing for resource sizing
