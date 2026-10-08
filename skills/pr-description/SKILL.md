---
name: pr-description
description: Write a clear pull request title and description from the actual diff — what changed, why, how it was tested, and what a reviewer should look at. Use whenever the user asks for a PR description, PR summary, or release note for a branch, or says "write up this change" — and always check for the repo's PR template first.
---

# PR Description

Turn a branch into a description a reviewer can act on without reading the whole diff first.

## Steps

1. **Read the change itself.** Run `git log <base>..HEAD --oneline` and `git diff <base>...HEAD
   --stat`, then read the diff for the files that matter. Describe what the code does, not what
   the commit messages claim.
2. **Find the repo's PR template** (`.github/PULL_REQUEST_TEMPLATE.md`,
   `PULL_REQUEST_TEMPLATE/`, `docs/`). If one exists, fill it in rather than inventing a shape.
3. **Write the title** in the repo's commit style (see the `conventional-commit` skill if it
   uses Conventional Commits): imperative, under about 70 characters, naming the outcome.
4. **Write the body** in this order, omitting a section only when it is genuinely empty:
   - **Why** — the problem or motivation, with the issue link if one exists.
   - **What changed** — a short bulleted list grouped by behavior, not by file.
   - **How it was tested** — the exact commands run and their result, plus manual checks. If
     something was not tested, say so.
   - **Risks and rollout** — migrations, config or env changes, breaking changes, flags,
     rollback path.
   - **Review guide** — where to start, and what deserves the closest look.
5. **Flag anything the diff contains that the description cannot honestly cover** (unrelated
   changes, generated files, large mechanical edits) and suggest splitting if it is mixed.

## Rules

- Never claim tests passed that you did not see pass. Use the real output.
- No filler ("this PR improves things"). Every sentence should help a reviewer decide or locate.
- Do not include secrets, internal URLs, or customer data from the diff or logs.
- Keep it proportional: a one-line fix gets a few lines, not five sections.

## Output

The title on its own line, then the body in Markdown, ready to paste. Mention any template used
and any item left blank because the information was not available.
