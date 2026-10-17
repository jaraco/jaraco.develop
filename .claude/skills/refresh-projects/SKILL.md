---
name: refresh-projects
description: Refresh jaraco's skeleton-based projects - clean each checkout, baseline with tox, merge jaraco/skeleton, repair ruff and other emergent failures, push to main, and chase CI to green. Use when asked to "refresh the projects", sync projects with skeleton, or get jaraco.com/projects green again.
---

# Refresh projects

Brings jaraco's maintained projects up to date with
[skeleton](https://github.com/jaraco/skeleton) and back to a green build.
Before starting, read <https://blog.jaraco.com/skeleton/> (and the linked
scm-approach and design pages). That document is the authoritative source for
conventions.

## Selecting projects

- The list lives in `~/code/jaraco/dotfiles/projects.txt`. Entries starting
  with `/` are `org/name`. Bare names are under `jaraco/`. Checkouts live at
  `~/code/<org>/<name>`.
- Skip entries tagged `[fork]` (not maintained here) and `[base]` (skeleton
  and tidelift themselves).
- `[lifted]` marks Tidelift-supported projects. Do these first.
- Some projects have no `.github/workflows/main.yml`. These are cherrypy and
  pypa projects with their own CI, plus a few non-packages such as dotfiles.
- Coherent System projects aren't skeleton-based either. A project is one if
  it has no tracked `pyproject.toml` (like jaraco.pdf), uses the
  `coherent.build` backend, or runs CI from `coherent-oss/system` (like
  tempora). Never merge skeleton into these, even when
  `git merge-base HEAD FETCH_HEAD` succeeds, because the merge would
  resurrect deleted skeleton files. Still run the baseline and fix failures.
  To get a baseline for a Coherent project, run
  `PYTHONSAFEPATH=1 uvx --python 3.X --from 'coherent.test>=0.7.0' python -m coherent.test`.
  coherent.build infers `Requires-Python` from the oldest CPython branch,
  so a CPython end-of-life breaks every Coherent project at once. Fix that in
  coherent-oss/system, not per project.
  To see every violation, fetch skeleton's `ruff.toml` and run
  `ruff check --config <it> --target-version py3XX .`, matching the inferred
  Requires-Python. To test a change to coherent.test itself, run another
  project with `uvx --from ~/code/coherent-oss/coherent.test python -m coherent.test`.
  UP036 after a CPython end-of-life means support is being dropped, so in
  coherent.build/coherent.test deliver that through a PR.
- Otherwise, merge skeleton only into projects that already share its
  history (where `git merge-base HEAD FETCH_HEAD` succeeds). If neither
  applies, leave the project alone and report it.

Baseline CI state per repo:

```bash
gh run list -R ORG/NAME -w main.yml -b main -e push -L 1 --json conclusion,createdAt
```

Use `-e push`, because `-b main` also matches fork PRs whose branch is named
`main`. Runs older than a few months usually have expired logs. Treat the local
`tox` run as the source of truth.

## Per-project procedure

