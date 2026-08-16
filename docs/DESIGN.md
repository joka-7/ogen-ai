# DESIGN.md — full context for `ogen-ai`

Complete design record for this repo: the goal, the landscape research, every
architectural decision *and the reasoning behind it*, the alternatives that were
evaluated and rejected, and the open work. If you're an agent or a person picking this
up cold, read this end to end — it's the "why" that `CLAUDE.md` only summarizes.

---

## 1. Goal & constraints

Build a single repository holding all AI coding-assistant configuration — rules, skills,
commands, and (later, §10) role agents — shared across every project as a **git submodule
mounted at `.ai/`**. One
source of truth, version-controlled, serving multiple tools (Claude Code, Gemini, Cursor,
Copilot, Codex, …) and multiple languages (Python already in use; plus TypeScript,
JavaScript, Kotlin, React, and more over time).

Owner context that shaped decisions:
- Primarily backend Python; works on Linux with no desktop environment.
- Claude Code is the primary tool.
- Values lean, deterministic setups; cost/token-conscious; wants things that actually work.

---

## 2. Landscape research (the facts the design rests on)

- **AGENTS.md is the cross-tool standard.** It's an open, tool-agnostic file now stewarded
  by the Linux Foundation's Agentic AI Foundation, read natively by Codex, Cursor, Copilot,
  Gemini CLI, Aider, Windsurf, Zed, Cline and 20–30+ other tools. This is the center of the
  whole design: write rules once, in AGENTS.md, and most tools just read them.
- **Claude Code does NOT read AGENTS.md natively** (as of mid-2026). It reads `CLAUDE.md`.
  Anthropic's documented workaround is a symlink (`ln -s AGENTS.md CLAUDE.md`) or an
  `@AGENTS.md` import inside CLAUDE.md. This is why the generator always wires CLAUDE.md to
  the generated AGENTS.md — otherwise Claude Code (the primary tool!) would load nothing.
- **Skills (SKILL.md) are now an open standard too.** Originally Anthropic, released open in
  late 2025, adopted by Claude Code, Codex, Cursor, VS Code and 30+ tools. Progressive
  disclosure: only the `description` frontmatter is always in context; the body loads when
  the agent decides the skill is relevant. So skills are portable, not Claude-only.
- **Monolithic always-on rule files hurt.** An ETH study found LLM-generated context files
  reduced task success in 5 of 8 settings and added ~2.4–3.9 steps per task, and that
  architecture-overview sections don't function as useful overviews. Takeaway baked into the
  design: keep AGENTS.md lean (commands, constraints, conventions), compile only relevant
  fragments, and push heavy/occasional procedures into skills.

---

## 3. Core architecture & reasoning

**One generated file: `AGENTS.md`. Everything else points at it or at the submodule.**

- `bin/ai-sync` reads a per-project manifest (`ai-config.toml`) and compiles the selected
  rule fragments — plus the project's own `ai-config.local.md` tail — into a single root
  `AGENTS.md` with an AUTO-GENERATED banner.
- It then wires each configured tool:
  - **Cursor / Codex / Copilot / Gemini CLI / Windsurf** read root AGENTS.md natively — no
    extra file needed.
  - **Claude Code**: `CLAUDE.md` → AGENTS.md (symlink or copy).
  - **Gemini**: `GEMINI.md` → AGENTS.md (for surfaces that want the named file).
  - **Copilot**: `.github/copilot-instructions.md` → AGENTS.md (dedicated path some setups
    pin to).
  - **Skills**: `skills/` symlinked/copied into `.claude/skills` and `.agents/skills`.
  - **Commands**: `commands/claude/` into `.claude/commands`.
  - **Agents**: `agents/claude/` into `.claude/agents`, gated on `[options] claude_agents`
    (default off). See §10.

**Why manifest-driven fragment assembly:** a Python repo shouldn't carry Kotlin rules into
its context window — that's the exact bloat the ETH study warns about. The manifest picks
fragments so each project's AGENTS.md contains only what it uses.

