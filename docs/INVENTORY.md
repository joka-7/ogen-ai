# Inventory

One-page index of everything this repo ships — every rule fragment, skill, command, and
agent, with a one-line purpose and how it reaches a consuming project. `README.md` explains
*how* the wiring works; this file is a flat list of *what exists*, for scanning.
`docs/HLD.md` and `docs/LLD.md` are the design-level views (system architecture and
per-file/function detail, respectively); `docs/DESIGN.md` carries the full rationale.

`docs/STRUCTURE.md` is the neighbouring list and the two do not overlap: **STRUCTURE says
which file, INVENTORY says what it does** and which tools it reaches. STRUCTURE is generated
from the real tree and CI-verified; this file carries the claims no filesystem walk can
derive — coverage, port confidence, the tool-grant matrix — which is why it is still written
by hand.

**This file is hand-maintained.** `tests/test_conventions.py` checks structural conventions
(frontmatter shape, tool grants, finding-ID prefixes) but does not check that this table is
current. When you add or remove a rule fragment, skill, command, or agent, update the
matching table here in the same commit.

## Rules (`rules/`)

Compiled into `AGENTS.md` per `[stack]` in a project's `ai-config.toml`. `base.md` is always
included; everything else is opt-in per project, so a Python repo doesn't carry Kotlin rules.

| Fragment | Included by | Covers |
|---|---|---|
| `base.md` | always | Working agreement, code quality, safety, output discipline |
| `languages/python.md` | `languages = ["python"]` | Modern typing, `mypy --strict`, dataclasses, one error hierarchy per package |
| `languages/typescript.md` | `... "typescript"` | `strict: true`, no `any`, `interface`/`type` split, discriminated unions |
| `languages/javascript.md` | `... "javascript"` | JS-specific conventions (no static typing to lean on) |
| `languages/kotlin.md` | `... "kotlin"` | Null safety (no `!!`), sealed classes, structured coroutines |
| `languages/go.md` | `... "go"` | Explicit error wrapping, small consumer-defined interfaces, goroutine-leak discipline |
| `languages/rust.md` | `... "rust"` | `Result` over panics, justified `unsafe`, borrowing over cloning |
| `languages/swift.md` | `... "swift"` | Value types by default, no force-unwrap, structured concurrency |
| `frameworks/react.md` | `frameworks = ["react"]` | React-specific conventions |
| `practices/testing.md` | `practices = ["testing"]` | Arrange-Act-Assert, deterministic, real objects over mocks |
| `practices/git-commits.md` | `... "git-commits"` | Conventional Commits, one logical change per commit |
| `practices/security.md` | `... "security"` | No hardcoded secrets, no logged PII, hostile-input validation |
| `practices/architecture.md` | `... "architecture"` | HLD/LLD checklists, contract-vs-implementation, centralized error handling, structured logging |
| `practices/documentation.md` | `... "documentation"` | The standard doc set (README tree, STRUCTURE/HLD/LLD), generated-not-written maps, mermaid diagrams |

## Skills (`skills/`)

Symlinked as a whole directory into `.claude/skills`, `.agents/skills` (Gemini),
`.cursor/skills`, `.github/skills`, and `.codex/skills`, per which tools are in
`[tools].targets` — see `docs/DESIGN.md` §11 for all but the first two, added after skills
gained adoption outside Claude/Gemini. Codex needs `CODEX_HOME=<project-root>/.codex` set in
its environment to actually read the wired files — the one thing `ai-sync` can't do itself.

| Skill | Purpose |
|---|---|
| `audit_repo` | Score a target repo 0–100 across six domains; writes `AUDIT_REPORT.md` |
| `conventional-commit` | Write a Conventional Commits message from the staged diff |
| `customize_config` | Scaffold `ai-project-config.toml` for project-local rule/weight overrides, outside `.ai/` |
| `port-module-to-ts` | Port a JS/Python module's behavior into TypeScript against the TS rules |
| `release-checklist` | Walk a repo from its last tag to a version-bumped, tagged commit; never pushes |
| `repo_tree` | Generate/refresh the annotated file tree in `docs/STRUCTURE.md` + `README.md`, and `--check` it for drift |
| `role_review` | Shared output schema, severity scale, and context-budget contract the role agents load |
| `scaffold-python-service` | Scaffold a new Python service — FastAPI + strict-mypy baseline, gate-verified |
| `write-design-doc` | Write HLD.md/LLD.md — either documenting an existing repo as-built, or proposing a new feature's design, against the HLD/LLD checklist |

## Commands (`commands/claude/`)

Canonically `$ARGUMENTS`-driven Claude commands, symlinked into `.claude/commands`. Four
opt-in ports adapt them into other tools' own conventions — none are symlinks, all rewrite
`$ARGUMENTS` into that tool's own mechanism where one exists:

