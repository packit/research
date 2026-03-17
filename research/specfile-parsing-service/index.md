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

**`RemoteParsingBackend`**: sends the spec content to the parser service, optionally including source files from `sourcedir` to preserve correct parsing for specs with `%include`/`%{load:...}` that depend on committed files, or `%(...)` / `%{lua:...}` that read source files (see section 6 for the rationale and trade-offs).

- `parse(content)` → POST `/parse` → service parses, returns `tainted` flag
- `expand(content, expression)` → POST `/expand` → service parses (hash-cached internally via `SpecParser._last_parse_hash`), expands, returns result

Every `expand()` call is a direct HTTP request — no client-side caching. The service-side hash cache ensures the spec is not re-parsed when content hasn't changed, so each `/expand` call is fast (just `rpm.expandMacro()` after a hash check). A typical operation makes ~20-30 `expand()` calls at ~2-5ms each (in-cluster), adding ~60-150ms — negligible for operations that take seconds (cloning, downloading sources, etc.).

When source files are included (section 6), the simplest approach is to re-send them with every request. For typical repos (< 200 KB) this is negligible. For larger repos, the repeated transfer could be reduced by caching tmpdirs on the service side (e.g. using deterministic paths like `/tmp/parse_{content_hash}/` on the shared tmpfs, so any gunicorn worker can find them). This needs care around concurrent cleanup, but is a possible optimization.

Client-side pre-caching (where `/parse` returns all expanded values and the backend serves subsequent `expand()` calls from a local cache) was considered, but it doesn't handle multiple `Specfile` instances well (packit creates separate instances for upstream and distgit specs), requires tracking which expressions to pre-cache, and adds cache invalidation complexity after write operations.

The backend works at the `SpecParser`/`Macros` level, not the `Specfile` level, because `Specfile.__init__()` calls `self._backend.parse()` — having the backend create a `Specfile` internally would be infinite recursion.

**Write operations** (`update_version()`, `update_tag()`, `add_changelog_entry()`) also work through this mechanism — they internally call `expand()`, which delegates to the backend. After a write modifies the spec text, the next `expand()` call sends the new content; the service detects the change (hash mismatch), re-parses, and returns the fresh expanded value.

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

**`POST /parse`** — parse spec, return tainted flag

Called during `Specfile.__init__()`. The service parses the spec and returns whether the result is tainted (dummy files were needed for `%include`/`%{load:...}`).

```json
Request:
{
    "content": "Name: example\nVersion: %{ver}\n...",
    "macros": [["ver", "1.0"]],
    "force_parse": true,
    "sanitize": true,
    "source_files": { "standard-dlls-mingw32": "<base64>", ... }
}

Response:
{
    "tainted": false
}
```

`source_files` is optional — see section 6 for when it's needed. With multipart+tarball variant, the source files are sent as a tar.gz part instead of base64 in JSON (see section 6 for trade-offs).

**`POST /expand`** — expand expressions in spec context

The primary workhorse. Every `Specfile.expand()` call becomes a `/expand` request. The service parses the spec (hash-cached internally via `SpecParser._last_parse_hash` — skips re-parsing if content unchanged), expands the expression, and returns the result.

```json
Request:
{
    "content": "...",
    "macros": [...],
    "force_parse": true,
    "sanitize": true,
    "expressions": ["%{version}", "1%{?dist}"],
    "source_files": { ... }
}

Response:
{
    "expanded": {"%{version}": "1.0", "1%{?dist}": "1.fc42"}
}
```

Multiple expressions can be batched in a single request to reduce round-trips — the backend collects pending `expand()` calls and sends them together where possible.

**`GET /health`** — liveness/readiness probe

### Serialization

**JSON** — native for both FastAPI and Flask, human-readable for debugging.

**Stateless** — each request carries complete spec content. The service-side `SpecParser._last_parse_hash` avoids redundant re-parses across requests within the same gunicorn worker.

