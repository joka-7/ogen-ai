# Repository structure

Every file in this repo and what is inside it — the map to open first if you've just
arrived and want to know which file answers your question.

The other docs each answer a different question, and none of them answers this one:
[`INVENTORY.md`](INVENTORY.md) lists what each rule/skill/command/agent *does* and which
tools it reaches; [`HLD.md`](HLD.md) is the system-level shape; [`LLD.md`](LLD.md) is
per-file/function behavior; [`DESIGN.md`](DESIGN.md) carries the reasoning behind all of it.

> **The tree below is generated. Do not edit between the markers.**
>
> ```bash
> python skills/repo_tree/gen_tree.py --project . --output docs/STRUCTURE.md
> ```
>
> Each line's note comes from the file itself — YAML frontmatter `description`, the first
> markdown heading, or a Python module docstring. Files that can't describe themselves get
> their line from [`.structure-notes.toml`](.structure-notes.toml), which always wins.
> `tests/test_structure_doc.py` fails if this file drifts from the real tree, so it can't
> quietly rot the way the hand-written layout lists it replaced did.

<!-- BEGIN GENERATED TREE (depth=all entries=all) -->
```text
ogen-ai/
├── .github/                           # CI configuration
│   └── workflows/
│       └── checks.yml                 # The only CI gate: Python 3.11 + the full unittest suite
├── adapters/                          # Templates and notes for tool-specific wiring that ai-sync emits or you merge
│   ├── README.md                      # What each adapter is for and which are hand-merged vs generated
│   ├── claude-agent-permissions.json  # Permissions.deny rules to merge into a project's .claude/settings.json by hand
│   └── cursor-rule.mdc.tmpl           # Template for the glob-scoped .cursor/rules/*.mdc that emit_cursor_mdc renders
├── agents/                            # Role subagents — Claude-only, opt-in via [options] claude_agents
│   └── claude/                        # Eleven role agents; the tools: grant is the enforcement, not the body text
│       ├── architect.md               # Reviews a target repo's structure and reports coupling, module boundaries,…
│       ├── ciso.md                    # Reviews a target repo for security exposure and reports hardcoded secrets,…
│       ├── developer.md               # Implements specific, already-approved backlog items in a target repo — the…
│       ├── docs-sync.md               # Keeps a target repo's documentation — in-code docs (README, docs/*.md,…
│       ├── engineering-manager.md     # Reviews a target repo's delivery health and reports CI gates, commit and PR…
│       ├── planner.md                 # Aggregates the completed role reports in .ai-reviews/ into one prioritized…
│       ├── product.md                 # Reviews a target repo from the user's side and reports docs-vs-behavior…
│       ├── qa.md                      # Reviews a target repo's test suite and reports test coverage, isolation, mock…
│       ├── senior-dev.md              # Reviews a target repo's line-level code quality and reports correctness…
│       ├── sre.md                     # Reviews a target repo's operability and reports healthchecks, graceful…
│       └── tracker.md                 # Keeps a target repo's Jira project in sync with its review backlog and…
├── bin/                               # The generator
│   └── ai-sync                        # Compiles AGENTS.md from the manifest and wires every tool target (stdlib only)
├── commands/                          # Slash commands
│   └── claude/                        # Canonical $ARGUMENTS-driven Claude commands; four opt-in ports adapt them
│       ├── docs-bootstrap.md          # Create a target repo's standard doc set from scratch
│       ├── review.md                  # Review the current diff against this repo's coding rules
│       ├── role-backlog.md            # Re-aggregate the role reports already on disk into a fresh prioritized…
│       ├── role-implement.md          # Implement specific, already-approved items from .ai-reviews/BACKLOG.md by…
│       ├── role-review.md             # Run a full multi-role review over a target repo (local path or git URL) and…
│       ├── role.md                    # Run a single role agent (qa, architect, product, engineering-manager, sre,…
│       ├── sync-docs.md               # Sync a target repo's in-code documentation and Confluence space with the…
│       ├── sync-tracker.md            # Sync a target repo's review backlog and implementation status to Jira via the…
│       └── test.md                    # Write or extend tests for the code in $ARGUMENTS following the testing rules
├── docs/                              # Design and reference docs
│   ├── .structure-notes.toml          # This file — hand-written notes for the generated tree
│   ├── DESIGN.md                      # Full rationale: every decision, the alternatives rejected, the sourcing
│   ├── HLD.md                         # System-level view: components, data flow, the role-agent trust boundary
│   ├── INVENTORY.md                   # Flat index of what exists and what each unit does
│   ├── LLD.md                         # Per-file/function detail: tool-grant matrix, ai-sync internals, file contracts
│   └── STRUCTURE.md                   # This map — which file is which (generated)
├── rules/                             # Rule fragments compiled into a project's AGENTS.md, per its manifest
│   ├── frameworks/                    # Opt-in per [stack].frameworks
│   │   └── react.md                   # React
│   ├── languages/                     # Opt-in per [stack].languages — one fragment per language
│   │   ├── go.md                      # Go
│   │   ├── javascript.md              # JavaScript
│   │   ├── kotlin.md                  # Kotlin
│   │   ├── python.md                  # Python
│   │   ├── rust.md                    # Rust
│   │   ├── swift.md                   # Swift
│   │   └── typescript.md              # TypeScript
│   ├── practices/                     # Opt-in per [stack].practices — cross-language engineering practice
│   │   ├── architecture.md            # Architecture (HLD/LLD)
│   │   ├── documentation.md           # Documentation
│   │   ├── git-commits.md             # Commits & PRs
│   │   ├── security.md                # Security
│   │   └── testing.md                 # Testing
│   └── base.md                        # Always included — working agreement, code quality, safety, output discipline
├── skills/                            # Portable Agent Skills (SKILL.md folders), wired whole into every target tool
│   ├── audit_repo/
│   │   ├── SKILL.md                   # Scan a target project and produce a scored (0-100) health report,…
│   │   └── run_audit.py               # Collect objective repository-health signals for the audit_repo skill.
│   ├── conventional-commit/
│   │   └── SKILL.md                   # Write a Conventional Commits-formatted git commit message from staged changes
│   ├── customize_config/
│   │   ├── SKILL.md                   # Scaffold and apply ai-project-config.toml — a project-local override file for…
│   │   └── init_config.py             # Scaffold `ai-project-config.toml` for the customize_config skill.
│   ├── port-module-to-ts/
│   │   └── SKILL.md                   # Port a JavaScript or Python module to TypeScript — translate its public API,…
│   ├── release-checklist/
│   │   └── SKILL.md                   # Walk through cutting a release — determine the version bump from commits…
│   ├── repo_tree/
│   │   ├── SKILL.md                   # Generate or refresh a repository's annotated file tree — the map of which…
│   │   └── gen_tree.py                # Render an annotated file tree of a repository into a docs file.
│   ├── role_review/
│   │   ├── SKILL.md                   # The shared output contract for the role agents (qa, architect, product,…
│   │   └── run_manifest.py            # Track role-review runs in a target repo's .ai-reviews/ directory.
│   ├── scaffold-python-service/
│   │   ├── template/                  # Files copied into a new service — FastAPI + strict-mypy baseline
│   │   │   ├── src/
│   │   │   │   └── example_service/
│   │   │   │       ├── __init__.py    # TODO: one-line package summary.
│   │   │   │       ├── errors.py      # Custom exception hierarchy, rooted at one base class per the Python rules.
│   │   │   │       └── main.py        # Typed FastAPI entrypoint.
│   │   │   ├── tests/
│   │   │   │   └── test_smoke.py      # One real smoke test exercising the entrypoint end to end, per the skill's…
│   │   │   ├── README.md              # README stub the scaffolded service starts from
│   │   │   └── pyproject.toml         # Baseline deps and the strict mypy/ruff config the scaffold ships with
│   │   └── SKILL.md                   # Scaffold a new Python backend service or package with the standard project…
│   └── write-design-doc/
│       └── SKILL.md                   # Produce an HLD/LLD design document — either documenting an existing repo's…
├── tests/                             # Stdlib unittest suite — run before and after touching bin/, agents/,…
│   ├── test_ai_sync.py                # Behavioral tests for bin/ai-sync.
│   ├── test_conventions.py            # Conformance tests for this repo's own agents, skills, and commands.
│   ├── test_run_manifest.py           # Behavioral tests for skills/role_review/run_manifest.py.
│   └── test_structure_doc.py          # Behavioral tests for skills/repo_tree/gen_tree.py, and a drift gate on…
├── .gitignore                         # Ignores __pycache__/, *.pyc, .DS_Store — nothing generated lives in this repo
├── CLAUDE.md                          # Working context for Claude Code sessions on ogen-ai itself (never generated)
├── LICENSE                            # MIT
├── README.md                          # Start here: what this repo is, how the wiring works, how to set it up
└── ai-config.example.toml             # Copy to a project as ai-config.toml — the per-project manifest
```
<!-- END GENERATED TREE -->

## Where to start

| If you want to… | Read |
|---|---|
| Understand what this repo is and set it up | [`README.md`](../README.md) |
| Know what rules/skills/commands/agents exist | [`INVENTORY.md`](INVENTORY.md) |
| Change a rule that reaches every project | `rules/` — one concern per fragment |
| Change how files get generated or wired | `bin/ai-sync`, then [`LLD.md`](LLD.md) §1 |
| Add or change a role agent | `agents/claude/`, then [`HLD.md`](HLD.md) §6 for the trust boundary |
| Understand why something is the way it is | [`DESIGN.md`](DESIGN.md) |
