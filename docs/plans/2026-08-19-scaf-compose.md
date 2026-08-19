# Scaf Compose v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add strict multi-template composition, inspection, and recoverable updates while preserving the existing single-template Copier flow.

**Architecture:** Replace the behavior-heavy Bash entry point with a thin launcher and a Python package. Keep policy code separate from Git, Copier, filesystem, and process adapters. Build complete candidates before destination mutation, and protect updates with durable rollback journals.

**Tech Stack:** Python 3.12 development environment, Python 3.10 minimum runtime, Copier 8.1.0, Jinja2, PyYAML, semantic-version, pytest, Bash, and Nix.

## Global Constraints

- Implement the contract in `docs/specs/2026-08-19-scaf-compose-design.md`.
- Keep dependency graphs flat. A child that contains `scaf.yaml` is invalid in v1.
- Resolve every Compose parent and child to a Git commit.
- Reject non-Git and dirty local Compose sources.
- Resolve a relative parent path from the invocation directory.
- Resolve a relative child path from the resolved parent root.
- Reject absolute, empty, parent-traversal, and backslash paths or globs.
- Treat only regular files as managed or rendered Compose output.
- Reject symlinks, devices, FIFOs, sockets, and file-directory transitions on managed Compose paths.
- Keep native Copier filesystem behavior on the single-template fallback.
- Validate managed-path ancestors with `lstat()` before planning and again before mutation or recovery.
- Preserve Copier 8.1.0 default ref selection: highest non-prerelease PEP 440 tag, then `HEAD`.
- Treat same-named branches and tags as ambiguous unless the selector is fully qualified.
- Compare `_min_scaf_version` with SemVer 2.0.0 precedence.
- Let only the parent define user-facing questions.
- Never run child `_tasks`.
- Run parent `_tasks` once during staged `create` only.
- Keep Scaf core text-oriented. Do not add YAML, TOML, or JSON merge behavior.
- Give every final path one explicit owner.
- Treat undeclared child conflicts and parent overlaps as hard errors.
- Expose child text only through explicit `context` globs.
- Do not write a root `.copier-answers.yml` for Compose projects.
- Store normalized configuration in `.scaf/manifest.yml`.
- Store exact source commits in `.scaf/lock.yml`.
- Store parent and child values under `.scaf/answers/`.
- Store managed-file hashes and modes in `.scaf/state.json`.
- Reserve final `.scaf/` paths for Scaf state and reject template ownership there.
- Require an explicit, absent destination for `create`.
- Build `create` output in a sibling staging directory and commit with one directory rename.
- Compute every update conflict before the first project mutation.
- Prepare and persist the rollback journal before the first update mutation.
- Keep parent tasks disabled during `update`, `preview`, and `validate`.
- Keep `scaf eject` and partial child updates out of v1.
- Preserve the current legacy invocation as a compatibility alias.
- Apply TDD to behavior, parsing, validation, recovery, and error handling.
- Do not add tests for dependency pins, Nix text, workflow text, or documentation text.
- Verify static packaging changes with builds, imports, ShellCheck, and Nix commands.

---

## Planned File Structure

### Runtime package

- Create `pyproject.toml` for the installable `scaf` application and console script.
- Create `requirements-runtime.in` as the runtime dependency source.
- Modify `requirements.in` to include runtime and development dependencies.
- Regenerate `requirements.txt` from `requirements.in`.
- Modify `scaf` into a thin source-checkout launcher.
- Create `src/scaf_cli/__init__.py` for the public package version.
- Create `src/scaf_cli/__main__.py` for `python -m scaf_cli`.
- Create `src/scaf_cli/version.py` for the release-managed version string.
- Create `src/scaf_cli/errors.py` for the seven public error classes.
- Create `src/scaf_cli/cli.py` for argument parsing, exit codes, and error display.
- Create `src/scaf_cli/legacy.py` for current invocation compatibility.
- Create `src/scaf_cli/paths.py` for relative-path validation and root-anchored globs.
- Create `src/scaf_cli/managed_paths.py` for `lstat()` safety and regular-file enforcement.
- Create `src/scaf_cli/atomic_fs.py` for durable writes and exclusive directory renames.
- Create `src/scaf_cli/versioning.py` for SemVer and runtime minimum checks.
- Create `src/scaf_cli/manifest.py` for `scaf.yaml` parsing and normalized models.
- Create `src/scaf_cli/git_client.py` for Git subprocess calls and repository facts.
- Create `src/scaf_cli/sources.py` for source location, selector classification, and locks.
- Create `src/scaf_cli/answers.py` for native Jinja answer mappings.
- Create `src/scaf_cli/copier_compat.py` for every pinned Copier 8.1.0 private call.
- Create `src/scaf_cli/copier_questions.py` for parent and child question policy.
- Create `src/scaf_cli/copier_render.py` for pinned task-free Copier rendering.
- Create `src/scaf_cli/inventory.py` for rendered bytes, modes, and classifications.
- Create `src/scaf_cli/filters.py` for the five built-in text filters.
- Create `src/scaf_cli/parent_context.py` for the parent `scaf` namespace.
- Create `src/scaf_cli/ownership.py` for conflict detection and final owners.
- Create `src/scaf_cli/composition.py` for `render`, `concat`, and `prefer`.
- Create `src/scaf_cli/state_files.py` for manifest, lock, answers, and managed state.
- Create `src/scaf_cli/staging.py` for candidate materialization and create commit.
- Create `src/scaf_cli/parent_tasks.py` for deferred parent task execution.
- Create `src/scaf_cli/candidate.py` for non-mutating resolution, rendering, ownership analysis, and candidate assembly.
- Create `src/scaf_cli/create.py` for Compose and single-template creation.
- Create `src/scaf_cli/validate.py` for static manifest validation.
- Create `src/scaf_cli/preview.py` for rendered ownership previews.
- Create `src/scaf_cli/status.py` for local project-state inspection.
- Create `src/scaf_cli/reports.py` for deterministic command output.
- Create `src/scaf_cli/reconciliation.py` for pure update planning.
- Create `src/scaf_cli/journal.py` for durable update-journal preparation.
- Create `src/scaf_cli/transactions.py` for update commit and rollback.
- Create `src/scaf_cli/recovery.py` for journal-state recovery and cleanup.
- Create `src/scaf_cli/update.py` for full-graph update orchestration.

### Test support

- Create `tests/conftest.py` for shared temporary paths.
- Create `tests/support/git_repositories.py` for committed local repository fixtures.
- Create `tests/support/copier_templates.py` for parent and child template fixtures.
- Create `tests/support/failing_file_ops.py` for deterministic transaction faults.
- Create focused unit tests beside each policy boundary under `tests/unit/`.
- Create command and pipeline tests under `tests/integration/`.

### Packaging and documentation

- Modify `install.sh` to install the Python application with `uv tool`.
- Modify `default.nix` to package the Python application and its runtime dependencies.
- Modify `flake.nix` to expose the package and its checks.
- Modify `.releaserc.json` to update `src/scaf_cli/version.py` during releases.
- Modify `README.md` with the new commands and compatibility syntax.
- Modify `CONTRIBUTING.md` with setup, test, lint, and fixture instructions.

### Dependency direction

```text
version/errors/paths/managed_paths/atomic_fs/versioning/manifest
    ↓
git_client/sources     answers/copier_compat/copier_questions/copier_render/inventory
          ↘                         ↙
           parent_context/filters
                    ↓
        ownership/composition/state_files
                    ↓
                candidate ─────────────→ create → staging
                    ├──────────────────→ preview
                    └→ reconciliation → journal → transactions/recovery → update
sources/copier_questions ──────────────→ validate
state_files/recovery ──────────────────→ status
create/validate/preview/update/status ─→ reports → cli/legacy
```

The command modules are facades. Pure modules do not import command, network, prompt, or process code.

---

### Task 1: Scaffold the Python application and pinned runtime

**Files:**
- Create: `pyproject.toml`
- Create: `requirements-runtime.in`
- Modify: `requirements.in`
- Modify: `requirements.txt`
- Modify: `scaf`
- Create: `src/scaf_cli/__init__.py`
- Create: `src/scaf_cli/__main__.py`
- Create: `src/scaf_cli/version.py`
- Create: `src/scaf_cli/cli.py`
- Create: `tests/unit/test_cli_bootstrap.py`

**Interfaces:**
- Produces: `scaf_cli.cli.build_parser() -> argparse.ArgumentParser`
- Produces: `scaf_cli.cli.main(argv: Sequence[str] | None = None) -> int`
- Produces: `scaf_cli.version.__version__: str`
- Consumes: no earlier task interfaces

- [ ] **Step 1: Write the failing bootstrap tests**

```python
import pytest

from scaf_cli.cli import build_parser, main
from scaf_cli.version import __version__


def test_parser_exposes_v1_commands():
    parser = build_parser()
    args = parser.parse_args(["create", "parent", "destination"])
    assert args.command == "create"
    assert args.parent_repo == "parent"
    assert args.destination == "destination"


def test_version_is_semver():
    assert __version__ == "1.26.2"


def test_main_exits_zero_for_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == "scaf 1.26.2"
```

- [ ] **Step 2: Run the tests and verify the import failure**

Run: `uv run --with pytest pytest tests/unit/test_cli_bootstrap.py -q`

Expected: FAIL because `scaf_cli` does not exist.

- [ ] **Step 3: Add the package metadata and runtime dependency source**

Use this runtime dependency set in `requirements-runtime.in`:

```text
binaryornot==0.4.4
copier==8.1.0
jinja2==3.1.6
packaging==25.0
pyyaml==6.0.2
pyyaml-include<2
semantic-version==2.10.0
```

Use one dependency source from `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "scaf"
dynamic = ["version", "dependencies"]
requires-python = ">=3.10"
description = "Compose and update projects from Copier templates"
readme = "README.md"

[project.scripts]
scaf = "scaf_cli.cli:console_main"

[project.optional-dependencies]
test = ["pytest==8.4.1"]

[dependency-groups]
dev = [
  "bandit==1.7.5",
  "black==24.3.0",
  "build>=1.2,<2",
  "isort==5.10.1",
  "pip-tools>=7.4,<8",
  "pre-commit>=4,<5",
  "ruff==0.0.290",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.dynamic]
version = {attr = "scaf_cli.version.__version__"}
dependencies = {file = ["requirements-runtime.in"]}

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

Add `-r requirements-runtime.in` at the start of `requirements.in`. Keep the existing development dependencies below it.

- [ ] **Step 4: Add the minimal package and parser**

```python
# src/scaf_cli/version.py
__version__ = "1.26.2"
```

```python
# src/scaf_cli/cli.py
from __future__ import annotations

import argparse
from collections.abc import Sequence