**Why the rules / skills / commands split matters (they port differently):**
- **Rules** → AGENTS.md. Always-on passive guidance. Ports everywhere via the standard.
- **Skills** → SKILL.md folders. On-demand, progressively disclosed. Ports well now.
- **Commands** → slash commands. User-invoked. **Port poorly** — Claude, Cursor, Gemini CLI
  each have their own format — so these are Claude-Code-primary, with per-tool adapters only
  where it's worth it.
- **Agents** → subagents with their own context, tool grant, and model tier. Delegated to, not
  invoked directly. **Port worst of all** — no cross-tool standard exists — so they are
  Claude-only and namespaced under `agents/claude/` for the same reason commands are. See §10.

**Shared vs project-local:** the submodule holds the *reusable* layer. Each project still
needs a thin *local* layer (build/test commands, "don't touch this dir") — that lives in the
project's `ai-config.local.md`, appended verbatim to AGENTS.md. Don't force project
specifics into the submodule.

---

## 4. Components

- `rules/base.md` — universal, language-agnostic engineering + agent-behavior rules.
- `rules/languages/{python,typescript,javascript,kotlin}.md` — per-language conventions.
- `rules/frameworks/react.md` — framework conventions.
- `rules/practices/{testing,git-commits,security}.md` — cross-cutting practices.
- `agents/claude/*.md` — the eight role subagents (§10) plus `skills/role_review/SKILL.md`,
  the output contract they share.
- `skills/{conventional-commit,scaffold-python-service,audit_repo,customize_config}/SKILL.md`
  — example portable skills. `audit_repo` ships `run_audit.py`, a stdlib-only collector
  script the skill runs before writing its report. `customize_config` ships
  `init_config.py`, which scaffolds a parent project's `ai-project-config.toml` — a
  project-local override file (custom coding rules + per-domain audit weights) that
  lives outside `.ai/` on purpose, since the submodule itself must never be hand-edited.
  `run_audit.py` reads that same file directly (`ProjectOverrides.load`, self-contained —
  not imported cross-skill) to bias `AuditOrchestrator`'s overall score toward the domains
  a project weights higher, and to pass custom rules through for the auditing agent to
  apply. See each skill's own docstrings for the algorithms.
- `commands/claude/{review,test}.md` — example Claude slash commands (`$ARGUMENTS` tail).
- `bin/ai-sync` — the generator/installer. Python 3.11+ (tomllib), **stdlib only by design**.
- `adapters/` — the Cursor `.mdc` template (emitted by the generator) and
  `claude-agent-permissions.json` (a hand-merged snippet the generator never writes).
- `ai-config.example.toml` — the manifest to copy into each project.

Rule fragments are deliberately lean and start with `## <Title>`. They were written fresh
(a first draft from another model was used only as raw content and then rewritten/expanded).

---

## 5. Alternatives evaluated and rejected

### 5a. A tool-oriented structure (the first external draft)
An early plan organized rules *by tool* (`tools/cursor.md`, `claude-code.md`, `gemini.md`)
and compiled to `.cursorrules` / `.clauderc`. Rejected because:
- It's the pre-standard fragmentation AGENTS.md exists to eliminate — you'd hand-maintain the
  same coding standards across three files forever. Rules must be split by **concern**
  (language/framework/practice), not by tool.
- `.clauderc` isn't a real Claude Code file (hallucinated). Claude Code uses CLAUDE.md +
  `.claude/`.
- `.cursorrules` is legacy; Cursor uses `.cursor/rules/*.mdc` and now reads root AGENTS.md.
- It covered only rules, silently dropping skills and commands.
- It missed the Claude-Code-needs-CLAUDE.md symlink entirely.
The rule *content* from that draft (TS/JS/Kotlin/React) was good and was kept, cleaned up.

### 5b. Four "industry research" claims — scored
1. **AI-dotfiles / prefer copy over symlink.** The engineering concern is real (symlinks
   dangle in sandboxes/containers without the initialized submodule, and break on Windows),
   but "industry standard" is overstated — Anthropic itself documents the symlink. **Acted
   on it:** added `link_mode = "copy"` (see §6). Valid, partial.
