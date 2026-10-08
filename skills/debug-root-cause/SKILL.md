---
name: debug-root-cause
description: Find and fix the root cause of a bug instead of patching its symptom — reproduce it, narrow it down (bisect if it is a regression), pin it with a failing test, then make the smallest fix. Use whenever the user reports a bug, a failing test, a crash, "this used to work", or "why does this happen", and asks for it to be fixed or diagnosed — even if they only paste an error message.
---

# Debug Root Cause

Fix the cause, not the symptom. A change that makes the error message go away without
explaining why it appeared is not a fix.

## Steps

1. **Reproduce first.** Get the failure to happen on demand with a concrete command, input,
   or test. If it cannot be reproduced, say so and gather what is missing (version, input,
   environment, logs) rather than guessing at a fix.
2. **Read the actual error.** Quote the exception, message, and the top frames in the project's
   own code. Do not skim; the first project-owned frame is usually the best lead.
3. **Narrow it down.**
   - Regression ("worked before"): `git bisect` between a known-good and known-bad commit,
     using the reproduction as the test, then read the offending diff.
   - Otherwise: shrink the input or the call path until removing anything more makes the bug
     vanish; add temporary logging at boundaries to find where actual and expected values
     first diverge.
4. **State the root cause in one sentence** that explains every observation — including why it
   does not fail elsewhere. If the sentence leaves an observation unexplained, keep looking.
5. **Write a failing test** that captures the bug at the lowest level that still reproduces it.
   Run it and watch it fail for the reason you stated.
6. **Make the smallest fix** that addresses the cause. Re-run the new test and the project's
   existing suite and gates.
7. **Check for siblings.** Grep for the same pattern elsewhere; report other occurrences rather
   than silently widening the diff.

## Rules

- No fix without a reproduction and a test that failed first, unless the user explicitly says
  the bug cannot be tested, in which case say what you verified instead.
- Never "fix" by catching and swallowing an exception, adding a retry, or special-casing the
  failing input, unless that is genuinely the correct behavior and you can say why.
- Remove temporary debug logging before finishing.
- Do not refactor unrelated code while you are here; note it instead.

## Output

Report: the reproduction, the root cause in one sentence, the evidence (bisect result or the
diverging value), the test added, the fix, and any sibling occurrences found but not changed.