1. **Clean.** Run `git status --short` (ignored files don't count). If there
   are tracked changes or untracked files that look meaningful, such as
   source, docs or newsfragments rather than `*.orig` or build leftovers,
   **stop and report** instead of discarding them. Some files are always
   disposable: report artifacts such as `diffcov.html` and `readme.html`,
   and an untracked `pyproject.toml` that contains only the
   `coherent.build` build-system stub (left over from building a
   Coherent System project). Otherwise:
   `git fetch origin && git switch main && git merge --ff-only origin/main
   && git clean -fdx`. If main can't fast-forward, stop and report. The exception is a local
   main that's ahead only by a stale merge whose parents are both already
   upstream. Move it to a backup branch and reset main.
   Review `git clean -ndx` first. If the clean is denied by the permission
   mode, skip it and use `tox -r` for a fresh environment.
2. **Baseline.** Run `tox` (current Python) and note what fails before
   touching anything. That tells you which failures the merge caused. Common
   non-lint causes are dead pytest plugins in test extras (pytest-pep8
   crashes under pytest 9 before collection) and `pkg_resources` imports
   (see below). Tests keyed to `date.today()` can also fail because
   calendar data expired. Classify those as data expiry, not merge fallout.
3. **Merge skeleton.** `git pull --no-edit gh://jaraco/skeleton`.
   - Keep the default merge message (`Merge https://github.com/jaraco/skeleton`).
   - "refusing to merge unrelated histories" means the project predates a
     history collapse. Pull the matching handoff branch first
     (`git pull gh://jaraco/skeleton 2023-handoff`), but only if the project
     is otherwise skeleton-based.
   - Conflicts: try `git mergetool -t known-merge`
     (`py -m jaraco.develop.merge`), which resolves placeholder and shebang
     conflicts. Resolve the rest by hand:
     - In `pyproject.toml`, the `# upstream` sections follow skeleton and the
       `# local` sections stay with the project.
     - In `ruff.toml`, take skeleton's upstream entries and keep the
       project's `# local` entries. Drop local entries that skeleton has since
       adopted upstream (B008, for example), and fix stray whitespace before
       `# local`, which otherwise conflicts every time.
     - Files the project deliberately customized or deleted keep the
       project's version.
     - A check the project disabled on purpose stays disabled, even when
       skeleton edits that line. An example is a commented-out
       `pytest-mypy` or `pytest-ruff` dependency.
     - Local `actions/cache@v1`/`v2` steps are dead (those versions are
       retired), so drop them.
     - `.github/workflows/main.yml` now delegates to the reusable
       `test-suite.yml`, so local matrix entries or steps can't carry over
       as-is. Check whether the customization is still needed (often it's
       stale) and take skeleton's version if not. If it is still needed,
       raise it as a PR.
   - Then `git commit --no-edit`.
   - "Already up to date" is fine. Confirm `ruff check .` is clean and CI is
     green, then move on.
4. **Ruff (jaraco/skeleton#210).** Fix only what tox reports. pytest-ruff
   shows only the first violation per file, so run `ruff check <file>` on
   each file tox flags to see all of them. Some projects
   deliberately exclude vendored sources (`collect_ignore` in `conftest.py`)
   or disable pytest-ruff, and a bare `ruff check .` reports false alarms
   there. A nested `ruff.toml` without `extend = "../ruff.toml"` silently
   replaces the root config for its subtree, so check for those too. Run
   `ruff check .` and
   `ruff format --check .`. Fix with `ruff check --fix .` (and `ruff format .`
   if needed), then **review the diff**. The autofixes are not always safe:
   - PLC0414/F401 can delete `import X as X` re-exports. Skeleton ignores
     PLC0414 now. Still check that no public name disappeared.
   - B009 (`getattr(obj, 'const')` → attribute access) can upset mypy when
     the attribute is dynamic. Run mypy (it runs under tox) to confirm.
   - Skeleton enables `allow-dict-calls-with-keyword-arguments`, so keep the
     `dict(a=1)` style. Don't rewrite it to literals.
   - RUF012 (mutable class attributes): annotate with `ClassVar` (bare
     `ClassVar` when the type is inferable). If the class attribute is an
     intentional, never-mutated default, use `# noqa` with a reason.
   - UP036 (outdated version block) often marks a `compat` shim for a Python
     below `requires-python`. Remove the shim and its call sites in a
     separate commit before the ruff commit.
   - Some patterns are intentional. Give these a `# noqa` with a reason
     instead of a code change:
     - BLE001 in error-handler callbacks
     - PLE0704 (bare `raise`) in `onerror` handlers and re-raise helpers
     - SIM115 where a file deliberately outlives the block
     - TRY004 where changing the exception type would change behavior
   - EXE001: for a console-script entry-point module, remove the shebang. For
     a script that runs through its shebang (e.g. mockproc), `chmod +x` it.
   - SIM115 for an optional file or stdout:
     `with (open(p) if p else contextlib.nullcontext(sys.stdout)) as f:`.
   - SIM115: prefer a real `with` when the handle would otherwise never be
     closed. Leaked handles can lose writes on PyPy. Use `noqa` only when the
     file deliberately outlives the block.
   - SIM905's autofix turns readable `"""...""".split()` word lists into
     long literals. Reject it and use a `# noqa`.
   - SIM102 often has no autofix when comments are present, so collapse
     those by hand and keep the comments.
   - Files synced from another upstream (CPython-derived code in
     configparser, importlib_*, backports) shouldn't be mass-rewritten. Add
     `[lint.per-file-ignores]` under `# local` for them, delivered as a PR
     that names the mass-fix alternative.
   - UP031 in log calls: when `log` may be a non-stdlib object (as in
     cssutils/encutils), use f-strings rather than lazy logging arguments.
   - Review "safe" autofixes too. G010 (`.warn` → `.warning`) assumes a
     stdlib logger and broke cssutils' custom handler. RUF059's `_` renames
     can expose F841. PLC0206 rewrites can shadow a variable the loop body
     reassigns. Rerun ruff and the tests after each round of fixes.
   - RUF012 sometimes exposes real shared-state bugs, such as a mutable class
     attribute that instances mutate. Check before reaching for `ClassVar`,
     and give a real bug its own commit and newsfragment.
   - Ruff 0.17 dropped some 0.16 defaults (DTZ011, for example), so their
     `# noqa` comments now trip RUF100 (unused noqa). Remove the codes and
     keep any explanatory comment.
   - RUF059 `_` renames: check that the name isn't consumed through
     `locals()`/`vars()` (e.g. `.format(**locals())`).
   - SIM118 (`in obj.keys()` → `in obj`) is only safe for real mappings.
     Check the type first.
   - PLW0602: removing a do-nothing `global x` can expose F821 when the
     name is never bound at module level. Find the intended binding site
     (often `main()`) rather than adding a `noqa`.
   - RUF012 on a class attribute built from `locals()`: before Python 3.14,
     any annotation in the class body adds `__annotations__` to `locals()`,
     so don't use `ClassVar` there. Use a tuple if the attribute is only
     used for membership checks.
   - When there are more than ~100 violations, split the ruff commit
     sensibly. Also confirm everything still parses on the minimum Python
     (`python3.10 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())"`),
     since f-string conversions can introduce newer syntax.
   - UP030/UP031 unsafe fixes can produce broken format strings (mixed
     numbered and unnumbered fields → F525). Rewrite them by hand or recheck.
   - `ruff check --fix .` also rewrites files excluded via `collect_ignore`.
     Revert those, or pass explicit paths.
   - Preserve line endings. Python `open().read()`/`write()` silently turns
     CRLF into LF. Check `git ls-files --eol`.
   - PLR0402's autofix (`import a.b as b` → `from a import b`) can break mypy
     when `a.b` is untyped. Import the needed names directly instead.
   - A `# noqa` for a multi-line string goes after the string's closing
     line. If it's placed inside the string, it becomes part of the string.
   - Use `--unsafe-fixes` only selectively, and only with review.
   - Don't fix a rule by adding it to the project's ignore list unless the
     rule is wrong for the project. If you do, put it under `# local` with a
     comment.

   When ruff fixes and other fixes touch the same file, keep them in
   separate commits. `git add -p` is interactive, so stage with `git stash`
   or by applying the fixes in sequence.

   Commit as:

   ```
   Repair the violations from Ruff 0.16's expanded defaults.

   Ref jaraco/skeleton#210.
   ```
   Before pushing, run `tox -e diffcov` and check its exit status. Piping it
   through `tail` hides failures from `&& git push`. Lint rewrites touch lines that were
   already uncovered, which fails diffcov in CI. Add a test or simplify. Put that
   test or simplification in its own commit, ahead of the ruff commit.
   Reordering local, unpushed commits (`git reset`, `--amend`) is fine.

   For packages that register a pytest plugin, diffcov reports import-time
   lines as uncovered. Ignore those.

   diffcov compares against `origin/main`, so it only enforces on PRs. On a
   direct push to main it passes trivially, so don't chase coverage of
   untestable interactive or hardware code too far.

   Doctests can use `getfixture('monkeypatch')` to cover side-effecting
   lines cheaply, without a new test module.

   Python 3.15 colorizes `--help` output under CI's `FORCE_COLOR`. Tests
   that assert on help text need `PYTHON_COLORS=0`.

   Some rule hits are real bugs and get their own bug-fix commits:
   - C417 on a bare `map(...)` statement is usually dead code that never
     runs.
   - B015 (pointless comparison) in tests usually means a missing
     `assert`. A missing `f` prefix on a continuation line of an implicitly
     concatenated string is another real bug.
   - `map(pattern.match, ...)` used where `filter` was meant, and PyMongo 4
     removals (`Collection.update`/`insert`/`remove`).
   - Python 2 leftovers such as `__unicode__`, `itertools.imap`/`ifilter`,
     `zip(...).sort()`, `obj.next()`, `WindowsError`, and the optparse-style
     `options, args = parser.parse_args()` used with argparse.
     Adding tests for diffcov tends to expose these. When a new test exposes a
     bug, commit the fix before the test so every commit passes. File an
     issue when a module looks largely broken.

   `pkg_resources` imports fail now that recent Setuptools no longer
   provides it. Swap `resource_stream` for
   `importlib.resources.files(pkg).joinpath(p).open('rb')`,
   `resource_filename` for `str(files(pkg) / p)`, and
   `require(x)[0].version` for `importlib.metadata.version(x)`. Treat the
   swap as a bugfix with a newsfragment. `git clean` removes an empty
   `newsfragments/` directory, so recreate it with `mkdir -p` first.

5. **Other failures.** Re-run `tox` and fix what's left: deprecations, test
   breakages from new Python or dependency releases, and mypy. Keep each
   concern in its own commit with a descriptive message. Add a towncrier
   newsfragment (`newsfragments/+<id>.bugfix.rst` or similar) only for
   user-facing changes. Lint fixes need none.
6. **Push** directly to main (`git push`), with no PR, then watch CI:

   ```bash
   gh run watch -R ORG/NAME <run-id> --exit-status
   gh run view -R ORG/NAME <run-id> --json conclusion
   ```

   With many agents polling in parallel, GitHub's secondary rate limit
   blocks `gh run ...` for minutes at a time. Poll sparingly (every 60s or
   more) and fall back to
   `gh api "repos/O/N/actions/workflows/main.yml/runs?branch=main&per_page=1"`,
   matching `head_sha` to the pushed commit.

   Confirm the conclusion with `gh run view`. Don't trust a wrapped
   command's exit code. One failed job cancels the rest of the matrix, so a
   second run may surface more failures.

   For Windows-only code, run `mypy --platform win32 .` locally, and run
   `ruff check` on platform-collected files to see what Windows CI will
   report. First check whether the matrix disables windows-latest, in which
   case CI won't verify those fixes.

   mypy only checks platform branches (such as `sys.platform == 'win32'`) on
   that platform. A `type: ignore` that is unused on Windows fails only in
   Windows CI. Use `# type: ignore[code, unused-ignore]` there.

   Fail-fast cancels the rest of the matrix after the first failure. To see
   every failure, rerun once (`gh run rerun --failed`) or push a throwaway
   branch. A cancelled job may already have passed, so read its log
   before rerunning. Skeleton's matrix includes 3.14t and PyPy, which fail when a
   C-extension dependency has no wheel for them (psycopg2, pywin32). Treat
   those separately from failures the merge caused. A local matrix
   exclusion goes in a PR.

   Lines that only run when a resource is missing, such as skip branches,
   are never covered in CI. Avoid touching them for lint, or mark them
   `# pragma: no cover`.

   During the merge, check `tox.ini` for git-pinned forks, stale pins and
   `extras` that no longer exist (fatal under tox 4).

   Network tests broken by a third-party site: `xfail` them with a
   reference to an issue.

   Look up the run with `-w main.yml`. Otherwise the newest run is often
   the "Dependency Graph" workflow.

   Before pushing, check open PRs for overlap with the refresh. Don't
   create a file a contributor PR also adds. Running
   `git merge-tree --write-tree origin/main <pr-head>` before and after the
   refresh shows whether the refresh introduces a conflict. Report any it
   does.

   When a lint rewrite touches rendering or formatting code, compare the
   generated output before and after, using a `git worktree` of the
   pre-change commit. That catches `vars()`/`locals()` breakage that tests
   miss.

   Before fixing a CI failure, search the project's open PRs. If a
   contributor PR already fixes it, report that rather than duplicating it,
   because merging someone else's PR is the maintainer's call. Also mention
   whether the refresh commits will conflict with that PR.

   Fix CI-only failures (other platforms or Python versions, diffcov, docs)
   as follows:
   - **Shared dependency or install failures** (one cause across many
     projects, such as a missing wheel or a CI image change): fix them once
     at the source (skeleton's `test-suite.yml`, or the upstream project)
     instead of per project. A missing wheel can also show up as pip
     backtracking to an ancient release of a dependency, which then fails
     (e.g. `No module named 'pkg_resources'`), or as pip's
     `resolution-too-deep`. Check the job log for
     unexpectedly old versions. When batching, have the coordinator do it so
     issues aren't duplicated.
   - **Minor issues:** fix directly and push.
   - **Significant issues:** file an issue on the project describing the
     concern, then fix it in a commit that references the issue
     (`Ref ORG/NAME#N` or `Closes ...`).
   - **Anything needing the maintainer's judgment:** push it to a branch and
     open a PR instead of committing to main. Examples are behavior changes,
     dropping support, a large redesign, or a disputed lint rule.

## Conventions

- The user's shell is xonsh. Bash-isms such as `set -- $x` misbehave
  silently. Wrap multi-step shell loops in `bash -c '...'`. macOS
  `/bin/bash` is 3.2, so there's no `declare -A`.

- Qualify cross-repo references (`jaraco/skeleton#210`, not `#210`).
- Don't pin ruff, and don't trust `.pre-commit-config.yaml` (it's
  best-effort). tox/pytest-ruff is authoritative.
- Don't add `.gitignore` or `LICENSE` files (jaraco/skeleton#197).
- Never force-push. Never rewrite main.

## Scaling out

With many projects, use one subagent per batch of about five projects, and
run batches in parallel. Each project is a separate checkout, so there's no
contention. Give each agent this procedure and its project list. Ask it to
report, per project:

- the baseline result
- the merge outcome
- commits pushed
- the final CI state
- any issues or PRs filed
- anything it stopped on

At the end, re-run the CI status query across all projects and summarize the
remaining reds. The goal is <https://jaraco.com/projects> mostly green.