from .version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scaf")
    parser.add_argument("--version", action="version", version=f"scaf {__version__}")
    commands = parser.add_subparsers(dest="command")

    create = commands.add_parser("create")
    create.add_argument("parent_repo")
    create.add_argument("destination")

    preview = commands.add_parser("preview")
    preview.add_argument("parent_repo")

    validate = commands.add_parser("validate")
    validate.add_argument("parent_repo_or_path")

    commands.add_parser("update")
    commands.add_parser("status")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
    return 0


def console_main() -> None:
    raise SystemExit(main())
```

Make `src/scaf_cli/__main__.py` call `console_main()`. Export `__version__` from `src/scaf_cli/__init__.py`.

- [ ] **Step 5: Replace the root script with a source launcher**

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec uv run --project "$ROOT" python -m scaf_cli "$@"
```

- [ ] **Step 6: Install tools, regenerate dependencies, and run the bootstrap tests**

Run: `uv sync --extra test --group dev`

Run: `uv run pip-compile --allow-unsafe --generate-hashes --output-file=requirements.txt requirements.in`

Run: `uv run python -c 'import copier, yamlinclude; assert copier.__version__ == "8.1.0"'`

Run: `uv run pytest tests/unit/test_cli_bootstrap.py -q`

Expected: 3 passed. The direct import command verifies the pinned runtime without adding a static dependency test.

- [ ] **Step 7: Commit the application scaffold**

```bash
git add pyproject.toml requirements-runtime.in requirements.in requirements.txt scaf src/scaf_cli tests/unit/test_cli_bootstrap.py
git commit -m "feat(cli): scaffold Python application"
```

---

### Task 2: Add public errors, SemVer checks, and root-anchored globs

**Files:**
- Create: `src/scaf_cli/errors.py`
- Create: `src/scaf_cli/versioning.py`
- Create: `src/scaf_cli/paths.py`
- Create: `tests/unit/test_versioning.py`
- Create: `tests/unit/test_paths.py`

**Interfaces:**
- Produces: seven `ScafError` subclasses from the specification
- Produces: `require_minimum_version(required: str | None, current: str) -> None`
- Produces: `normalize_relative_path(raw: str, field: str) -> str`
- Produces: `RootGlob.parse(raw: str, field: str) -> RootGlob`
- Produces: `RootGlob.matches(path: str) -> bool`
- Consumes: `scaf_cli.version.__version__`

- [ ] **Step 1: Write failing SemVer and path tests**

```python
import pytest

from scaf_cli.errors import ScafValidationError
from scaf_cli.paths import RootGlob, normalize_relative_path
from scaf_cli.versioning import require_minimum_version


@pytest.mark.parametrize("required", ["1", "1.0", "v1.0.0", "1.0.0-"])
def test_rejects_non_semver_minimum(required):
    with pytest.raises(ScafValidationError, match="_min_scaf_version"):
        require_minimum_version(required, "1.26.2")


def test_uses_semver_prerelease_order():
    with pytest.raises(ScafValidationError, match="requires Scaf 2.0.0"):
        require_minimum_version("2.0.0", "2.0.0-rc.1")


def test_ignores_semver_build_metadata_for_precedence():
    require_minimum_version("1.26.2+template.9", "1.26.2+build.1")


@pytest.mark.parametrize("raw", ["", "/README.md", "../README.md", "a/../b", r"docs\\x.md"])
def test_rejects_unsafe_relative_paths(raw):
    with pytest.raises(ScafValidationError):
        normalize_relative_path(raw, "compose path")


def test_globs_are_root_anchored():
    root_readme = RootGlob.parse("README.md", "context")
    all_readmes = RootGlob.parse("**/README.md", "context")
    direct_docs = RootGlob.parse("docs/*.md", "context")
    assert root_readme.matches("README.md")
    assert not root_readme.matches("nested/README.md")
    assert all_readmes.matches("README.md")
    assert all_readmes.matches("nested/README.md")
    assert direct_docs.matches("docs/guide.md")
    assert not direct_docs.matches("docs/deep/guide.md")


def test_segment_operators_are_case_sensitive():
    assert RootGlob.parse("src/?.py", "context").matches("src/a.py")
    assert not RootGlob.parse("src/?.py", "context").matches("src/ab.py")
    assert RootGlob.parse("src/[ab].py", "context").matches("src/a.py")
    assert RootGlob.parse("src/[!a].py", "context").matches("src/b.py")
    assert not RootGlob.parse("README.md", "context").matches("readme.md")
```

- [ ] **Step 2: Run the focused tests and verify the missing modules**

Run: `uv run pytest tests/unit/test_versioning.py tests/unit/test_paths.py -q`

Expected: FAIL because the modules do not exist.

- [ ] **Step 3: Add the public exception hierarchy**

```python
class ScafError(Exception):
    """Base class for user-facing Scaf errors."""


class ScafValidationError(ScafError):
    """The manifest, path, destination, strategy, or version is invalid."""


class ScafResolveError(ScafError):
    """A source or ref cannot resolve to a stable commit."""


class ScafAnswerError(ScafError):
    """A required child answer cannot be resolved."""


class ScafConflictError(ScafError):
    """A final output path has ambiguous ownership."""


class ScafTemplateError(ScafError):
    """A parent render, filter, context access, or task failed."""


class ScafUpdateConflictError(ScafError):
    """A safe update cannot preserve local project changes."""


class ScafTransactionError(ScafError):
    """A create commit, update commit, rollback, or recovery failed."""
```

- [ ] **Step 4: Implement SemVer comparison with `semantic_version.Version`**

```python
from semantic_version import Version

from .errors import ScafValidationError


def require_minimum_version(required: str | None, current: str) -> None:
    if required is None:
        return
    try:
        minimum = Version(required)
        running = Version(current)
    except ValueError as error:
        raise ScafValidationError(
            f"_min_scaf_version must be a SemVer 2.0.0 string: {required!r}"
        ) from error
    if running < minimum:
        raise ScafValidationError(
            f"This template requires Scaf {minimum} or newer; running {running}."
        )
```

- [ ] **Step 5: Implement segment-based, case-sensitive glob matching**

Use recursive matching where only a complete `**` segment crosses directories:

```python
from dataclasses import dataclass
from fnmatch import fnmatchcase
from functools import lru_cache

from .errors import ScafValidationError


def normalize_relative_path(raw: str, field: str) -> str:
    if not isinstance(raw, str) or not raw or raw.startswith("/") or "\\" in raw:
        raise ScafValidationError(f"Invalid {field}: {raw!r}")
    parts = raw.split("/")
    if any(part in {"", ".."} for part in parts):
        raise ScafValidationError(f"Invalid {field}: {raw!r}")
    normalized = "/".join(part for part in parts if part != ".")
    if not normalized:
        raise ScafValidationError(f"Invalid {field}: {raw!r}")
    return normalized


@dataclass(frozen=True)
class RootGlob:
    raw: str
    parts: tuple[str, ...]

    @classmethod
    def parse(cls, raw: str, field: str) -> "RootGlob":
        normalized = normalize_relative_path(raw, field)
        return cls(raw=normalized, parts=tuple(normalized.split("/")))

    def matches(self, path: str) -> bool:
        path_parts = tuple(normalize_relative_path(path, "rendered path").split("/"))

        @lru_cache(maxsize=None)
        def match(pattern_index: int, path_index: int) -> bool:
            if pattern_index == len(self.parts):
                return path_index == len(path_parts)
            pattern = self.parts[pattern_index]
            if pattern == "**":
                return match(pattern_index + 1, path_index) or (
                    path_index < len(path_parts) and match(pattern_index, path_index + 1)
                )
            return (
                path_index < len(path_parts)
                and fnmatchcase(path_parts[path_index], pattern)
                and match(pattern_index + 1, path_index + 1)
            )

        return match(0, 0)
```

- [ ] **Step 6: Run the focused tests**

Run: `uv run pytest tests/unit/test_versioning.py tests/unit/test_paths.py -q`

Expected: all tests pass.

- [ ] **Step 7: Commit the validation primitives**

```bash
git add src/scaf_cli/errors.py src/scaf_cli/versioning.py src/scaf_cli/paths.py tests/unit/test_versioning.py tests/unit/test_paths.py
git commit -m "feat(compose): add validation primitives"
```

---

### Task 3: Parse and normalize `scaf.yaml`

**Files:**
- Create: `src/scaf_cli/manifest.py`
- Create: `tests/unit/test_manifest.py`

**Interfaces:**
- Produces: `DependencySpec`, `RenderRule`, `ConcatRule`, `PreferRule`, and `ComposeManifest`
- Produces: `parse_manifest(text: str, current_version: str) -> ComposeManifest`
- Produces: `load_manifest(root: Path, current_version: str) -> ComposeManifest`
- Consumes: `RootGlob`, `normalize_relative_path()`, and `require_minimum_version()`

- [ ] **Step 1: Write failing schema tests**

Cover these behaviors in one parameter table:

```python
@pytest.mark.parametrize(
    ("yaml_text", "message"),
    [
        ("unknown: true", "Unknown scaf.yaml field"),
        ("dependencies: [{name: python}]", "repo"),
        (
            "dependencies: [{name: python, repo: a}, {name: python, repo: b}]",
            "Duplicate dependency name 'python'",
        ),
        (
            "dependencies: [{name: python, repo: a}]\ncompose:\n  x:\n    strategy: concat",
            "sources",
        ),
        (
            "dependencies: [{name: python, repo: a}]\ncompose:\n  x:\n    strategy: prefer\n    source: missing",
            "unknown child 'missing'",
        ),
        (
            "dependencies: []\ncompose:\n  /absolute:\n    strategy: render",
            "compose path",
        ),
    ],
)
def test_rejects_invalid_manifest(yaml_text, message):
    with pytest.raises(ScafValidationError, match=message):
        parse_manifest(yaml_text, "1.26.2")
```

Add a positive test that parses every dependency field and every strategy. Assert normalized tuples and default values.

Add negative tests for child names that are unsafe Jinja identifiers. Add a negative test for any compose target under `.scaf/`.

- [ ] **Step 2: Run the manifest tests and verify the missing parser**

Run: `uv run pytest tests/unit/test_manifest.py -q`

Expected: FAIL because `scaf_cli.manifest` does not exist.

- [ ] **Step 3: Add immutable manifest models**

