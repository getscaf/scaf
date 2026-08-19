# Scaf Compose — Final v1 Specification

**Version:** 1.0.0-draft  
**Status:** Proposal  
**Date:** 2026-05-11

---

## 1. Overview

Scaf Compose lets a parent template assemble one project from multiple independent Copier child templates while keeping prompts, file ownership, and merge behavior explicit.

The parent template owns the end-user experience and the composition policy. Child templates remain ordinary Copier templates rendered in isolation. Scaf then assembles their outputs according to a strict ownership map. There is no implicit merge behavior, no silent overwrite precedence, and no ecosystem-specific file merging in Scaf core.

### 1.1 Goals

1. Reuse existing Copier templates as child building blocks where feasible.
2. Let a parent template define a single coherent prompt surface for end users.
3. Make final-project file ownership explicit and inspectable.
4. Fail on unresolved conflicts instead of overwriting silently.
5. Keep Scaf core format-agnostic; parent templates may add domain-specific Jinja extensions.
6. Support safe updates through Scaf-managed state rather than pretending a composed project is a native Copier output.

### 1.2 Non-Goals for v1

The following are intentionally out of scope for v1:

1. Nested composition.
2. Auto-exposing child questions to users.
3. Native child `copier update` semantics.
4. Format-aware YAML/TOML/JSON merging in Scaf core.
5. `scaf eject`.
6. Partial child update, such as `scaf update --child <name>`.
7. Implicit parent-over-child override behavior.
8. Loading all child text files into the parent template context by default.

### 1.3 Design Principles

1. **Parent owns composition.** The parent template decides how child outputs become a final project.
2. **Explicit over implicit.** Every final output path has exactly one owner. Ambiguity is an error.
3. **Prompt surface is parent-owned.** The parent `copier.yaml` defines every user-facing question.
4. **Children are rendered through Copier.** Scaf delegates child rendering to Copier, with v1 restrictions documented below.
5. **Ecosystem-agnostic core.** Scaf provides text-oriented primitives only. Semantic merging belongs in parent extensions.
6. **Flat dependencies only.** A parent may depend on children; children may not declare Scaf Compose dependencies in v1.

### 1.4 Terminology

| Term | Definition |
|---|---|
| **Parent template** | A template repository containing `copier.yaml`, `scaf.yaml`, and optional `template/` files. |
| **Child template** | A Copier template rendered as a dependency of the parent. |
| **Render output** | Files produced by a child in its isolated temporary directory. |
| **Excluded file** | A child output removed entirely from Compose processing. |
| **Suppressed file** | A child output kept for explicit composition but never auto-emitted as child pass-through. |
| **Context file** | A child text file explicitly exposed to parent templates under `scaf.children.<name>.text`. |
| **Pass-through file** | A non-excluded, non-suppressed child file that may be copied automatically if uncontested. |
| **Managed file** | A final-project file tracked in `.scaf/state.json` for update reconciliation. |
| **Owner** | The single source responsible for a final output path: parent-only render, child pass-through, or a compose rule. |

---

## 2. Dispatch Model

When a user runs:

```bash
scaf create <parent-repo> <destination> [--vcs-ref <ref>]
```

Scaf resolves the template repository and checks its root. A relative local `<parent-repo>` argument is resolved against the invocation working directory before dispatch:

1. If `scaf.yaml` is present and valid, Scaf uses the Compose pipeline.
2. If `scaf.yaml` is absent, Scaf uses the existing single-template Copier flow.
3. If `scaf.yaml` is present but invalid, Scaf fails with `ScafValidationError`. It must not silently fall back to single-template mode.

Compose mode requires the parent and every child to resolve to a Git commit. The existing single-template flow may still use a non-Git local directory. If a local directory contains `scaf.yaml` but does not satisfy the Compose Git-source rules in §4.3, Scaf raises `ScafResolveError`; it must not fall back to single-template mode.

---

## 3. Parent Template Contract

A parent template repository has this shape:

```text
parent-template/
├── copier.yaml
├── scaf.yaml
└── template/
```

The parent `copier.yaml` defines all user-facing questions. The parent `scaf.yaml` declares child templates, maps parent answers into child answers, classifies child outputs, and declares compose rules.

---

## 4. `scaf.yaml` Schema

```yaml
_min_scaf_version: "1.0.0"  # optional SemVer 2.0 minimum

dependencies:
  - name: <string>              # required, unique
    repo: <string>              # required
    ref: <string>               # optional branch, tag, or commit
    answers:                    # optional child answer mapping
      <child_question>: <literal_or_jinja>
    exclude:                    # removed entirely from Compose processing
      - <glob>
    suppress:                   # not auto-emitted; still available for explicit compose
      - <glob>
    context:                    # text allowlist for parent Jinja context
      - <glob>

compose:
  "<path>":
    strategy: render | concat | prefer

    # concat only
    sources: [<child_name>, ...]
    separator: "\n\n"
    dedupe_lines: false
    header: null

    # prefer only
    source: <child_name>
```

### 4.1 Path and Glob Rules

All paths and globs are POSIX-style paths relative to either:

