---
name: engineering-guides
description: Look up the full engineering guides for coding, architecture, testing, and documentation — language-agnostic principles plus Python, TypeScript, and C++ specifics, each as a short cheat sheet and a detailed reference with code. Use when the user asks how to structure a service, design HLD/LLD, apply DI/adapters/facades, write or review tests (pytest, Vitest/Jest, GoogleTest), choose an async or concurrency model, set up logging, CI/CD, or docs, or wants the reasoning behind a rule in AGENTS.md.
---

# Engineering Guides

The always-on rules in `AGENTS.md` are the short constraints. This skill holds the long form:
explanations, trade-offs, and worked code. Load only the files the task needs.

## How the guides are organized

Two layers, each in a **short** cheat sheet and a **detailed** version:

- `reference/general/` — language-agnostic principles: what good code, architecture, tests,
  and docs mean.
- `reference/{python,typescript,cpp}/` — the same principles made concrete: idioms, tooling,
  frameworks, worked examples.

All paths below are relative to `.ai/skills/engineering-guides/`.

## Which file to read

| Task | Start with (short) | Go deeper (detailed) |
|---|---|---|
| Naming, idioms, async, formatting | `reference/<lang>/coding-guide-short.md` | `reference/<lang>/coding-guide-detailed.md` |
| System design, HLD/LLD, patterns, ops | `reference/<lang>/architecture-guide-short.md` | `reference/<lang>/architecture-guide-detailed.md` |
| Writing or reviewing tests, mocking | `reference/<lang>/testing-guide-short.md` | `reference/<lang>/testing-guide-detailed.md` |
| Language-agnostic "why" | `reference/general/{coding,architecture,testing}-principles-short.md` | `...-detailed.md` |
| What a repo must document and how | `reference/general/documentation-principles-short.md` | `reference/general/documentation-principles-detailed.md` |

`<lang>` is `python`, `typescript`, or `cpp`. There is no per-language documentation guide
on purpose: docstring and JSDoc style are coding concerns and live in the coding guides.

## Steps

1. Identify the topic (coding, architecture, testing, documentation) and the language.
2. Read the **short** file first. Stop there if it answers the question.
3. Open the **detailed** file only for the section you need — use its headings; the files are
   500–660 lines.
4. When the guide and the project's existing conventions disagree, follow the project and say
   so; the guides are defaults, not mandates.
5. Cite the guide section you relied on in your answer or review comment.

## Rules

- Do not paste whole guides into the conversation or into `AGENTS.md`; quote the relevant
  lines. Bloating always-on context is what this split exists to avoid.
- If a language has no guide here (Go, Rust, Kotlin, Swift, JavaScript), use the general
  principles plus that language's rule fragment, and say the language guide does not exist.