### HTTP round-trips per operation

| Operation                                | `/parse` | `/expand`  | Notes                                        |
| ---------------------------------------- | -------- | ---------- | -------------------------------------------- |
| `Specfile.__init__()`                    | 1        | 0          | Initial parse                                |
| Read `expanded_version`/`release`/`name` | 0        | 1-3        | One per tag access (or batched)              |
| `set_specfile_content()`                 | 1        | ~5-10      | Re-parse after text change, then expand tags |
| `download_remote_sources()`              | 0        | ~2-4       | Expand source URLs                           |
| `add_changelog_entry()`                  | 0        | ~1-2       | Expand EVR values                            |
| **Total per propose-downstream**         | **~3-4** | **~15-25** | ~60-150ms total overhead at ~3-5ms per call  |

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

## 6. File dependencies during parsing

### Current behavior

Packit parses specfiles before source tarballs are available — in upstream repos they're created later by `create_archive()`, in dist-git repos they're in the lookaside cache and downloaded later by `download_source_files()`. The specfile library handles this via `force_parse=True` (`RPMSPEC_ANYARCH | RPMSPEC_FORCE` flags), which suppresses missing-file errors. For `%include`/`%{load:...}`, the library creates dummy files for missing includes and marks the result as `tainted=True`.

Importantly, `rpm.spec()` does not read the actual content of source or patch files during parsing. RPM only needs files to exist — it reads the first 13 bytes to detect compression type for `%setup`, nothing more. The specfile library's `_make_dummy_sources()` creates dummy files with correct magic bytes, satisfying RPM. Patches on disk are never read during parsing — they're applied at build time during `%prep`.

The only mechanisms that read actual file content during parsing are `%include`/`%{load:...}` (the dummy file mechanism is best-effort — if the included content defines macros or affects syntax, dummy files will likely lead to broken parsing or `RPMException`), and explicit `%(...)` shell expansions or `%{lua:...}` blocks that open and read files.

### What changes with the remote service

| File type                             | Available today? | Read during parsing?           | Impact of remote service                             |
| ------------------------------------- | ---------------- | ------------------------------ | ---------------------------------------------------- |
| Source tarballs (lookaside)           | No               | No (dummy suffices)            | No change                                            |
| Patches (committed)                   | Yes              | No (applied at build time)     | No change                                            |
| `%include`/`%{load:...}` targets      | If committed     | Yes (content as spec input)    | Regression — dummy files are best-effort (see below) |
| Files read by `%(...)` / `%{lua:...}` | If committed     | Yes (arbitrary shell/Lua code) | Regression — see examples below                      |

The actual gap: `%include`/`%{load:...}` targets (dummy files are best-effort and unlikely to produce correct results when the included content defines macros or affects syntax), and committed source files explicitly read by `%(...)` or `%{lua:...}` during parsing.

### How big are dist-git repos?

Since tarballs are in the lookaside (not in the git checkout), the committed content in dist-git repos is small:

| Repo                         | Files | Total size |
| ---------------------------- | ----- | ---------- |
| **mingw-crt**                | 6     | 89 KB      |
| **python-rpm-macros**        | 17    | 117 KB     |
| **gawk**                     | 7     | 81 KB      |
| **kernel** (extreme outlier) | 101   | 11.3 MB    |

### Option A: Spec content only (not recommended)

Send only the spec file text. No source files. Core packit operations (Name, Version, Release, source URLs, changelog) are unaffected — these tags rarely depend on external file content. Regresses parsing for specs that use `%include`/`%{load:...}` with committed files, or read committed files via `%(...)` / `%{lua:...}`. `force_parse` reduces but does not eliminate hard failures — if a missing `%include`/`%{load:...}` target leads to undefined macros that break spec syntax, parsing will still fail with `RPMException`.

Could introduce a regression for some dist-git specs.

### Option B: Send sourcedir content alongside spec (recommended)