- the child render root, for dependency `exclude`, `suppress`, and `context`; or
- the final project root, for `compose` keys.

Invalid paths include:

- absolute paths
- paths containing `..`
- paths with platform-specific separators such as `\\`
- empty paths

Scaf normalizes each candidate to a POSIX relative path and matches each glob against the entire normalized path from the applicable render or project root. Matching is case-sensitive and implicitly root-anchored; it is not suffix matching.

Glob operators have these semantics:

- `*` matches zero or more characters within one path segment.
- `?` matches one character within one path segment.
- `[abc]` and `[!abc]` match character classes within one path segment.
- A `**` path segment matches zero or more complete path segments.

Therefore, `README.md` matches only the root-level file, `docs/*.md` matches Markdown files directly under root-level `docs/`, and `**/README.md` matches root-level and nested copies. Implementations may use any glob engine only if it reproduces these semantics; they must not expose the right-anchored suffix behavior of `pathlib.PurePath.match()`.

### 4.2 Minimum Scaf Version

`_min_scaf_version` is optional. When present, it must be a SemVer 2.0.0 string. Scaf compares it with the running Scaf version using SemVer precedence, including prerelease ordering and ignoring build metadata.

If the value is malformed or the running version is lower, Scaf raises `ScafValidationError` immediately after parsing `scaf.yaml` and before prompting, resolving children, or rendering. An omitted field imposes no minimum.

### 4.3 Dependency Fields

#### `name`

Required. A unique identifier for the child. It is used:

- under `scaf.children.<name>` in the parent Jinja context
- in `.scaf/answers/<name>.yml`
- in compose rule `source` and `sources` fields

#### `repo`

Required. A Git repository reference Scaf can resolve through Copier. Remote Git references and local Git repositories are valid. A local working tree must have a `HEAD` commit and no tracked, staged, or untracked changes; Scaf must not lock Copier's synthetic snapshot of a dirty tree.

Local path bases are explicit:

- A relative local `<parent-repo>` CLI argument is resolved against the invocation working directory and stored as a canonical absolute path.
- A relative dependency `repo` is resolved against the root of the resolved parent template containing `scaf.yaml`, never against the invocation directory or destination. The manifest preserves that normalized parent-relative locator so update can resolve it against the candidate parent root.
- An absolute dependency `repo` is canonicalized and stored as an absolute path.

The lock records each source's resolved commit. Update resolves the stored parent path or the candidate parent's dependency path again; a missing path, non-Git directory, dirty working tree, or missing `HEAD` raises `ScafResolveError` without falling back to the previous lock. Non-Git local directories remain supported only by the existing single-template fallback.

#### `ref`

Optional. A branch, tag, or commit accepted by Scaf's existing repository resolver. Scaf Compose v1 does not interpret semantic-version ranges in this field; values such as `~1.0` are passed as literal refs and are invalid unless a repository actually has a ref with that name.

For a Git source with no `ref`, Scaf preserves Copier 8.1's resolver default: select the highest non-prerelease tag whose name is valid under PEP 440, or `HEAD` when no such tag exists. Sorting release tags is resolver behavior, not support for range expressions.

Scaf classifies an explicit selector before passing it to Copier:

- `refs/heads/<name>` is a branch selector.
- `refs/tags/<name>` is a tag selector.
- `HEAD` is a moving selector governed by the branch movement rules.
- For any other value, Scaf queries the source's branch and tag refs. Exactly one match determines the kind. If both `refs/heads/<name>` and `refs/tags/<name>` exist, Scaf raises `ScafResolveError` and requires a fully qualified ref. If neither exists but the value resolves directly to a commit object, Scaf classifies it as a commit selector and stores the full object ID; otherwise resolution fails.

Scaf never silently prefers a tag over a same-named branch or vice versa. The same rules apply to the parent `--vcs-ref`, and the resulting selector kind is persisted in `lock.yml`.

The field is intentionally named `ref`, not `version`, because v1 does not add semver-range behavior to Scaf's resolver.

#### `answers`

Optional. Maps child question names to literal values or Jinja expressions evaluated before child rendering.

Jinja expressions may reference:

- parent answers
- explicitly documented Scaf static variables available before child rendering

They may not reference child render output or the compose context.

#### `exclude`

Optional. Files removed entirely from Compose processing.

Excluded files:

- do not participate in conflict detection
- are not available to compose strategies
- are not exposed in parent Jinja context
- are never emitted to the final project

Use `exclude` when the child output should be treated as if it never existed.

#### `suppress`

Optional. Files kept in child render output but removed from automatic child pass-through.

Suppressed files:

- may be used by `render`, `concat`, or `prefer` compose rules
- may be exposed to parent templates if also matched by `context`
- do not participate as automatic pass-through files
- are never emitted unless a compose rule owns their final path

Use `suppress` when a child output should not be copied directly but may still be useful for composition.

#### `context`

Optional. Explicit allowlist of child text files exposed to parent templates under:

```jinja
scaf.children.<name>.text
```

`context` controls Jinja visibility only. `concat` and `prefer` operate on child render output directly and do not require files to be allowlisted in `context`.

