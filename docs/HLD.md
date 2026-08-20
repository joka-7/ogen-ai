# High-Level Design

This is the system-level view: what `ogen-ai` is, its boundaries, its major components, and
how data flows through it. It complements — does not replace — `docs/DESIGN.md`, which
carries the full reasoning, alternatives rejected, and per-decision rationale. Read this
first for the shape of the system; go to `DESIGN.md` when you need the "why" behind a
specific line here. `docs/LLD.md` goes one level deeper still, into per-file/function
behavior. `docs/INVENTORY.md` is the flat list of every fragment/skill/command/agent that
exists.

## 1. Problem and scope

Every AI coding assistant (Claude Code, Cursor, Gemini CLI, Copilot, Windsurf, Codex, …)
wants project-specific instructions, but each reads them from a different file in a
different shape. Maintaining that by hand per project — and per tool, per project —
duplicates the same rules N times and lets them drift.

`ogen-ai` is **one source of truth**, mounted into every consuming project as a git
submodule at `.ai/`, that a generator (`bin/ai-sync`) compiles into each tool's own format.
Write a rule, a skill, a command, or an agent once here; it reaches every tool a project
opts into.

**Out of scope, deliberately:** this repo does not run inside a consuming project's CI, does
not execute or lint the consuming project's code, and does not hold any credentials —
`bin/ai-sync` is a pure generator that reads this repo and a project's manifest and writes
files. Nothing here calls out to a network service except the opt-in MCP tool grants on two
agents (`tracker`, `docs-sync`), and those calls happen in the *consuming* project's Claude
Code session, never in `ai-sync` itself.

## 2. Actors

- **A maintainer of `ogen-ai`** — edits fragments, skills, commands, agents in this repo.
- **A consuming project** — a git repo with `ogen-ai` mounted at `.ai/` and an
  `ai-config.toml` manifest declaring its stack and which tools it targets.
- **`bin/ai-sync`** — the generator, invoked from the consuming project's root.
- **An AI coding assistant** (Claude Code, Cursor, Gemini CLI, Copilot, Windsurf, Codex) —
  reads the files `ai-sync` wired up, inside a session working on the consuming project.
- **A human running a role-review** (Claude Code only, opt-in) — invokes `/role-review`,
  `/role`, `/role-implement`, `/sync-tracker`, `/sync-docs` against a target repo (which may
  or may not be the same repo `ogen-ai` is mounted into).

## 3. Component map

```
┌─────────────────────────────────────────────────────────────────────┐
│ ogen-ai (this repo, mounted at .ai/ in a consuming project)         │
│                                                                       │
│  rules/{base,languages/*,frameworks/*,practices/*}.md  ── fragments  │
│  skills/<name>/SKILL.md                                ── on-demand  │
│  commands/claude/*.md                                  ── Claude     │
│  agents/claude/*.md                                     subagents/   │
│                                                           subagents   │
│  adapters/  (templates + notes for tool-specific wiring)             │
│  bin/ai-sync  ─────────────────────────────────────────► generator   │
│  tests/  (unittest suite covering ai-sync + conventions)             │
└─────────────────────────────────────────────────────────────────────┘
                              │  reads
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ consuming project root                                               │
│  ai-config.toml         ── manifest: [stack] [tools] [options]       │
│  ai-config.local.md     ── optional project-specific rule tail       │
└─────────────────────────────────────────────────────────────────────┘
                              │  ai-sync compiles + wires
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ generated / wired output, per [tools].targets                        │
│  AGENTS.md  (the one real generated file)                            │
│  CLAUDE.md, GEMINI.md, .github/copilot-instructions.md  (→ AGENTS.md)│
│  .claude/{skills,commands,agents}, .agents/skills, .cursor/{skills,  │
│  rules,commands,agents}, .github/{skills,prompts,agents}, .codex/    │
│  skills, .windsurf/workflows                                         │
└─────────────────────────────────────────────────────────────────────┘
                              │  read natively by
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ AI coding assistant session, working on the consuming project        │
│  Claude Code adds: the role-agent layer (§6) — /role-review,        │
│  /role, /role-backlog, /role-implement, /sync-tracker, /sync-docs    │
└─────────────────────────────────────────────────────────────────────┘
```

## 4. Data flow

1. A maintainer edits a fragment, skill, command, or agent in `ogen-ai` and merges it.
2. A consuming project runs `git submodule update --remote .ai` to pull the change, and
   maintains `ai-config.toml` (its own manifest: which languages/frameworks/practices,
   which tool targets, which options) plus an optional `ai-config.local.md` tail for rules
   specific to that project alone.
3. `python .ai/bin/ai-sync` runs from the project root:
   - Reads `ai-config.toml`.
   - Assembles `AGENTS.md` from `rules/base.md` + the fragments named in `[stack]`, in a
     fixed order (base → languages → frameworks → practices → the local tail under a
     `## Project-specific` heading), stamped with a "do not edit by hand" banner.
   - Warns (never fails) if the assembled `AGENTS.md` estimate crosses `[options].token_budget`.
   - For each tool named in `[tools].targets`, wires that tool's own entrypoint and
     directories — see LLD §2 for exactly what each target gets.
4. The AI assistant's own session, running in the consuming project, reads whatever got
   wired for it — natively, with no `ogen-ai`-specific runtime involved from that point on.
