# General Documentation Principles (Detailed)

Quick reference: [documentation-principles-short.md](./documentation-principles-short.md).

> **General-only, on purpose.** There is no per-language variant of this guide. Docstrings,
> JSDoc, and doc comments are a *coding* concern and live in each language's coding guide
> ([Python](../python/coding-guide-detailed.md) ·
> [TypeScript](../typescript/coding-guide-detailed.md) ·
> [C++](../cpp/coding-guide-detailed.md)). This guide is about the **repository**.

Documentation is the interface between a codebase and every person who did not write it —
including its author six months later. It is judged by one question: *can someone who has
never seen this repo become productive in it without interrupting anyone?*

---

## Table of Contents

1. [The Standard Doc Set](#1-the-standard-doc-set-)
2. [Why the Directory Map Is Separate](#2-why-the-directory-map-is-separate-)
3. [Generated vs. Hand-Written](#3-generated-vs-hand-written-)
4. [Writing the Annotation](#4-writing-the-annotation-)
5. [Diagrams](#5-diagrams-)
6. [Honesty and Traceability](#6-honesty-and-traceability-)
7. [Keeping Documentation Alive](#7-keeping-documentation-alive-)
8. [Anti-Patterns](#8-anti-patterns-)

---

## 1. The Standard Doc Set 📁

A reader arriving at any repo should find the same four files in the same places. The
consistency is most of the value: once someone learns the layout, they know it for every
repo, and "where is that documented?" stops being a question anyone asks.

### `README.md` — the front door

Answers, in this order:

1. **What is this?** One or two sentences. Not the tech stack — the purpose.
2. **Why does it exist?** What it replaced, or what was impossible without it.
3. **How do I run it?** Copy-pasteable commands: install, run, test. If a newcomer has to
   translate your instructions before running them, they are not instructions.
4. **Repo structure.** A top-level tree — directories only — so the shape is visible without
   a click.
5. **Where to go next.** Links into `docs/`.

A README that stops after installation instructions has documented the easiest part of the
job and skipped the rest.

### `docs/STRUCTURE.md` — the annotated map

Every file, and one line each saying **what is inside it**. This is the file people actually
need and the one most repos don't have. See §2.

### `docs/HLD.md` and `docs/LLD.md` — the design views

Per the [architecture guide](./architecture-principles-detailed.md#design-documents-hld--lld-)'s
checklists. The HLD's *Static view* section is where the block diagram and the directory map
both belong.

### Two exemptions, and only two

A standard nobody can follow gets ignored wholesale, so it has to be honest about where it
doesn't apply:

- **No system, no HLD/LLD.** A documentation, content, or configuration-only repo has no
  components, no data flow, and no error contract. Writing two files of empty headings to
  satisfy a checklist produces documentation that is worse than absent — it looks like
  someone answered the question. State the exemption in the README instead.
- **Small enough to fit, no separate map.** If the full annotated tree fits readably in the
  README — roughly one screen — that *is* `docs/STRUCTURE.md`, and splitting it out adds a
  click for nothing. Split when it stops fitting.

Neither exemption relaxes anything else: the tree is still generated, still verified in CI,
and there is still exactly one of it.

### `docs/INVENTORY.md` — optional, for repos that ship many units

When a repo ships dozens of discrete things (rules, plugins, endpoints, commands), an index
by **purpose** is a different lookup from an index by **path**, and both earn their place.
`STRUCTURE.md` answers "which file"; `INVENTORY.md` answers "what does it do, and what
reaches it".

---

## 2. Why the Directory Map Is Separate 🗺️

An HLD block diagram and a directory map look redundant and are not:

| | Block diagram | Directory map |
|---|---|---|
| Answers | How is the system **shaped**? | Which file do I **open**? |
| Unit | Component / service | File / directory |
| Changes when | The architecture changes | Any file is added or renamed |
| Audience | Someone deciding *what* to change | Someone about to *make* the change |

A component named "Auth Service" tells a newcomer nothing about whether the token logic is in
`auth/tokens.py` or `middleware/session.py`. The map is the last mile, and skipping it means
every newcomer re-derives it by reading the whole tree.

### The core rule

> **A map nothing verifies is worse than no map.**

A missing map costs a reader five minutes of exploring. A *stale* map costs an hour of
confusion plus their trust in every other document in the repo — after being misled once,
a reader starts verifying everything, which is the same as having no documentation at all.

This is not hypothetical: hand-written layout lists drift within weeks, because the commit
that adds a file has no reason to touch the doc that lists files. The only durable answers
are to generate the map and fail the build on drift, or to not ship one.

### One map, not several

The failure mode is worse than staleness alone. Repos accumulate layout descriptions in the
README, in a contributor guide, in the HLD, in a docs index — four maps of one territory,
each drifting independently. That is not four times the documentation; it is four chances to
be wrong and no way for a reader to know which one to believe.

**Pick one canonical, verified map. Everywhere else keeps only its orientation value** —
what each directory is *for* — and links to it.

---

## 3. Generated vs. Hand-Written ✍️

The split is not about effort. It is about **which facts a machine can check.**

| Generate | Write by hand |
|---|---|
| File trees | Why this design, and what was rejected |
| API / CLI reference | How to get started |
| Config-key tables | What surprises people |
| Dependency and license lists | Trade-offs and their reasoning |
| Anything derivable from the code | Anything only a person knows |

### Marked regions

Generated content lives between explicit markers inside an otherwise hand-written file:

```markdown
<!-- BEGIN GENERATED TREE -->
...generated content...
<!-- END GENERATED TREE -->
```

This keeps prose and generated content in one readable document while making the boundary
unambiguous. Two rules follow:

- **Never hand-edit between the markers.** The next regeneration silently discards it.
- **Stamp the generation parameters into the marker** (depth, filters). A checker can then
  rebuild the block exactly as it was made, without being told, which is what makes the CI
  gate possible on files generated with different settings.

### The override file

Some files cannot describe themselves: `LICENSE`, `.gitignore`, lockfiles, templates, data
fixtures. Give the generator a hand-written override file keyed by path, and let an override
always outrank a derived note.

This escape hatch is what keeps a generator honest. Without it you get one of two failures:
a tree full of blank lines, or a generator that starts inventing descriptions — and an
invented description is worse than a blank one, because a reader can't tell it apart from a
real one.

### Tracked files only

Generate from the version-control file list (`git ls-files`), not a raw directory walk. This
honours ignore rules for free, keeps build output and local scratch files out of the map, and
makes the CI gate exact: what is committed is what is mapped.

---

## 4. Writing the Annotation 📝

The tree is only worth reading because of the notes. A tree of bare filenames helps nobody —
the filesystem already provides that.

**A note says what is inside the file, not what its name already says.**

| ❌ | ✅ |
|---|---|
| `errors.py` — errors module | `errors.py` — exception hierarchy, one base class per package |
| `client.ts` — the client | `client.ts` — HTTP client with retry/backoff; the only file that imports the vendor SDK |
| `config/` — configuration | `config/` — loaded once at startup, validated, then immutable |

### Prefer derivable descriptions

Design your files so their description can be *extracted* rather than *maintained*:

- YAML frontmatter `description:` for documents that have it
- The first heading of a markdown file
- The module docstring of a source file

A description that lives in two places drifts. A description extracted from the file itself
is correct by construction — and it means writing a good module docstring pays twice.

### Length

One line. If a file needs a paragraph, that belongs in the LLD, and the tree note should say
what it is and let the reader follow the link.

---

## 5. Diagrams 📊

### Use Mermaid

| | Mermaid | ASCII box art | Image file |
|---|---|---|---|
| Renders on GitHub | ✅ native | ✅ (as text) | ✅ |
| Survives editing | ✅ | ❌ one word breaks alignment | ❌ needs the source file |
| Readable diff | ✅ | ❌ | ❌ binary |
| Editable without tooling | ✅ | ✅ | ❌ |

ASCII box art looks appealing because it needs nothing to render, and then the first person
to add a word to a label spends ten minutes realigning the box — or, more often, doesn't, and
the diagram decays. Mermaid text is edited like code because it is code.

### A diagram must show a mechanism

A diagram earns its place by showing something a list cannot: a flow, a boundary, a state
machine, a fan-out and where it converges. A box-per-item diagram of things that have no
relationships is a list drawn badly — write the list.

### What each design view needs

- **HLD static view:** the component block diagram **and** the directory map.
- **HLD dynamic view:** a sequence or flow diagram of the primary use case, end to end.
- **LLD:** usually none. Interface signatures and pseudocode carry more precision per line
  than a class diagram of the same thing.

---

## 6. Honesty and Traceability 🔍

- **Every claim traces to real code** — a file path, a function name, a config key that
  exists. If you cannot point at it, cut the claim.
- **Document what the code does, not what it was meant to do.** Aspirational architecture
  presented as built is the most expensive documentation failure there is: it survives review
  (it sounds right), and it is only discovered by someone who relied on it.
- **An honest gap beats a confident guess.** "No documented backup strategy" is actionable.
  A plausible-sounding invented one is a trap. When documenting an existing system, write
  the gap under its section rather than skipping the section silently — a missing section
  reads as "not applicable", which is a different claim.
- **Separate proposals from descriptions.** If a doc describes something not yet built, say
  so in the document, at the top, unmissably.

---

## 7. Keeping Documentation Alive 🔄

### Same commit, always

Update docs in the same commit as the behavior they describe. A doc-only follow-up commit is
a doc that will not get written — the context is gone, the urgency is gone, and the person
who understood the change has moved on.

### Automate the checkable parts

Anything a machine can verify, a machine should verify:

- The generated tree matches the real tree (fail CI on drift).
- Internal links resolve.
- Documented CLI flags match the parser.
- Code samples in docs actually compile or run.

Documentation that only a human remembers to update has a half-life measured in sprints.
This is the same reasoning as testing: not distrust of people, but recognition that the
failure is silent, and silent failures need machines.

### Review docs like code

A pull request that changes behavior without changing its documentation is incomplete, the
same way one without tests is incomplete. Say so in review.

---

## 8. Anti-Patterns 🚫

| Anti-pattern | Why it hurts | Fix |
|---|---|---|
| **Stale directory map** | Misleads and destroys trust in every other doc | Generate it; fail CI on drift |
| **Two maps of one layout** | One is always wrong, and the reader can't tell which | One canonical map; everything else links to it |
| **Docstring restating the signature** | Costs a line, adds nothing the reader can't see | Explain the approach, the flow, the edge cases |
| **README stops at install** | Documents the easiest part and skips the rest | Add purpose, structure, and where to go next |
| **Diagram of a system that no longer exists** | Confidently wrong, and looks authoritative | Diagram mechanisms that change slowly; delete the rest |
| **"Docs in a follow-up commit"** | Never happens | Same commit, or it isn't done |
| **Aspirational architecture as built** | Survives review; discovered only by whoever relied on it | Label proposals as proposals, at the top |
| **Hand-maintained generated content** | Silently discarded on the next generation | Put it outside the markers, or in the generator's input |
