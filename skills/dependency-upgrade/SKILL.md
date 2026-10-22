---
name: dependency-upgrade
description: Upgrade a project's dependencies safely — read the changelog and breaking changes, bump one logical group at a time, update the lockfile, and run the project's own gates after each step. Use whenever the user asks to upgrade, bump, update, or patch a dependency or framework version, to handle a Dependabot or Renovate PR, or to fix a vulnerable package.
---

# Dependency Upgrade

Move dependencies forward without breaking the build, one reviewable step at a time.

## Steps

1. **Establish a green baseline.** Find the project's own gates (lint, types, tests, build)
   from its CI config or manifest scripts and run them before changing anything. If they are
   already red, stop and report that; an upgrade on a red baseline proves nothing.
2. **Inventory what is outdated** with the ecosystem's own tool (`npm outdated`, `pip list
   --outdated`, `go list -u -m all`, `cargo outdated`, Gradle versions report). Separate
   patch, minor, and major bumps, and note which are security fixes.
3. **Group the work.** Patch and minor bumps of unrelated packages can go together; a major
   bump, a framework, or anything others depend on goes alone. Keep tooling (linters,
   compilers) separate from runtime dependencies.
4. **Read before bumping.** For each major (and any minor that touches code you use), read the
   release notes or changelog for breaking changes, removed APIs, and new minimum runtime
   versions. Search the repo for each removed or changed API you use.
5. **Bump, then update the lockfile with the ecosystem's own command** — never hand-edit a
   lockfile. Keep version ranges consistent with the project's existing pinning style.
6. **Run the gates** after each group. On failure, fix forward if the cause is a documented
   breaking change; otherwise revert that group and report why.
7. **Check for transitive surprises**: review the lockfile diff for unexpected added, removed,
   or duplicated packages and license changes.

## Rules

- Never upgrade everything in one commit. One group per step so a failure has one suspect.
- Do not disable or loosen a gate (skip a test, relax a type rule) to get an upgrade through.
- Do not change the runtime or language version unless asked; if a dependency requires it,
  stop and report.
- For a vulnerable package, confirm the fixed version actually resolves in the lockfile and
  that the advisory affects the code path in use; say so if you cannot tell.

## Output

Report per group: old and new versions, breaking changes that applied and how they were
handled, the gate results, and anything deliberately left on an old version with the reason.