Binary files matched by `context` appear in `scaf.children.<name>.paths` but not in `text`. Accessing them through `text` raises `ScafTemplateError`.

---

## 5. Prompt and Answer Model

### 5.1 Parent-Owned Prompts

The parent template's `copier.yaml` defines every user-facing question and its order. Child questions are never automatically exposed to the user in v1.

If a parent wants the user to choose a value used by a child, the parent must define its own question and map that answer into the child.

All `getscaf/copier-*` repository names used in examples are illustrative contract fixtures. Their full HTTPS `.git` form demonstrates Copier-recognized source syntax, but the document does not claim those names are reachable repositories.

For example:

```yaml
# parent copier.yaml
linter:
  type: str
  default: ruff
  choices: [ruff, flake8]
```

```yaml
# scaf.yaml
dependencies:
  - name: python
    repo: https://github.com/getscaf/copier-python.git
    answers:
      linter: "{{ linter }}"
```

This avoids cross-child prompt collisions, prompt-order ambiguity, and accidental child variable exposure.

### 5.2 Child Question Resolution

For each active child question, Scaf resolves a value in this order:

1. Value supplied in `dependencies[].answers`.
2. Child default value, if the question is active.
3. No value required, if the child question's `when:` condition evaluates false.
4. Otherwise, raise `ScafAnswerError` before rendering final output.

Scaf should use Copier's own question/default/`when:` behavior where practical by rendering children non-interactively with the mapped answers. If Copier would prompt interactively for a child value, Scaf treats that as an unresolved child answer and fails.

### 5.3 Child Answer Storage

The resolved parent answer set is stored in:

```text
.scaf/answers/parent.yml
```

Each resolved child answer set is stored in:

```text
.scaf/answers/<child_name>.yml
```

Scaf-composed projects do not write a root `.copier-answers.yml` for Compose state. A composed project is not a native Copier project for update purposes.

---

## 6. Ownership and Conflict Semantics

At assembly time, every final output path must have exactly one owner. There is no implicit precedence stack.

Valid owners are:

1. **Parent-only rendered file** — a parent output path that does not overlap any non-excluded child path.
2. **Uncontested child pass-through** — exactly one non-excluded, non-suppressed child produces the path and no parent produces it.
3. **`strategy: render`** — parent-owned compose rule.
4. **`strategy: concat`** — Scaf-owned text concatenation from explicit child sources.
5. **`strategy: prefer`** — Scaf-owned selection of one child source.

### 6.1 When a Compose Rule Is Required

A compose rule is required when:

1. Two or more non-excluded, non-suppressed children would auto-emit the same path.
2. The parent renders a path also produced by any non-excluded child, including suppressed child files.
3. A suppressed child file should be emitted into the final project.
4. The parent intentionally replaces, merges, or derives a final file from child output at the same path.

Parent-only files do not require compose rules.

### 6.2 Truth Table

| Child status for path | Parent produces path? | Rule required? |
|---|---:|---:|
| Child does not produce path | Yes | No |
| One non-suppressed child | No | No |
| One non-suppressed child | Yes | Yes |
| One suppressed child | No | No |
| One suppressed child | Yes | Yes |
| Multiple non-suppressed children | Any | Yes |
| Excluded child only | Yes or no | No conflict |

### 6.3 Parent Overlaps

A parent-rendered path that overlaps any non-excluded child path without a matching compose rule raises `ScafConflictError`. Scaf must not merely warn and overwrite.

---

## 7. Compose Strategies

### 7.1 `strategy: render`

The parent owns the final file.

```yaml
compose:
  "README.md":
    strategy: render
```

Rules:

- The parent template must render the target path.
- A static parent file may be UTF-8 text or binary and is copied byte-for-byte.
- A Jinja-templated parent file must be UTF-8 text; Scaf does not attempt to decode or template binary content.
- Missing parent output is a validation error.
- If both `template/<path>` and `template/<path>.jinja` would render the same final path, Scaf raises `ScafValidationError`.

Use `render` for hand-authored merges, parent-owned replacements, and files derived from child context.

### 7.2 `strategy: concat`

The final file is built by concatenating UTF-8 text output from explicit children.

```yaml
compose:
  ".gitignore":
    strategy: concat
    sources: [python, docker, ci]
    separator: "\n\n"
    dedupe_lines: true
    header: "# Generated by Scaf Compose\n"
```

Rules:

- `sources` is required and defines order.
- Every listed source must be a known child.
- Every listed source must produce the target path and it must not be excluded.
- Sources may be suppressed.
- The target must be UTF-8 text in every source.
- Binary files cannot use `concat`.
- There is no implicit dependency-order fallback.
- `dedupe_lines`, when enabled, processes only the source bodies in `sources` order and removes duplicate lines while preserving their first occurrence across those bodies.
- Deduplication happens before Scaf inserts `header` or joins the processed bodies with `separator`. Header and separator text is structural and is never deduplicated.

Good uses include `.gitignore` and `.env.example`. Do not use `concat` for semantically structured dependency files where entries can conflict.

### 7.3 `strategy: prefer`

The final file is copied from one child.

