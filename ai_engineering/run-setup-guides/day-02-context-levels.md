# Day 02 — Context levels: the same question, three ways

| | |
|---|---|
| **Folder** | `02_with_context_level/` — `context_experiments.py`, `mentor_given.py`, `day02_prompt_context_actual_results.md` |
| **Command** | `& $py -m streamlit run 02_with_context_level\context_experiments.py` (from `$ai`) |
| **Needs** | Ollama + a model. `mentor_given.py` also needs the `openai` package (now in requirements). |
| **Time** | 1–2 hours (most of it is running tests and writing observations) |
| **Depends on** | Day 01 — you need your list of observed failures. |

---

## 1. What you are learning

You hold the **model and the question constant** and change only what the model
is *given*. Three versions of the same request:

| Version | The model receives | Idea |
|---|---|---|
| **A — Baseline** | The question only | What does the model do on its own? |
| **B — Improved instructions** | A system prompt + the question | Do rules (don't invent, say when you don't know, ask when unclear) change behaviour? |
| **C — Instructions + context** | The system prompt + *supplied facts* + the question | Does grounding it in text you control make it answer from that text? |

The lesson is not "C is best". It is that **each lever fixes a different
failure**, and each introduces a new one:

- Instructions reduce invented facts but cannot add *knowledge*.
- Context adds knowledge but, if the instructions say "only use the context",
  the model may refuse questions that don't need it (your own results show
  Version C saying "I don't know" to a general-knowledge question).
- Testing is only fair if you control exactly what each version receives.

This is the seed of RAG (Day 07): context supplied automatically instead of by
hand.

## 2. Setup

Same as Day 01 — Ollama running and a model pulled. Choose a fast model:

```powershell
$env:OLLAMA_MODEL = "llama3.2:3b"
```

The Streamlit app loads `.env`, and the shell variable wins. `.env` also holds
`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`; `context_experiments.py` reads those
three but does not use them. Only `mentor_given.py` does.

## 3. Run

### The comparison app

```powershell
Set-Location $ai
& $py -m streamlit run 02_with_context_level\context_experiments.py
```

You get a question box, a **Relevant Context (Version C only)** box and one
button, **Send — Compare All 3 Versions**. It answers A, then B, then C, with
streamed text, one under another.

