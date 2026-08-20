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
- **Skills** → SKILL.md folders. Ports to Claude, Gemini, Cursor, and Copilot — see §11.
- **Commands** → slash commands. **Fragmented, not absent.** Cursor (`.cursor/commands/`),
  Windsurf ("workflows", `.windsurf/workflows/`), and Copilot (`.github/prompts/*.prompt.md`,
  VS Code Copilot Chat only — not yet the Copilot CLI) each have their own format and none
  match this repo's `description`-only-frontmatter-plus-`$ARGUMENTS` shape. Claude-Code-primary
  by default because porting means a transform per target, not a symlink — one transform now
  exists (`[options].cursor_commands`, §11), the other two remain undone for the reason §8's
  investigation note gives: Cursor was the only target with a real example fetched to build
  the transform against; Windsurf's and Copilot's exact conventions weren't confirmed to the
  same standard, so guessing at them was declined rather than shipped unverified.
- **Agents** → subagents with their own context, tool grant, and model tier. **Also
  fragmented, not absent**: Cursor has them (`.cursor/agents/`, `name`/`description`/`model`/
  `readonly`/`is_background` frontmatter — confirmed by reading two real examples,
  `security-auditor.md` and `verifier.md`, in a public repo), Copilot has them in Visual
  Studio 2026.4+ (`.github/agents/*.agent.md`, a different shape again), Windsurf has
  subagent support with an unconfirmed file convention. Claude-only today for a sharper
  reason than commands, and this one is now confirmed rather than suspected: `readonly` is a
  coarse write-toggle, not a tool allowlist. The real `security-auditor.md` example has to
  state "no command execution" as **prose in its body**, the same advisory-only pattern this
  repo's own `ciso.md` explicitly rejects ("You have no Bash tool. This is deliberate, not an
  oversight" — a structural claim, not a promise). Cursor does have a project-wide shell
  allow/deny mechanism (`.cursor/cli.json`, `permissions.allow`/`permissions.deny` on command
  patterns) — structurally the same category as this repo's own
  `adapters/claude-agent-permissions.json` gap-filler for the Bash-holding reviewers, with the
  same "not a security boundary, not per-agent" caveat this repo already states about its own
  version, and public security research reports denylist-bypass techniques against it. Given
  that, porting `ciso`/`planner` specifically and keeping their "structurally cannot execute
  code" claim would be false advertising on Cursor as the format stands; the reviewing roles
  that already tolerate a fenced/advisory Bash grant (`qa`, `architect`, `product`,
  `engineering-manager`, `sre`) are a smaller lift. See §10.

**Shared vs project-local:** the submodule holds the *reusable* layer. Each project still
needs a thin *local* layer (build/test commands, "don't touch this dir") — that lives in the
project's `ai-config.local.md`, appended verbatim to AGENTS.md. Don't force project
specifics into the submodule.

---

## 4. Components

- `rules/base.md` — universal, language-agnostic engineering + agent-behavior rules.
- `rules/languages/{python,typescript,javascript,kotlin,go,rust,swift}.md` — per-language
  conventions.
- `rules/frameworks/react.md` — framework conventions.
- `rules/practices/{testing,git-commits,security,architecture}.md` — cross-cutting practices.
- `agents/claude/*.md` — the eleven role subagents (§10, §12) plus `skills/role_review/SKILL.md`,
  the output contract the seven reviewing roles share.
- `skills/{conventional-commit,scaffold-python-service,audit_repo,customize_config,
  release-checklist}/SKILL.md` — example portable skills. `audit_repo` ships
  `run_audit.py`, a stdlib-only collector script the skill runs before writing its report.
  `customize_config` ships
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

The original four are all shipped:

1. **`skills/scaffold-python-service/template/`** is a real FastAPI + strict-mypy baseline
   now — a typed app factory, an `Error`-rooted exception hierarchy, a smoke test — verified
   against its own `ruff`/`mypy --strict`/`pytest` gates before being checked in, built around
   a placeholder `example_service` package the skill renames.