```python
@dataclass(frozen=True)
class DependencySpec:
    name: str
    repo: str
    ref: str | None
    answers: Mapping[str, object]
    exclude: tuple[RootGlob, ...]
    suppress: tuple[RootGlob, ...]
    context: tuple[RootGlob, ...]


@dataclass(frozen=True)
class RenderRule:
    strategy: Literal["render"] = "render"


@dataclass(frozen=True)
class ConcatRule:
    sources: tuple[str, ...]
    separator: str = "\n\n"
    dedupe_lines: bool = False
    header: str | None = None
    strategy: Literal["concat"] = "concat"


@dataclass(frozen=True)
class PreferRule:
    source: str
    strategy: Literal["prefer"] = "prefer"


ComposeRule = RenderRule | ConcatRule | PreferRule


@dataclass(frozen=True)
class ComposeManifest:
    minimum_scaf_version: str | None
    dependencies: tuple[DependencySpec, ...]
    compose: Mapping[str, ComposeRule]
```

- [ ] **Step 4: Implement strict key and type validation**

The parser must reject unknown top-level, dependency, and strategy fields. Apply version validation immediately after YAML decoding. Then parse dependencies before compose rules.

Use these exact field sets:

```python
TOP_LEVEL_FIELDS = {"_min_scaf_version", "dependencies", "compose"}
DEPENDENCY_FIELDS = {"name", "repo", "ref", "answers", "exclude", "suppress", "context"}
RENDER_FIELDS = {"strategy"}
CONCAT_FIELDS = {"strategy", "sources", "separator", "dedupe_lines", "header"}
PREFER_FIELDS = {"strategy", "source"}
```

Require child names to match `[A-Za-z_][A-Za-z0-9_]*`. Reject duplicate names, empty `concat.sources`, unknown children, invalid paths, reserved `.scaf/` targets, and invalid globs. Keep dependency order and compose mapping order.

- [ ] **Step 5: Run the manifest tests**

Run: `uv run pytest tests/unit/test_manifest.py -q`

Expected: all tests pass.

- [ ] **Step 6: Commit the manifest parser**

```bash
git add src/scaf_cli/manifest.py tests/unit/test_manifest.py
git commit -m "feat(compose): parse strict manifests"
```

---

### Task 4: Resolve Git sources and classify refs

**Files:**
- Create: `src/scaf_cli/git_client.py`
- Create: `src/scaf_cli/sources.py`
- Create: `tests/support/git_repositories.py`
- Create: `tests/unit/test_sources.py`

**Interfaces:**
- Produces: `ResolvedSource(locator: str, resolved_locator: str, root: Path, requested_ref: str | None, selector_kind: Literal["omitted", "branch", "tag", "commit"], selected_ref: str, commit: str)`
- Produces: `ResolutionWorkspace(root: Path)` as a context manager that owns every temporary clone and checkout
- Produces: `ResolutionWorkspace.resolve(locator: str, requested_ref: str | None, base: Path, require_clean: bool = True) -> ResolvedSource`
- Produces: `ResolutionWorkspace.verify_locked_tag(source: ResolvedSource, selected_ref: str, commit: str) -> None`
- Consumes: `ScafResolveError`

- [ ] **Step 1: Build committed local repository fixtures**

Add helpers that initialize a repository, set test identity, commit files, create tags, create branches, and return commit IDs.

```python
def commit_files(repo: Path, files: Mapping[str, str], message: str) -> str:
    for relative, content in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
```

- [ ] **Step 2: Write failing ref policy tests**

Cover:

- A relative parent path uses the invocation directory.
- A relative child path uses the resolved parent root and keeps its normalized parent-relative locator.
- An absolute local path remains canonical.
- A `file://` bare remote exercises clone and remote-ref handling without network access.
- `ResolvedSource.resolved_locator` stores the canonical path used for Git operations.
- A dirty, non-Git, or unborn local repository raises `ScafResolveError`.
- An omitted selector chooses the highest non-prerelease PEP 440 tag.
- Equivalent spellings `1.0` and `v1.0` preserve Copier and Git stable tag order.
- If no valid release tag exists, an omitted selector chooses `HEAD`.
- A same-named branch and tag is ambiguous.
- `refs/heads/name` and `refs/tags/name` are unambiguous.
- A full commit ID is classified as `commit`.
- An annotated tag resolves to its peeled commit object ID.
- If a range-like literal ref such as `~1.0` is absent, resolution fails.
- Tracked, staged, and untracked local changes each make a source dirty.
- Dispatch can inspect a committed local Git tree with `require_clean=False` without reading dirty working-tree files.
- A selected tag that moved from its locked commit is rejected.
- Successful context exit removes all temporary clones and checkouts.
- Exceptional context exit removes temporary data without changing a local source repository.

- [ ] **Step 3: Run the source tests and verify the missing resolver**

Run: `uv run pytest tests/unit/test_sources.py -q`

Expected: FAIL because the resolver modules do not exist.

- [ ] **Step 4: Implement the narrow Git subprocess adapter**

`GitClient` must expose these operations only:

```text
is_repository(path: Path) -> bool
is_clean(path: Path) -> bool
head(path: Path) -> str
list_refs(path: Path, namespace: str) -> Mapping[str, str]
resolve_commit(path: Path, selector: str) -> str
clone(locator: str, destination: Path) -> None
checkout(path: Path, commit: str) -> None
```

Run Git with `LC_ALL=C`. Capture stderr. Convert every non-zero result to `ScafResolveError` with the locator and selector.

- [ ] **Step 5: Implement selector classification and default selection**

Use `packaging.version.Version` only for omitted release-tag selection. Do not interpret ranges in an explicit ref.

```python
VALID_REQUEST_KINDS = frozenset({"omitted", "branch", "tag", "commit"})


def highest_release_tag(tags: Mapping[str, str]) -> str | None:
    releases: list[tuple[str, Version]] = []
    for name in sorted(tags):
        try:
            parsed = Version(name)
        except InvalidVersion:
            continue
        if not parsed.is_prerelease:
            releases.append((name, parsed))
    ranked = sorted(releases, key=lambda item: item[1], reverse=True)
    return ranked[0][0] if ranked else None
```

Treat explicit `HEAD` as a moving branch-kind selector with `selected_ref="HEAD"`. Store full commit object IDs.

Use `locator` for persisted manifest identity. Use `resolved_locator` for clone and Git calls. Peel annotated tags to commit objects before locking.

When `require_clean=False`, inspect only a separate checkout of the selected commit. Never inspect uncommitted local files through that result.

Create every remote clone and detached local checkout under `ResolutionWorkspace.root`. A `ResolvedSource.root` is valid only before workspace exit. Canonical local source repositories are never workspace-owned.

- [ ] **Step 6: Run the source tests**

Run: `uv run pytest tests/unit/test_sources.py -q`

Expected: all tests pass with local repositories only.

- [ ] **Step 7: Commit Git source resolution**

```bash
git add src/scaf_cli/git_client.py src/scaf_cli/sources.py tests/support/git_repositories.py tests/unit/test_sources.py
git commit -m "feat(compose): resolve Git sources"
```

---

### Task 5: Resolve parent and child answers through Copier

**Files:**
- Create: `src/scaf_cli/answers.py`
- Create: `src/scaf_cli/copier_compat.py`
- Create: `src/scaf_cli/copier_questions.py`
- Create: `tests/support/copier_templates.py`
- Create: `tests/unit/test_answers.py`

**Interfaces:**
- Produces: `DeferredTask(command: str | tuple[str, ...], extra_env: Mapping[str, str])`
- Produces: `Copier81Compatibility.require_supported_version() -> None`
- Produces: `Copier81Compatibility.collect_answers(worker: copier.Worker) -> Mapping[str, object]`
- Produces: `Copier81Compatibility.render_without_tasks(worker: copier.Worker) -> None`
- Produces: `Copier81Compatibility.finalize_tasks(worker: copier.Worker) -> tuple[DeferredTask, ...]`
- Produces: `collect_parent_answers(source: ResolvedSource, supplied: Mapping[str, object], defaults: bool, interactive: bool, ignore_removed: bool) -> Mapping[str, object]`
- Produces: `evaluate_answer_mapping(mapping: Mapping[str, object], parent_answers: Mapping[str, object]) -> Mapping[str, object]`
- Produces: `resolve_child_answers(child_name: str, source: ResolvedSource, supplied: Mapping[str, object]) -> Mapping[str, object]`
- Consumes: `ResolvedSource`, `DependencySpec`, `ScafAnswerError`, and `ScafValidationError`

- [ ] **Step 1: Add Copier template fixture builders**

Create clean local Git templates with configurable `copier.yaml`, template files, and commits. Keep every fixture offline.

- [ ] **Step 2: Write failing answer tests**

Test these exact cases:

- Parent questions preserve declared order.
- `--answers-file` values are parsed and validated by Copier.
- `--defaults` resolves parent defaults without a prompt.
- A child mapping overrides a child default.
- An active child default fills a missing mapping.
- A false `when:` condition makes an answer unnecessary.
- An active child question without a mapping or default raises `ScafAnswerError`.
- An unknown mapped child question raises `ScafValidationError`.
- Plain strings such as `"3.12"`, `"False"`, and `"[1]"` remain strings.
- An exact Jinja expression preserves a boolean, integer, list, or mapping value.
- A partial Jinja string produces text.
- A child mapping cannot access child output or an unknown variable.
- A monkeypatched incompatible Copier version fails before any private Worker call.

- [ ] **Step 3: Run the answer tests and verify the missing behavior**

Run: `uv run pytest tests/unit/test_answers.py -q`

Expected: FAIL because answer resolution does not exist.

- [ ] **Step 4: Add a Copier 8.1.0 compatibility guard**

At compatibility-adapter construction, compare `copier.__version__` with `8.1.0`. If the versions differ, raise an error before private Worker calls.

Keep `_ask()`, `_check_unsafe()`, `_render_folder()`, `_render_string()`, and every other private Copier call in `copier_compat.py`. Question and render modules consume only `Copier81Compatibility` methods.

Finalize tasks while the Worker environment is alive:

```python
@dataclass(frozen=True)
class DeferredTask:
    command: str | tuple[str, ...]
    extra_env: Mapping[str, str]


class Copier81Compatibility:
    def finalize_tasks(self, worker: Worker) -> tuple[DeferredTask, ...]:
        self.require_supported_version()
        result: list[DeferredTask] = []
        for task in worker.template.tasks:
            if isinstance(task.cmd, str):
                command: str | tuple[str, ...] = worker._render_string(task.cmd)
            else:
                command = tuple(worker._render_string(str(part)) for part in task.cmd)
            result.append(DeferredTask(command=command, extra_env=dict(task.extra_env)))
        return tuple(result)
```

- [ ] **Step 5: Evaluate mapped answers with a native Jinja environment**

