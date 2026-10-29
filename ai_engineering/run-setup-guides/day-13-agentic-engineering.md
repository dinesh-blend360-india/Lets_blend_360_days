# Day 13 — Agentic engineering: designing a pilot you could defend

| | |
|---|---|
| **Folder** | `13_agentic_engineering/` — `design_card.json`, `validate_card.py`, `tests/`, `README.md` |
| **Commands** | `& $py validate_card.py` · `& $py -m pytest -q` |
| **Needs** | **Only Python.** No model. No code to write beyond editing a JSON file. |
| **Time** | 2–3 hours — this is a *thinking and writing* day |
| **Depends on** | Days 10–12 (the assistant being "productionised"), Day 09's decision habits |

Materials in `day_11_to_16/` (local, git-ignored): the Day 13 presentation, the
**Learner Challenge** and the **Reflection Guide** (Word).

---

## 1. What you are learning

Days 01–12 build a *prototype*. A customer's real question is: **"What would it
take to run this reliably for real users?"** Day 13 is not about deploying
anything. It is about producing a **credible, honest design** and being able to
defend it.

The deliverable is a **Hypothetical Agentic System Design Card**
(`design_card.json`) plus a written reflection. The card covers:

| Section | The question it answers |
|---|---|
| Current prototype | What *actually exists today*? (label: `EXISTING`) |
| Business outcome | Who benefits, how, and what is still unknown? |
| Architecture | What is the model allowed to decide, and what must be deterministic code? Where does a human approve? |
| **Lifecycle (10 stages)** | For each stage — **Discover, Plan, Build, Verify & Review, UAT, Release, Roll Out, Run, Monitor, Improve** — who owns it, what evidence is produced, and what is handed to the next stage? |
| **Golden cases (≥ 3)** | Normal path, dependency failure, and an access/misuse boundary — with input, expected result, and how you would test it |
| Pilot conditions | What must be true to go, what blocks, how to recover |
| Alternative | A different design, with its trade-offs |
| Risks and unknowns | The top three of each |

The most important discipline is **labelling**. Every item is tagged
`EXISTING` / `OBSERVED` (it really happened), `HYPOTHESIZED` / `PROPOSED`
(you are suggesting it), or `NEEDS VALIDATION`. A design that blurs "we built
this" with "we would build this" is dishonest, however well written.

Other ideas:

- **Autonomy boundaries.** Model decides *whether to answer, retrieve or propose*;
  code owns identity, authorisation, schema checks, idempotency, confirmation, audit.
- **Ownership and handoffs.** Every control needs a named owner and an evidence trail.
- **Failure thinking.** Design for the timeout *after* a write succeeded, not just
  the happy path.
- **Pilot thinking.** Read-only first; earn trust before adding actions.
- **Defending a design.** You will be asked: *why is this control needed, what
  failure does it prevent, who owns it, what would you measure, what experiment
  would validate it?*

Reference: the Blend360 *Agentic DevOps Loop* guide (linked in the challenge).

## 2. Setup

Nothing. Check:

```powershell
Set-Location "$ai\13_agentic_engineering"
& $py -m pytest -q          # 2 passed
```

Edit `design_card.json` in any editor (VS Code highlights JSON errors as you type).

## 3. Run

```powershell
& $py validate_card.py
```

You will see **`Day 13 design card is structurally complete`** — and nothing else.
If there are problems it prints one line per problem and exits with an error.

The workflow is: **write → validate → reread as a sceptic → revise.**

## 4. What to test

**Make the card yours.** The shipped card describes the Day 10–12 assistant. Either
sharpen it or redo it for a project you understand better. Then:

- [ ] Fill every `owner` and `handoff` with something specific (a *role*, not "TBD").
- [ ] Label every section honestly. Is anything marked `EXISTING` that you could not
  actually demonstrate today?
- [ ] Write **three golden cases** that are genuinely different: a normal request, a
  dependency failure (e.g. a ticket API times out *after* committing), and an access
  boundary (a user who must not see a document).
- [ ] For each golden case, write how you would **score** it (what is checked, by
  code or by a person).
- [ ] State the **three biggest unknowns** and, for each, *the cheapest experiment that
  would settle it*.
- [ ] Name **one alternative design** and a real downside of *your own* choice.

