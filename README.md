# ogen-ai

One source of truth for AI coding-assistant rules, skills, commands, and agents, shared across
every repo as a git submodule. Write rules once; Claude Code, Cursor, Gemini, Copilot,
Codex and any other [AGENTS.md](https://agents.md)-aware tool read them.

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
  standard) are symlinked into `.claude/skills` and `.agents/skills`.
- **Commands** (`commands/claude/`) are symlinked into `.claude/commands`. Slash commands
  port poorly across tools, so these are Claude-Code-primary.
- **Agents** (`agents/claude/`) are symlinked into `.claude/agents` — **only when
  `claude_agents = true`**. Claude-only, and off by default. See [Role agents](#role-agents).

## Role agents

Seven subagents that review a target repo from different professional lenses and converge on
one backlog. Off by default; set `claude_agents = true` in `[options]` to install them.

```bash
/role-review <path-or-git-url>    # full pass: 5 roles in parallel → prioritized backlog
/role ciso <path-or-git-url>      # one lens on demand
```

`/role-review` clones (or uses) the target, runs the `audit-repo` scan **once**, fans out
`qa`, `architect`, `product`, `engineering-manager`, and `ciso` in parallel — each in its own
context, each reading only its slice of the scan — then runs `planner` to deduplicate the five
reports into `BACKLOG.md`. Reports land in `<target>/.ai-reviews/`, which the command adds to
`.git/info/exclude` so they never dirty the target's git status.

It stops there. `developer` is the only role that can edit anything, and it runs only after
you approve specific backlog items by name.

The trust boundary is enforced by tool grants, not by instructions: `ciso` and `planner` have
no `Bash` at all — `ciso` structurally cannot execute code from an untrusted repo — and the
reviewing roles have no `Edit`/`Write`, returning reports for the command to persist.

One gap remains: a subagent's `tools:` list can grant or withhold `Bash`, but can't express
"Bash, but only read commands", and four reviewers need it to run a test suite or read git
metadata. `adapters/claude-agent-permissions.json` closes that with `permissions.deny` rules —
merge it into your project's `.claude/settings.json` by hand (`ai-sync` never writes that file;
it's yours). Note those rules apply **project-wide, not per-agent**, so they'll also block you
from running those commands in a normal session — drop any line that conflicts with how you work.

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
  rather than restating it.

## Keep it lean

`AGENTS.md` loads every session — cost you pay on every turn. Keep fragments to commands,
constraints, and conventions; push heavy or occasional procedures into skills, which only
load their description until invoked. Skip architecture-overview prose in `AGENTS.md` — it
tends not to help agents and inflates the context.