2. **`ai-sync` now warns on a token budget.** `check_token_budget` estimates AGENTS.md's size
   at ~chars/4 (a rough heuristic — an exact tokenizer would be a dependency, which the
   stdlib-only rule forecloses) and warns, never fails, past `[options].token_budget`
   (default `6000`; `0` disables). Keeps the always-on cost visible without gating the run on it.
3. **Go, Rust, and Swift fragments** are in under `rules/languages/`, each in the existing
   fragment shape and wired into `LANG_GLOBS` for Cursor `.mdc` scoping.
   `tests/test_conventions.py`'s `TestLangGlobs` checks both directions — a fragment with no
   glob, or a glob with no fragment, fails the suite rather than silently doing nothing.
4. **Two more skills.** `release-checklist` walks a target repo from its last tag to a
   version-bumped, tagged commit — deriving the bump from Conventional Commits since that
   tag, running whatever gate commands its CI config defines, and refusing to bump over a
   failing gate — then stops; it never pushes the tag or publishes, per `rules/base.md`'s
   rule on large or irreversible actions. `port-module-to-ts` ports a JS/Python module's
   behavior into TypeScript against `rules/languages/typescript.md`, explicitly as a port
   (behavior parity, no opportunistic fixes) rather than a rewrite.

Two judgment calls from building the role-agent layer, deliberately left as-is rather than
decided here: whether `sre`'s Bash grant (§10) should be withheld outright like `ciso`'s
rather than fenced, and whether `/role-implement` should gain an opt-in commit flag instead
of always leaving the change for manual review.

**Update, superseding the paragraph this replaced:** commands and agents are now ported to
every platform investigated with sufficient confidence — see §11's "Commands and agents to
Gemini, Copilot, and Windsurf" and "Cursor agents" subsections for the full sourcing per
platform. Summary: Gemini and Cursor commands, Copilot prompts, and Windsurf workflows are all
built (`gemini_commands`/`cursor_commands`/`copilot_commands`/`windsurf_commands`); Gemini,
Cursor, and Copilot agents are all built (`gemini_agents`/`cursor_agents`/`copilot_agents`).
The `ciso`/`planner` Cursor question was resolved as a real decision, not left open: the user
chose the weaker-honest-claim option over excluding them, so the Cursor port carries an
explicit disclaimer rather than repeating a guarantee the format can't back — Gemini's and
Copilot's ports keep the claim in full, since their tool-restriction mechanisms are confirmed
(Gemini, primary docs) or strongly evidenced (Copilot, real examples) to actually work.
**Codex skills are now built too** (`.codex/skills`, unconditional on the target, same as
every other platform) — an initial "structurally out of scope" finding turned out to be
incomplete: `CODEX_HOME` is a real, documented environment variable, not a fixed path, so the
project-relative fix is "wire the files, document the one-time `CODEX_HOME` env var setup,"
not "impossible." See §11's Codex paragraphs for both passes. Left undone, each for a stated
reason rather than silently: Windsurf agents (no real example, plus rebrand ambiguity between
`.windsurf/` and `.devin/` conventions), Windsurf skill wiring (two sources actively disagreed
and neither was resolved with a real example), and Codex's commands/agents (commands: the
equivalent mechanism is reportedly deprecated in favor of skills; agents: no convention found
at all).

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

Eleven subagents under `agents/claude/`. Seven *reviewing* roles — `qa`, `architect`,
`product`, `engineering-manager`, `sre`, `senior-dev`, `ciso` — fan out in parallel over a
target repo, each in its own context. `planner` then aggregates their reports into one
deduplicated, prioritized backlog. `developer` implements, but only items a human has
explicitly approved; `tracker` and `docs-sync` sync that state outward to Jira and Confluence
once it exists — see §12 for those three, added in a later pass than the original eight.
Driven by `/role-review` (full pass), `/role <name>` (single lens), `/role-backlog`
(re-aggregate without re-reviewing), `/role-implement` (the approval gate — see below),
`/sync-tracker`, and `/sync-docs`.

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
context window — seven roles each burning 25 file reads in one context would blow it out,
while seven subagents each burning 25 in their own do not.

