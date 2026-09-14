## Verification before done

- Self-review confirms what you assumed; it does not substitute for actually running the
  check. Before calling anything done, run the real command — tests, build, lint,
  type-check — and look at its output. "The diff looks right" is not verification.
- If the change is non-trivial (touches more than one file, a public contract, or logic you
  didn't write), get an independent look before declaring it finished: a reviewer, a second
  pass, or a subagent with no investment in your own assumptions — not another read-through
  of the same reasoning that produced the change.
- State exactly what you verified and how: the command run and its result, not "looks good"
  or "should work." If a check couldn't run — no test for this path, no way to execute the
  build here — say that explicitly instead of reporting success.
- An objection or finding is only as good as the evidence behind it: cite the exact
  `file:line` or command output it's based on. "This might be an issue" without a citation
  isn't a finding, it's a guess.
- Never mark something done with verification skipped, degraded, or incomplete unless you've
  said so out loud. A silent skip is worse than an honest "I couldn't verify this."
