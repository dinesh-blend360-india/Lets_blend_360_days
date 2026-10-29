# Day 09 — Architecture decisions: prompt, RAG, fine-tuning, or no LLM?

| | |
|---|---|
| **Folder** | `09_fine_tuning/` — `src/`, `data/`, `tests/`, `submissions/`, `outputs/` |
| **Commands** | `& $py -m src.scenario_loader --list` · `… --export-template S01` · `& $py -m src.decision_evaluator --submission …` |
| **Needs** | Nothing but Python. **No model, no GPU, no Ollama, no internet, no training.** |
| **Time** | 1.5–3 hours (most of it is *thinking*, which is the point) |
| **Depends on** | Context from Days 02, 06, 07. No files are required. |

---

## 1. What you are learning

The folder is named `fine_tuning`, but **you do not fine-tune anything today.**
The skill is *deciding* — and, above all, learning that **fine-tuning is usually
not the answer**.

Given a business need, there are five basic architectures. Pick the **smallest
one that is defensible**:

| Architecture | Use when | Why |
|---|---|---|
| `PROMPT_CONTEXT` | A bounded task over a tiny, supplied piece of text | Least infrastructure |
| `RAG` | Knowledge is current, private or changing, and needs citations | Keeps facts *outside* the model's weights |
| `FINE_TUNING` | A *persistent behaviour or format* that prompting has measurably failed to deliver, and you have good reviewed examples | Changes how the model behaves, not what it knows |
| `COMBINATION` | Changing knowledge **and** a stubborn behaviour problem | RAG owns knowledge; tuning (if justified) owns behaviour |
| `NO_LLM` | Exact, reproducible business rules | Code is testable, versioned, auditable |

…and one more outcome: **`DECISION_DEFERRED`** — when essential facts are
unknown, the right answer is "discovery first", not a guess.

Core ideas to take away:

- **Knowledge vs behaviour.** Fine-tuning changes *behaviour* (tone, format,
  patterns). It does **not** reliably add facts, keep facts current, or provide
  citations. Facts belong in retrieval.
- **Measure a prompt baseline before tuning.** "Prompting isn't working" is only
  a claim until you have evidence.
- **Fine-tuning needs data you can defend:** reviewed examples, a train/validation/test
  split, no sensitive data, evaluations, a base model, cost and a maintenance plan.
- **A decision is only as good as its stated assumptions.** Each scenario lists
  assumptions that could flip the answer.
- **A "decision card"** forces you to write the outcome, the choice, the rationale,
  a rejected alternative, the key risk, the question that would change your mind,
  and a validation plan. That is a one-page version of how an FDE justifies a design.

## 2. Setup

Nothing. Check the tool runs:

```powershell
Set-Location "$ai\09_fine_tuning"
& $py -m pytest -q          # 16 passed
```

## 3. Run

All commands from `09_fine_tuning`:

```powershell
# See the eight scenarios and each one's reference answer
& $py -m src.scenario_loader --list

# Read one in full (business scenario, assumptions, constraints)
& $py -m src.scenario_loader --show S06

# Create a blank answer sheet for a scenario (written to submissions\)
& $py -m src.scenario_loader --export-template S01
```

Edit `submissions\S01_submission.json` (fields below), then score it:

```powershell
& $py -m src.decision_evaluator --submission .\submissions\S01_submission.json
```