2. **Manifest-driven fragment assembly.** Correct — it's exactly this design. (Minor: bloat
   is "context clutter," not "context poisoning," which means corrupting content.)
3. **Migrate rules → local MCP servers, load directives on-demand.** *Rejected — the weak
   claim, and it contradicts #4.* On-demand loading of your own directives is what **Skills**
   already do via progressive disclosure; you don't need a server. MCP is for **live external
   systems** (DB schema, Jira, Figma, live API docs), and it's a running process with a wide
   attack surface — 40+ CVEs were disclosed against MCP implementations Jan–Apr 2026 — versus
   a skill, which is just a text file. The whole "Skills vs MCP vs Rules" literature exists to
   correct exactly this confusion: they're complementary layers, not a migration. Revisit MCP
   only for genuinely dynamic external context, never for static coding conventions.
4. **Strict rules-vs-skills separation.** Correct, and it's what we built: rules always-on in
   AGENTS.md, skills on-demand.

---

## 6. `link_mode`: symlink vs copy

`AGENTS.md` is always a real generated file. `[options].link_mode` controls the rest:
- `"symlink"` (default) — CLAUDE.md/GEMINI.md/copilot link to AGENTS.md; skills/commands link
  into the submodule. Zero drift, nothing duplicated. But links dangle in a sandbox/container
  that has the working tree without the initialized submodule, and break on Windows.
