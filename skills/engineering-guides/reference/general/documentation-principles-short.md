# General Documentation Principles (Short)

Cheat sheet for what a repository must document and how. Full explanations:
[documentation-principles-detailed.md](./documentation-principles-detailed.md).

> **General-only, on purpose.** There are no per-language variants of this guide: how to
> write a docstring or a JSDoc block is a *coding* concern and already lives in each
> language's [coding guide](../python/coding-guide-short.md). This guide is about the
> repository, not the function.

## The Standard Doc Set 📁

Every repo carries these four, in these paths, so a reader never has to guess:

| File | Answers | Without it |
|---|---|---|
| `README.md` | What is this, why does it exist, how do I run it — **plus a top-level repo tree** | A newcomer starts by guessing |
| `docs/STRUCTURE.md` | **Which file do I open?** — the annotated tree, one line per file | You read the whole repo to find one thing |
| `docs/HLD.md` | How is the system shaped? | Every change is a local guess |
| `docs/LLD.md` | How does this module actually behave? | Contracts get re-derived from the code, wrongly |

Add `docs/INVENTORY.md` when the repo ships many discrete units (rules, plugins, endpoints)
worth indexing by *purpose* rather than by path.

**Two honest exemptions**, and only these two:

- **A repo with no system in it** — a documentation, content, or configuration-only repo —
  has no HLD or LLD to write. Say so in the README rather than shipping two empty headings.
- **A repo small enough that its full tree fits in the README** doesn't need a separate
  `docs/STRUCTURE.md`; the README tree *is* the map. Split it out when the full tree stops
  being readable inline — roughly when it no longer fits on one screen.

Everything else in this guide applies either way: the map is still generated, still verified,
and still the only one.

## The Core Rule 🎯

> **A map nothing verifies is worse than no map.** A missing directory map costs a reader
> five minutes. A *wrong* one costs them an hour and their trust in every other doc.

So: generate the tree and fail CI on drift, or don't ship one. Never maintain two
hand-written maps of the same layout — the second one is already wrong.

## Generated vs. Written ✍️

| Generate | Write by hand |
|---|---|
| File trees, API/CLI references, config-key tables, dependency lists | Why this design, what was rejected, how to get started, what surprises people |
| Anything derivable from the code | Anything only a person knows |

- Mark generated regions (`<!-- BEGIN GENERATED … -->` / `<!-- END … -->`) and **regenerate,
  never hand-edit**. Durable prose goes outside the markers or into the generator's input.
- Prefer descriptions **derivable from the file itself** — frontmatter, first heading, module
  docstring — so a tool can produce and check them instead of a human maintaining them.
- Give the generator a hand-written override file for what can't describe itself (`LICENSE`,
  lockfiles, templates). The escape hatch is what keeps the generator honest instead of
  guessing.

## Diagrams 📊

- **Mermaid, inline in the doc.** It renders natively on GitHub, survives editing, and
  produces a readable diff. ASCII box art fails all three — one added word destroys the
  alignment, and the diff is unreadable.
- A diagram earns its place by showing a **mechanism** (a flow, a boundary, a state machine),
  not by restating a list that reads better as a list.
- HLD gets the block diagram *and* the directory map: the block diagram says how the system
  is shaped, the directory map says which file to open. They are not substitutes.

## Honesty Rules 🚫

- Every claim traces to real code — a file path, a function, a config key that exists. If you
  can't point at it, cut it.
- **"Not documented" beats a plausible guess.** A reader can act on a known gap; they can't
  detect a confident fabrication.
- Say what the code *does*, not what it was supposed to do. Aspirations go in an issue.

## Keeping It Alive 🔄

- Update docs **in the same commit** as the behavior they describe. A doc-only follow-up
  commit is a doc that will not get written.
- Wire the drift check into CI next to the test step. Documentation that only a human
  remembers to update is documentation with a half-life.
- Review docs like code: a PR that changes behavior and not its docs is incomplete.

## Anti-Patterns 🚫

Stale directory map · Two maps of one layout · Docstring restating the signature ·
README that stops at `npm install` · Diagram of a system that no longer exists ·
Doc-only follow-up commit "coming later" · Aspirational architecture presented as built.