```yaml
compose:
  "favicon.ico":
    strategy: prefer
    source: assets
```

Rules:

- `source` is required.
- The source must be a known child.
- The source must produce the target path and it must not be excluded.
- The source may be suppressed.
- Valid for text or binary files.

Use `prefer` when one child is authoritative for the path.

---

## 8. Pipeline

The Compose pipeline has six phases:

```text
Resolve → Render Children → Render Parent → Compose → Stage → Commit
```

### 8.1 Phase 1: Resolve

1. Parse `scaf.yaml` and validate its schema.
2. Resolve the parent prompt model from parent `copier.yaml`.
3. Prompt the user using parent questions only, or load answers from CLI/files.
4. Resolve child repositories and `ref` selectors.
5. Parse child `copier.yaml` files where available.
6. Validate answer keys against child questions where resolvable.
7. Resolve child answer sets.

### 8.2 Phase 2: Render Children

Each child renders into an isolated temporary directory through Copier.

Child `_tasks` are disabled.

Scaf classifies each child output path as:

1. `excluded`
2. `suppressed`
3. pass-through candidate
4. context file, if matched by `context` and decodable as UTF-8

Excluded files are removed from further Compose processing. Suppressed files remain available for explicit composition.

### 8.3 Phase 3: Render Parent

The parent template renders after child output is available.

The parent render receives:

- parent answers in the normal Copier namespace
- the `scaf` namespace described in §9

### 8.4 Phase 4: Compose

Scaf evaluates compose rules and builds a complete ownership map.

At the end of this phase, every final output path must have exactly one owner. If a path has zero owners due to an invalid rule, or multiple candidate owners due to conflict, Scaf fails before assembly.

### 8.5 Phase 5: Stage

Scaf builds a complete candidate from the resolved ownership map before it mutates the destination.

For `create`, the required `<destination>` argument names the final project directory. A relative destination is resolved from the current working directory; an absolute destination is used as given. Scaf does not derive it from `project_name` or another answer.

Scaf must fail with `ScafValidationError` before rendering if the destination already exists. It assembles all managed output and the complete candidate `.scaf/` metadata in a sibling staging directory on the same filesystem. Scaf itself does not write the destination during staging; the separate limits for unsandboxed parent-task side effects are defined in §12.3.

For `update`, Scaf computes the full reconciliation plan and checks every conflict before changing any project file. It then prepares `.scaf/transactions/<id>.prepared/` with:

- a machine-readable operation plan
- byte-for-byte content and mode backups for every file to replace or delete
- records of paths that the candidate will create
- the previous manifest, lock, answers, and state
- the complete candidate manifest, lock, answers, and state

Scaf writes the journal to `.scaf/transactions/.<id>.tmp/` and atomically renames it to `<id>.prepared/` only when complete. The prepared journal must exist before the first project mutation. Journal preparation failure removes the temporary journal, raises `ScafTransactionError`, and leaves managed files and persisted state unchanged.

### 8.6 Phase 6: Commit

For `create`, Scaf renames the fully staged directory to the destination only after rendering, validation, state generation, and permitted parent tasks succeed. The same-filesystem directory rename is the commit point. If an earlier step fails, Scaf removes the staging directory and re-raises that error with its original class and context. If the final rename fails, Scaf removes staging and raises `ScafTransactionError` with the source and destination paths. Scaf performs no managed destination write before the commit rename and never falls back to piecemeal copying. This guarantee does not claim to undo writes that an unsandboxed parent task makes outside staging.

For `update`, Scaf applies the prepared plan with same-directory temporary files and atomic file renames, and it writes the candidate `.scaf/` metadata as part of that same recoverable transaction. After every operation is durable, Scaf atomically renames `<id>.prepared/` to `<id>.committed/`. That same-parent directory rename is the commit marker.

A write, rename, delete, mode-change, or state-persistence failure triggers rollback at this transaction boundary. Scaf restores every backed-up path and the previous `.scaf/` metadata and removes newly created paths without deleting backup data during rollback. After restoration is durable, it atomically renames `<id>.prepared/` to `<id>.aborted/` and may recursively clean up that directory. Scaf then raises `ScafTransactionError` with the failed operation and path. It must not continue with a partial update or silently retain mixed candidate and previous state. If rollback also fails, Scaf retains the `.prepared` journal and reports both failures.

Before `scaf update` or `scaf status` does other work, it checks journal directory suffixes. A `.prepared` journal is rolled back idempotently. A `.committed` or `.aborted` journal is terminal and receives cleanup only; recursive cleanup never changes its suffix, so a crash during deletion cannot make it look uncommitted. A `.tmp` journal predates project mutation and can be removed. Recovery failure raises `ScafTransactionError` and blocks further mutation until recovery succeeds.

---

## 9. Parent Jinja Context

The parent render receives parent answers plus the `scaf` namespace.

Example:

```python
{
    # parent answers only
    "project_name": "my-app",
    "python_version": "3.12",

    "scaf": {
        "children": {
            "python": {
                "paths": ["README.md", "Makefile", "pyproject.toml"],
                "text": {
                    "README.md": "...",
                    "Makefile": "..."
                }
            }
        },
        "compose": {
            "required_paths": ["README.md", "Makefile"]
        }
    }
}
```