- `"copy"` — real files/dirs written into the project. Portable and container-safe (config
  survives even if `.ai/` isn't checked out), Windows-friendly. Cost: re-run `ai-sync` after
  pulling rule updates. Copied dirs carry a `.ai-managed` marker so re-runs refresh safely.

Safety in both modes: a hand-written file at a target path is never clobbered without
`--force` (files are detected as "ours" by the AUTO-GENERATED banner; dirs by the marker).

On Linux with the submodule always initialized, `symlink` is simplest. Use `copy` for
containerized/CI/cross-platform agent runs.

---

## 7. How it's tested

`tests/` holds an executable `unittest` suite — run it with
`python -m unittest discover -s tests -v`. It used to be a prose list of behaviors to keep
green by hand; that list is now the test names themselves, so this section just says where
each concern lives instead of restating it.

- `tests/test_ai_sync.py` builds the *parent* project root harness against a fixture
  submodule (a temp dir, `ln -s` to a small fixture `.ai/`, an `ai-config.toml`, then
  `ai-sync --dry-run` and for real) and covers: AGENTS.md assembly order (base + languages +
  frameworks + practices + local tail); missing-fragment warnings; symlink resolution
  (`CLAUDE.md == AGENTS.md`, always relative); idempotent re-runs; non-symlink collisions
  skipped without `--force`; copy mode producing real files that survive `.ai/` being removed
  and excluding `__pycache__`/`*.pyc`; the `claude_agents` gate producing no `.claude/agents`
  action when the key is absent, false, or the `claude` target is missing, and wiring it when
  true; `gemini`/`copilot`/`cursor_mdc` targets; and that `--dry-run` changes nothing at all,
  including the parent directories of would-be targets — a real bug the suite caught (§7a).
- `tests/test_conventions.py` asserts this repo's own `agents/`, `skills/`, and `commands/`
  content against the conventions §10 describes, since `ai-sync` performs no frontmatter
  validation of its own. This is what makes the tool-grant matrix (§10, "Tool grants are the
  enforcement") a checked invariant rather than a claim: `Edit`/`Write` only on `developer`,
  no `Bash` on `ciso` or `planner`, every reviewer's finding-ID prefix present in the shared
  contract, and the fan-out and single-role commands agreeing on the role list.
- `tests/test_run_manifest.py` covers `skills/role_review/run_manifest.py` (§10): opening and
  reusing a run, archiving on a new commit, staleness detection via exit code, and the CLI's
  usage errors.

### 7a. A bug the suite found

Writing `test_dry_run_changes_nothing_at_all` surfaced that `--dry-run` printed "nothing
changed" while still creating empty `.claude/` and `.github/` directories — `write_file`,
`rel_symlink`, `place_file`, and `place_tree` each called `mkdir` on the target's parent
before checking the dry-run flag. Fixed by moving those `mkdir` calls behind the same guard
as the writes they precede. Left as a note because it is exactly the kind of defect a
behavioral suite catches that manual `--dry-run` inspection does not: the directories were
easy to miss by eye and easy to assert against.

---

## 8. Open next steps

1. **Fill `skills/scaffold-python-service/template/`** with a real FastAPI + strict-mypy
   baseline (`pyproject.toml`, typed `main.py`, `errors.py`) so the skill scaffolds the
   actual preferred setup, not a stub.
2. **Token-budget check in `ai-sync`** — warn when assembled AGENTS.md crosses a threshold,
   keeping the always-on cost visible (directly serves the lean-context principle).
3. **More language fragments** (Go, Rust, Swift) under `rules/languages/`; add matching globs
   to `LANG_GLOBS` in `bin/ai-sync` for Cursor `.mdc` scoping.
4. **More skills** (e.g. release-checklist, "port module to TS").

---

## 9. Editing conventions

- Fragments start with `## <Title>`, stay tight, one concern each.
- `bin/ai-sync` is **stdlib-only** — don't add dependencies.
- The `.ai` mount path is referenced in `commands/claude/*`, `agents/claude/*`,
  `skills/*/SKILL.md`, and `README.md`; update those if it changes.
- Keep AGENTS.md content to commands/constraints/conventions. No architecture-overview prose
  in the always-on file — put design narrative here in DESIGN.md instead.

---

## 10. The role-agent layer

Added after the original design conversation, so unlike §1–§7 this was new scope rather than a
listed next step. Recorded here because it introduces the fourth artifact type.

### What it is

Eight subagents under `agents/claude/`. Six *reviewing* roles — `qa`, `architect`, `product`,
`engineering-manager`, `sre`, `ciso` — fan out in parallel over a target repo, each in its own
context. `planner` then aggregates their reports into one deduplicated, prioritized backlog.
`developer` implements, but only items a human has explicitly approved. Driven by
`/role-review` (full pass), `/role <name>` (single lens), `/role-backlog` (re-aggregate
without re-reviewing), and `/role-implement` (the approval gate — see below).

`sre` was added after the original five to close a gap the design already knew about:
`engineering-manager`'s own body notes that `audit_data.json` has no delivery-health domain,
and neither it nor `architect` asks whether a failure is visible, survivable, or reversible.
It reviews deployment and configuration surface — healthchecks, graceful shutdown, retries,
observability, resource limits, rollback safety — never application source, so it does not
duplicate `architect`. It is `sonnet`: matching deployment artifacts against a known
operability checklist is pattern work, not the open-ended trade-off reasoning `opus` is
reserved for. Its `Bash` grant is fenced rather than withheld outright (unlike `ciso`): git
metadata on deploy paths is useful and inert, but its body explicitly forbids `docker build`,
`terraform plan`/`apply`, `kubectl`, and `helm` — a `plan` downloads and runs provider
plugins, and a build runs the target repo's own tooling, both of which are executing
untrusted code from the agent's side regardless of what the command name suggests. The
permissions adapter (below) now denies those too.

### Why agents rather than more skills

Skills are procedures the *current* agent loads into the *current* context. That is the wrong
shape here for two reasons. First, isolation is the point: several lenses reviewing the same
repo should not see each other's conclusions, or they converge and stop being separate
lenses. Second, a review of a large repo is exactly the workload that should not share a
context window — six roles each burning 25 file reads in one context would blow it out, while
six subagents each burning 25 in their own do not.

The shared *methodology* is still a skill: `skills/role_review/SKILL.md` holds the output
schema, severity scale, finding-ID convention, and context-budget protocol. Duplicating that
across eight agent files would have been eight copies to drift apart. Roles load it; they do
not restate it.

### Reuse of `audit_repo` rather than duplication

`audit_repo` already scores six domains that map closely onto most of the reviewing roles
(`sre` is the exception — its lens is deployment surface, which `audit_repo` doesn't scan, so
it works primarily from CI config and git metadata instead). Rather than re-implement that
analysis in six prompts, the orchestrator runs `run_audit.py` **once** and writes
`audit_data.json` into the reviews directory; each role reads only its own domain slice as a
mechanical starting point, then does the qualitative work a static scan can't. One scan, many
lenses. The alternative — each role invoking the scanner — would rescan the tree once per role
for identical mechanical result sets.

### Tool grants are the enforcement

The trust boundary is expressed in `tools:`, not in prose, because prose is advisory and a
tool grant is not:

- `ciso` and `planner` get **no `Bash`**. For `ciso` this is the substantive guarantee that a
  security review of an untrusted repo never executes that repo's code — no scanner, no build,
  no test suite. It reads and greps, nothing else.
- Reviewing roles get **no `Edit`/`Write`**. They return their report as their final message
  and the orchestrating command persists it. A reviewer structurally cannot alter what it
  reviews.
- Only `developer` can modify a repo, and only against named, human-approved items.

Model tiers follow the reasoning load rather than the role's seniority: `opus` for `architect`,
`ciso`, `planner`, and `developer` (design judgment, security false-negative cost, cross-report
synthesis, and code that must pass strict gates); `sonnet` for `qa`, `product`, and
`engineering-manager`, which are largely mechanical or metadata-driven. Aliases, not pinned
model IDs, so the agents survive version bumps.

**The one gap:** `tools:` is all-or-nothing per tool. It cannot express "Bash, but only read
commands", and four reviewers need Bash to run a test suite or read git metadata. Their
read-only constraint is therefore prompt-level, backed by
`adapters/claude-agent-permissions.json` — `permissions.deny` rules the user merges into
their own `.claude/settings.json`. Not auto-installed: that file is hand-maintained, so
writing it would either clobber it or be skipped by the no-clobber invariant. Those rules are
also project-wide rather than per-agent, which the README states plainly rather than
presenting the snippet as a drop-in.

### Opt-in by default

Gated on `[options] claude_agents`, defaulting to `false`, mirroring `cursor_mdc`. Eight agent
descriptions are always-on context cost in any project that installs them, and a project that
never runs a multi-role review shouldn't pay it. The consequence, worth remembering: the
feature ships dormant and does nothing until a project flips the key.

### Output lands outside this submodule

Reports are written to `<target>/.ai-reviews/`, and the command appends that path to the
target's `.git/info/exclude` rather than its committed `.gitignore` — so reviews never dirty
`git status` and never get committed by accident, without editing a tracked file. Nothing is
ever written into `.ai/`, per the same boundary `customize_config` exists to enforce.

### The run manifest

`.ai-reviews/manifest.json`, written by `skills/role_review/run_manifest.py`, exists because
findings are pinned to a commit — every report is stamped `@ <short-sha>` and a `file:line`
is only meaningful against the code that produced it — but nothing recorded which commit a
given set of reports described. `--begin` opens a run for the current sha, archiving the
prior run's reports under `archive/<old-sha>/` if HEAD has moved, or reusing the run in place
if it hasn't, so re-running the fan-out at one commit is idempotent the same way an `ai-sync`
re-run is. `--status` exits non-zero when the reports on disk predate HEAD, which is what lets
`/role-implement` refuse — or at least warn loudly before — implementing against a stale
finding.

### The approval gate is a command, not an inference

The original design left the human-approval handoff as prose: `/role-review` and `/role` both
state that `developer` must not be invoked, and the actual invocation was left to the main
session inferring, from a later human message, that specific items were approved. That is the
one load-bearing safety property in this whole layer, and it rested on inference rather than
a checked step.

`/role-implement` makes it a command instead. It requires a backlog to exist, refuses to run
with an empty item list rather than guessing "the critical ones," checks the backlog's
currency via the run manifest, requires a clean worktree so `developer`'s diff is
attributable, and echoes the resolved backlog text back to the user before launching anything.
It is the only command permitted to invoke `developer` — `/role-review`, `/role`, and
`/role-backlog` all still refuse to, and `tests/test_conventions.py` checks that refusal is
stated, not just implied, in each of their bodies.