5. **Claude Code only, opt-in:** if `claude_agents = true`, the role-agent layer is also
   wired into `.claude/agents`, and a human can drive a review/implement/sync cycle against
   any target repo (not necessarily the one `ogen-ai` is mounted into) via the commands in
   §6. That cycle writes its own artifacts to `<target>/.ai-reviews/`, never into `.ai/` or
   into the project the assistant happens to be running from.

Re-running `ai-sync` is idempotent: unchanged output is reported "ok (symlink current)" and
nothing is rewritten; a hand-written file sitting at a target path is never clobbered without
`--force`.

## 5. `link_mode`: the one structural choice that changes everything downstream

`[options].link_mode` picks how *everything except `AGENTS.md` itself* is placed:

- **`symlink`** (default) — links point back into `.ai/`. Zero duplication, but the link
  dangles if a session runs in a sandbox/container that has the working tree without the
  submodule initialized, and symlinks do not work on Windows.
- **`copy`** — real files and directories are written into the project, marked with a
  `.ai-managed` marker so re-runs can refresh them safely without clobbering hand-edits.
  Portable and container-safe at the cost of needing a re-run after every submodule update.

This one flag is why `bin/ai-sync` carries two parallel placement primitives (`rel_symlink`
vs. `place_file`/`place_tree` — LLD §1) instead of one.

## 6. The role-agent layer (Claude Code only, opt-in)

Eleven subagents under `agents/claude/`, installed only when `claude_agents = true`. Seven
review a target repo from different professional lenses and converge on one backlog;
`developer` and `docs-sync` act on it once a human approves; `tracker` and `docs-sync` also
push that state to Jira/Confluence. Full role-by-role detail is in `docs/DESIGN.md` §10 and
§12; LLD §3 has the tool-grant matrix and file-format contract every agent must satisfy.

```
/role-review <target>   ──►  qa, architect, product, engineering-manager,
                              sre, senior-dev, ciso   (parallel, each own context)
                                        │
                                        ▼
                                    planner  ──►  .ai-reviews/BACKLOG.md
                                        │
                    (human names approved items, by row # or finding ID)
                                        │
                                        ▼
                            /role-implement <items>  ──►  developer (writes code)
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                      ▼
            /sync-tracker ──► tracker                /sync-docs ──► docs-sync
            (Jira, via Atlassian MCP)          (in-repo docs + Confluence, via MCP)
```

**Trust boundary, enforced by tool grants, not instructions.** Withholding a tool is the
only real enforcement in this layer — everything in an agent body is advisory. `ciso`,
`planner`, and `tracker` hold no `Bash` at all; the reviewing roles hold no `Edit`/`Write`
and return a report for the invoking command to persist; only `developer` and `docs-sync`
can write to the target repo, each scoped to a different domain (code vs.
documentation-shaped content). `docs-sync`'s scope is a body rule, not a tool-grant
guarantee — Claude Code cannot glob-scope `Edit`/`Write` — the same weaker category as
`sre`'s fenced (git-metadata-only) `Bash`. See `docs/DESIGN.md` §10/§12 for the full
per-role reasoning and `adapters/claude-agent-permissions.json` for the `Bash` deny-rules
that close the "Bash but read-only" gap a `tools:` list cannot express by itself.

**External systems.** `tracker`/`docs-sync` are the only components in this repo that ever
reach outside a target repo, and they do it exclusively through MCP tool grants
(`mcp__atlassian__*`) — never credentialed `Bash` — so an untrusted target repo's content can
never reach a credential through them, preserving the same isolation principle as the git-only
Bash fence on every other role.

## 7. Non-functional properties

- **Stdlib-only.** `bin/ai-sync` and `skills/role_review/run_manifest.py` depend on nothing
  beyond the Python 3.11+ standard library (`tomllib`) — no install step for either.
- **Idempotent by design.** Both `ai-sync` re-runs and `run_manifest.py --begin` at an
  unchanged commit are safe to repeat.
- **Traceable.** Every review run is pinned to a `<short-sha>` in `.ai-reviews/manifest.json`;
  a stale backlog is a detectable, non-zero-exit condition (`run_manifest.py --status`), not
  a silent trap `/role-implement` can walk into.
- **Context-budget aware.** `AGENTS.md` loads every session, so its size is estimated and
  flagged (never hard-failed) past a configurable budget; reviewing roles work from a shared,
  explicit context budget defined in `skills/role_review/SKILL.md` rather than reading a
  target repo unbounded.
- **Tested.** `tests/` is a stdlib `unittest` suite covering `ai-sync`'s generator behavior,
  `run_manifest.py`'s ledger logic, and the structural conventions (frontmatter shape, tool
  grants, finding-ID prefixes) that are this repo's actual trust-boundary enforcement — see
  `docs/DESIGN.md` §7 and LLD §5.

## 8. What can change without touching `bin/ai-sync`

Adding a rule fragment, a skill, a command, or an agent to `agents/claude/` needs **no**
generator change — those directories are placed as whole trees. What *does* need a change:
a new language (needs a `LANG_GLOBS` entry for Cursor `.mdc` scoping — LLD §1), a new tool
target (needs a `wire_tools` branch), or a new cross-platform port (needs a new `emit_*`
function). See `README.md`'s "Extending" section for the walkthrough, and LLD §1 for exactly
where each of those lives in `bin/ai-sync`.