| Port | Option | Destination | Argument mechanism |
|---|---|---|---|
| Cursor | `cursor_commands` | `.cursor/commands/*.md` | none confirmed — fallback phrase |
| Gemini | `gemini_commands` | `.gemini/commands/*.toml` | `{{args}}` (confirmed, primary docs) |
| Copilot | `copilot_commands` | `.github/prompts/*.prompt.md` | `${input:arguments}` (confirmed, real examples) |
| Windsurf | `windsurf_commands` | `.windsurf/workflows/*.md` | none confirmed — fallback phrase |

All off by default. See `docs/DESIGN.md` §11 for what's confirmed by a fetched primary doc
versus a real example versus a documented fallback for each.

| Command | Purpose |
|---|---|
| `/review` | Review the current staged diff against this repo's rules |
| `/test` | Write or extend tests for `$ARGUMENTS`, following the testing rules |
| `/role <name> [target]` | Run one role agent against a target repo |
| `/role-review [target]` | Fan out all seven reviewing roles in parallel → prioritized backlog |
| `/role-backlog [target]` | Re-aggregate reports already on disk, without re-reviewing |
| `/role-implement <items> [target]` | The only path to invoking `developer` — requires named, approved items |
| `/sync-tracker [target]` | Push backlog/implementation status to Jira via `tracker` |
| `/sync-docs [target]` | Sync in-repo docs and Confluence with the code via `docs-sync` |
| `/docs-bootstrap [target]` | Create the standard doc set (repo tree, README section, HLD, LLD) for a repo that lacks it |

## Agents (`agents/claude/`)

Native install is Claude-only, symlinked into `.claude/agents` only when `claude_agents =
true` (opt-in — see `docs/DESIGN.md` §10). Model tier and tool grant are the actual
enforcement, not a suggestion in the body text; `tests/test_conventions.py` checks this
table's claims.

Three opt-in ports adapt them into other tools' own agent conventions, each mapping this
table's `Bash`/`Edit`/`Write` grants into that tool's own tool-restriction mechanism:

| Port | Option | Destination | `ciso`/`planner`'s "cannot execute code" claim |
|---|---|---|---|
| Gemini | `gemini_agents` | `.gemini/agents/*.md` | **Kept in full** — Gemini's own docs confirm an explicit per-agent tool allowlist |
| Copilot | `copilot_agents` | `.github/agents/*.agent.md` | Kept, high confidence — real examples show the same withholding pattern, not confirmed against primary docs |
| Cursor | `cursor_agents` | `.cursor/agents/*.md` | **Weakened, with an explicit disclaimer** — confirmed Cursor's format cannot express it |

All off by default. See `docs/DESIGN.md` §11 for the full reasoning per platform. `tracker`
and `docs-sync` carry `mcp__atlassian__*` tools, and none of the three ports have a confirmed
mapping for Claude Code's `mcp__` naming — each port skips those two agents entirely, with a
warning naming why, rather than shipping a version that has silently lost its only way to
reach Jira or Confluence. See `docs/DESIGN.md` §12.

| Agent | Model | Bash | Edit/Write | Purpose |
|---|---|---|---|---|
| `qa` | sonnet | yes | no | Test suite quality: coverage, isolation, mock quality |
| `architect` | opus | yes | no | Structure: coupling, module boundaries, design-pattern fit |
| `product` | sonnet | yes | no | Docs-vs-behavior drift, API/CLI coherence, user-facing errors |
| `engineering-manager` | sonnet | yes | no | Delivery health: CI gates, commit hygiene, bus factor, dependency freshness |
| `sre` | sonnet | yes (fenced) | no | Operability: healthchecks, graceful shutdown, retries, observability, rollback |
| `senior-dev` | opus | yes | no | Line-level code quality: correctness, error handling, readability, abstraction fit |
| `ciso` | opus | **no** | no | Security exposure: secrets, authz gaps, injection, supply chain — never executes target code |
| `planner` | opus | no | no | Aggregates the reviewing roles' reports into one deduplicated backlog |
| `developer` | opus | yes | **yes** | Implements only backlog items a human has explicitly named and approved |
| `tracker` | sonnet | **no** | no | Syncs the backlog and implementation status to Jira, via the Atlassian MCP server |
| `docs-sync` | sonnet | yes | **yes** (docs only) | Syncs in-repo docs and Confluence pages with what the code actually says |

## Platform coverage