The shared *methodology* is still a skill: `skills/role_review/SKILL.md` holds the output
schema, severity scale, finding-ID convention, and context-budget protocol. Duplicating that
across seven reviewing-role files would have been seven copies to drift apart. Roles load it;
they do not restate it. `tracker` and `docs-sync` deliberately don't load it — they take
actions, not findings, and have their own output schemas defined in their own bodies.

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
- `developer` can modify a repo, and only against named, human-approved items. `docs-sync`
  (added later, §12) is the one other write-capable role — scoped to documentation-shaped
  content, not code, but that scope is a body rule, not a tool grant: Claude Code cannot
  glob-scope `Edit`/`Write` the way it can withhold a tool outright, so `docs-sync`'s
  boundary is the same category of guarantee as `sre`'s fenced `Bash` — stated plainly,
  not structurally airtight, and flagged as such rather than presented as equally hard.

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

Gated on `[options] claude_agents`, defaulting to `false`, mirroring `cursor_mdc`. Eleven agent
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

---

## 11. Skills, commands, and agents reach more platforms

Added Aug 2026, after §1's original platform survey. At the time of that survey, skills
(the `SKILL.md` folder convention) had no adoption outside Claude and Gemini, which is why
§3/§4 wired them only to `.claude/skills` and `.agents/skills`. Both Cursor and Copilot have
since adopted the same convention — Cursor auto-discovers skills from `.cursor/skills/`
(a mechanism separate from the glob-scoped `.cursor/rules/*.mdc` files `cursor_mdc`
produces), and Copilot discovers skills from `.github/skills/`, and also directly from
`.claude/skills/` and `.agents/skills/` — so a project already targeting `claude` or
`gemini` alongside `copilot` picks up skills there with no dedicated wiring at all. The
dedicated `.github/skills/` path exists for the copilot-only case, where nothing else would
wire skills anywhere.

Wiring for both is unconditional on the target being selected, matching how skills reach
`claude`/`gemini` — no extra opt-in flag, unlike `cursor_mdc` (a genuinely optional derived
artifact) or `claude_agents` (opinionated, context-costly agents). Skills are neither; a
project that lists `cursor` or `copilot` as a target wants what that tool can use.

**Provenance caveat, stated plainly because it matters:** the exact discovery paths above
were sourced from web search in August 2026, not a fetched primary doc. This environment's
network policy blocked direct `WebFetch` access to `cursor.com/docs` and
`docs.github.com` at the time — only the search tool itself reached external results, likely
because it runs through Anthropic's own infrastructure rather than this sandbox's egress
proxy. Two independent secondary sources agreed on both paths, which is reasonable grounds to
ship, but not the same as reading the vendor's own documentation. Spot-check against a real
Cursor and Copilot install before relying on this wiring for a new project, and prefer
re-verifying against primary docs over trusting this note if the two ever disagree.

### Commands to Cursor

`WebFetch` was blocked for `cursor.com` directly, but not for `github.com` and
`raw.githubusercontent.com` — apparently a domain-specific policy, not a blanket one. That
opened a better path than search summaries: fetching real, byte-for-byte config files from
public repos via `curl` (bypasses `WebFetch`'s own summarizing model, which paraphrased
rather than quoted verbatim on a first attempt) and `raw.githubusercontent.com`. A real
`.cursor/commands/code-review.md` example (`hamzafer/cursor-commands`) confirmed Cursor
commands are plain markdown with **no frontmatter at all** — just a bare `# Title` body,
invoked as `/filename`, inserted into the chat input verbatim.