Each evaluation writes a new folder `outputs\run_history\<UTC-timestamp>\`
(`manifest.json`, `result.json`, `report.md`) and refreshes
`outputs\reports\latest_report.md`. Earlier runs are never overwritten.

**The second tool — a fine-tuning readiness checklist:**

```powershell
& $py -m src.fine_tuning_readiness --export-template .\submissions\fine_tuning_readiness.json
# edit each item: READY / NOT_READY / NEEDS_REVIEW, with an evidence-based reason
& $py -m src.fine_tuning_readiness --assess .\submissions\fine_tuning_readiness.json
```

It never trains anything and never invents data.

### The submission fields

| Field | What to put |
|---|---|
| `scenario_id` | Already filled (e.g. `S01`) |
| `selected_architecture` | **Exactly one of:** `PROMPT_CONTEXT`, `RAG`, `FINE_TUNING`, `COMBINATION`, `NO_LLM`, `DECISION_DEFERRED` |
| `reasoning` | Why — mention the problem type and the scenario's requirements |
| `rejected_alternative` | **Exactly one architecture label** (same list) — *not a sentence* |
| `key_risk` | The main thing that could go wrong |
| `discovery_question` | The one question whose answer could change your decision |
| `validation_plan` | How you would test it works, with measurable criteria |
| `staged_approach` | `null`, except **required for S06** (it is staged: RAG first, then tune) |

> **The explanation of *why you rejected* an option goes in `reasoning`.**
> `rejected_alternative` accepts only a label. A sentence there is rejected.

## 4. What to test

**Do this first, before opening any answer:** work through all eight scenarios
*yourself* and write your decision on paper. `data\reference_decision_cards.json`
holds the reference answers — **do not read it until you have committed to yours**,
or you learn nothing.

- [ ] `--list` the scenarios and `--show` each. For every one, name the *primary
  problem*: knowledge, behaviour, action, deterministic, or unknown.
- [ ] Fill in and evaluate **all eight** submissions. Note where you disagree with
  the reference — and whether the scenario's *assumptions* justify your view.
- [ ] **S08 is a trap by design.** "Fine-tune our company data" with no requirements.
  The best answer is `DECISION_DEFERRED` — list what you would need to ask.
- [ ] **S06 is staged.** Write out the five stages (RAG baseline → measure → review
  data → tune the *behaviour* → compare combined against baseline).
- [ ] **Evaluate the blank template** and read the error.
- [ ] **Put a sentence in `rejected_alternative`** and read that error.
- [ ] **Open `outputs\run_history\<id>\result.json`** — every dimension shows the
  keywords it matched. Find a dimension where your answer was good but scored low.
- [ ] **Complete the readiness checklist** for S03 (the fine-tuning scenario) with
  *honest* statuses. How many items are genuinely `READY`?
- [ ] Re-read your S01 answer and ask: could this be solved with **no LLM at all**?

## 5. What to expect

`--list`:

```text
S01 | PROMPT_CONTEXT | Small transformation task
S02 | RAG | Changing internal policies
S03 | FINE_TUNING | Consistent specialized output behavior
S04 | RAG | Current product information
S05 | NO_LLM | Deterministic eligibility rule
S06 | COMBINATION | Private knowledge plus specialized behavior
S07 | PROMPT_CONTEXT | Tiny known context
S08 | DECISION_DEFERRED | Missing discovery information
```

**An unedited template fails — by design — with a Python traceback** whose last
line tells you what is missing:

```text
ValueError: Submission has empty required fields: ['discovery_question', 'reasoning',
'rejected_alternative', 'selected_architecture', 'validation_plan']
```

It looks like a crash. It is a validation message.

**A sentence in `rejected_alternative`** gives:

```text
ValueError: rejected_alternative must be one of ['COMBINATION', 'DECISION_DEFERRED',
'FINE_TUNING', 'NO_LLM', 'PROMPT_CONTEXT', 'RAG']; got 'FINE_TUNING was rejected because…'
```

**A valid S01 submission** (I wrote a sensible one — `PROMPT_CONTEXT`, rejecting
`FINE_TUNING`) printed the run folder path and scored **70 / 100**:

| Dimension | Score | Max |
|---|---:|---:|
| Architecture alignment | 25 | 25 |
| Problem identification | 15 | 15 |
| Requirements alignment | 15 | 15 |
| Rejected alternative | 10 | 10 |
| **Key risk** | **0** | 10 |
| **Discovery question** | **0** | 10 |
| **Validation plan** | **0** | 10 |
| Staged approach (n/a) | 5 | 5 |

with `Missing requirements: key_risk, discovery_question, validation_plan` and
generic suggestions ("Strengthen key risk using scenario-specific requirements").

**Why it scored 0 on three dimensions.** The scorer counts whether specific
words appear in your text (case-insensitive substring). For S01 the *risk*
keywords are just `omit` and `format`. My risk — "the model may invent action
items that are not in the notes" — is a genuinely good risk and contains neither
word, so: 0. Likewise for discovery (`fields`, `quality`) and validation
(`representative`, `schema`). The score measures *vocabulary overlap with the
reference*, not the quality of your thinking.

`--assess` on an unedited readiness file lists ten items all `NEEDS_REVIEW`
("Document current evidence."), then a `guidance` line and four `limitations`
(e.g. "Fine-tuning does not keep changing knowledge current").

Tests: `16 passed`.

## 6. If something goes wrong

| You see | Cause | Fix |
|---|---|---|
| `ValueError: Submission has empty required fields` | Template not filled in | Fill every required field |
| `rejected_alternative must be one of […]` | You wrote a sentence | Use a single label; put the reason in `reasoning` |
| `selected_architecture must be one of […]` | A typo or lowercase (`rag` is rejected) | Use the exact upper-case label |
| `rejected_alternative must differ from selected_architecture` | You rejected the thing you chose | Reject a *different* option |
| `ModuleNotFoundError: src` | Not in the folder | `Set-Location "$ai\09_fine_tuning"`, then `& $py -m src…` |
| `S06 submission requires staged_approach` | Left `null` for S06 | Describe the stages; it is required only for S06 |
| Scores seem unfair | They are keyword-based | Read `result.json`; see section 8 |
| Files appear under `outputs\` and `submissions\` | Normal | They are git-ignored |

## 7. Learn more

- **When to fine-tune:** read the provider guidance (OpenAI, Anthropic, Google,
  Hugging Face) on "when to fine-tune vs prompt vs RAG".
- **LoRA / QLoRA / PEFT:** parameter-efficient fine-tuning — how it works and
  why it is cheaper than full tuning. (Hugging Face `peft`, `trl`.)
- **Supervised fine-tuning data:** instruction/response pairs, quality over
  quantity, deduplication, leakage between train and test.
- **Catastrophic forgetting** and **overfitting** in fine-tuning.
- **Distillation** — training a small model on a large model's outputs.
- **Cost models:** training cost vs inference cost vs the cost of a stale model.
- **Decision-record practice:** "Architecture Decision Records (ADRs)" — the
  decision card is a tiny one.
- **When rules beat models:** decision tables, business-rule engines.

## 8. What you might be missing

- **No real fine-tuning happens here**, and none is needed for the exercise. If
  you want to *feel* it, do a tiny LoRA run on a small open model as a
  separate project — but only after you can justify it with Day 09's checklist.
- **The score is a vocabulary match, not an assessment of reasoning.** (Section 5.)
  The README says this itself: *"lexical matching cannot fully judge reasoning
  quality; review the explanation manually as well."* Treat the number as a prompt to
  read the *Missing requirements* list, not as a grade. Two equally good
  answers can score very differently depending on which words they happen to use.
- **The rubric keywords are visible** in `data\architecture_scenarios.json`. You
  *can* read them and write to them. Resist: it defeats the exercise. Write your
  honest answer first, score it, and *then* read why it lost points.
- **The reference answers are not unconditional.** Each scenario lists
  assumptions that could change them. A well-argued answer that differs from the
  reference, citing an assumption, shows more judgement than a lucky match.
- **`rejected_alternative` scores 10 only if it matches the reference's rejected
  option; any other valid, different label gets 5.** So rejecting the "wrong"
  option costs 5 points even if your reasoning is sound.
- **The readiness assessment checks what you *wrote*, not the world.** Marking
  an item `READY` makes it pass; nothing verifies there is a dataset.
- **`S03` and `S06` are the only scenarios where fine-tuning is the answer, and
  both are conditional** on reviewed data. In the real world the proportion is
  smaller still.
- **"Action" problems** (README): when the system must *cause a change*, the
  decision must already name permissions, confirmation, idempotency and audit —
  you will implement exactly these on Days 10 and 12.
- **Privacy and data are decision inputs, not afterthoughts.** Training data may
  contain personal data; RAG documents need access control (Day 13's biggest
  unknown). Both are fields on the card.
- **Fine-tuning is not a fix for hallucination.** Day 07/08 showed a RAG system
  fabricating answers about content it didn't have. Tuning would not cure that.
- **Latency/cost constraints are fields too.** "Measured service targets" appear
  repeatedly; nobody gave you numbers. Real projects must.
- **This is a thinking day.** Rushing it with `--export-template` and guesses
  teaches the least of any day.

## 9. Where this leads

Day 10 begins the *action* side: tools, permissions, confirmation. Day 13's
design card is the same discipline applied to a whole pilot. The habit of writing
"what would change my mind" returns in Day 15 as "what would block a release".