Rules:

- Parent answers remain in the normal flat Copier namespace.
- Child answers are not added unless the parent asked equivalent questions itself.
- `scaf.children.<name>.paths` includes all non-excluded child output paths, including suppressed and binary paths.
- `scaf.children.<name>.text` includes only `context`-allowlisted UTF-8 files.
- Binary means the file cannot be decoded as UTF-8.
- Missing `text` keys raise `ScafTemplateError` under strict undefined behavior.
- Conflict maps are not part of the Jinja context. Use `scaf preview` and `scaf status` for inspection.

### 9.1 Built-in Filters

Scaf provides a small set of string-oriented filters.

#### `section(heading, required=True)`

Extracts a Markdown section by heading. Returns content from the heading line exclusive to the next heading of equal or higher level exclusive, trimmed.

```jinja
{{ scaf.children.python.text["README.md"] | section("## Development") }}
```

If the heading is missing and `required=True`, Scaf raises `ScafTemplateError`. If `required=False`, it returns an empty string.

#### `between(start_marker, end_marker, required=True)`

Extracts content between two marker strings, exclusive of both markers.

```jinja
{{ scaf.children.python.text["Makefile"] | between("# --- build ---", "# --- end build ---") }}
```

If either marker is missing and `required=True`, Scaf raises `ScafTemplateError`. If `required=False`, it returns an empty string.

#### `lines_matching(pattern)`

Returns only lines matching a regular expression pattern.

```jinja
{{ content | lines_matching("^[^#]") }}
```

#### `lines_removing(pattern)`

Returns all lines except those matching a regular expression pattern.

```jinja
{{ content | lines_removing("^\\s*#") }}
```

#### `dedupe_lines`

Removes duplicate lines while preserving the first occurrence.

```jinja
{{ combined_content | dedupe_lines }}
```

### 9.2 Parent Extensions

Parent templates may register additional Jinja filters through Copier's extension mechanism.

```yaml
# copier.yaml
_extensions:
  - my_template.jinja_extensions.YAMLMergeExtension
```

Scaf core does not provide format-aware merge filters in v1.

---

## 10. Project State

Scaf stores local state under `.scaf/`:

```text
.scaf/
├── manifest.yml
├── lock.yml
├── state.json
├── answers/
│   ├── parent.yml
│   ├── python.yml
│   └── docker.yml
└── transactions/  # present only while an update commit or recovery is pending
```

### 10.1 `manifest.yml`

A normalized snapshot of the effective `scaf.yaml` used for the last successful run. It also records the parent repository, the requested parent ref, requested dependency refs, output classification, and compose rules. Requested refs remain distinct from the exact commits in `lock.yml`.

Manual edits to `.scaf/manifest.yml` are unsupported in v1.

### 10.2 `lock.yml`

Records the full resolved Git commit object ID for the parent and every child used by the last successful run. Each entry also records whether the requested selector was omitted, a branch, an explicit tag, or a commit so update can enforce the corresponding movement rules. For an omitted selector, the entry records the selected release tag name or `HEAD` as well as the commit.

### 10.3 `answers/`

Stores resolved parent and child answer sets.

### 10.4 `state.json`

Stores per-managed-file metadata needed for update reconciliation, including:

- path
- owner kind
- source children
- SHA-256 hash over exact file bytes
- file mode and executable bit
- binary/text classification when needed

### 10.5 `transactions/`

Stores the update journals described in §8.5–§8.6. Directory suffixes encode atomic transaction state: `.tmp`, `.prepared`, `.committed`, or `.aborted`. The directory is normally absent or empty and is never treated as user-editable project state.

A Scaf-composed project is not a valid target for native `copier update`. Composed projects must be updated with `scaf update`.

---

## 11. Update Model

`scaf update` does not call child `copier update`. It renders a fresh candidate project from stored Compose state, then reconciles that candidate against the current working tree using `.scaf/state.json`.

### 11.1 Ref Resolution Policy

The manifest stores requested refs; the lock stores the exact commits produced by resolving them during the last successful run.

On every update, Scaf:

1. Uses the stored requested parent ref unless the user supplies `--vcs-ref <branch-or-tag-or-commit>`. A supplied ref replaces the stored requested parent ref only after the whole update succeeds.
2. If the effective parent selector remains omitted and its lock entry records a selected release tag, resolves that recorded tag directly and verifies that it still points to the locked commit.
3. Resolves the requested parent ref through the same repository resolver used by `scaf create`. An omitted parent ref uses Copier 8.1's default: the highest non-prerelease PEP 440-valid tag, or `HEAD` when the repository has no such tag.
4. Loads `scaf.yaml` from that resolved parent and treats it as the candidate manifest. This lets a newer parent ref change child refs and composition policy.
5. For each candidate child whose name and repository match its previous manifest entry, if both selectors are omitted and the lock records a selected release tag, resolves that recorded tag directly and verifies its commit before selecting the current default.
6. Resolves every child `ref` in the candidate manifest. An omitted child ref uses the same highest-release-or-`HEAD` rule.
7. Renders and reconciles the whole candidate graph. Updating one requested ref never performs a partial child update.