`emit_cursor_commands` in `bin/ai-sync` transforms `commands/claude/*.md` accordingly: strips
this repo's `description:` frontmatter (Cursor has nowhere to put it), and rewrites
`$ARGUMENTS` — a Claude-only convention with no confirmed Cursor equivalent; the one real
example found took no arguments at all. Cursor reportedly inserts a command's body into the
chat input and lets the user type additional text in the same message, so `$ARGUMENTS` is
replaced with a fixed phrase pointing at that same-message text, distinguishing the
trailing-token idiom (`"...say so briefly. $ARGUMENTS"` → a closing sentence) from inline use
(`"$ARGUMENTS is <role> [path]"` → mid-sentence noun phrase, capitalized only when it opens a
sentence). This is an adaptation built from one confirmed example, not a verified-correct
spec — gated behind `[options].cursor_commands`, off by default, unlike skills wiring, because
changing content deserves an explicit opt-in the way an unchanged symlink does not.

At the time this was written, Windsurf and Copilot command porting stopped here — no equally
solid real example had been found for either. Both were revisited (below) once the user asked
for full platform coverage, and both are now built.

### Commands and agents to Gemini, Copilot, and Windsurf

Requested explicitly: full coverage, not just Cursor. Same discipline as above — verify with
a real fetched example or a primary doc before writing a transform, and say plainly when that
bar wasn't cleared rather than shipping a guess.

**Gemini is the best-sourced platform in this table**, because its docs live in its own
GitHub repo (`google-gemini/gemini-cli`) and were fetched directly — `raw.githubusercontent.com`
reached them even though `cursor.com` and `docs.github.com` stayed blocked, which turned out
to be a domain-specific policy rather than "no external docs at all" (worth remembering: a
blocked `WebFetch` on one domain doesn't mean every domain is blocked, and a project's docs
being GitHub-hosted is itself worth checking before assuming a summary is the best available).
`docs/cli/custom-commands.md` confirms `.gemini/commands/*.toml` with `description` and
`prompt` fields and a real `{{args}}` placeholder — a documented mechanism, not a guess, so
`$ARGUMENTS` maps to it directly. `docs/core/subagents.md` confirms `.gemini/agents/*.md` with
`name`/`description`/`kind`/`tools` frontmatter, and states outright: *"the subagent only has
access to the tools you explicitly grant it."* That is the same "harder guarantee than any
deny list" framing this repo's own `adapters/claude-agent-permissions.json` uses for Claude's
Bash-holding reviewers — except here it's Gemini's own documented behavior, not an external
hardening layer. Tool names (`read_file`, `grep_search`, `glob`, `run_shell_command`, `replace`,
`write_file`) come from `docs/tools/file-system.md` and `docs/tools/shell.md`, also fetched
directly, not guessed. Because the guarantee is real and documented, `ciso` and `planner` keep
their full "cannot execute code" claim on the Gemini port — the only platform where that's true
without a disclaimer.

