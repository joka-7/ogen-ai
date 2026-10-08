# Changelog

Consumers pin this repo as a submodule; read this before bumping. Releases are tagged
`vMAJOR.MINOR.PATCH` — a major bump means a manifest or generated-output change that
needs action in the consuming project.

## Unreleased

### Security
- `ai-sync` validates `ai-config.toml` before writing (list types, safe fragment names,
  contained `local_tail`, known `link_mode`) and refuses writes that resolve outside the
  project.
- `run_manifest.py` rejects non-hex archive ids and writes the manifest atomically.
- `sre` and `engineering-manager` no longer hold Bash; `run_manifest.py --git-meta` writes
  the git facts they read. `docs-sync` confirms before any Confluence update.
- `qa` and `product` only execute target code when the target is an owned local path.

### Changed
- `ai-sync` no longer overwrites hand-written `AGENTS.md` or generated command/agent
  ports without `--force`; ownership is recorded in `.ai-sync-state.json`. The first run
  after upgrading skips unrecorded ports with a warning — pass `--force` once to adopt them.
- An existing real `.claude/skills` (etc.) directory now gets shared entries added beside
  its own instead of being skipped or deleted.
- Skill directories renamed to kebab-case: `audit-repo`, `customize-config`, `repo-tree`,
  `role-review`.
- `role-review` findings carry a stable **Fingerprint**; the tracker's ticket marker uses it.

### Added
- Roles `privacy` (PRV), `performance` (PRF), `frontend` (FE): reviewers with no Bash, opt-in
  to `/role-review` by naming them; the default fan-out is unchanged.
- Skills `debug-root-cause`, `dependency-upgrade`, `threat-model`, `pr-description`,
  `db-migration-safety`. `port-module-to-ts` is now the language-generic `port-module`.
- `ai-sync --check` (exit 1 when output is stale) and `ai-sync --clean`.
- `[options] atlassian_server` to match the project's Atlassian MCP alias.
- CI: `mypy --strict`, scaffold-template gates, Python 3.13.