Send all committed files from `sourcedir` alongside the spec content. The service reconstructs the directory on disk and parses with full file access — identical to local parsing.

Since dummy files for `%include`/`%{load:...}` are unreliable (see above), sending the real sourcedir content is needed to avoid regressions. The network cost is low — dist-git repos without lookaside tarballs are typically under 200 KB.

#### Is sending files over the network practical?

Since tarballs are in the lookaside (not in the checkout), committed dist-git content is rather small, see above table.

#### What files to send

The `RemoteParsingBackend` has access to `sourcedir` (passed to `SpecParser` during `Specfile.__init__`). In packit, dist-git sets `sourcedir = working_dir` (repo root), upstream sets `sourcedir = absolute_specfile_dir` (spec's parent). Since tarballs are never in the checkout, everything present in sourcedir is a committed file within the size ranges above. The backend lists the directory and includes all files.

#### How to send source files

There are ~3-4 `/parse` calls per operation (section 3), so source files are sent 3-4 times. For typical repos (< 200 KB) this is negligible regardless of encoding. For larger repos (python-huggingface-hub at 4.9 MB, kernel at 11.3 MB) the choice of mechanism matters more.

**JSON with base64 `source_files` field:**

The `content` field carries the current in-memory spec content, `source_files` carries the auxiliary files from disk as base64-encoded values. Option A is just this without the `source_files` field — same API, same Content-Type.

|                | Pro                                       | Con                                                           |
| -------------- | ----------------------------------------- | ------------------------------------------------------------- |
| API simplicity | Pure JSON, same format for both options   |                                                               |
| Spec freshness | `content` is always the in-memory version |                                                               |
| Binary files   | Base64 handles them                       | 33% size overhead                                             |
| Large repos    |                                           | 4.9 MB → 6.5 MB, 11.3 MB → 15 MB per request                  |
| Serialization  |                                           | 429 files in a JSON dict; 15 MB JSON blobs to parse/serialize |

**Multipart with tarball of source files:**

Spec content + metadata as JSON in one part, source files as tar.gz in the other. The tarball contains only source files (not the spec), avoiding the stale-spec problem — the in-memory spec content comes from the JSON part.

|                  | Pro                                                         | Con                            |
| ---------------- | ----------------------------------------------------------- | ------------------------------ |
| Compression      | Text files compress ~65%: 4.9 MB → ~1.7 MB, 11.3 MB → ~4 MB |                                |
| Large repos      | Efficient regardless of size                                |                                |
| API complexity   |                                                             | Multipart instead of pure JSON |
| Tarball security | Service is sandboxed (tmpfs, no secrets, no network)        |                                |

For typical repos (< 200 KB), both approaches work well and the difference is negligible. For larger repos, tarball could be ~4× more efficient.

#### Service-side handling

1. Receive spec content and source files (either as JSON or multipart)
2. Create tmpdir on tmpfs (`/tmp`)
3. Write spec content and source files to tmpdir
4. `Specfile(path=tmpdir/spec, sourcedir=tmpdir, ...)` — standard local parsing
5. Collect all expanded values
6. Return response, clean up tmpdir

### Could we avoid network transfer? (shared volume approach)

Sandcastle uses shared PVC mounting — the worker and Sandcastle pod mount the same PersistentVolumeClaim. Could the parser service use the same pattern?

- Sandcastle creates per-task PVCs and pods. The parser service is a long-running pod — it can't mount PVCs that are created/destroyed dynamically per task.
- A single shared PVC would require ReadWriteMany storage (NFS/CephFS), create concurrent access issues across 4 workers, and let the parser see all workers' repo checkouts — widening the attack surface.
- Creating a separate pod per parse adds 1-5 seconds of startup per parse

## 7. Open topics

- [ ] Agree on high-level architecture
- [ ] Profile actual CPU/memory of specfile parsing for resource sizing