A branch selector may advance on a plain `scaf update`. An omitted selector may advance when the resolver selects a different, higher PEP 440 release tag, or when `HEAD` advances in a repository with no valid release tags. A commit selector cannot advance. Every selected tag is immutable within a project: before an omitted selector may advance, Scaf verifies the previously selected tag against its locked commit. A missing or moved previous tag, or an explicit tag that resolves differently from its lock entry, raises `ScafResolveError` and identifies the tag instead of accepting new output.

Explicit tags are literal Git refs and never mean a compatible range. To move the parent to a different tag or commit, the user supplies a different `--vcs-ref`. To move a child to a different tag or commit, the parent template must publish a `scaf.yaml` with the new child ref, and the user selects a parent ref containing that change. Per-child CLI ref overrides remain out of scope for v1.

If any requested ref cannot be resolved, Scaf raises `ScafResolveError` before rendering. It must not fall back to the previous lock. Failed resolution or reconciliation leaves the previous manifest, lock, answers, and state unchanged.

### 11.2 Update Steps

1. Recover or clean up any existing transaction journal as required by §8.6.
2. Load `.scaf/manifest.yml`, `.scaf/lock.yml`, `.scaf/state.json`, and stored answers.
3. Apply the ref resolution policy in §11.1 and load the candidate parent manifest.
4. Render a fresh candidate project in temporary space.
5. Build the candidate ownership map and validate it.
6. Compute the complete reconciliation plan and check every path for conflicts without mutating the project.
7. Prepare the rollback journal with previous bytes, modes, state, and the candidate state.
8. Commit managed-file and `.scaf/` metadata changes through the transaction boundary in §8.6.
9. After all candidate data is durable, atomically rename the journal from `.prepared` to `.committed`, then clean up the terminal journal without changing that suffix.

### 11.3 Safe Update Rules

For each managed file:

1. If current content and mode equal previous managed content and mode, replace with candidate and record candidate state.
2. If current content and mode equal candidate but differ from previous, leave the file unchanged and record candidate as the new managed state.
3. If current differs from previous, but candidate equals previous, preserve current local edits and retain previous managed state.
4. If current, previous, and candidate are pairwise different, raise `ScafUpdateConflictError`.
5. If the candidate deletes a managed file and current equals previous, delete it.
6. If the candidate deletes a managed file and current has local edits, raise `ScafUpdateConflictError`.
7. If the candidate introduces a new managed path that would overwrite an unmanaged local file, raise `ScafUpdateConflictError` unless contents and mode are identical.

This update model is intentionally conservative. It favors preserving user edits and surfacing conflicts over attempting semantic merges.

### 11.4 Parent Tasks During Update

Parent `_tasks` do not run during `scaf update` in v1. Task side effects are not tracked as Scaf-managed output and may cause future update conflicts.

Parent template authors should prefer generating managed files through `template/` rather than mutating them in tasks.

---

## 12. Copier Feature Compatibility

Scaf Compose renders children through Copier, so many ordinary Copier features work during child rendering.

### 12.1 Supported Child Features

Supported to the extent Copier supports them during non-interactive rendering:

1. Normal file rendering.
2. Question defaults.
3. `when:` conditions.
4. Child Jinja extensions required for child rendering.
5. Template subdirectories such as `_subdirectory`.
6. Choice validation and other standard question validation.

### 12.2 Unsupported or Restricted Child Features

1. Child `_tasks` are not run.
2. Child-native `copier update` semantics are not preserved.
3. Child behavior that assumes direct rendering into the final assembled project is unsupported.
4. Non-Git local directories and dirty local Git working trees are unsupported as Compose parents or children.
5. `_skip_if_exists` has no special Compose update semantics; Scaf uses its own managed-file reconciliation.

### 12.3 Parent Tasks

Parent `_tasks`, if any, run once in the staged project after managed output and candidate `.scaf/` state are complete but before the create commit rename. They do not run during `scaf update` in v1.

Copier 8.1 runs these tasks as ordinary subprocesses with the invoking user's permissions and the staging root as their working directory. Scaf does not sandbox them. Template authors must confine task writes to staging; writes to the destination by absolute path or to any other external path are unsupported and cannot be detected or rolled back reliably.

A task's in-staging file side effects are not added to managed state. A task-created file remains unmanaged, and a task modification to a managed file appears as a local modification during the first update. Tasks must not modify staged `.scaf/` metadata; Scaf checks it after tasks and raises `ScafTemplateError` if it changed.

A non-zero exit, signal, or forbidden metadata change aborts create. At this process boundary, Scaf stops before later tasks or the commit rename, removes the staging directory, and raises `ScafTemplateError` with the task command and exit or signal details. External task side effects may remain; Scaf reports them when known but must not delete or rewrite paths it did not create through the staged pipeline.

---

## 13. Validation and Error Handling

Scaf Compose prioritizes clear, actionable errors. Errors should explain what happened, why it is unsafe, and how the template author or user can fix it.

### 13.1 Error Classes

