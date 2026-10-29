# Day 08 — Evaluating RAG, stage by stage

| | |
|---|---|
| **Folder** | `08_rag_evaluation/` — `src/`, `tests/`, `test_inputs/`, `outputs/` |
| **Commands** | `& $py -m src.evaluator` · `& $py -m src.evaluator --case-id receipt_numeric_threshold` |
| **Needs** | Ollama + the Day 06 index for real runs. The unit tests need neither. |
| **Time** | 1–1.5 hours (a full run takes a minute or two with `llama3.2:3b`) |
| **Depends on** | Day 07 (it calls Day 07's pipeline) and Day 06 (the index) |

---

## 1. What you are learning

Day 07 builds a RAG pipeline. Day 08 asks: **how do you know it works?** and,
more usefully, **when it fails, which stage failed?**

A RAG answer can be wrong for five different reasons, and each needs a different fix:

| Stage | The question | Failure means |
|---|---|---|
| `CORPUS_COVERAGE` | Does the knowledge base even contain the answer? | You need *documents*, not code or prompts |
| `RETRIEVAL` | Did search return the right chunk? | Fix chunking, embeddings, k |
| `CONTEXT_CONSTRUCTION` | Did the right chunk reach the prompt? | Fix the context budget/builder |
| `GENERATION_GROUNDING` | Did the model use the evidence correctly? | Fix the prompt or the model |
| `CITATION_MAPPING` | Do the cited IDs exist and match? | Fix citation handling |
| `RUNTIME_OR_CONFIGURATION` | Could the pipeline run at all (Ollama, model)? | Fix your environment — this is not a quality result |

Each case is recorded with the question, what was retrieved, the exact context
sent, the answer, the citations and a verdict — so you can *diagnose*, not just
see a red mark. You also learn:

- **Evidence labels.** For answerable cases you state which chunk *should* be
  retrieved (`expected_relevant_chunk_ids`); only then can retrieval be scored.
- **Honest labelling of unanswerable cases.** If the corpus lacks the answer, the
  case is **not scorable** and is reported `BLOCKED_MISSING_SOURCE` — you must
  not "pass" or "fail" a model for a document nobody gave it.
- **Statuses:** `PASS`, `FAIL`, `BLOCKED_MISSING_SOURCE`,
  `SKIPPED_RUNTIME_UNAVAILABLE`, `NEEDS_MANUAL_REVIEW`.
- **Immutable history.** Each run goes in its own timestamped folder and never
  overwrites an earlier one.
- **The limits of keyword checks.** Rules like "the answer must contain
  *receipt*" are reproducible but shallow.

## 2. Setup

```powershell
Set-Location "$ai\08_rag_evaluation"
$env:OLLAMA_MODEL = "llama3.2:3b"
```

Prerequisites for a real run:

1. Ollama running with a model.
2. **The Day 06 index must exist** (Day 06, step 3.2). Without it the run cannot retrieve.

The defaults need no configuration — Day 08 finds `..\07_rag` and Day 06's
structure index by relative path. Override only if you moved things:

```powershell
$env:DAY07_PROJECT_DIR = "..\07_rag"
$env:DAY06_INDEX_DIR   = "..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure"
```

Remember: **this day does not read `.env`.** The model comes from
`$env:OLLAMA_MODEL`, or the default `llama3.2:3b`.

## 3. Run

```powershell
# 3.1 Unit tests — mocked, no model, no index (17 pass, 1 skipped)
& $py -m pytest -m "not integration" -q

# 3.2 The full evaluation: all 8 cases against the live pipeline
& $py -m src.evaluator

# 3.3 One case
& $py -m src.evaluator --case-id receipt_numeric_threshold

# 3.4 Print without creating a run folder
& $py -m src.evaluator --case-id receipt_numeric_threshold --no-write

# 3.5 The one live integration test (off unless you opt in)
$env:RUN_DAY08_INTEGRATION = "1"
& $py -m pytest tests\test_integration.py -m integration -v
```

Other options: `--cases-file <json>` for your own cases, `--output-dir <folder>`
to write elsewhere.

Each run creates a folder `outputs\runs\<UTC-timestamp>\` with `results.json`
(everything, including the exact context sent to the model), `results.csv`
(one row per case), `summary.md` and `run_manifest.json`; plus
`outputs\summaries\latest_summary.md` and `outputs\failure_analysis\failure_analysis.md`.
All of these are **git-ignored** because they contain retrieved document text.

## 4. What to test

- [ ] **Read the eight cases** in `test_inputs\day08_common_cases.json`. Which are
  `SUPPORTED_IN_CORPUS` and which `MISSING_FROM_CORPUS`?
- [ ] **Run the full evaluation, then open `results.csv` and read the `answer`
  column** — not just the status. This is the single most important step today.
- [ ] **Open the `FAIL` case** (`receipt_numeric_threshold`). Read its
  `answer_checks` block and find *why* it failed.
- [ ] **Compare two models**: run once with `llama3.2:3b`, once with
  `qwen3:4b`. Compare the `answer` and `insufficient_evidence` columns.
- [ ] **Run it twice** with the same model. Are the runs identical? (Each gets its
  own folder; diff the two `results.csv`.)
- [ ] **Add a case.** Copy one entry in the cases file, change the question, set
  `corpus_precondition` honestly, and re-run.
- [ ] **Break it on purpose, two ways.** (1) `$env:OLLAMA_MODEL = "no-such-model"` → a
  clean `SKIPPED_RUNTIME_UNAVAILABLE` (stage `RUNTIME_OR_CONFIGURATION`) with the
  message *"Ollama model 'no-such-model' is unavailable… run 'ollama pull …'"*.
  (2) `$env:DAY06_INDEX_DIR = "C:
ope\missing"` → **no tidy status**: a raw
  `FileNotFoundError … metadata.json` traceback. Compare how differently the two
  are handled and ask which one a user should see.
- [ ] **Read `outputs\failure_analysis\corpus_gap_analysis.md`** — the committed
  audit of what the corpus does and does not contain.

## 5. What to expect

Observed with `llama3.2:3b` on this machine (a live model — yours can differ):

```text
Cases evaluated: 8
- PASS: 0
- FAIL: 1
- BLOCKED_MISSING_SOURCE: 7
```

| Case | Corpus | Status | Stage |
|---|---|---|---|
| annual_leave_direct | missing | BLOCKED_MISSING_SOURCE | CORPUS_COVERAGE |
| vacation_leave_paraphrase | missing | BLOCKED_MISSING_SOURCE | CORPUS_COVERAGE |
| five_consecutive_days_approval | missing | BLOCKED_MISSING_SOURCE | CORPUS_COVERAGE |
| international_trip_approvals | missing | BLOCKED_MISSING_SOURCE | CORPUS_COVERAGE |
| **receipt_numeric_threshold** | **supported** | **FAIL** | **GENERATION_GROUNDING** |
| parental_leave_unsupported | missing | BLOCKED_MISSING_SOURCE | CORPUS_COVERAGE |
| annual_vs_parental_leave | missing | BLOCKED_MISSING_SOURCE | CORPUS_COVERAGE |
| sick_leave_exact_terminology | missing | BLOCKED_MISSING_SOURCE | CORPUS_COVERAGE |

**Zero passes is expected.** Seven of eight questions are about annual, parental
or sick leave, which the 11-chunk expense-and-travel corpus simply does not
contain. They are *blocked*, not failed. Do not read "0 PASS" as a broken
evaluator.

**Why the one answerable case FAILed — and why that is instructive.** Retrieval
was right (`expected_evidence_found: true`), the evidence reached the context
(`expected_evidence_in_context: true`), the citation was valid, and the model's
answer was **`"500"`** — which is *correct*. It failed only because the keyword
rule requires the answer to contain the word **"receipt"**:

```json
"answer_checks": { "behavior_ok": true, "required_terms_present": false,
                   "missing_required_terms": ["receipt"],
                   "semantic_grounding": "NEEDS_MANUAL_REVIEW" }
```

A `FAIL` can mean "the check is stricter than the answer needed to be". Always
open the record before concluding anything.

**What the answers actually were** (this is what the status column hides):

| Case (all labelled BLOCKED) | `insufficient_evidence` | Answer the model gave |
|---|---|---|
| annual_leave_direct | True | `not available` — abstained ✔ |
| vacation_leave_paraphrase | **False** | **`30`** + a citation |
| five_consecutive_days_approval | **False** | **`true`** + a citation |
| international_trip_approvals | **False** | **`The manager who approved the request`** + a citation |
| parental_leave_unsupported | **False** | **`30`** + a citation |
| annual_vs_parental_leave | True | `Insufficient evidence` ✔ |
| sick_leave_exact_terminology | **False** | **`Before submitting, check each item`** + a citation |

**Five of the seven unanswerable questions received a confident, cited,
fabricated answer.** The `"30"` is the expense-claim deadline, offered as a leave
entitlement. The evaluator labels all seven `BLOCKED_MISSING_SOURCE` — correctly,
because it cannot score a case with no source — which means **the summary table
makes a system that hallucinates look the same as one that behaves.** Only
reading the answers reveals it.

`MRR` in the manifest is `1.0`; that is computed over the **one** labelled case.

Tests: `17 passed, 1 skipped`. The integration test, with the opt-in variable and
a live model, takes about 40 s and passes.

## 6. If something goes wrong

| You see | Cause | Fix |
|---|---|---|
| `FileNotFoundError: Day 07 project not found` | The default path pointed at `7_rag` before it was corrected to `07_rag` | Confirm `..\07_rag` exists, or set `$env:DAY07_PROJECT_DIR = "..\07_rag"` |
| Every case `SKIPPED_RUNTIME_UNAVAILABLE` | Ollama down, or the model name is not installed (the message names it) | Start Ollama; `$env:OLLAMA_MODEL = "llama3.2:3b"` |
| `FileNotFoundError: …\metadata.json` (a traceback, no status) | The Day 06 index does not exist or `DAY06_INDEX_DIR` is wrong | Build the index (Day 06 step 3.2) |
| Integration test shows `skipped` | Needs `$env:RUN_DAY08_INTEGRATION = "1"` | Set it |
| Tests pass but real run fails | Tests are mocked | Check Ollama, the index, and the model name |
| Run is very slow | `qwen3:4b` | Use `llama3.2:3b` |
| You cannot find the results | They are under `outputs\runs\<timestamp>\` | `Get-ChildItem outputs\runs` |

## 7. Learn more

- **RAG evaluation frameworks:** RAGAS, TruLens, DeepEval, ARES — read what they
  measure (faithfulness, answer relevance, context precision/recall) and compare
  with Day 08's staged view.
- **Retrieval metrics:** Recall@k, MRR, nDCG (Day 06 gave the first two).
- **LLM-as-judge** for groundedness — and its weaknesses (Day 15 covers this).
- **Faithfulness vs correctness vs relevance** — three different properties.
- **Abstention and calibration:** how to make a system say "I don't know" reliably;
  confidence thresholds; "refusal" training.
- **Dataset design:** how many cases are enough? Stratify by type (direct, paraphrase,
  multi-part, unanswerable, adversarial).
- **The "lost in the middle" effect** when many chunks are stuffed in a prompt.

## 8. What you might be missing

- **Read the answers, not the status.** (Section 5.) A green or "blocked" summary
  can hide fabricated answers. When you present Day 08 results, report both:
  *"7 cases were unscorable because the corpus lacks the source; of those, the
  model abstained in 2 and fabricated an answer in 5."*
- **The evaluator cannot grade the unanswerable cases at all.** It is honest about
  that, but it means the most important behaviour — *refusing to guess* — is
  **not automatically measured here**. Day 15 builds a check for it.
- **The only answerable case is 1 in 8.** One data point cannot support any claim
  about quality. To get a meaningful evaluation you need many more *answerable*
  cases — which means more documents.
- **Close the loop yourself:** write a short fake leave policy, drop it into Day
  05's samples, re-chunk, rebuild the Day 06 index, add the new chunk IDs as
  `expected_relevant_chunk_ids`, set those cases to `SUPPORTED_IN_CORPUS`, and
  rerun. That is the real "fix" for six of the seven blocked cases — and it is a
  *data* fix, not a code or prompt fix. This is also a good portfolio exercise.
- **Keyword rules misjudge.** `required_terms_present` failed a correct `"500"`.
  The opposite also happens: a wrong answer containing the right words passes.
  Semantic grounding is always flagged `NEEDS_MANUAL_REVIEW` for this reason.
- **Evaluation inherits every upstream weakness.** Bad chunks (Day 05) or weak
  embeddings (Day 06) show up here as retrieval failures; the stage labels are how
  you tell.
- **Run history is local and ignored by git.** Results are not committed; copy
  the folder you want to keep as evidence.
- **The model name is not recorded anywhere in the run output.** `run_manifest.json`
  stores paths, `top_k`, the context budget and the index details — but **no model
  name**. Write down which model produced each run, or you will not be able to
  reproduce or explain it later.
- **`outputs\summaries\implementation_status.md`** and the corpus-gap document are
  committed *records* written when the day was built; they describe that run, not
  yours.
- **Run-to-run variation** exists even at temperature 0 when models change or
  Ollama updates. Pin and record the model version for any result you cite.

## 9. Where this leads

Day 15 generalises this idea — golden cases, deterministic checks, hard gates and
a judge — to the whole assistant. The staged-failure thinking here is exactly
what Day 16's traces give you for every request.
