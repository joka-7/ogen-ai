---
name: audit-repo
description: Scan a target project and produce a scored (0-100) health report, AUDIT_REPORT.md, across Architecture & Design, Clean Code, Documentation, Security, Scalability, and Testing. Use whenever the user asks to audit, review the health of, score, or grade a repository/codebase — or asks something narrower that's really one of these domains, like "check for hardcoded secrets", "how's our test coverage", "is this over-engineered", or "grade our documentation".
---

# Audit Repository

Produce `AUDIT_REPORT.md`: a scored health report for the target project across six domains
— Architecture & Design, Clean Code, Documentation, Security, Scalability, Testing.

This is a two-stage audit, not a single script run. `run_audit.py` collects objective,
re-derivable signals (type-annotation ratios, docstring presence, secret regexes, loop
nesting, test-to-source ratio, …). It cannot judge things that need a reader's eye — whether
a docstring truly explains the algorithm versus restating the signature, or whether a design
is genuinely decoupled. That second pass is yours.

## Steps

1. Run the collector: `python .ai/skills/audit_repo/run_audit.py --project <path> --output audit_data.json`
   (defaults: `--project .`, `--output audit_data.json`; see `--help` for `--max-line-length`
   and `--max-file-bytes`). It scans the tree, detects the tech stack, and writes both a JSON
   file and a short score summary to stdout.
2. Load `audit_data.json`. Each domain has a `score`, a `confidence` (`high`/`medium`/`low`),
   `findings` (each with a `file`/`line` when available), and raw `metrics`. Treat the score
   as a first-pass mechanical signal, not the final word — `confidence` tells you how much to
   trust it as-is:
   - **high** (Clean Code, Security): mostly countable facts (annotation coverage, regex
     hits). Spot-check a couple of findings, don't re-derive the whole domain.
   - **medium** (Scalability, Testing): the metric is real but the interpretation needs
     context (a flagged O(n²) loop over 10 items isn't a problem; over 10M rows it is).
   - **low** (Architecture & Design, Documentation): the script can only proxy the actual
     question. Read the code yourself before trusting the number.
3. For every `low`/`medium`-confidence domain, and for any specific finding you're unsure
   about, open the real file at the given line and check it against the domain's actual
   definition (below) — not against the heuristic that flagged it.
4. For Documentation specifically: open each function/class the script flagged as
   "I/O-only" and confirm whether the docstring narrates the *approach* — why this algorithm,
   what the flow does, edge cases, complexity — versus a bare parameter/return list. The
   script's keyword-and-length heuristic is a coarse proxy; your read is the real score.
5. Recompute each domain's final score (0-100) and an overall score (mean of the six) —
   adjusting the script's number up or down based on what you actually found. If a domain
   genuinely doesn't apply (e.g. a pure library with no infra to assess for "infrastructure
   security hygiene"), say so explicitly in that section rather than forcing a number.
6. Write `AUDIT_REPORT.md` at the target project's root using the structure below.

## Domain definitions (score against these, not just the raw metrics)

- **Architecture & Design** — use of intentional, long-term design patterns; decoupled
  architecture; separation of concerns. The script's signals (god files, import cycles,
  absence of layering directories) are smells, not proof either way.
- **Clean Code** — PEP 8 for Python; explicit type annotations everywhere (Python 3.12+
  idioms); for TypeScript/JS, strict typing (no stray `any`, no `@ts-ignore` suppressions)
  and modern ES+ standards.
- **Documentation** — full docstrings/annotations present, and the docstrings explain the
  underlying algorithm and flow of the solution, not just inputs/outputs. A one-line
  docstring restating the signature does not satisfy this domain even if "present".
- **Security** — hardcoded secrets, proper permission management (least privilege, no
  root containers), infrastructure security hygiene (`.gitignore` covering secrets, safe
  Dockerfile defaults, no `eval`/`shell=True`/`pickle.loads` on untrusted input).
- **Scalability** — memory management (generators over eagerly-built lists where it
  matters), efficient data flows, and loop/algorithmic bottlenecks under realistic data
  volumes — not against every nested loop in the abstract.
- **Testing** — coverage (reported % if available, otherwise test-to-source ratio as a
  weaker proxy — say which one you're using), test isolation, and quality of mocks (mocking
  true I/O boundaries, not over-mocking internals).

## Report structure

```markdown
# Repository Audit Report

**Project:** <name> · **Stack:** <detected languages/frameworks> · **Date:** <date>
**Overall score:** <n>/100

## Architecture & Design — <score>/100 (confidence: <level>)
<2-4 sentence summary>

**Strengths**
- ...

**Issues**
- `path/to/file.py:42` — <concrete issue, why it matters>

**Recommendations** (priority order)
1. ...

<repeat the above block for Clean Code, Documentation, Security, Scalability, Testing>

## Methodology
<one paragraph: what run_audit.py measured mechanically vs. what you verified by reading
code directly, and any domain you excluded or scored on incomplete signal>
```

## Rules

- Every issue must cite a real `file:line`. If the script's JSON didn't give you one, open
  the file and find it — never invent a location.
- Don't inflate or deflate a score to be polite or harsh — justify each one against the
  domain definitions above, not vibes.
- If the project isn't the stack the script expected, has no tests, or has no docs, say so
  plainly in that domain's summary instead of forcing a score that implies false precision.
- Keep the report itself lean — no restating obvious file contents, no architecture-overview
  padding beyond what's needed to justify a score. This repo's own rules on output discipline
  apply to what you write here too.