**Context rule:** the context box is given to Version C *only*. Clear it for
questions that have no context; otherwise C is answering with leftover text
from the previous test. (Your recorded Test 3 shows this symptom: its Version C
answered from facts that were not in the assignment's context.)

### The mentor-supplied starter (command line)

`mentor_given.py` is a skeleton you are meant to **finish**. It calls the model
through the OpenAI-compatible client, pointed at Ollama. It does **not** read
`.env`, so set three variables in the window first:

```powershell
$env:LLM_BASE_URL = "http://localhost:11434/v1"
$env:LLM_API_KEY  = "ollama"          # Ollama ignores it; the client needs something non-empty
$env:LLM_MODEL    = "llama3.2:3b"
Set-Location "$ai\02_with_context_level"
& $py mentor_given.py
```

It asks for a question, runs A, B and C, and asks for context before C. Without
the variables it stops with `RuntimeError: Set LLM_BASE_URL, LLM_API_KEY and LLM_MODEL.`

**Your task in that file:** Version B and Version C each contain
`ADD YOUR INSTRUCTIONS HERE`. Until you replace those placeholders, B and C
send an almost-empty instruction, so they behave like A. Write instructions
from the failures you saw on Day 01.

## 4. What to test

Run these five (they are the ones in your results file), **clearing the context
box between tests**:

| # | Question | Context to give Version C |
|---|---|---|
| 1 | Explain the difference between annual leave and sick leave. | *(none — leave empty)* |
| 2 | Rewrite this leave request professionally: I need leave tomorrow for personal work. | *(none)* |
| 3 | I want to take five days of annual leave. Does this require manager approval? | `Employees receive 20 days of annual leave per calendar year. Leave requests of more than three consecutive days require manager approval.` |
| 4 | What is our company's parental leave policy? | *(none)* |
| 5 | Who should approve my travel request? | *(none)* |

For each, answer in writing:

- [ ] Which version invented something (a company name, a number, a policy)?
- [ ] Which version said "I don't know" — and was that the *right* answer?
- [ ] Did B ask a clarifying question when the question was ambiguous?
- [ ] Did C use **your** context, or something else? (Quote the sentence it relied on.)
- [ ] Did C refuse a question it should have answered (Test 1, 2)? Why?

Then experiment — change one thing at a time:

- [ ] Delete the line `Use only supplied context for internal company information.` from the system prompt (`sys_inst`) and rerun Tests 1–2. Does C stop refusing?
- [ ] Give C **wrong** context (say 10 days instead of 20). Does it follow your context or its own sense of what is true?
- [ ] Give C context that is **irrelevant** to the question. Does it say so?
- [ ] Ask the same question three times. How stable is each version?

## 5. What to expect

Observed on this machine with `llama3.2:3b` (a live model — yours may differ), for
Test 3 with the correct context:

| Version | Answer (abridged) |
|---|---|
| A | "In most cases, taking annual leave without manager approval is not recommended…" followed by a list of *possible scenarios*. Hedged, generic, never says yes or no. |
| B | "Yes, it generally requires manager approval… check your handbook or HR." Shorter and more cautious, but it **states a general rule as if it were policy** — it has no policy. |
| C | "According to the provided context, leave requests of more than three consecutive days require manager approval. Since you are requesting 5 days… it does require manager approval." Correct, and traceable to your text. |

That is the intended A → B → C story: A rambles, B hedges, C answers *from the
evidence*.

Timing is **not** a fair comparison between versions here: the first call after
Ollama has been idle includes loading the model into memory (A took ~48 s, B ~10 s,
C ~6 s in that order). Only compare timings once the model is warm.

From your recorded results (an older run with `qwen2.5:3b`) the patterns to
recognise:

- Test 4: Version A treated an unrelated company (Alibaba) as the user's company
  — an unsupported assumption. B and C said the policy was not provided.
- Test 5: nothing in any version could identify the real approver; B and C gave
  generic possibilities instead of inventing a definite policy, which is *safer*
  but still not an answer. Some questions need data nobody gave the model.
- Tests 1–2: C sometimes answered "I don't know" because the instructions said
  to use only supplied context. That is **over-restriction**, not a bug.

## 6. If something goes wrong

| You see | Cause | Fix |
|---|---|---|
| `RuntimeError: Set LLM_BASE_URL, LLM_API_KEY and LLM_MODEL.` | `mentor_given.py` ignores `.env` | Set the three `$env:` variables (above) |
| `ModuleNotFoundError: No module named 'openai'` | Package missing from an older install | `& $py -m pip install -r "$ai\requirements.txt"` (it is in the file now) |
| Version C answers about 24 leave days when your context said 20 | Old text still in the context box | Clear the box; re-run |
| Connection refused to `localhost:11434/v1` | Ollama is not running | Start Ollama |
| Streamlit shows nothing after you click | Empty question | Type a question first (it warns) |
| Version B == Version A in `mentor_given.py` | You have not replaced `ADD YOUR INSTRUCTIONS HERE` | Write real instructions |

## 7. Learn more

- **Prompt engineering basics:** role, task, constraints, output format,
  examples (few-shot). Search "few-shot prompting".
- **Hallucination types:** invented facts vs unsupported inference vs
  instruction-ignoring. Try to classify each failure you recorded.
- **System prompt hierarchy and why instructions leak:** read about prompt
  injection (it returns on Days 07 and 10).
- **Grounding vs retrieval:** supplying context by hand (today) vs automatically
  (Day 07).
- **Evaluating prompts:** a prompt change is a code change. Keep the test
  questions fixed and diff the answers — a tiny version of Day 15.

## 8. What you might be missing

- **Your results file has an open item.** `day02_prompt_context_actual_results.md`
  ends with *"Recommended retest before submission"*: Test 3's recorded Version
  C used the wrong context (it mentions 24 days and 16 used, not your 20-day
  context), so it is **not valid evidence yet**. Re-run it with exactly the
  context in the table above and update the file. The result shown in section 5
  is what a correct run looks like.
- **Model mismatch.** The results file says `qwen2.5:3b`; `.env` now says
  `qwen3:4b`. Different models give different outputs, so a fresh run will not
  match the recorded text. Note the model name next to every result you keep.
- **The system prompt contains a joke line** — *"wrong answer might cause global
  warming."* It was likely added to test whether emphatic wording changes
  behaviour. Try removing it. Real prompts should state real consequences
  ("incorrect leave advice affects pay"), not invented ones.
- **There is no real retrieval.** "Context" is whatever you type. If you forget
  to clear it, you are testing your own mistake. Day 07 automates the supplying.
- **Prompts are not a security boundary.** "Use only supplied context" is a
  request, not a rule. Nothing stops the model ignoring it.
- **Version C is not "the answer".** It is best only when the context contains
  the answer. With missing or wrong context it can be confidently wrong, and it
  trusted the context you gave it even if you gave it something false.
- **Sample size.** Five questions on one small model is an illustration, not
  proof that instructions or context "work".
- **`context_experiments.py` contains a lot of commented-out code** — earlier
  attempts at the same thing. That is normal exploration; do not copy the
  commented parts into anything you submit.
- **Streamed output** (`stream=True`) is nicer to watch but is shown in the UI
  only; it is not saved. Copy results out as you go.

## 9. Where this leads

Day 03 stops asking "is the answer good?" and asks "is the answer *usable by
code*?" — forcing a fixed JSON shape. Day 07 replaces your hand-typed context
with retrieved context.