```python
from jinja2 import Environment, StrictUndefined, meta, nodes
from jinja2.nativetypes import NativeEnvironment


def evaluate_answer_mapping(
    mapping: Mapping[str, object], parent_answers: Mapping[str, object]
) -> dict[str, object]:
    native_environment = NativeEnvironment(undefined=StrictUndefined)
    text_environment = Environment(undefined=StrictUndefined)
    result: dict[str, object] = {}
    for name, value in mapping.items():
        if not isinstance(value, str):
            result[name] = value
            continue
        if not any(marker in value for marker in ("{{", "{%", "{#")):
            result[name] = value
            continue
        ast = native_environment.parse(value)
        unknown = meta.find_undeclared_variables(ast) - parent_answers.keys()
        if unknown:
            names = ", ".join(sorted(unknown))
            raise ScafValidationError(f"Child answer '{name}' uses unknown variables: {names}")
        exact_expression = (
            len(ast.body) == 1
            and isinstance(ast.body[0], nodes.Output)
            and len(ast.body[0].nodes) == 1
            and not isinstance(ast.body[0].nodes[0], nodes.TemplateData)
        )
        environment = native_environment if exact_expression else text_environment
        result[name] = environment.from_string(value).render(**parent_answers)
    return result
```

V1 exposes no additional static answer variables because the specification defines none by name.

- [ ] **Step 6: Resolve child defaults and `when:` with Copier**

Construct a quiet Worker with mapped data and `defaults=True`. Call `Copier81Compatibility.collect_answers()` without rendering. Catch Copier validation errors and the required-question `ValueError`. Convert them to `ScafAnswerError` with child and question names.

Return only visible child question values. Do not return Copier metadata keys.

- [ ] **Step 7: Run the answer tests**

Run: `uv run pytest tests/unit/test_answers.py -q`

Expected: all tests pass.

- [ ] **Step 8: Commit answer resolution**

```bash
git add src/scaf_cli/answers.py src/scaf_cli/copier_compat.py src/scaf_cli/copier_questions.py tests/support/copier_templates.py tests/unit/test_answers.py
git commit -m "feat(compose): resolve template answers"
```

---

### Task 6: Render children without tasks and inventory their output

**Files:**
- Modify: `src/scaf_cli/copier_compat.py`
- Create: `src/scaf_cli/copier_render.py`
- Create: `src/scaf_cli/inventory.py`
- Create: `src/scaf_cli/managed_paths.py`
- Create: `tests/unit/test_inventory.py`
- Create: `tests/integration/test_child_render.py`

**Interfaces:**
- Produces: `PathFacts(path: Path, kind: Literal["missing", "regular", "directory", "symlink", "other"], mode: int | None)`
- Produces: `inspect_managed_path(project_root: Path, relative_path: str) -> PathFacts`
- Produces: `require_safe_ancestors(project_root: Path, relative_path: str) -> None`
- Produces: `FileRecord(path: str, content: bytes, mode: int, kind: Literal["text", "binary"])`
- Produces: `ChildRender(name: str, source: ResolvedSource, answers: Mapping[str, object], files: Mapping[str, FileRecord], excluded: tuple[str, ...], suppressed: tuple[str, ...], context_paths: tuple[str, ...])`
- Produces: `render_child(name: str, source: ResolvedSource, spec: DependencySpec, answers: Mapping[str, object]) -> ChildRender`
- Consumes: `DependencySpec`, `ResolvedSource`, and resolved child answers

- [ ] **Step 1: Write failing inventory tests**

Test classification precedence in this order:

1. `excluded`
2. `suppressed`
3. pass-through candidate
4. context visibility as an independent flag

Assert that binary context matches appear in `paths` but not in `text`. Assert that modes and executable bits survive collection.

- [ ] **Step 2: Write a failing child-task integration test**

Create a child with `_tasks` that writes `task-ran`. Render it through Scaf. Assert that `task-ran` does not exist and normal output does exist.

Also cover `_subdirectory`, child Jinja extensions, child validation, and absence of child `.copier-answers.yml` output.

Add rendered-output tests for a file symlink, directory symlink, FIFO, and socket. Each case must raise `ScafValidationError` without reading the target.

- [ ] **Step 3: Run the render tests and verify failure**

Run: `uv run pytest tests/unit/test_inventory.py tests/integration/test_child_render.py -q`

Expected: FAIL because child rendering and inventory do not exist.

- [ ] **Step 4: Implement output collection**

```python
@dataclass(frozen=True)
class FileRecord:
    path: str
    content: bytes
    mode: int
    kind: Literal["text", "binary"]

    @property
    def text(self) -> str:
        if self.kind == "binary":
            raise ScafTemplateError(f"Binary file '{self.path}' is not text context.")
        return self.content.decode("utf-8")
```

Walk entries in sorted POSIX-path order and inspect each with `lstat()`. Reject symlinks and non-regular leaf objects before any byte read. Store `stat.S_IMODE(lstat_result.st_mode)`. Classify UTF-8 decoding failures as binary.

- [ ] **Step 5: Render through the pinned Worker without executing tasks**

Keep private Copier calls in one method:

```python
class Copier81Compatibility:
    def render_without_tasks(self, worker: Worker) -> None:
        self.require_supported_version()
        worker._check_unsafe("copy")
        worker._ask()
        worker._render_folder(worker.template_copy_root)
```

Construct the Worker with `unsafe=True`, `quiet=True`, `overwrite=False`, resolved commit as `vcs_ref`, and an internal answers path. Delete the internal answers file before inventory.

The adapter owns cleanup on every error. Wrap Copier render and extension errors with `ScafTemplateError`. Preserve `ScafAnswerError` from answer resolution.

- [ ] **Step 6: Reject nested Compose children**

If a child root contains `scaf.yaml`, raise `ScafValidationError` after source resolution and before rendering.

- [ ] **Step 7: Run the render tests**

Run: `uv run pytest tests/unit/test_inventory.py tests/integration/test_child_render.py -q`

Expected: all tests pass and the child task marker remains absent.

- [ ] **Step 8: Commit child rendering**

```bash
git add src/scaf_cli/copier_compat.py src/scaf_cli/copier_render.py src/scaf_cli/inventory.py src/scaf_cli/managed_paths.py tests/unit/test_inventory.py tests/integration/test_child_render.py
git commit -m "feat(compose): render isolated children"
```

---

### Task 7: Build parent context, filters, rendering, and deferred tasks

**Files:**
- Create: `src/scaf_cli/filters.py`
- Create: `src/scaf_cli/parent_context.py`
- Create: `src/scaf_cli/parent_tasks.py`
- Modify: `src/scaf_cli/copier_render.py`
- Create: `tests/unit/test_filters.py`
- Create: `tests/unit/test_parent_context.py`
- Create: `tests/integration/test_parent_render.py`

**Interfaces:**
- Produces: `build_parent_context(children: Sequence[ChildRender], required_paths: Sequence[str]) -> Mapping[str, object]`
- Produces: `register_builtin_filters(environment: jinja2.Environment) -> None`
- Produces: `ParentRender(files: Mapping[str, FileRecord], deferred_tasks: tuple[DeferredTask, ...])`
- Produces: `render_parent(source: ResolvedSource, parent_answers: Mapping[str, object], scaf_context: Mapping[str, object]) -> ParentRender`
- Produces: `run_parent_tasks(tasks: Sequence[DeferredTask], staging_root: Path) -> None`
- Consumes: `ChildRender`, `DeferredTask`, and parent answers

- [ ] **Step 1: Write failing filter tests**

Cover:

- `section()` stops at the next equal or higher heading and trims its result.
- `section(required=False)` returns an empty string.
- `between()` excludes both markers.
- Missing required markers raise `ScafTemplateError`.
- `lines_matching()` and `lines_removing()` preserve source order.
- `dedupe_lines()` preserves the first line and its line ending.
- Invalid regular expressions raise `ScafTemplateError`.

- [ ] **Step 2: Write failing context and parent render tests**

Assert the exact shape:

```python
assert context == {
    "scaf": {
        "children": {
            "python": {
                "paths": ["Makefile", "README.md", "logo.png"],
                "text": {"Makefile": "build:\n", "README.md": "# Python\n"},
            }
        },
        "compose": {"required_paths": ["Makefile", "README.md"]},
    }
}
```

Test strict missing-key errors, static binary parent files, Jinja binary rejection, parent extensions, duplicate static/Jinja destination paths, and rejected parent symlink output.

Add a parent extension used inside a string task and a sequence task. Assert that both commands are finalized before Worker cleanup.

- [ ] **Step 3: Run the tests and verify the missing modules**

Run: `uv run pytest tests/unit/test_filters.py tests/unit/test_parent_context.py tests/integration/test_parent_render.py -q`

Expected: FAIL because parent context and rendering do not exist.

- [ ] **Step 4: Implement all five filters as pure string functions**

Use `splitlines(keepends=True)` for line filters. Compare duplicate lines without `\r` or `\n`, then preserve the first matched line unchanged.

If Copier supplies source context, include the template path and line in the filter error.

- [ ] **Step 5: Build the explicit parent namespace**

Sort child paths. Preserve compose declaration order in `required_paths`. Include every non-excluded path in `paths`. Include only allowlisted UTF-8 files in `text`. Do not include child answers or conflict maps.

- [ ] **Step 6: Render the parent with strict undefined behavior**

Pass parent answers in the flat data of Copier and pass `scaf` as one additional data key. Add built-in filters to the existing Copier Worker Jinja environment. Parent extensions must remain active.

Set `StrictUndefined` before rendering. Use the task-free render path from Task 6. While the Copier Worker and extension environment are alive, call `Copier81Compatibility.finalize_tasks()`. Store only finalized commands and environment values in `ParentRender`.

Before rendering, map static and `.jinja` source paths to final paths. If both forms target one output, raise `ScafValidationError`.

- [ ] **Step 7: Implement deferred parent task execution**

Execute finalized string tasks with `shell=True`. Execute finalized sequence tasks as argument lists with `shell=False`. The task runner must not import Copier or Jinja.

Use the staging root as `cwd`. Inherit the process environment and overlay Copier task variables, including `STAGE=task`. Stop after the first non-zero exit or signal. Raise `ScafTemplateError` with the command and result.

- [ ] **Step 8: Run the parent tests**

Run: `uv run pytest tests/unit/test_filters.py tests/unit/test_parent_context.py tests/integration/test_parent_render.py -q`

Expected: all tests pass.

- [ ] **Step 9: Commit parent rendering**

```bash
git add src/scaf_cli/filters.py src/scaf_cli/parent_context.py src/scaf_cli/parent_tasks.py src/scaf_cli/copier_render.py tests/unit/test_filters.py tests/unit/test_parent_context.py tests/integration/test_parent_render.py
git commit -m "feat(compose): render parent context"
```

---

### Task 8: Compute ownership and compose final files

**Files:**
- Create: `src/scaf_cli/ownership.py`
- Create: `src/scaf_cli/composition.py`
- Create: `tests/unit/test_ownership.py`
- Create: `tests/unit/test_composition.py`