**Copilot's commands and agents are confirmed against real examples, not primary docs.**
`learn.microsoft.com` and `code.visualstudio.com` stayed blocked throughout, so
`.github/prompts/*.prompt.md`'s schema comes from a community reference doc
(`github/awesome-copilot`'s `instructions/prompt.instructions.md`, fetched directly) rather
than Microsoft's own documentation — it names `description`/`agent`/`tools`/`argument-hint`
fields and a real `${input:variableName}` placeholder, which `$ARGUMENTS` maps to.
`.github/agents/*.agent.md`'s schema comes from real files in that same repo: `debug.agent.md`,
`azure-policy-analyzer.agent.md`, `context7.agent.md`, and `doublecheck.agent.md` were all
fetched directly. The last two matter most — both omit `edit` and `execute` from their `tools:`
list entirely, which is the observed mechanism for a read-only agent on this platform. That's
real-world evidence of intent (independently-authored agents converge on the same withholding
pattern), not a doc stating the enforcement outright the way Gemini's does — so `ciso`/`planner`
keep their full claim on the Copilot port too, but the docstring says plainly that this is
higher confidence than a guess and lower than Gemini's primary-doc-confirmed guarantee.

**Windsurf's command format ("workflows") is confirmed against one real example**
(`gotalab/ide-rules`, `python-project-setup.md`, fetched directly): `.windsurf/workflows/*.md`
keeps a `description:` frontmatter field — this repo's own shape, unlike Cursor's bare-body
convention — with no confirmed argument-substitution syntax in that example, so `$ARGUMENTS`
gets the same fallback-phrase treatment as the Cursor port.

**Windsurf agents and Windsurf skills were investigated and explicitly not built.** For
skills, two sources disagreed: one described `.windsurf/skills/` as auto-discovered and
portable unmodified from Claude/Cursor; a real, checked-in porting guide
(`addyosmani/agent-skills`, `docs/windsurf-setup.md`, fetched directly) showed the opposite —
skills pasted manually into `.windsurfrules`, no auto-discovery. Neither claim was resolved
with a real `.windsurf/skills/` example, so nothing was wired rather than picking a side by
guessing. For agents, no real `.windsurf/agents/*.md` example was found at all, and Windsurf's
mid-2026 rebrand to "Devin Desktop" surfaced a second convention (`.devin/skills/` with
`allowed-tools`/`triggers` fields, different from what the Windsurf-branded sources described)
whose precedence wasn't confirmed either — an active-rebrand ambiguity on top of a missing
example, not a case where more searching would obviously resolve it.

**Codex, revisited twice.** The first pass undersold the investigation — it guessed a couple
of doc paths and stopped. Redone properly: Codex's own `docs/skills.md` (fetched directly,
though it punts to `developers.openai.com/codex/skills`, a domain blocked here like
`cursor.com`) plus a real setup guide (`ComposioHQ/awesome-codex-skills`, fetched directly)
confirmed Codex skills load from `$CODEX_HOME/skills`, defaulting to `~/.codex/skills` — the
user's home directory, not the project, with no project-level override found in `docs/config.md`.

That second pass concluded "structurally out of scope" — every other platform's path is
project-relative and git-shareable, Codex's confirmed mechanism wasn't, so `ai-sync` (a
project-root generator) had no path to write into without becoming a different kind of tool.
**That conclusion was wrong, or at least incomplete — asked to double-check, a third pass
found `CODEX_HOME` is itself a real, documented environment variable, not a fixed path.**
Confirmed via a GitHub issue on `openai/codex` and a third-party reference (Codex's own
`developers.openai.com/codex/environment-variables` page stayed blocked): `CODEX_HOME`
defaults to `~/.codex` but can be set to anything, including a project-relative path — the
example found was literally `CODEX_HOME=/workspace/.codex`.

That changes the fix from "impossible" to "one step outside `ai-sync`'s reach, not inside
it." `ai-sync` now wires `.codex/skills` exactly like every other platform's skills path —
`if "codex" in targets: place(submodule / "skills", project_root / ".codex" / "skills")`,
unconditional, matching the others. What `ai-sync` genuinely cannot do is set an environment
variable in the invoking shell on the project's behalf — that's the one piece left as a
documented setup step (`CODEX_HOME=<project-root>/.codex`, in a shell profile, `.envrc`, or
CI config), stated in `README.md`, `adapters/README.md`, and the manifest comment, not
silently assumed. No command port: custom prompts (the command-equivalent) are reportedly
deprecated in favor of skills, so there's nothing worth building a transform for. No agent
port: no custom-agent convention was found at all, unlike skills.

The lesson worth keeping, separate from the Codex-specific outcome: a "structural, not
possible" conclusion is itself a claim that deserves the same scrutiny as any other finding
in this section — worth one more pass checking for an escape hatch (an env var, a config
override) before it gets written down as settled.

### Cursor agents

