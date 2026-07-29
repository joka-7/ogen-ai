# DESIGN.md — full context for `ogen-ai`

Complete design record for this repo: the goal, the landscape research, every
architectural decision *and the reasoning behind it*, the alternatives that were
evaluated and rejected, and the open work. If you're an agent or a person picking this
up cold, read this end to end — it's the "why" that `CLAUDE.md` only summarizes.

---

## 1. Goal & constraints

Build a single repository holding all AI coding-assistant configuration — rules, skills,
and commands — shared across every project as a **git submodule mounted at `.ai/`**. One
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

**Why manifest-driven fragment assembly:** a Python repo shouldn't carry Kotlin rules into
its context window — that's the exact bloat the ETH study warns about. The manifest picks
fragments so each project's AGENTS.md contains only what it uses.

**Why the rules / skills / commands split matters (they port differently):**
- **Rules** → AGENTS.md. Always-on passive guidance. Ports everywhere via the standard.
- **Skills** → SKILL.md folders. On-demand, progressively disclosed. Ports well now.
- **Commands** → slash commands. User-invoked. **Port poorly** — Claude, Cursor, Gemini CLI
  each have their own format — so these are Claude-Code-primary, with per-tool adapters only
  where it's worth it.

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
- `skills/{conventional-commit,scaffold-python-service,audit_repo,customize_config}/SKILL.md`
  — example portable skills. `audit_repo` ships `run_audit.py`, a stdlib-only collector
  script the skill runs before writing its report. `customize_config` ships
  `init_config.py`, which scaffolds a parent project's `ai-project-config.toml` — a
  project-local override file (custom coding rules + per-domain audit weights) that
  lives outside `.ai/` on purpose, since the submodule itself must never be hand-edited.
  See each skill's own docstrings for the algorithms.
- `commands/claude/{review,test}.md` — example Claude slash commands (`$ARGUMENTS` tail).
- `bin/ai-sync` — the generator/installer. Python 3.11+ (tomllib), **stdlib only by design**.
- `adapters/` — templates for tool-specific emission (currently the Cursor `.mdc` template).
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

`ai-sync` runs from a *parent* project root. To test without a real submodule, create a temp
dir, `ln -s <ogen-ai> .ai`, drop in an `ai-config.toml`, and run `ai-sync --dry-run` then
for real. Verified behaviors: correct AGENTS.md assembly (base + languages + frameworks +
practices + local tail); symlink resolution (CLAUDE.md == AGENTS.md); idempotent re-runs;
non-symlink collisions skipped without `--force`; copy mode producing real files that survive
`.ai/` being removed. Keep all of these green when changing the generator.

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
- The `.ai` mount path is referenced in `commands/claude/*` and `README.md`; update those if
  it changes.
- Keep AGENTS.md content to commands/constraints/conventions. No architecture-overview prose
  in the always-on file — put design narrative here in DESIGN.md instead.