**Interfaces:**
- Produces: `Owner(kind: Literal["parent", "child", "render", "concat", "prefer"], sources: tuple[str, ...])`
- Produces: `OwnershipConflict(path: str, candidates: tuple[str, ...], reason: str)`
- Produces: `OwnershipAnalysis(by_path: Mapping[str, Owner], conflicts: tuple[OwnershipConflict, ...])`
- Produces: `analyze_ownership(manifest: ComposeManifest, children: Sequence[ChildRender], parent_files: Mapping[str, FileRecord]) -> OwnershipAnalysis`
- Produces: `require_ownership_map(analysis: OwnershipAnalysis) -> Mapping[str, Owner]`
- Produces: `compose_files(ownership: Mapping[str, Owner], manifest: ComposeManifest, children: Sequence[ChildRender], parent_files: Mapping[str, FileRecord]) -> Mapping[str, FileRecord]`
- Consumes: manifest rules, `ChildRender`, and parent `FileRecord` values

- [ ] **Step 1: Encode the specification truth table as failing tests**

Use a parameterized test for all seven rows in section 6.2. Add separate tests for:

- Two non-suppressed children without a rule.
- A parent overlap with a suppressed child.
- A parent overlap with a non-suppressed child.
- An excluded child path.
- A suppressed-only path with no final owner.
- A parent or non-excluded child output under reserved `.scaf/`.
- One final file path that is the directory prefix of another final file path.
- A rule whose required source output is missing.

Assert that analysis returns every conflict. Then assert actionable `ScafConflictError` text from `require_ownership_map()` and section 13.4.

- [ ] **Step 2: Write failing strategy tests**

Cover:

- `render` takes parent bytes and modes.
- `render` rejects missing parent output.
- `concat` follows explicit source order.
- `concat` accepts suppressed sources.
- `concat` rejects missing, excluded, or binary sources.
- `concat` deduplicates source-body lines before header and separators.
- `prefer` copies text or binary bytes and modes.
- `prefer` rejects unknown, missing, or excluded sources.
- Parent-only and uncontested child pass-through files remain unchanged.

- [ ] **Step 3: Run the ownership tests and verify failure**

Run: `uv run pytest tests/unit/test_ownership.py tests/unit/test_composition.py -q`

Expected: FAIL because ownership and composition do not exist.

- [ ] **Step 4: Implement ownership as a pure classification pass**

```python
@dataclass(frozen=True)
class Owner:
    kind: Literal["parent", "child", "render", "concat", "prefer"]
    sources: tuple[str, ...]


@dataclass(frozen=True)
class OwnershipConflict:
    path: str
    candidates: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class OwnershipAnalysis:
    by_path: Mapping[str, Owner]
    conflicts: tuple[OwnershipConflict, ...]
```

Collect all parent paths, non-excluded child paths, pass-through candidates, and compose keys. Apply explicit compose rules first. Then classify parent-only and single-child pass-through paths.

Treat final path-prefix collisions as structural ownership conflicts. Return every conflict in sorted path order. `require_ownership_map()` raises one actionable `ScafConflictError` from that analysis. Preview can display the same conflicts without mutating output.

Suppressed-only paths with no rule are intentionally absent from final output.

- [ ] **Step 5: Implement all three strategies**

For concat without deduplication, preserve each UTF-8 body exactly. Insert the header once, then join bodies with the configured separator.

For concat with deduplication, remove duplicate logical lines from source bodies in source order. Preserve the first line ending. Add the header and separators afterward.

Use mode `0o644` for concat output. Preserve source mode for render, prefer, and pass-through output.

- [ ] **Step 6: Run the ownership and composition tests**

Run: `uv run pytest tests/unit/test_ownership.py tests/unit/test_composition.py -q`

Expected: all tests pass.

- [ ] **Step 7: Commit ownership and strategies**

```bash
git add src/scaf_cli/ownership.py src/scaf_cli/composition.py tests/unit/test_ownership.py tests/unit/test_composition.py
git commit -m "feat(compose): enforce file ownership"
```

---

### Task 9: Write Compose state and stage create candidates

**Files:**
- Create: `src/scaf_cli/state_files.py`
- Create: `src/scaf_cli/staging.py`
- Create: `src/scaf_cli/atomic_fs.py`
- Create: `tests/unit/test_state_files.py`
- Create: `tests/integration/test_create_staging.py`

**Interfaces:**
- Produces: `ManagedFileState(path: str, owner: str, sources: tuple[str, ...], sha256: str, mode: int, executable: bool, kind: Literal["text", "binary"])`
- Produces: `ProjectState(manifest: Mapping[str, object], lock: Mapping[str, object], answers: Mapping[str, Mapping[str, object]], files: tuple[ManagedFileState, ...])`
- Produces: `write_candidate(staging_root: Path, files: Mapping[str, FileRecord], state: ProjectState) -> None`
- Produces: `load_project_state(project_root: Path) -> ProjectState`
- Produces: `rename_directory_noreplace(source: Path, destination: Path) -> None`
- Produces: `commit_create(staging_root: Path, destination: Path) -> None`
- Consumes: manifest, resolved source locks, answers, ownership, and final files

- [ ] **Step 1: Write failing state serialization tests**

Assert these stable shapes:

```yaml
# .scaf/lock.yml
schema_version: 1
parent:
  repo: /canonical/parent
  requested_ref: null
  selector_kind: omitted
  selected_ref: v1.0.0
  commit: 0123456789abcdef0123456789abcdef01234567
children: {}
```

```json
{
  "schema_version": 1,
  "files": [
    {
      "path": "README.md",
      "owner": "render",
      "sources": [],
      "sha256": "exact-lowercase-hex",
      "mode": 420,
      "executable": false,
      "kind": "text"
    }
  ]
}
```

Also assert normalized manifest content, parent and child answer files, sorted paths, and no root `.copier-answers.yml`.

Round-trip state through `load_project_state()`. Reject missing files, malformed YAML or JSON, unknown schema versions, duplicate managed paths, and unsafe paths.

A successful create must not leave `.scaf/transactions/`. That directory exists only while update commit or recovery work is pending.

- [ ] **Step 2: Write failing create staging tests**

Test:

- The staging directory is a destination sibling.
- Existing destinations fail before a renderer callback runs.
- File bytes and modes are exact.
- A render or state error removes staging.
- The final directory appears only after one rename.
- A rename error removes staging and raises `ScafTransactionError`.
- A destination created after initial validation is never replaced, even when it is an empty directory.
- An unsupported exclusive-rename platform fails instead of using overwrite-capable fallback behavior.

- [ ] **Step 3: Run the state and staging tests**

Run: `uv run pytest tests/unit/test_state_files.py tests/integration/test_create_staging.py -q`

Expected: FAIL because state writing and staging do not exist.

- [ ] **Step 4: Implement deterministic state builders**

Hash exact file bytes with SHA-256. Store `stat.S_IMODE(mode)` as an integer. Set `executable` from any execute bit.

Write YAML with `sort_keys=False` and safe types. Write JSON with two-space indentation, sorted object keys, and a final newline.

The normalized manifest must include source locators, requested refs, dependency fields, output classifications, and compose rules. The lock must keep requested selectors separate from resolved commits.

- [ ] **Step 5: Implement same-filesystem create staging**

Use `tempfile.mkdtemp(prefix=f".{destination.name}.scaf-", dir=destination.parent)`. Materialize managed files and complete `.scaf/` state there.

Recheck that the destination is absent after candidate completion. Then call `rename_directory_noreplace()` as the commit point. Never use overwrite semantics or copy files as a fallback.

On Linux, call `renameat2(AT_FDCWD, source, AT_FDCWD, destination, RENAME_NOREPLACE)` through `ctypes`. On macOS, call `renamex_np(source, destination, RENAME_EXCL)`. Convert `EEXIST` and unsupported-platform results to `ScafTransactionError`. Do not fall back to plain `rename()`.

- [ ] **Step 6: Run the state and staging tests**

Run: `uv run pytest tests/unit/test_state_files.py tests/integration/test_create_staging.py -q`

Expected: all tests pass.

- [ ] **Step 7: Commit state and staging**

```bash
git add src/scaf_cli/state_files.py src/scaf_cli/staging.py src/scaf_cli/atomic_fs.py tests/unit/test_state_files.py tests/integration/test_create_staging.py
git commit -m "feat(compose): stage project state"
```

---

### Task 10: Implement `scaf create` and single-template dispatch

**Files:**
- Create: `src/scaf_cli/candidate.py`
- Create: `src/scaf_cli/create.py`
- Modify: `src/scaf_cli/cli.py`
- Create: `tests/integration/test_create_command.py`
- Create: `tests/integration/test_single_template_fallback.py`

**Interfaces:**
- Produces: `AnswerInputs(values: Mapping[str, object], defaults: bool, interactive: bool, ignore_removed: bool)`
- Produces: `DispatchResult(mode: Literal["single", "compose"], source: ResolvedSource | None, local_root: Path)`
- Produces: `CandidateRequest(workspace: ResolutionWorkspace, parent: ResolvedSource, answers: AnswerInputs)`
- Produces: `CompositionAnalysis(parent: ResolvedSource, manifest: ComposeManifest, parent_answers: Mapping[str, object], children: tuple[ChildRender, ...], parent_render: ParentRender, classifications: Mapping[str, Mapping[str, tuple[str, ...]]], ownership: OwnershipAnalysis)`
- Produces: `ComposeCandidate(analysis: CompositionAnalysis, files: Mapping[str, FileRecord], state: ProjectState)`
- Produces: `resolve_dispatch(workspace: ResolutionWorkspace, parent_repo: str, vcs_ref: str | None, invocation_dir: Path) -> DispatchResult`
- Produces: `resolve_composition(request: CandidateRequest) -> CompositionAnalysis`
- Produces: `build_compose_candidate(analysis: CompositionAnalysis) -> ComposeCandidate`
- Produces: `CreateOptions(parent_repo: str, destination: Path, vcs_ref: str | None, answers_file: Path | None, defaults: bool, injected_answers: Mapping[str, object])`
- Produces: `create_project(options: CreateOptions, invocation_dir: Path) -> None`
- Consumes: all create-side interfaces from Tasks 3 through 9

- [ ] **Step 1: Write an end-to-end Compose create test**

Build one parent and three committed children. Include render, concat, prefer, pass-through, excluded, suppressed, context, binary, and executable outputs.

Run `main(["create", parent, destination, "--defaults"])`. Assert final bytes, modes, owners, locks, answers, and state hashes.

- [ ] **Step 2: Write failing safety and task tests**

Cover:

