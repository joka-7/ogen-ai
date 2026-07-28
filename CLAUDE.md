# CLAUDE.md — working on `ogen-ai`

Context for continuing this project in Claude Code. (This file is for working *on*
`ogen-ai` itself; `ai-sync` never generates it — it only writes into parent projects.)

## What this repo is

One source of truth for AI coding-assistant config (rules, skills, commands), consumed by
every project as a git submodule mounted at `.ai/`. Write rules once; Claude Code, Cursor,
Gemini, Copilot, Codex and any other AGENTS.md-aware tool read them. See `README.md`.

## Architecture & the decisions behind it

- **AGENTS.md is the standard; it's the only generated file.** Everything else (CLAUDE.md,
  GEMINI.md, copilot-instructions.md, skills, commands) is wired to it. Chosen because
  AGENTS.md is now the cross-tool standard read natively by most agents.
- **Claude Code needs `CLAUDE.md`, not AGENTS.md** — so `ai-sync` points CLAUDE.md at the
  generated AGENTS.md (symlink, or a real copy in copy mode).
- **Manifest-driven fragment assembly** (`ai-config.toml`): compile only the languages/
  frameworks a project uses. Deliberate — monolithic always-on rule files measurably
  degrade agent performance and inflate context. Keep fragments lean (commands, constraints,
  conventions; no architecture-overview prose).
- **Rules vs Skills split is intentional.** Rules = always-on standards in AGENTS.md.
  Skills = on-demand procedures (progressive disclosure). Don't move procedures into rules.
- **MCP was considered and rejected for serving rules.** On-demand loading is what Skills
  already do; MCP is for *live external* systems (DB schema, Jira, live docs) and adds a
  running process + attack surface. Only revisit MCP if we later want dynamic external
  context — never for static coding conventions.
- **`link_mode`: symlink (default) vs copy.** Copy mode writes real files that survive
  sandboxes/containers without the initialized submodule, and works on Windows.

## Layout

- `rules/{base,languages/*,frameworks/*,practices/*}.md` — the fragments.
- `skills/<name>/SKILL.md` — portable Agent Skills (frontmatter `name` + `description`).
- `commands/claude/*.md` — Claude slash commands (least portable; Claude-primary).
- `bin/ai-sync` — the generator/installer (Python 3.11+, stdlib only).
- `adapters/`, `ai-config.example.toml`, `README.md`.

## How to work on it / test

`ai-sync` runs from a *parent* project root. To test changes without a real submodule:

```bash
mkdir /tmp/sample && cd /tmp/sample
ln -s /path/to/ogen-ai .ai
cp .ai/ai-config.example.toml ai-config.toml   # edit stack/targets
python .ai/bin/ai-sync --dry-run               # inspect actions
python .ai/bin/ai-sync                          # then verify AGENTS.md + symlinks
```

Re-runs must stay idempotent; hand-written files at target paths must not be clobbered
without `--force`. Both are covered — keep them covered.

## Open next steps (from the design conversation)

1. **Fill `skills/scaffold-python-service/template/`** with a real FastAPI + strict-mypy
   baseline (`pyproject.toml`, typed `main.py`, `errors.py`) so the skill scaffolds our
   actual setup, not a stub.
2. **Token-budget check in `ai-sync`** — warn when assembled AGENTS.md crosses a threshold,
   to keep the always-on cost visible.
3. **More language fragments** as needed (Go, Rust, Swift) under `rules/languages/`; add a
   glob to `LANG_GLOBS` in `bin/ai-sync` for Cursor `.mdc` scoping.
4. **More skills** (e.g. release-checklist, "port module to TS").

## Editing conventions

- Fragments start with `## <Title>` and stay tight. One concern per fragment.
- The `.ai` mount path is referenced in `commands/claude/*` and `README.md`; if it changes,
  update those.
- `bin/ai-sync` is stdlib-only by design — don't add dependencies to it.