| | Rules (`AGENTS.md`) | Skills | Commands | Agents |
|---|---|---|---|---|
| Claude Code | ✅ `CLAUDE.md` | ✅ `.claude/skills` | ✅ `.claude/commands` | ✅ `.claude/agents` (opt-in) |
| Gemini | ✅ `GEMINI.md` | ✅ `.agents/skills` | ✅ `.gemini/commands`¹ (opt-in) | ✅ `.gemini/agents`¹ (opt-in) |
| Cursor | ✅ native | ✅ `.cursor/skills` | ✅ `.cursor/commands`¹ (opt-in) | ✅ `.cursor/agents`¹ ² (opt-in) |
| Copilot | ✅ `.github/copilot-instructions.md` | ✅ `.github/skills` | ✅ `.github/prompts`¹ (opt-in) | ✅ `.github/agents`¹ (opt-in) |
| Windsurf | ✅ native | not wired³ | ✅ `.windsurf/workflows`¹ (opt-in) | not built⁴ |
| Codex | ✅ native | ✅ `.codex/skills`⁵ (needs `CODEX_HOME` set) | not built⁵ | not confirmed⁵ |
| Other `AGENTS.md` readers | ✅ native | not confirmed | not confirmed | not confirmed |

The Skills column is unchanged content (a symlink or copy of `skills/`, unconditional on the
target being selected, same as this repo's other whole-directory wiring); Codex's needs the
`CODEX_HOME` step noted above to actually be read. Every ✅ in Commands/Agents is instead a
text or format transform this repo generates — not something the target tool reads
unmodified — gated behind its own `{platform}_commands`/`{platform}_agents` option, off by
default. Confidence differs per cell either way, spelled out below and in each `emit_*`
function's docstring in `bin/ai-sync`.

¹ **Confidence varies by how it was verified**, not by whether it works: Gemini's commands
and agents are confirmed against Gemini's own docs, fetched directly from
`google-gemini/gemini-cli` — the strongest standard in this table, including an explicit
statement that a subagent's tool list is a real, enforced allowlist. Cursor's are confirmed
against real example files fetched from public repos. Copilot's are confirmed against real
examples and a community reference doc, not Copilot's own primary docs — `learn.microsoft.com`
and `code.visualstudio.com` were network-blocked in this sandbox. Windsurf's command port is
confirmed against exactly one real example. See `docs/DESIGN.md` §11 for the full sourcing.

² **A trust-boundary gap, confirmed rather than suspected.** The role-agent layer's core
safety property (`ciso`/`planner` structurally cannot execute code — `docs/DESIGN.md` §10) is
enforced by per-agent tool grants. Reading two real `.cursor/agents/*.md` examples confirmed
Cursor's `readonly: true` is a coarse write-toggle, not a tool allowlist: a real security-review
agent has to state "no command execution" as prose in its body because `readonly` doesn't
cover shell execution — the same advisory-only pattern `ciso.md` was written to avoid. The
Cursor port therefore gives `ciso`/`planner` an explicit disclaimer instead of repeating a
claim the format can't back; Gemini's and Copilot's ports keep the claim in full, per ¹.

³ **Conflicting evidence, not resolved.** One source described `.windsurf/skills/` as
auto-discovered, working unmodified from Claude/Cursor; another — a real, checked-in guide
for porting skills to Windsurf — showed manual concatenation into `.windsurfrules` instead,
with no auto-discovery. No real example resolved which is current. Left unwired rather than
guessed at either way.

⁴ **No real example found, plus active rebrand ambiguity.** Windsurf's subagent support is
real (confirmed via search) but no `.windsurf/agents/*.md`-shaped example was found to build
a transform against, and Windsurf's mid-2026 rebrand to "Devin Desktop" introduced a second,
differently-shaped convention (`.devin/skills/` with `allowed-tools`/`triggers` fields) whose
precedence over the Windsurf-branded paths wasn't confirmed either.

⁵ **Codex skills needed a second look before the fix showed up.** Codex's own `docs/skills.md`
(fetched directly) and a real setup guide (`ComposioHQ/awesome-codex-skills`, fetched
directly) confirm skills load from `$CODEX_HOME/skills`, defaulting to `~/.codex/skills` —
the user's home directory, not the project. A first pass stopped there and called it
structurally out of scope. Asked to double-check: `CODEX_HOME` is a real, documented
environment variable, not a fixed path — confirmed via a GitHub issue on `openai/codex` and a
third-party reference naming a project-relative example (`CODEX_HOME=/workspace/.codex`).
`ai-sync` now wires `.codex/skills` exactly like every other platform's skills path; the
project still has to set `CODEX_HOME=<project-root>/.codex` itself (shell profile, `.envrc`,
or CI config) — that one step is genuinely outside what a project-root generator can do,
since it can't mutate the invoking shell's environment. No command port: Codex's commands
(custom prompts) are reportedly deprecated in favor of skills. No agent port: no custom-agent
convention was found at all, unlike skills. See `docs/DESIGN.md` §11 for both passes.