- Invalid `scaf.yaml` never falls back to Copier.
- A non-Git local parent with `scaf.yaml` raises `ScafResolveError`.
- A dirty local Git parent with uncommitted `scaf.yaml` raises `ScafResolveError`.
- A parent without `scaf.yaml` uses normal Copier copy behavior.
- A child task never runs.
- A parent task runs once after files and `.scaf/` exist.
- A parent task does not run after a composition failure.
- A parent task failure removes staging and leaves no destination.
- A parent task change to staged `.scaf/` raises `ScafTemplateError`.
- A task-created file remains absent from managed state.
- A task-modified managed file keeps the pre-task state hash and appears locally modified on the first update.
- Cleanup does not remove an external path that an unsandboxed task created.
- A Compose parent without `copier.yaml` raises `ScafValidationError`.
- A Git ref that adds `scaf.yaml` dispatches to Compose.
- A Git ref that removes `scaf.yaml` dispatches to the single-template flow.
- Candidate analysis and assembly never create or mutate the destination.
- Create cleans all resolution workspace paths after success and every failure.
- An existing destination prevents prompt, source, render, and task work.
- User-facing errors print the public class name and actionable message without a traceback.

- [ ] **Step 3: Run the create tests and verify failure**

Run: `uv run pytest tests/integration/test_create_command.py tests/integration/test_single_template_fallback.py -q`

Expected: FAIL because command orchestration does not exist.

- [ ] **Step 4: Implement the Compose create sequence**

Implement reusable candidate construction before destination mutation:

```text
resolve_dispatch
1. For a non-Git local source, inspect the working directory directly.
2. Reject a dirty local working tree that contains an uncommitted scaf.yaml.
3. For a Git or remote source, resolve the requested ref first.
4. Inspect scaf.yaml in that selected Git tree.
5. Return single mode if scaf.yaml is absent.
6. Require a clean local Git source and copier.yaml for Compose mode.

resolve_composition
1. Parse scaf.yaml and enforce _min_scaf_version.
2. Resolve parent answers from AnswerInputs.
3. Resolve child sources and child answers.
4. Render and inventory children in isolated temporary directories.
5. Build parent context and render the parent with finalized deferred tasks.
6. Return classifications and complete ownership analysis without mutation.

build_compose_candidate
1. Require conflict-free ownership.
2. Compose final file bytes and modes.
3. Build the complete raw candidate ProjectState.

create_project
1. Validate that the explicit destination is absent.
2. Enter one `ResolutionWorkspace` for dispatch, parent, and child sources.
3. Resolve dispatch and use single-template fallback when selected.
4. Resolve analysis and build a ComposeCandidate inside that workspace.
5. Materialize the candidate in sibling staging.
6. Snapshot staged .scaf metadata.
7. Run finalized parent tasks in staging.
8. Reject staged .scaf metadata changes.
9. Commit staging with the exclusive directory rename.
10. Exit the workspace and remove its temporary roots.
```

Temporary source and render directories must survive until parent rendering and composition finish. Consume `CompositionAnalysis` and `ComposeCandidate` before `ResolutionWorkspace` exit. Cleanup must preserve the original Scaf error class.

Snapshot every staged `.scaf/` path, byte sequence, and mode before parent tasks. Reject additions, removals, content changes, and mode changes afterward.

- [ ] **Step 5: Implement single-template fallback**

Call Copier with the resolved parent locator, explicit destination, parent `--vcs-ref`, merged answer data, defaults setting, and normal task behavior.

Merge answer-file data with `CreateOptions.injected_answers`. Reject duplicate keys with different values before Copier runs.

A non-Git local directory remains valid only on this path. Preserve its root `.copier-answers.yml` behavior.

Do not apply the Compose clean-tree or commit rules until `scaf.yaml` is found. An invalid `scaf.yaml` can never return to this fallback.

- [ ] **Step 6: Add create command options**

Add `--vcs-ref`, `--answers-file`, and `--defaults` to `create`. Resolve relative source, destination, and answers-file paths from the invocation directory.

Catch `ScafError` in `main()`. Print `<ClassName>: <message>` to stderr and return exit code 2. Let unexpected exceptions retain their tracebacks.

- [ ] **Step 7: Run the create tests**

Run: `uv run pytest tests/integration/test_create_command.py tests/integration/test_single_template_fallback.py -q`

Expected: all tests pass.

- [ ] **Step 8: Commit create orchestration**

```bash
git add src/scaf_cli/candidate.py src/scaf_cli/create.py src/scaf_cli/cli.py tests/integration/test_create_command.py tests/integration/test_single_template_fallback.py
git commit -m "feat(compose): create composed projects"
```

---

### Task 11: Implement static `validate`

**Files:**
- Create: `src/scaf_cli/validate.py`
- Create: `src/scaf_cli/reports.py`
- Modify: `src/scaf_cli/cli.py`
- Create: `tests/integration/test_validate_command.py`

**Interfaces:**
- Produces: `ValidationReport(parent: str, children: tuple[str, ...], deferred_checks: tuple[str, ...])`
- Produces: `validate_parent(locator: str, offline: bool, invocation_dir: Path) -> ValidationReport`
- Produces: `format_validation(report: ValidationReport) -> str`
- Consumes: manifest, source, and Copier question interfaces

- [ ] **Step 1: Write failing validate tests**

Assert that online validation can resolve children and validate answer keys. Assert that `--offline` performs no clone, fetch, prompt, or render call.

Both modes must validate local schema, fields, paths, strategies, known manifest children, and `_min_scaf_version`.

- [ ] **Step 2: Run the validate tests and verify failure**

Run: `uv run pytest tests/integration/test_validate_command.py -q`

Expected: FAIL because static validation does not exist.

- [ ] **Step 3: Implement validation with explicit depth**

Offline mode parses a local parent path only. It reports unresolved remote child question checks. Online mode enters a `ResolutionWorkspace`, resolves sources, and loads Copier question models without rendering. Both successful and failed validation remove workspace-owned paths.

Neither mode collects interactive answers.

- [ ] **Step 4: Wire `--offline` and format deterministic output**

Add validate `--offline`. Format children in manifest order and deferred checks in sorted order.

- [ ] **Step 5: Run the validate tests**

Run: `uv run pytest tests/integration/test_validate_command.py -q`

Expected: all tests pass.

- [ ] **Step 6: Commit static validation**

```bash
git add src/scaf_cli/validate.py src/scaf_cli/reports.py src/scaf_cli/cli.py tests/integration/test_validate_command.py
git commit -m "feat(compose): validate manifests"
```

---

### Task 12: Implement rendered `preview`

**Files:**
- Create: `src/scaf_cli/preview.py`
- Modify: `src/scaf_cli/reports.py`
- Modify: `src/scaf_cli/cli.py`
- Create: `tests/integration/test_preview_command.py`

**Interfaces:**
- Produces: `PreviewOptions(parent_repo: str, vcs_ref: str | None, answers_file: Path | None, defaults: bool)`
- Produces: `SourceSummary(locator: str, requested_ref: str | None, selected_ref: str, commit: str)`
- Produces: `PreviewReport(parent: SourceSummary, children: tuple[SourceSummary, ...], classifications: Mapping[str, Mapping[str, tuple[str, ...]]], ownership: OwnershipAnalysis)`
- Produces: `preview_parent(options: PreviewOptions, invocation_dir: Path) -> PreviewReport`
- Produces: `format_preview(report: PreviewReport) -> str`
- Consumes: dispatch and `CompositionAnalysis` interfaces from Task 10

- [ ] **Step 1: Write failing preview tests**

Assert that preview reports:

- Resolved children and refs.
- Excluded, suppressed, context, and pass-through files.
- Required compose paths and strategy sources.
- Unresolved conflicts.
- Managed owner counts.

Assert that preview creates no destination, persists no state, and runs no tasks. Assert resolution workspace cleanup after success and render failure.

- [ ] **Step 2: Run the preview tests and verify failure**

Run: `uv run pytest tests/integration/test_preview_command.py -q`

Expected: FAIL because rendered preview does not exist.

- [ ] **Step 3: Implement preview through ownership analysis**

Enter one `ResolutionWorkspace`, then call `resolve_dispatch()` and `resolve_composition()` from Task 10. Report `CompositionAnalysis.ownership`, including every conflict. Copy source identity into `SourceSummary` before workspace exit. Do not expose temporary root paths in the report. Do not call `build_compose_candidate()`, staging, state persistence, or parent task execution. Always clean temporary directories.

- [ ] **Step 4: Wire preview options and deterministic output**

Add preview `--vcs-ref`, `--answers-file`, and `--defaults`. Format paths in sorted order and children in manifest order.

- [ ] **Step 5: Run the preview tests**

Run: `uv run pytest tests/integration/test_preview_command.py -q`

Expected: all tests pass.

- [ ] **Step 6: Commit rendered preview**

```bash
git add src/scaf_cli/preview.py src/scaf_cli/reports.py src/scaf_cli/cli.py tests/integration/test_preview_command.py
git commit -m "feat(compose): preview ownership"
```

---

### Task 13: Compute safe update reconciliation plans

**Files:**
- Create: `src/scaf_cli/reconciliation.py`
- Create: `tests/unit/test_reconciliation.py`

**Interfaces:**
- Produces: `FileSnapshot(content: bytes, mode: int)`
- Produces: `WriteOperation(path: str, candidate: FileSnapshot)`
- Produces: `DeleteOperation(path: str)`
- Produces: `StateOnlyOperation(path: str, candidate_state: ManagedFileState)`
- Produces: `KeepOperation(path: str, retained_state: ManagedFileState)`
- Produces: `ReconciliationOperation = WriteOperation | DeleteOperation | StateOnlyOperation | KeepOperation`
- Produces: `ReconciliationPlan(operations: tuple[ReconciliationOperation, ...], result_state: ProjectState)`
- Produces: `plan_reconciliation(previous_state: ProjectState, current_root: Path, candidate: ComposeCandidate) -> ReconciliationPlan`
- Consumes: previous state and the complete raw candidate from Task 10

- [ ] **Step 1: Encode all seven safe-update rules as failing tests**

Use byte and mode changes independently. Include these cases:

```text
current == previous                         -> write candidate
current == candidate != previous           -> state-only
current != previous and candidate == previous -> keep local and old state
all three differ                           -> conflict
candidate deletes unchanged managed file   -> delete
candidate deletes locally changed file     -> conflict
new managed path overlaps unmanaged file   -> conflict unless bytes and mode match
```

Assert that any conflict prevents every planned mutation.

Reject a symlink target, a symlinked ancestor, a device, a FIFO, a socket, and every file-directory transition. Place an outside sentinel behind each symlink and assert that its bytes remain unchanged.

Assert that `result_state` starts from candidate manifest, lock, and answers. For rule 3, replace only that candidate file entry with its previous managed entry. Assert that deletes remove file entries and identical unmanaged files gain candidate entries.

