---
name: threat-model
description: Produce a threat model for a feature or system using STRIDE over its data flows and trust boundaries, with concrete mitigations and residual risks. Use whenever the user asks for a threat model, security design review, "what could go wrong security-wise", or wants a design doc checked for security before building — pairs with write-design-doc.
---

# Threat Model

Find how a design can be attacked while it is still cheap to change. This is a design-time
analysis; it reads a design or the code's structure and does not probe a running system.

## Steps

1. **Define the scope in two sentences**: what is being modeled and what is out of scope.
2. **Gather the design.** Read the design doc or HLD (see the `write-design-doc` skill) and the
   entry points in the code. If neither exists, reconstruct the picture from the repo and say
   it is reconstructed.
3. **List assets** worth protecting: data (credentials, personal data, business records),
   capabilities (who can perform which action), and availability.
4. **Draw the data flows** as a short list or a Mermaid diagram: actors, processes, data
   stores, external services, and the **trust boundaries** between them (internet to service,
   service to datastore, tenant to tenant, user to admin).
5. **Apply STRIDE at each boundary and flow**, one row per credible threat:
   - **S**poofing identity — can a caller pretend to be someone else?
   - **T**ampering — can data or code be modified in transit, at rest, or by a client?
   - **R**epudiation — can an action be denied for lack of an audit trail?
   - **I**nformation disclosure — can data leak through responses, logs, errors, or side channels?
   - **D**enial of service — can one caller exhaust a shared resource?
   - **E**levation of privilege — can a caller reach an action beyond their role?
6. **Rate each threat** by likelihood and impact (low/medium/high) in this system's context,
   not in the abstract, and drop threats that are not credible here.
7. **Name a mitigation for each remaining threat** — a specific control (validation at X,
   authorization check on Y, rate limit on Z) — and mark it *exists*, *planned*, or *missing*.
8. **Record residual risk and open questions**: what is accepted, by whom, and what needs an
   answer before the design can be called safe.

## Rules

- Be specific: "an unauthenticated caller can replay the webhook because the signature has no
  timestamp" beats "spoofing is possible".
- Distinguish a verified fact from an assumption. Cite the file or doc section for each claim
  about current behavior.
- Do not invent mitigations the stack cannot support; suggest the nearest real option.
- Do not scan for secrets or write exploit code; that is a different task.

## Output

A document with: scope, assets, data-flow diagram, a STRIDE table (threat, boundary, rating,
mitigation, status), residual risks, and open questions. Offer to append it to the design doc.