- `ScafValidationError` — invalid manifest, invalid paths or destination, invalid strategy configuration, or an incompatible Scaf version.
- `ScafResolveError` — a parent or child repository ref cannot be resolved.
- `ScafAnswerError` — unresolved child answer.
- `ScafConflictError` — ambiguous final path ownership.
- `ScafTemplateError` — parent render, parent task, or context/filter error.
- `ScafUpdateConflictError` — safe update reconciliation cannot proceed.
- `ScafTransactionError` — a staged create commit, update commit, rollback, or recovery operation fails.

### 13.2 Parse/Resolve-Time Validation

Scaf validates:

1. `_min_scaf_version` is valid and satisfied when present.
2. Duplicate dependency names.
3. Unknown top-level or strategy-specific fields.
4. Invalid paths and globs.
5. Unknown compose strategies.
6. Missing required strategy fields.
7. `concat.sources` references known children.
8. `prefer.source` references a known child.
9. `answers` keys reference real child questions where resolvable.
10. Jinja in `answers` references only allowed variables.
11. The parent and every child source resolve to stable Git commits; local working trees are clean.
12. Every explicit parent and child selector has an unambiguous branch, tag, or commit classification.
13. The `create` destination does not already exist.

### 13.3 Render/Compose-Time Validation

Scaf validates:

1. Every active child question has a resolved answer.
2. Every child/child conflict has a compose rule.
3. Every parent/child overlap has a compose rule.
4. `render` rules produce the target parent output path.
5. `concat` sources all produce the target path as UTF-8 text.
6. Binary paths use pass-through ownership, `prefer`, or `render` backed by a static parent file copied byte-for-byte. Binary paths cannot use `concat` or a Jinja-templated parent file.
7. Missing context keys fail under strict undefined behavior.
8. New managed paths do not overwrite unmanaged local files during update.

### 13.4 Example Errors

#### Missing Compose Rule

```text
ScafConflictError: Both 'python' and 'docker' produce 'Makefile',
but no compose rule is defined for it.

Add a compose rule:

  compose:
    "Makefile":
      strategy: render

Or suppress/exclude one child output:

  dependencies:
    - name: docker
      suppress:
        - Makefile
```

#### Unresolved Child Answer

```text
ScafAnswerError: Child 'python' requires answer for 'linter',
but it has no active default and is not mapped in dependencies[].answers.

Define a parent question and map it:

  dependencies:
    - name: python
      answers:
        linter: "{{ linter }}"

Or pin a literal value:

  dependencies:
    - name: python
      answers:
        linter: "ruff"
```

#### Parent Overlap Without Rule

```text
ScafConflictError: Parent renders 'README.md', and child 'python'
also produces 'README.md'. Parent-over-child overwrite is not implicit.

Declare ownership explicitly:

  compose:
    "README.md":
      strategy: render
```

#### Missing Required Section

```text
ScafTemplateError: In template/README.md.jinja, line 12:

  {{ scaf.children.python.text["README.md"] | section("## Development") }}

Heading '## Development' was not found in child 'python' file 'README.md'.
If this section is optional, pass required=False.
```

---

## 14. CLI

### 14.1 Commands

```bash
scaf create <parent-repo> <destination> [--vcs-ref <ref>] [--answers-file <path>] [--defaults]
scaf preview <parent-repo> [--vcs-ref <ref>] [--answers-file <path>] [--defaults]
scaf validate <parent-repo-or-path> [--offline]
scaf update [--vcs-ref <ref>]
scaf status
```

For `create`, `<destination>` is always explicit and follows the assembly rules in §8.5 for both Compose parents and the existing single-template fallback. `--vcs-ref` selects the parent branch, tag, or commit; when omitted, the parent uses Copier 8.1's highest-release-or-`HEAD` default. On `update`, `--vcs-ref` replaces the stored requested parent ref only after a successful reconciliation.

### 14.2 `scaf preview`

Dry-runs enough of the pipeline to show:

- resolved children
- excluded files
- suppressed files
- context files
- pass-through candidates
- required compose paths
- unresolved conflicts
- managed file ownership summary

Example:

```text
Scaf Preview — https://github.com/myorg/fullstack-python-template.git

Children:
  python   https://github.com/getscaf/copier-python.git          ref v1.0.3
  docker   https://github.com/getscaf/copier-docker.git          ref v2.0.1
  ci       https://github.com/getscaf/copier-github-actions.git  ref v0.3.2

Required compose paths:
  README.md    → render   ✓ parent owns output
  Makefile     → render   ✓ parent owns output
  .gitignore   → concat   ✓ python, docker, ci

Pass-through files:
  python: pyproject.toml, src/__init__.py
  docker: Dockerfile, docker-compose.yml
  ci: .github/workflows/ci.yml

Suppressed files:
  python: README.md, Makefile
  docker: README.md, Makefile
  ci: README.md

All final paths have exactly one owner.
```

### 14.3 `scaf validate`

Performs schema and static manifest validation.

With network access, it may resolve child templates to validate child answer keys. With `--offline`, it validates only locally available information.

