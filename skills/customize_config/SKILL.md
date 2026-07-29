---
name: customize-config
description: Scaffold and apply ai-project-config.toml — a project-local override file for custom coding rules and per-domain audit scoring weights (e.g. make Security high priority, keep Clean Code normal) — without ever hand-editing files inside the ogen-ai submodule (.ai/). Use whenever the user wants to add a project-specific coding rule, change how strict the audit_repo skill is about one domain, prioritize one audit domain over another, or asks to "customize"/"override" rules or scoring for just this project.
---

# Customize Config

Scaffold `ai-project-config.toml` in the **parent project's root** (never inside `.ai/`)
so a project can add its own coding rules and re-weight the `audit_repo` skill's domain
scores, without modifying the shared submodule.

## Why a separate file from `ai-config.toml` / `ai-config.local.md`

This repo already has two project-local mechanisms — don't confuse them with this one:

- `ai-config.toml` — `ai-sync`'s manifest. Picks which rule *fragments* compile into
  `AGENTS.md`, and which tools get wired up. Unrelated to auditing.
- `ai-config.local.md` — a prose tail appended verbatim to `AGENTS.md`. Always-on context
  for every AI tool reading `AGENTS.md` (build/test commands, "don't touch this dir").
- **`ai-project-config.toml` (this skill)** — read only by the `audit_repo` skill, at audit
  time. Structured, not prose: a list of custom rule strings the auditing agent should apply,
  and a numeric weight per audit domain. It has no effect on `AGENTS.md` or `ai-sync` at all.

## The core boundary

**Never edit anything under `.ai/` to satisfy a customization request.** Files there are
shared and get overwritten by `git submodule update --remote`; anything written there is lost
silently. Every customization in this skill's scope goes into `ai-project-config.toml` at the
parent project's root instead.

## Steps

1. Check whether `ai-project-config.toml` already exists at the project root.
   - If not: `python .ai/skills/customize_config/init_config.py --project <path>` (default
     `.`) to scaffold it with the default template (every domain at weight `1.0`, an empty,
     commented `conventions` list). It refuses to overwrite an existing file — pass `--force`
     only if the user explicitly asks to reset it.
   - If it exists: open it directly; don't re-run the scaffolder.
2. Edit the file to what the user asked for:
   - A new project rule → add a one-sentence string to `[rules.custom].conventions`.
   - "Make X high priority" / "I don't care as much about Y" → change that domain's value
     under `[audit.weights]`. Suggested bands: `0.5` low, `1.0` normal, `1.5` high, `2.0`
     critical, `0.0` excludes the domain from the overall score entirely.
3. Validate what you wrote: `python .ai/skills/customize_config/init_config.py --check <path>`.
   It parses the file and prints the resolved rules/weights plus any warnings (unknown domain
   name — likely a typo against the six audit domains; negative weight — clamped to `0.0`).
   Fix anything it flags before telling the user you're done.
4. **Custom rules are agent-applied, not script-enforced.** When the `audit_repo` skill next
   runs, its own instructions have it read this file's `conventions` and factor them into its
   manual review of Architecture & Design / Clean Code — there is no regex enforcing them.
   Don't imply to the user that a custom rule is being mechanically checked; it's a checklist
   item for the auditing agent's read-through.
5. **Weights are not yet consumed by `run_audit.py`.** As of this skill's introduction, the
   script always uses an unweighted mean across the six domains. Applying `[audit.weights]`
   requires a small, separate change to `run_audit.py` (see below) — don't tell the user their
   weights are already affecting scores until that change has actually landed.

## `run_audit.py` integration (not yet implemented — describes the follow-up change)

To make `[audit.weights]` actually affect scoring, `skills/audit_repo/run_audit.py` needs:

1. A small config loader of its own — `tomllib`-parse `ai-project-config.toml` if present at
   the audited project's root, defaulting every domain to weight `1.0` if the file is absent
   or a domain isn't listed. Kept self-contained inside `run_audit.py` (not imported from
   `customize_config/init_config.py`) so the two skills stay independently copyable — this
   repo's `ai-sync` can place `skills/` in `symlink` or `copy` mode, and a skill script should
   never assume a sibling skill's exact path.
2. `AuditOrchestrator.run()` gains a `domain_weights: dict[str, float]` parameter. The overall
   score changes from a plain mean to a weighted mean, renormalized so it stays 0-100:
   `overall = sum(score * weight for domain) / sum(weight for domain)` (guarding
   `sum(weights) == 0`, which would otherwise divide by zero if every domain were zeroed out).
3. `AuditReport` gains a `custom_rules: list[str]` field, populated from
   `ai-project-config.toml` and passed through untouched into the JSON output — `run_audit.py`
   doesn't interpret them, it only carries them to where step 4 above reads them.
4. `main()` gains nothing new by default: it auto-detects `ai-project-config.toml` at
   `--project`'s root (no new required flag), matching how it already auto-detects the
   project's own `ai-config.toml` conceptually in the wider `ai-sync` flow.

## Rules

- Don't write or suggest writing anything under `.ai/` to satisfy a customization request —
  that's the one thing this skill exists to prevent.
- Don't claim a weight is affecting the audit's overall score until the `run_audit.py` change
  above has actually been made in this repo.
- Keep `[rules.custom]` entries short and mechanically checkable-by-a-reader — a vague rule
  ("write good code") gives the auditing agent nothing to judge against.
