# ogen-ai

One source of truth for AI coding-assistant rules, skills, commands, and agents, shared across
every repo as a git submodule. Write rules once; Claude Code, Cursor, Gemini, Copilot,
Codex and any other [AGENTS.md](https://agents.md)-aware tool read them.

See [`docs/INVENTORY.md`](docs/INVENTORY.md) for a flat list of everything this repo ships —
every rule fragment, skill, command, and agent — and which tools each one reaches.

## How it works

- **Rules** live as small fragments under `rules/` (by language, framework, and practice).
- A per-project manifest (`ai-config.toml`) picks which fragments apply, so a Python repo
  doesn't carry Kotlin rules into the context window.
- `bin/ai-sync` compiles the selected fragments — plus your project-specific tail — into a
  single root **`AGENTS.md`**, then wires up each tool:

| Tool | Wiring | Why |
|------|--------|-----|
| Cursor, Codex, Copilot, Gemini CLI, Windsurf, … | read root `AGENTS.md` natively | the cross-tool standard |
| **Claude Code** | `CLAUDE.md` → symlink to `AGENTS.md` | Claude Code reads `CLAUDE.md`, not `AGENTS.md` |
| Copilot | `.github/copilot-instructions.md` → `AGENTS.md` | dedicated path some setups pin to |
| Gemini | `GEMINI.md` → `AGENTS.md` | for surfaces that want the named file |

`AGENTS.md` is the **only** generated file. Everything else is a symlink to it or to this
submodule, so there's nothing to keep in sync by hand.

- **Skills** (`skills/`, `SKILL.md` folders — the portable [Agent Skills](https://agents.md)
  standard) are symlinked into `.claude/skills`, `.agents/skills` (Gemini),
  `.cursor/skills` (Cursor), `.github/skills` (Copilot), and `.codex/skills` (Codex) —
  whichever tools are in `[tools].targets`. Copilot also reads `.claude/skills`/`.agents/skills`
  directly, so a project targeting `claude` or `gemini` alongside `copilot` already gets
  skills there without the dedicated path.
  > The Cursor and Copilot paths were sourced from web search in August 2026, not a fetched
  > primary doc — this environment's network policy blocked direct access to `cursor.com`
  > and `docs.github.com` at the time. Spot-check against a real Cursor/Copilot install
  > before depending on this wiring in a new project.
  >
  > **Codex needs one extra step.** Codex only reads skills from `$CODEX_HOME/skills`,
  > which defaults to `~/.codex/skills` — your home directory, not the project. Set
  > `CODEX_HOME=<project-root>/.codex` (shell profile, `.envrc`, or your CI's env config)
  > for Codex to actually pick up what's wired to `.codex/skills`; `ai-sync` can't set an
  > environment variable for you. No command or agent port exists for Codex — its commands
  > (custom prompts) are reportedly deprecated in favor of skills, and no custom-agent
  > convention was found. See `docs/DESIGN.md` §11.
- **Commands** (`commands/claude/`) are symlinked into `.claude/commands` — canonical, always
  on for `claude`. Four opt-in ports adapt them into other tools' own conventions:
  `cursor_commands`, `gemini_commands`, `copilot_commands`, `windsurf_commands`. Each is a
  text transform, not a symlink, and each rewrites `$ARGUMENTS` into that tool's own mechanism
  where a real one was confirmed (Gemini's `{{args}}`, Copilot's `${input:...}`) or a fallback
  phrase where none was found (Cursor, Windsurf). See `docs/INVENTORY.md`'s Commands table for
  what's confirmed how, per port.
- **Agents** (`agents/claude/`) are symlinked into `.claude/agents` — **only when
  `claude_agents = true`**, off by default. See [Role agents](#role-agents). Three opt-in
  ports adapt them for other tools: `gemini_agents`, `copilot_agents`, `cursor_agents`. All
  map this repo's `tools:` grant into that platform's own mechanism, but the guarantee differs:
  Gemini's and Copilot's ports keep `ciso`/`planner`'s "cannot execute code" claim in full
  (confirmed real tool allowlists); Cursor's port carries an explicit disclaimer instead,
  because Cursor's `readonly` field was confirmed unable to express that guarantee. See
  `docs/DESIGN.md` §11 for the investigation behind each.

## Role agents

Eleven subagents. Seven review a target repo from different professional lenses and converge
on one backlog; `developer` and `docs-sync` act on it once approved; `tracker` and `docs-sync`
also sync that state to Jira and Confluence. Off by default; set `claude_agents = true` in
`[options]` to install them.

```bash
/role-review <path-or-git-url>    # full pass: 7 roles in parallel → prioritized backlog
/role ciso <path-or-git-url>      # one lens on demand
/role-backlog <path-or-git-url>   # re-aggregate reports already on disk, no re-review
/role-implement 1,3 <path-or-git-url>  # implement approved backlog items — the only way in
/sync-tracker <path-or-git-url>   # push backlog/implementation status to Jira
/sync-docs <path-or-git-url>      # sync in-repo docs and Confluence with the code
```

`/role-review` clones (or uses) the target, runs the `audit-repo` scan **once**, fans out
`qa`, `architect`, `product`, `engineering-manager`, `sre`, `senior-dev`, and `ciso` in
parallel — each in its own context, each reading only its slice of the scan — then runs
`planner` to deduplicate
the reports into `BACKLOG.md`. Reports land in `<target>/.ai-reviews/`, which the command adds
to `.git/info/exclude` so they never dirty the target's git status. A `manifest.json` in the
same directory tracks which commit each run describes, archiving prior reports under
`archive/<sha>/` when the target moves on rather than silently overwriting them.

It stops there. Among the reviewing roles, none can edit anything; `developer` implements code
and `docs-sync` syncs documentation, and both leave a diff for review rather than committing.
`/role-implement` is the only command that can invoke `developer` — it refuses to run with no
items named, checks the backlog isn't stale against the current commit, and requires a clean
worktree before it will launch anything.

`tracker` and `docs-sync` reach outside the target repo entirely, via Atlassian's official
Rovo MCP server (`mcp__atlassian__*`) — `tracker` opens and transitions Jira issues from the
backlog and `developer`'s reports, `docs-sync` updates Confluence pages alongside its in-repo
edits. Neither runs automatically: `/sync-tracker` and `/sync-docs` are checkpoints you invoke,
typically after `/role-implement`, not a passive background process — subagents only run when
a session invokes them. Both require the target project to have that MCP server connected
first; `tracker`/`docs-sync` say so and stop rather than fabricate a sync if it isn't. The
`mcp__atlassian__*` tool names are real, confirmed against that server's own repo, but the
connection alias (`atlassian`) is project-specific MCP configuration this repo doesn't control
— if your project uses a different alias or a different Jira/Confluence MCP server, edit
`tracker.md`/`docs-sync.md`'s `tools:` list to match before they'll do anything.

The trust boundary is enforced by tool grants, not by instructions: `ciso`, `planner`, and
`tracker` have no local `Bash` at all — `ciso` structurally cannot execute code from an
untrusted repo — and the reviewing roles have no `Edit`/`Write`, returning reports for the
command to persist. `docs-sync`'s edit scope (documentation-shaped files only) is the one
exception stated plainly rather than structurally enforced — Claude Code can't glob-scope
`Edit`/`Write`, so that boundary is a body rule, the same category as `sre`'s fenced `Bash`.

One gap remains: a subagent's `tools:` list can grant or withhold `Bash`, but can't express
"Bash, but only read commands", and six reviewers plus `docs-sync` need it to run a test suite,
read git metadata, or read deployment manifests. `adapters/claude-agent-permissions.json`
closes that with `permissions.deny` rules — merge it into your project's `.claude/settings.json`
by hand (`ai-sync` never writes that file; it's yours). Note those rules apply **project-wide,
not per-agent**, so they'll also block you from running those commands in a normal session —
drop any line that conflicts with how you work.

## Set up in a new project

```bash
# 1. add this repo as a submodule at .ai
git submodule add <this-repo-url> .ai

# 2. create the manifest
cp .ai/ai-config.example.toml ai-config.toml
$EDITOR ai-config.toml          # pick your languages / frameworks / tools

# 3. (optional) project-specific rules — build/test commands, "do not touch" dirs
$EDITOR ai-config.local.md

# 4. generate + wire everything
python .ai/bin/ai-sync
```

Commit `AGENTS.md`, the symlinks, and (if enabled) `.cursor/rules/*.mdc`. Re-run
`python .ai/bin/ai-sync` whenever you change the manifest or pull new rules.

Handy Makefile target for the parent repo:

```makefile
ai-sync: ; python .ai/bin/ai-sync
```

Pulling rule updates later:

```bash
git submodule update --remote .ai && python .ai/bin/ai-sync
```

## Link mode vs copy mode

`AGENTS.md` is always a real generated file. For everything else, `[options].link_mode`
controls how it's placed:

- `"symlink"` (default) — `CLAUDE.md`/`GEMINI.md`/copilot link to `AGENTS.md`; skills and
  commands link into the submodule. Zero drift, nothing duplicated. But links dangle if an
  agent runs in a **sandbox or container that has the working tree without the initialized
  submodule**, and symlinks break on Windows.
- `"copy"` — real files and directories are written into the project. Portable and
  container-safe (the config survives even if `.ai/` isn't checked out), Windows-friendly.
  Cost: re-run `ai-sync` after pulling rule updates, and copied dirs carry a `.ai-managed`
  marker so re-runs refresh them safely. Hand-written files at a target path are never
  clobbered without `--force`.

On Linux with the submodule always initialized, `symlink` is simplest. Use `copy` for
containerized/CI/cross-platform agent runs.

## `ai-sync` flags

- `--dry-run` — show every action, change nothing.
- `--force` — replace a real (non-symlink) file sitting at a target path.
- `--project PATH` — operate on a project root other than the current directory.

## Token budget

`AGENTS.md` loads every session, so `ai-sync` estimates its size (~chars/4, a rough
heuristic) and warns — never fails — when it crosses `[options].token_budget` (default
`6000`; `0` disables). If you hit it, trim `[stack]` to what the project actually uses, or
move an occasional procedure out of `rules/` and into a skill, which only loads on demand.

## Extending

- **New language rule:** add `rules/languages/<name>.md` (start with `## <Name>`), then list
  `<name>` under `[stack].languages`. For glob-scoped Cursor `.mdc`, add a glob in
  `LANG_GLOBS` in `bin/ai-sync`.
- **New framework/practice:** same, under `rules/frameworks/` or `rules/practices/`.
- **New skill:** add `skills/<name>/SKILL.md` (required frontmatter: `name`, `description`;
  make the description "pushy" so it triggers). Bundle scripts/templates in the folder.
- **New command:** add `commands/claude/<name>.md`. Use `$ARGUMENTS` for the invocation tail.
- **New agent:** add `agents/claude/<name>.md` (frontmatter: `name`, `description`, `tools`,
  `model`; filename must match `name`). Say in the description both when to use it *and when
  not to* — that's what auto-delegation keys off. Grant the narrowest tool set that lets it do
  its job: withholding a tool is the only real enforcement, since the body's instructions are
  advisory. Reviewing roles should load the `role-review` skill for the shared output schema
  rather than restating it. A new reviewing role must also be added to
  `skills/role_review/SKILL.md`'s finding-ID list and to the fan-out in
  `commands/claude/role-review.md` and `commands/claude/role.md` —
  `tests/test_conventions.py` fails until those enumerations agree.

## Tests

```bash
python -m unittest discover -s tests -v
```

Covers `ai-sync`'s generator behavior (assembly, symlink/copy modes, the `claude_agents` gate,
idempotent re-runs), the role-review run manifest, and the agent/skill/command conventions
above — including the tool-grant matrix that is the actual enforcement of the trust boundary.
Run this before and after any change under `bin/`, `agents/`, `commands/`, or `skills/`.

## Keep it lean

`AGENTS.md` loads every session — cost you pay on every turn. Keep fragments to commands,
constraints, and conventions; push heavy or occasional procedures into skills, which only
load their description until invoked. Skip architecture-overview prose in `AGENTS.md` — it
tends not to help agents and inflates the context.
