## Documentation

- Every repo carries the same doc set, so a reader knows where to look before they arrive:
  `README.md` (what it is, why it exists, how to run it, a short repo tree, links into
  `docs/`), `docs/STRUCTURE.md` (the annotated file tree — which file to open),
  `docs/HLD.md` and `docs/LLD.md` (per the architecture checklist). Add
  `docs/INVENTORY.md` when the repo ships many discrete units worth indexing.
- **A directory map nothing verifies is a lie.** Generate the tree and fail CI on drift, or
  don't ship one. Never keep two hand-written maps of the same layout — the second is
  already wrong.
- Generated regions are marked (`<!-- BEGIN GENERATED … -->`) and regenerated, never
  hand-edited. Durable prose goes outside the markers or into the generator's own input.
- A file's one-line description says what is *inside* it, not what its name already says.
  Prefer descriptions derivable from the file itself (frontmatter, first heading, module
  docstring) so they can be generated and checked rather than maintained.
- Diagrams are **mermaid**, inline in the doc that needs them — it renders natively on
  GitHub, survives editing, and diffs. ASCII box art does none of these.
- Docs state what the code actually does. If you can't point at the file, function, or config
  key behind a claim, cut the claim — an honest "not documented" beats a plausible guess a
  reader can't tell is fabricated.
- Update docs in the same commit as the behavior they describe. A doc-only follow-up commit
  is a doc that will not get written.