`scaf validate` does not guarantee render-time success. Use `scaf preview` to exercise rendering and conflict detection.

### 14.4 `scaf status`

Shows current project state:

- parent repo and locked ref
- child repos and locked refs
- managed file counts by owner kind
- suppressed and excluded counts
- local update conflicts if detectable

### 14.5 Commands Omitted from v1

```bash
scaf eject
scaf update --child <name>
```

These may be added after the v1 ownership and state model has proven stable.

---

## 15. Worked Composition Example

A parent template composes a Python library template, a Docker template, and a GitHub Actions CI template. The repository names and tags below are illustrative contract fixtures, not a network smoke test. They use URL and ref forms that Copier 8.1 recognizes; a runnable template must substitute reachable Git repositories and tags that implement the shown questions and output contract.

### 15.1 Parent Template Structure

```text
fullstack-python-template/
├── copier.yaml
├── scaf.yaml
└── template/
    ├── README.md.jinja
    ├── Makefile.jinja
    └── .github/
        └── CODEOWNERS.jinja
```

### 15.2 `scaf.yaml`

```yaml
_min_scaf_version: "1.0.0"

dependencies:
  - name: python
    repo: https://github.com/getscaf/copier-python.git
    ref: "v1.0.3"
    answers:
      project_name: "{{ project_name }}"
      python_version: "{{ python_version }}"
      linter: "{{ linter }}"
    suppress:
      - README.md
      - Makefile
    context:
      - README.md
      - Makefile

  - name: docker
    repo: https://github.com/getscaf/copier-docker.git
    ref: "v2.0.1"
    answers:
      project_name: "{{ project_name }}"
      base_image: "python:{{ python_version }}-slim"
    suppress:
      - README.md
      - Makefile
    context:
      - README.md
      - Makefile

  - name: ci
    repo: https://github.com/getscaf/copier-github-actions.git
    ref: "v0.3.2"
    answers:
      project_name: "{{ project_name }}"
      language: "python"
    suppress:
      - README.md
    context:
      - README.md

compose:
  "README.md":
    strategy: render

  "Makefile":
    strategy: render

  ".gitignore":
    strategy: concat
    sources: [python, docker, ci]
    separator: "\n\n"
    dedupe_lines: true
    header: "# Generated by Scaf Compose\n"
```

### 15.3 Parent `copier.yaml`

```yaml
project_name:
  type: str
  help: Project name

project_description:
  type: str
  help: A short description of your project

python_version:
  type: str
  default: "3.12"
  choices: ["3.10", "3.11", "3.12", "3.13"]

linter:
  type: str
  default: "ruff"
  choices: ["ruff", "flake8"]

team_name:
  type: str
  help: Team name for CODEOWNERS
```

### 15.4 `template/README.md.jinja`

````markdown
# {{ project_name }}

{{ project_description }}

## Quick Start

```bash
make setup
make run
```

## Development

{{ scaf.children.python.text["README.md"] | section("## Development") }}

## Docker

{{ scaf.children.docker.text["README.md"] | section("## Configuration", required=False) }}

## CI

{{ scaf.children.ci.text["README.md"] | section("## Workflows", required=False) }}
````

### 15.5 `template/Makefile.jinja`

```makefile
.DEFAULT_GOAL := help

# Python
{{ scaf.children.python.text["Makefile"] | lines_removing("^\\.DEFAULT_GOAL") }}

# Docker
{{ scaf.children.docker.text["Makefile"] | lines_removing("^\\.DEFAULT_GOAL") }}

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \\033[36m%-20s\\033[0m %s\n", $$1, $$2}'
```

### 15.6 Why This Composition Is Valid

1. Root-level child `README.md` and `Makefile` files are suppressed, so they are not emitted automatically; the root-relative bare globs do not affect nested files with the same names.
2. Those root-level files are explicitly allowlisted in `context`, so parent templates can read them.
3. Final `README.md` and `Makefile` are explicitly owned by `strategy: render` rules.
4. `.gitignore` is explicitly owned by `strategy: concat` with ordered sources.
5. All final output paths have exactly one owner.

---

## 16. Future Work

The following may be added after v1:

1. Child-question exposure, likely namespaced rather than flat.
2. Prompt deduplication and custom prompt ordering.
3. Nested composition.
4. `scaf eject`.
5. `scaf update --child <name>`.
6. Conditional dependencies.
7. Format-aware merge helpers or optional merge-extension packages.
8. Source-path remapping for compose rules.
9. Lazy context loading beyond explicit `context` allowlists.
10. Richer update and merge behavior.
11. Project-local manifest editing with explicit lock/state reconciliation.

---

## 17. Summary

Scaf Compose v1 is intentionally strict:

- Parent owns prompts.
- Parent owns composition.
- Every final path has exactly one owner.
- Parent/child overlaps are hard conflicts unless declared.
- Child questions are not auto-exposed.
- Child text is exposed only through explicit `context` allowlists.
- Scaf core provides only text-oriented composition helpers.
- State is Scaf-owned under `.scaf/`.
- Updates use conservative managed-file reconciliation.

This design keeps v1 shippable while preserving a path to richer composition features later.