- [ ] **Step 2: Run the reconciliation tests and verify failure**

Run: `uv run pytest tests/unit/test_reconciliation.py -q`

Expected: FAIL because reconciliation does not exist.

- [ ] **Step 3: Implement snapshot comparison as a pure function**

Call `require_safe_ancestors()` and inspect targets with `lstat()` before reading current bytes. Accept only missing or regular targets. Use exact bytes and `stat.S_IMODE`. Compare hashes only after safe reads. Do not modify the project while planning.

Reject candidate path-prefix changes that require a managed file to become a directory or a managed directory path to become a file.

```python
import hashlib


def same_file(left: FileSnapshot, right: FileSnapshot) -> bool:
    return left.content == right.content and left.mode == right.mode


def matches_managed(snapshot: FileSnapshot, managed: ManagedFileState) -> bool:
    digest = hashlib.sha256(snapshot.content).hexdigest()
    return digest == managed.sha256 and snapshot.mode == managed.mode
```

Use `matches_managed()` for current-to-previous and candidate-to-previous comparisons. Aggregate all path conflicts.

Build `result_state` from `candidate.state`. Apply state-only, retained-state, and delete decisions after every path is conflict-free. Never derive manifest, lock, answers, owners, or sources from file bytes. Raise one `ScafUpdateConflictError` that lists each path and reason in sorted order.

- [ ] **Step 4: Run the reconciliation tests**

Run: `uv run pytest tests/unit/test_reconciliation.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit reconciliation policy**

```bash
git add src/scaf_cli/reconciliation.py tests/unit/test_reconciliation.py
git commit -m "feat(compose): plan safe updates"
```

---

### Task 14: Add durable update transactions and recovery

**Files:**
- Create: `src/scaf_cli/journal.py`
- Create: `src/scaf_cli/transactions.py`
- Create: `src/scaf_cli/recovery.py`
- Create: `tests/support/failing_file_ops.py`
- Create: `tests/unit/test_transactions.py`
- Create: `tests/integration/test_transaction_recovery.py`

**Interfaces:**
- Produces: `PreparedTransaction(identifier: str, project_root: Path, journal_root: Path, plan: ReconciliationPlan)`
- Produces: `prepare_transaction(project_root: Path, plan: ReconciliationPlan, previous_state: ProjectState) -> PreparedTransaction`
- Produces: `load_prepared_transaction(journal_root: Path, project_root: Path) -> PreparedTransaction`
- Produces: `commit_transaction(transaction: PreparedTransaction) -> None`
- Produces: `rollback_transaction(transaction: PreparedTransaction) -> None`
- Produces: `recover_transactions(project_root: Path) -> None`
- Consumes: `ReconciliationPlan` and serialized project state

- [ ] **Step 1: Write failing journal layout tests**

Require this durable content before mutation:

```text
.scaf/transactions/.<id>.tmp/
├── operations.json
├── backups/
├── candidates/
├── previous-state/
└── result-state/
```

Use numeric operation IDs in `operations.json`. Do not place raw project paths into backup filenames.

Use this versioned operation schema:

```json
{
  "schema_version": 1,
  "transaction_id": "018f5f4e",
  "operations": [
    {
      "id": 0,
      "kind": "mkdir",
      "path": ".github",
      "existed": false
    },
    {
      "id": 1,
      "kind": "mkdir",
      "path": ".github/workflows",
      "existed": false
    },
    {
      "id": 2,
      "kind": "write",
      "path": ".github/workflows/ci.yml",
      "candidate": "candidates/2",
      "candidate_mode": 420,
      "existed": false
    },
    {
      "id": 3,
      "kind": "delete",
      "path": "old.txt",
      "backup": "backups/3",
      "backup_mode": 420,
      "existed": true
    }
  ],
  "created_entries": [
    {"path": ".github", "kind": "directory"},
    {"path": ".github/workflows", "kind": "directory"},
    {"path": ".github/workflows/ci.yml", "kind": "file"}
  ],
  "metadata": {
    "previous": "previous-state",
    "result": "result-state"
  }
}
```

For a new write, set `existed` to false, omit `backup`, and add its file and missing ancestors to `created_entries`. Emit missing-directory operations shallowest first. Journal write and delete project operations by normalized path and ID. Record state-only and keep decisions only in `result-state/`. Persist result metadata last. Roll back project operations in reverse order, then restore previous metadata.

Assert that the temporary journal becomes `<id>.prepared/` with one same-parent rename.

- [ ] **Step 2: Write deterministic failure tests**

Inject failures for:

- Journal file write.
- Journal prepare rename.
- Managed directory creation.
- Managed file write.
- Managed file rename.
- Delete.
- Mode change.
- State persistence.
- Rollback restore.
- Terminal journal cleanup.
- File `fsync()` after content or mode changes.
- Directory `fsync()` after mkdir, rename, delete, marker rename, or cleanup.
- Candidate `.scaf/` persistence that preserves the active transaction directory.
- A managed ancestor replaced by a symlink between planning and commit.
- A managed ancestor replaced by a symlink before rollback.

After each commit failure, assert complete previous bytes, modes, and state. If rollback also fails, assert that `.prepared` remains and both errors appear.

For symlink-swap failures, assert that an outside sentinel remains unchanged. If safe rollback cannot validate every ancestor, preserve `.prepared`.

Inject parent-directory fsync failure after each terminal rename. Assert that `.committed` or `.aborted` remains terminal and that recovery never rolls it back.

- [ ] **Step 3: Write crash and restart-recovery tests**

Assert:

- `.tmp` is removed without project mutation.
- `.prepared` rolls back idempotently.
- `.committed` receives cleanup only.
- `.aborted` receives cleanup only.
- Cleanup never changes a terminal suffix.
- Recovery failure blocks update and status work.
- Recovery works in a new process with no in-memory `PreparedTransaction`.
- Unknown journal schema versions, fields, operations, duplicate IDs, unsafe project paths, or invalid backup references block recovery.
- A nested new file creates and records each missing directory.
- Reverse rollback removes only transaction-created empty directories and retains every pre-existing directory.

- [ ] **Step 4: Run the transaction tests and verify failure**

Run: `uv run pytest tests/unit/test_transactions.py tests/integration/test_transaction_recovery.py -q`

Expected: FAIL because transaction support does not exist.

- [ ] **Step 5: Implement durable preparation**

Serialize `previous_state` under `previous-state/` and `plan.result_state` under `result-state/`. Do not accept a second raw candidate state.

Write each file, flush it, and call `os.fsync()`. Fsync each new directory after entries are durable. Rename `.tmp` to `.prepared` only after all backups, candidates, and state snapshots are durable.

After each `.prepared`, `.committed`, or `.aborted` marker rename, fsync `.scaf/transactions/`. After terminal cleanup, fsync that directory again.

If the `.prepared` rename succeeds but its parent-directory fsync fails, perform safe rollback before any project mutation. Keep `.prepared` only if rollback cannot finish.

If a terminal marker rename succeeds and its parent-directory fsync fails, keep the terminal suffix. Raise `ScafTransactionError` and never rename it back or treat it as prepared. Recovery applies cleanup-only semantics to that visible terminal suffix.

If terminal directory removal succeeds but the cleanup fsync fails, report `ScafTransactionError`. Do not recreate the removed terminal directory.

Remove `.tmp` after preparation failure. Leave managed files and stored state unchanged.

- [ ] **Step 6: Implement atomic operations and rollback**

Before every commit and rollback operation, call `require_safe_ancestors()` and re-read the target with `lstat()`. If an ancestor or target became unsafe, abort before byte access.

Write replacement content to a same-directory temporary file. Apply mode before `os.replace()`. Fsync the file and parent directory.

After each delete, fsync the containing directory. After each mode change, fsync the file and its containing directory. Expose these calls through the fault-injectable file-operations adapter.

Create missing candidate directories in shallowest-first order and fsync each parent. During reverse rollback, call `os.rmdir()` only for recorded transaction-created directories that are empty. Never recursively remove a created directory.

Keep backup data until rollback reaches a durable terminal state. Rename `.prepared` to `.committed` after all candidate operations and state are durable.

On failure, restore backups and prior metadata. Remove created paths. Rename `.prepared` to `.aborted` only after durable restoration.

- [ ] **Step 7: Run the transaction tests**

Run: `uv run pytest tests/unit/test_transactions.py tests/integration/test_transaction_recovery.py -q`

Expected: all tests pass.

- [ ] **Step 8: Commit transaction support**

```bash
git add src/scaf_cli/journal.py src/scaf_cli/transactions.py src/scaf_cli/recovery.py tests/support/failing_file_ops.py tests/unit/test_transactions.py tests/integration/test_transaction_recovery.py
git commit -m "feat(compose): add recoverable transactions"
```

---

### Task 15: Implement full-graph `update`

**Files:**
- Create: `src/scaf_cli/update.py`
- Modify: `src/scaf_cli/cli.py`
- Create: `tests/integration/test_update_command.py`

**Interfaces:**
- Produces: `update_project(project_root: Path, vcs_ref: str | None) -> None`
- Consumes: locked sources, candidate construction from Task 10, reconciliation, journals, recovery, and transactions

- [ ] **Step 1: Write failing ref movement tests**

Use local repositories with multiple commits and tags. Cover:

- A branch can advance.
- Explicit `HEAD` can advance.
- An omitted selector can advance to a higher valid release tag.
- An omitted selector with no valid release tags can advance with `HEAD`.
- A commit selector cannot advance.
- A moved or missing previously selected tag raises `ScafResolveError`.
- An explicit tag that moved raises `ScafResolveError`.
- Failed resolution preserves prior state.
- `--vcs-ref` replaces the stored parent request only after success.
- A candidate parent can change the complete child graph and compose policy.
- A same-name, same-repository child verifies its previously selected omitted tag before advancement.
- A replacement child with a different repository has no inherited tag lock.

- [ ] **Step 2: Write failing update integration tests**

Assert full candidate rendering, all seven reconciliation rules, prepared transactions, parent-task suppression, and previous state preservation after any failure.

Reject missing, malformed, or unsupported `.scaf/` state before source resolution or mutation.

Assert that update never calls child-native `copier update`. Assert that child `_skip_if_exists` never changes full-candidate reconciliation.

Reuse matching stored parent answers without prompting. Drop answers for removed parent questions. Resolve new active defaults. Raise `ScafAnswerError` for a new active question without a stored value or default.

- [ ] **Step 3: Run the update tests and verify failure**

Run: `uv run pytest tests/integration/test_update_command.py -q`

Expected: FAIL because full-graph update does not exist.

- [ ] **Step 4: Implement update in the specification order**

```text
1. Recover or clean terminal journals.
2. Load manifest, lock, answers, and managed state.
3. Enter one `ResolutionWorkspace` for the complete update.
4. Resolve the effective parent ref and candidate parent manifest.
5. Verify immutable locked tags before allowing omitted selectors to advance.
6. Build `AnswerInputs` from stored parent answers with `defaults=True`, `interactive=False`, and `ignore_removed=True`.
7. Call `resolve_composition()` and `build_compose_candidate()` for the complete candidate graph.
8. Compute the complete reconciliation plan from that `ComposeCandidate`.
9. Prepare the rollback journal.
10. Commit project and .scaf operations.
11. Mark the journal committed and clean terminal data.
12. Exit the resolution workspace on success or failure.
```

Include a requested parent override only in `result_state`. Roll it back after any pre-terminal failure. If directory fsync fails after the `.committed` rename, keep the terminal state.

- [ ] **Step 5: Wire the update CLI command**

Add update `--vcs-ref`. Run update from the current project directory. Reject `update --child` and `eject` as unknown commands.

- [ ] **Step 6: Run the update tests**

Run: `uv run pytest tests/integration/test_update_command.py -q`

Expected: all tests pass.

- [ ] **Step 7: Commit full-graph update**

```bash
git add src/scaf_cli/update.py src/scaf_cli/cli.py tests/integration/test_update_command.py
git commit -m "feat(compose): update composed projects"
```

---

### Task 16: Implement local `status`

**Files:**
- Create: `src/scaf_cli/status.py`
- Modify: `src/scaf_cli/reports.py`
- Modify: `src/scaf_cli/cli.py`
- Create: `tests/integration/test_status_command.py`

**Interfaces:**
- Produces: `StatusReport(parent: Mapping[str, str], children: tuple[Mapping[str, str], ...], owner_counts: Mapping[str, int], excluded_count: int, suppressed_count: int, local_changes: tuple[str, ...])`
- Produces: `status_project(project_root: Path) -> StatusReport`
- Produces: `format_status(report: StatusReport) -> str`
- Consumes: stored state, current file snapshots, and journal recovery

- [ ] **Step 1: Write failing status tests**

Assert parent and child locks, owner counts, excluded and suppressed counts, and detectable local conflicts.

Assert recovery before report generation. Assert that a recovery failure blocks the report. Reject missing or malformed `.scaf/` state with a user-facing error.

Replace a managed file and a managed ancestor with symlinks to an outside sentinel. Report both as unsafe local conflicts without reading the sentinel.

- [ ] **Step 2: Run the status tests and verify failure**

Run: `uv run pytest tests/integration/test_status_command.py -q`

Expected: FAIL because local status does not exist.

- [ ] **Step 3: Implement status after recovery**

Read state without source resolution. Validate each managed path with `lstat()` and `require_safe_ancestors()` before byte access. Compare safe current hashes and modes with managed state. Report conflicts that are detectable without a candidate render.

- [ ] **Step 4: Wire and format the status command**

Run status from the current project directory. Format locks in manifest order and changed paths in sorted order.

- [ ] **Step 5: Run the status tests**

Run: `uv run pytest tests/integration/test_status_command.py -q`

Expected: all tests pass.

- [ ] **Step 6: Commit local status**

```bash
git add src/scaf_cli/status.py src/scaf_cli/reports.py src/scaf_cli/cli.py tests/integration/test_status_command.py
git commit -m "feat(compose): report project status"
```

---

### Task 17: Preserve compatibility, package the application, and document v1

**Files:**
- Create: `src/scaf_cli/legacy.py`
- Modify: `src/scaf_cli/cli.py`
- Modify: `install.sh`
- Modify: `default.nix`
- Modify: `flake.nix`
- Modify: `.releaserc.json`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Create: `tests/integration/test_legacy_cli.py`

**Interfaces:**
- Produces: `LegacyInvocation(argv: list[str], injected_answers: Mapping[str, object])`
- Produces: `normalize_legacy_argv(argv: Sequence[str]) -> LegacyInvocation`
- Produces: installed `scaf` console entry point
- Consumes: all command interfaces

- [ ] **Step 1: Write failing legacy behavior tests**

Cover the current forms:

```text
scaf my-app
scaf my-app TEMPLATE
scaf my-app --defaults --vcs-ref main TEMPLATE
scaf --upgrade
scaf --uninstall
```

Normalize project creation to the new `create <repo> <destination>` contract. Preserve `is_project_slug` data for the single-template fallback. If no template is supplied, keep the two-template chooser.

Mock upgrade and uninstall process calls. Do not alter the user environment during tests.

- [ ] **Step 2: Run the legacy tests and verify failure**

Run: `uv run pytest tests/integration/test_legacy_cli.py -q`

Expected: FAIL because the compatibility adapter does not exist.

- [ ] **Step 3: Implement argument normalization before argparse dispatch**

Known v1 command names bypass legacy handling. A first positional token that is not a command becomes the legacy project slug. Preserve option values and a final template locator.

Return `{"is_project_slug": slug.replace("-", "_")}` in `LegacyInvocation.injected_answers`. The CLI passes that mapping into `CreateOptions`.

Keep `--upgrade` and `--uninstall` as top-level maintenance flags.

- [ ] **Step 4: Replace single-file installation with `uv tool` installation**

Make `install.sh` install the selected Git ref as an application:

```bash
uv tool install --force "git+https://github.com/sixfeetup/scaf.git@${BRANCH}"
```

Keep the existing dependency bootstrap and destination diagnostics. Verify that the generated console script resolves to the installed package.

Convert `install.sh` to explicit Bash because it already uses arrays, `&>`, and `OSTYPE`. Use `#!/usr/bin/env bash` and `set -euo pipefail`.

