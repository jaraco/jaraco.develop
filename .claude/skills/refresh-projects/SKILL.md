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
- Otherwise, merge skeleton only into projects that already share its
  history (where `git merge-base HEAD FETCH_HEAD` succeeds). If neither
  applies, leave the project alone and report it.

Baseline CI state per repo:

```bash
gh run list -R ORG/NAME -w main.yml -b main -L 1 --json conclusion,createdAt
```

Runs older than a few months usually have expired logs. Treat the local
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
   && git clean -fdx`. If main can't fast-forward, stop and report.
2. **Baseline.** Run `tox` (current Python) and note what fails before
   touching anything. That tells you which failures the merge caused.
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
       project's `# local` entries.
     - Files the project deliberately customized or deleted keep the
       project's version.
     - `.github/workflows/main.yml` now delegates to the reusable
       `test-suite.yml`, so local matrix entries or steps can't carry over
       as-is. Check whether the customization is still needed (often it's
       stale) and take skeleton's version if not. If it is still needed,
       raise it as a PR.
   - Then `git commit --no-edit`.
   - "Already up to date" is fine. Confirm `ruff check .` is clean and CI is
     green, then move on.
4. **Ruff (jaraco/skeleton#210).** Run `ruff check .` and
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
   - SIM905's autofix turns readable `"""...""".split()` word lists into
     long literals. Reject it and use a `# noqa`.
   - SIM102 often has no autofix when comments are present, so collapse
     those by hand and keep the comments.
   - Files synced from another upstream (CPython-derived code in
     configparser, importlib_*, backports) shouldn't be mass-rewritten. Add
     `[lint.per-file-ignores]` under `# local` for them, delivered as a PR
     that names the mass-fix alternative.
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
   Before pushing, run `tox -e diffcov`. Lint rewrites touch lines that were
   already uncovered, which fails diffcov in CI. Add a test or simplify.

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

   Confirm the conclusion with `gh run view`. Don't trust a wrapped
   command's exit code. One failed job cancels the rest of the matrix, so a
   second run may surface more failures.

   mypy only checks platform branches (such as `sys.platform == 'win32'`) on
   that platform. A `type: ignore` that is unused on Windows fails only in
   Windows CI. Use `# type: ignore[code, unused-ignore]` there.

   Fix CI-only failures (other platforms or Python versions, diffcov, docs)
   as follows:
   - **Minor issues:** fix directly and push.
   - **Significant issues:** file an issue on the project describing the
     concern, then fix it in a commit that references the issue
     (`Ref ORG/NAME#N` or `Closes ...`).
   - **Anything needing the maintainer's judgment:** push it to a branch and
     open a PR instead of committing to main. Examples are behavior changes,
     dropping support, a large redesign, or a disputed lint rule.

## Conventions

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