Confirmed against two real `.cursor/agents/*.md` examples (`wchen02/cursor-agent-learning`,
`security-auditor.md` and `verifier.md`, fetched directly): frontmatter fields
`name`/`description`/`model`/`readonly`/`is_background`. This is the investigation §8 flagged
as an open question and closed with a finding, not a guess (see §8's newest item): `readonly`
is confirmed to be a coarse write-toggle, not a tool allowlist, because the real
`security-auditor.md` example has to state "no command execution" as **prose in its body** —
if `readonly` structurally covered shell execution, that sentence would be redundant.

`emit_cursor_agents` sets `readonly` from whether the source grant has `Edit`/`Write` (an
accurate mapping — that dimension genuinely is what `readonly` covers) and `model: inherit`
(matching the real example, rather than guessing an opus/sonnet-to-Cursor-model mapping with
no confirmed basis). For `ciso` and `planner` — the two roles with no `Bash` at all on Claude —
`CURSOR_NO_BASH_DISCLAIMER` is prepended to the ported body, stating plainly that this port's
"cannot execute code" claim is only as strong as the project's own `.cursor/cli.json` shell
deny list, if one exists, which is itself confirmed to be project-wide rather than per-agent
and to have reported bypass techniques. This was the user's explicit choice among two options
presented: weaken the claim honestly, or exclude `ciso`/`planner` from the Cursor port
entirely. Every other role already tolerated a fenced or absent Bash grant on Claude, so only
these two needed the decision.

---

## 12. Three more roles: senior-dev, tracker, docs-sync

Requested directly, not inferred: a ninth reviewing role focused on line-level code quality,
and two roles that sync review/implementation state to third-party systems — Jira and
Confluence — kept "always in sync with the flow of the code."

### `senior-dev`

The least novel of the three — a seventh reviewing role, same shape as the existing six.
Positioned deliberately narrow against what already exists: `architect` owns structure and
coupling, `qa` owns test coverage and mock quality, `/review` (the command) checks staged-diff
rule compliance. `senior-dev` owns what's left — correctness judgment, error-handling
soundness, readability, and abstraction fit in the implementation itself, the read a senior
engineer gives a pull request. `opus`, matching the other judgment-heavy roles, because
"would I approve this" is a trade-off call, not a checklist match. Finding prefix `SDR`;
`planner` gained one new dedup rule (`SDR`+`QA` on the same bug-with-no-test is one item, not
two) and no others, since `senior-dev`'s lane barely overlaps the rest by design.

### Why tracker and docs-sync needed a real architecture decision, not just a new agent file

Every prior role only ever touched the local target repo — read it, and for `developer` alone,
wrote to it. Jira and Confluence are outside that boundary entirely, which raised a question
none of the other ten roles ever had to answer: how does a subagent reach an authenticated
third-party system without every existing trust-boundary guarantee in this file becoming
meaningless? Three sub-decisions, each asked rather than assumed:

**Integration mechanism: MCP, not credentialed Bash.** The alternative — agents running
authenticated `curl`/CLI calls directly — was rejected because it would have been a real
regression: every existing Bash-holding role (even `sre`) is fenced to git-metadata-only
specifically so that untrusted target-repo content can never reach a credential. An MCP tool
grant keeps that intact — credentials live in the MCP server's own configuration, which this
repo never sees, the same isolation principle as every other tool grant in this layer, just
applied to a new category of tool. Confirmed for real: Atlassian's official Rovo MCP server
(`atlassian/atlassian-mcp-server`, fetched directly) exposes exactly the tools these two roles
need — `createJiraIssue`, `editJiraIssue`, `transitionJiraIssue`, `addCommentToJiraIssue`,
`getJiraIssue`, `searchJiraIssuesUsingJql` for Jira; `getConfluencePage`,
`createConfluencePage`, `updateConfluencePage`, `searchConfluenceUsingCql` for Confluence —
real tool names, not invented ones, though the exact byte-for-byte spelling came from
Atlassian Community forum discussion rather than the server's own "Supported tools" reference
page, which lives on `support.atlassian.com` and stayed blocked in this sandbox like every
other non-GitHub Atlassian/Microsoft domain this investigation has hit.

**The alias is a real, unavoidable gap.** `tools: mcp__atlassian__*` only works if the
consuming project connected that exact server under the alias `atlassian` — MCP server
configuration is the project's own `.mcp.json`/Claude Code settings, which `ai-sync` has no
path to (nor should it: that's where the credentials are scoped, deliberately outside this
repo's reach). A project using a different alias, or a community Jira/Confluence MCP server
instead of Atlassian's official one, has to hand-edit `tracker.md`/`docs-sync.md`'s `tools:`
list before either role does anything — stated in both agent files and `adapters/README.md`,
not silently assumed to just work.

**Trigger model: commands at checkpoints, not automation.** "Always in sync with the flow of
the code" isn't literally achievable by a subagent — subagents only run when a session invokes
them; there's no passive watcher. The closest honest approximation is `/sync-tracker` and
`/sync-docs`, invoked at defined points (typically right after `/role-implement`, which now
suggests both in its final report) rather than a git hook, which was considered and set aside:
a hook fires outside any Claude Code session and would need its own design this repo doesn't
have today. This was a direct choice among three options presented, not a default.

### `docs-sync` and the second write-capable role

`docs-sync` needs to edit the target repo's documentation, which conflicts with a claim
stated as absolute everywhere in this design record up to this section: "only `developer`
edits." That claim is now false, on purpose. Reconciled by scoping, not by dropping the
principle: `docs-sync` may only touch documentation-shaped content (`README*`, `docs/**`,
`CHANGELOG*`, other `*.md`, docstrings, comments) — never source logic, never tests' logic.
That scope is enforced by `docs-sync.md`'s own rules, not by the tool grant, because Claude
Code cannot glob-scope `Edit`/`Write` the way it can withhold a tool outright. This is the
same category of guarantee as `sre`'s fenced `Bash` — a body rule, stated plainly as such
rather than presented as equal in strength to `ciso`'s "no `Bash` at all," which *is*
structural. Every place this design record and the README previously said "only `developer`
edits" as an absolute now says "`developer` and `docs-sync`, each scoped to a different
domain" instead — `README.md`, this section's own §10 cross-reference, the permissions
adapter's comment, and `developer.md`'s own description.

`docs-sync` and `tracker` also both skip `role-review`'s shared skill entirely — the schema
that skill defines is for reviewing roles reporting findings; these two take actions and
report what they did, in their own schema, defined in their own agent bodies rather than a
shared skill (there's no third role yet to make a shared contract worth the indirection).

### A bug §11's cross-platform ports didn't know to expect

`emit_cursor_agents`/`emit_gemini_agents`/`emit_copilot_agents` (§11) glob every file under
`agents/claude/*.md` with no per-role special-casing — deliberate, since adding an agent was
supposed to need no `ai-sync` change at all. That assumption broke the moment an agent's
`tools:` list could contain something none of the three platforms' tool maps had ever seen:
`mcp__atlassian__*`. Each port's tool map (`GEMINI_TOOL_MAP`, `COPILOT_TOOL_MAP`, Cursor's
readonly-toggle logic) only translates Claude's built-in tool names, so an unmapped
`mcp__`-prefixed entry was silently dropped rather than translated — `tracker.md` ported to
Gemini kept its description of managing Jira issues but lost every tool that could actually
do it. Caught by actually running the port and reading the output, not by inspection.

Fixed by refusing to guess at a mapping instead of shipping a defanged agent: `_has_mcp_tools`
detects any `mcp__`-prefixed tool, and each of the three port functions skips that agent
entirely — with a warning naming which agent and why — rather than porting it missing the one
tool its whole purpose depends on. A real per-platform mapping stays possible later (Gemini's
own docs already name a different convention, `mcp_<server>_<tool>`, single underscores), but
skip-with-a-reason is the honest default until one is confirmed for each platform the same way
every other claim in §11 was: against a fetched primary doc or a real example, not a guess.