Remove the current ShellCheck classes before the commit:

- Replace flag-bearing `echo` calls with `printf` (`SC3037`).
- Quote path, URL, tool, and argument expansions (`SC2086`).
- Keep argument vectors as Bash arrays instead of scalar `$@` assignments (`SC2124`).
- Retain Bash redirection only after the shebang change (`SC3020`).
- Read `OSTYPE` only in Bash (`SC3028`).
- Test commands directly instead of reading `$?` afterward (`SC2181`).
- Use `curl --fail --show-error --location` for downloads.

- [ ] **Step 5: Package the Python application in Nix**

The locked Nixpkgs has top-level Copier 9.4.1 and no `python3Packages.copier`. Define this verified Copier 8.1.0 override in `default.nix`:

```nix
copier81 = pkgs.copier.overridePythonAttrs (old: rec {
  version = "8.1.0";
  src = pkgs.fetchFromGitHub {
    owner = "copier-org";
    repo = "copier";
    tag = "v${version}";
    hash = "sha256-JJLOfc3Rm7q8nP6muRZCBi4IuGaMJ7AkxYNp69e5If4=";
  };
  POETRY_DYNAMIC_VERSIONING_BYPASS = version;
  dependencies =
    builtins.filter (dependency: (dependency.pname or "") != "pydantic") old.dependencies
    ++ [ pkgs.python3Packages.pydantic_1 ];
});
```

The locked `python3Packages.pyyaml-include` is 1.3.1 and satisfies Copier 8.1.0. Build Scaf with `python3Packages.buildPythonApplication`, `pyproject = true`, and the runtime dependency source from Task 1. Include `copier81` and `pkgs.git` in the wrapped runtime. Preserve the current Nix runtime tool list for legacy templates.

Expose the package from `flake.nix`. Keep ShellCheck for `scaf` and `install.sh`. Add an import and `scaf --version` check to the Nix check phase.

- [ ] **Step 6: Update release version replacement**

Add a `.releaserc.json` replacement for:

```python
__version__ = "${nextRelease.version}"
```

Add `src/scaf_cli/version.py` to release assets. Keep `package.json` as the release tool version source.

- [ ] **Step 7: Update user and contributor documentation**

Document all five v1 commands, explicit destinations, parent and child contracts, state ownership, update limits, and legacy syntax.

Document `uv sync --extra test --group dev`, focused pytest commands, `uv run pre-commit run --all-files`, and offline Git fixture rules.

- [ ] **Step 8: Run the legacy and full automated suite**

Run: `uv run pytest tests/integration/test_legacy_cli.py -q`

Run: `uv run pytest -q`

Expected: all tests pass.

- [ ] **Step 9: Verify static packaging changes directly**

Run: `uv build`

Run: `uv tool run --from dist/scaf-*.whl scaf --version`

Run: `shellcheck scaf install.sh`

Run: `nix build . --no-link`

Run: `uv run ruff .`

Run: `uv run black --check .`

Run: `uv run isort --check-only .`

Run: `uv run bandit -r src`

Expected: every command exits 0.

No new test asserts static dependency, Nix, release, or documentation text. The build and smoke commands verify those files.

- [ ] **Step 10: Run the final repository gate**

Run: `uv run pre-commit run --all-files`

Expected: every hook passes.

- [ ] **Step 11: Commit compatibility, packaging, and documentation**

```bash
git add src/scaf_cli/legacy.py src/scaf_cli/cli.py install.sh default.nix flake.nix .releaserc.json README.md CONTRIBUTING.md tests/integration/test_legacy_cli.py
git commit -m "feat(compose): ship v1 command suite"
```

---

## Final Acceptance Matrix

| Specification area | Primary tasks | Required evidence |
|---|---:|---|
| Dispatch and parent contract | 3, 4, 10 | Compose and fallback integration tests |
| Manifest, paths, globs, and minimum version | 2, 3 | Parameterized parser tests |
| Parent prompts and child answers | 5 | Copier question tests |
| Child restrictions and output classification | 6 | Task suppression and inventory tests |
| Parent context, filters, extensions, and tasks | 7, 10 | Parent render and staged task tests |
| Ownership truth table and strategies | 8 | Pure policy tests |
| Six-phase create pipeline | 9, 10 | Atomic staging integration tests |
| Project state | 9 | Serialization and hash tests |
| Validate and preview | 11, 12 | Side-effect and report tests |
| Safe reconciliation | 13 | Seven-rule policy tests |
| Journal commit, rollback, and recovery | 14 | Fault-injection and crash tests |
| Ref movement and full-graph update | 15 | Local Git history tests |
| Status | 16 | State and local-change tests |
| CLI, installation, Nix, and compatibility | 1, 17 | Full suite, build, import, ShellCheck, and Nix build |
| Explicit v1 exclusions | 3, 6, 15 | Nested graph and omitted-command tests |

## Completion Gate

Before branch integration, run these commands from the repository root:

```bash
uv sync --extra test --group dev
uv run pytest -q
uv run ruff .
uv run black --check .
uv run isort --check-only .
uv run bandit -r src
shellcheck scaf install.sh
uv build
nix build . --no-link
uv run pre-commit run --all-files
```

Read every exit code. Do not claim completion from a partial command set.