**Test the validator itself** (a good habit — know what a check does and doesn't do):

- [ ] Blank one `handoff` → `Incomplete stage: Discover`.
- [ ] Swap two stages, or delete one → `Lifecycle must contain the ten stages in order`.
- [ ] Put a bad label (`MAYBE`) on a stage → `Incomplete stage: …`.
- [ ] Delete a golden case → `At least three unique golden cases are required`.
- [ ] Delete the `label` from `architecture` → `Missing evidence label: architecture`.

**Then defend it aloud.** Pick one lifecycle stage and answer the five defence
questions above. If you cannot, the stage is decoration.

## 5. What to expect

```text
Day 13 design card is structurally complete
```

and `2 passed` from pytest. These were verified; each mutation in the checklist
above produced exactly the message shown.

The shipped card contains: **10 lifecycle stages** (`Discover, Plan, Build,
Verify & Review, UAT, Release, Roll Out, Run, Monitor, Improve`), each with a
label, owner, evidence and handoff; **3 golden cases** (`D13-01` normal,
`D13-02` dependency failure, `D13-03` access boundary); pilot go / no-go /
recovery conditions; an alternative (a fixed retrieval-and-request workflow);
three risks (unauthorised policy access, duplicate action after a timeout, a
model/prompt change that passes a demo but regresses real cases); and three
unknowns (who may read which documents; which service platform and identity
provider; acceptable latency, quality, retention and availability targets).

**And — critically — this also passes the validator:**

| Change to the card | Validator says |
|---|---|
| Replace every golden case's input/expected/method with the letter `x` | **passes** |
| Make all three golden cases the same category | **passes** |
| Delete the top risks | **passes** |
| Delete the unknowns | **passes** |
| Set every owner to `TBD` | **passes** |

The validator checks the *shape* — ten stages in order, non-empty fields, valid
labels, at least three unique cases — and **nothing about meaning**. A card full of
placeholders is "structurally complete". The pytest suite is the same: two tests,
one for the shipped card and one for a blank handoff.

## 6. If something goes wrong

| You see | Cause | Fix |
|---|---|---|
| `Lifecycle must contain the ten stages in order` | A stage missing, misspelled or reordered | Match the names exactly, including `Verify & Review` and `Roll Out` |
| `Incomplete stage: X` | Missing `owner`, `evidence`, `handoff`, or an invalid `label` | Fill all four |
| `At least three unique golden cases are required` | Fewer than three, or duplicate `id`s | Add cases with unique IDs |
| `Incomplete golden case: D13-02` | Missing `input`, `expected`, `method` or `label` | Fill them |
| `Missing evidence label: pilot_conditions` | Section has no `label` | Add one of the five valid labels |
| A Python JSON error (`JSONDecodeError`) | A comma, quote or bracket mistake | Let your editor point at the line |
| Valid labels rejected | Labels are case- and space-sensitive: `NEEDS VALIDATION` has a space | Copy exactly |

## 7. Learn more

- The **Blend360 Agentic DevOps Loop** reference in the challenge brief.
- **Release engineering for ML/LLM systems:** versioning prompts, models and tools
  as one *bundle*; canary and shadow rollouts; rollback.
- **Observability and incident response** for AI systems (Day 16 starts this).
- **Threat modelling** (STRIDE) for an assistant with tools; OWASP Top 10 for LLM
  applications.
- **Authorisation models:** RBAC, ABAC, document-level security, and why retrieval
  must enforce it *before* content reaches the model.
- **SRE ideas:** SLIs/SLOs, error budgets, runbooks, blameless post-mortems.
- **Acceptance testing (UAT)** with business owners; what "sign-off" really commits.
- **Pre-mortems:** imagine the pilot failed and write the cause.

## 8. What you might be missing

- **The validator is a form-checker, not a reviewer.** (Section 5.) Passing it earns
  you nothing on its own. A *reviewer* will read the content, so write for them.
- **There are required parts the validator never looks at.** The challenge asks for
  a system boundary, operations (release bundle, named owners, observability,
  incident response, rollback), a trade-off against an alternative, three risks,
  and three unknowns/customer questions. Check your card against the brief by hand.
- **The golden cases must cover three *kinds*** — normal, dependency failure,
  access boundary. Nothing enforces it.
- **Hypothetical must not look observed.** The brief says: *"Do not label
  hypothetical outcomes as observed test results"* and the reflection guide says
  *"Do not invent metrics, passed evaluations, incidents, or approvals."* Numeric
  targets must be marked *proposed*. This is the easiest way to lose credibility.
- **You are allowed — expected — to say "I don't know yet."** The best designs
  name their blockers. A card with no unknowns is not confident; it is unexamined.
- **Do not copy the Calix example.** The brief says to extract the *principle* and
  adapt it, not reuse its rules or integrations.
- **The card is a *separate* submission from the reflection.** The reflection is a
  Word document following the Reflection Guide's eight prompts (current vs future
  state; key hypotheses; autonomy and safety; failure thinking; evaluation design;
  trade-offs; pilot readiness; next experiment).
- **Access control is the central unknown.** Day 10's "permission" is a flag an
  operator sets. A pilot needs real identity and document-level authorisation, and
  you cannot design D13-03 honestly without admitting that.
- **A timeout after a write is the most instructive failure.** A blind retry can
  duplicate the action; reporting failure contradicts what happened. Day 12's
  idempotency key is the pattern you would cite.
- **AI tools may help you draft, but you must defend every line.** Expect to be
  asked about any of it.
- **It is a JSON file.** Editing it badly can produce a decoding error before the
  validator even runs — keep a copy before big edits (`git diff` is your friend).

## 9. Where this leads

Day 14 standardises how a tool is exposed; Day 15 turns your three hypothetical
golden cases into real, runnable ones; Day 16 adds the observability your
"Monitor" stage promised. Day 17 asks you to present the whole story.
