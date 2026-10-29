# Day 11 — Agents: the ReAct loop

| | |
|---|---|
| **Folder** | `11_agents/` — `main.py`, `enterprise_agent.py`, `evidence/`, `tests/`, `sample_thought_chain.txt` |
| **Commands** | Deterministic: `& $py enterprise_agent.py --demo direct` · Live: `& $py main.py "<request>"` |
| **Needs** | Deterministic demos and tests: nothing. `main.py`: Ollama **and** a model (see setup). |
| **Time** | 1.5–2 hours |
| **Depends on** | Day 10 (the enterprise agent calls Day 10's tools). Contrast with Day 12. |

---

## 1. What you are learning

Day 10 let a model ask for **one** tool. An **agent** lets it ask for a
*sequence* — each step depending on what the last one returned. The pattern is
**ReAct** (Reason + Act):

```text
Thought        "I need the employee's balance first."
Action         get_available_leave_balance
Action Input   {"user_id": "E103"}
Observation    {"leave_balance": 5}            <- produced by YOUR code, not the model
Thought        "I have 5 days; now the festival date."
...
Final Answer   "Demo leave request printed for 2027-01-14."
```

Two programs show two sides:

| Program | What it is |
|---|---|
| `main.py` | A **live** leave assistant. A local model writes the Thought/Action text; Python parses it, runs one of three demo tools, and feeds back the Observation. |
| `enterprise_agent.py` | A bounded loop over **Day 10's real tools** (`lookup_internal_knowledge`, `create_service_request`), with run IDs and recorded traces. `--demo` replays scripted steps, so it needs no model. |

Ideas to take away:

- **The model never executes anything.** It emits *text*; Python parses it,
  validates the tool name and arguments, and runs only functions on an allow-list.
- **Bounded loops.** `MAX_LOOPS = 10`. When the budget is spent the run stops with
  an explicit status instead of looping forever.
- **A missing or malformed action dispatches nothing.**
- **Trust the executor's record, not the model's claim.** The output reports the
  actions that *actually ran*.
- **Business rules live in code.** The loop checks the employee ID, the verified
  balance, the dates, duplicates and past dates itself — the prompt asks for them,
  the code **enforces** them.
- **Agent vs workflow.** An agent chooses its own steps (flexible, variable).
  Day 12 builds the same task as a fixed workflow (rigid, predictable). Compare.

## 2. Setup

For the live program you must choose a model *and set it in the shell*:

```powershell
Set-Location "$ai\11_agents"
$env:OLLAMA_MODEL = "llama3.2:3b"
```

`main.py` does **not** read `.env`. Its built-in default is `qwen3:4b`
(installed, but slow on a CPU — a run can exceed five minutes and look frozen).

Demo data (hard-coded in `main.py`; **not real HR data**):

| Employee | Name | Balance |
|---|---|---|
| `E101` | Priya | 3 |
| `E102` | Rahul | 0 |
| `E103` | Anita | 5 |

| Festival | Date |
|---|---|
| Dussehra | 2026-10-20 |
| Diwali | 2026-11-08 |
| Pongal | 2027-01-14 |
| Holi | 2027-03-04 |
| Onam | 2026-08-26 |

These dates are fixed and **will fall into the past**: a past date is refused
("Never request leave for a date before today"). Dussehra and Onam are already
past as of late October 2026, which makes them handy refusal tests. Later in the
year, use an explicit future `YYYY-MM-DD`.

## 3. Run

### Tests and deterministic demos (no model)

```powershell
& $py -m pytest -q                              # 14 passed

& $py enterprise_agent.py --demo direct         # answers with no tool
& $py enterprise_agent.py --demo two-tools      # chains two lookups
```

The demos print a JSON record: a `run_id`, a `status`, an `answer`, and a
`trace` list of `Thought` / `Action` / `Observation` / `Final Answer` steps.
Saved copies are in `evidence\direct.json` and `evidence\two_tools.json` — those
are the files Day 11–16 submissions refer to. The two-tools demo uses Day 10's
**mock** knowledge backend, and says so; it does not claim live retrieval.

### The live agent

```powershell
& $py main.py "My user ID is E103. Request leave for Pongal."
```

Run with no argument, it uses that same sentence. It prints each loop —
Reason, Action, Observation — and ends with `----- Done -----`.

## 4. What to test

Live agent (run each; **read every loop**, not only the answer):

- [ ] `My user ID is E103. Request leave for Pongal.` — the happy path: festival →
  balance → request → done.
- [ ] `My user ID is E102. Request leave for Diwali.` — balance is 0: it should
  *not* request leave and should say why.
- [ ] `My user ID is E101. Request leave for Diwali, Holi and Pongal.` — three
  days, balance exactly 3. Should it proceed? Now add **Onam**: four days (and one
  already past) — it must refuse *all* of them.
- [ ] `When is Diwali?` — the rules say a date-only question must **not** check a
  balance. Does it obey?
- [ ] `Request leave for Pongal.` — **no employee ID**. It must ask, not guess.
- [ ] `My user ID is E999. Request leave for Pongal.` — unknown user.
- [ ] `My user ID is E103. Request leave for Dussehra.` — a past date.
- [ ] **A loop that goes wrong:** in `main.py` lower `MAX_LOOPS` to 2 and rerun.
  You should see the explicit "Stopped after … loops" message.
- [ ] **Compare two models** on the same request. Count loops and compare the
  quality of each Thought.

Enterprise agent / tests:

- [ ] Read `evidence\two_tools.json` — find each `Observation` and match it to its `Action`.
- [ ] Read the tests — the names say what each guards. In `test_agent.py`: a request
  **without a balance check is rejected**, an **insufficient balance rejects all
  requested days**, an **unregistered tool never executes**, a **guessed employee ID is
  rejected**, and the model **cannot claim success without an action**. In
  `test_enterprise_agent.py`: a direct answer uses **no tool**, a **parallel tool batch
  is rejected before execution**, a **rejected write cannot be reported as submitted**,
  and the **step budget returns an explicit status**. Break one rule in the code and
  watch the matching test fail.
- [ ] Open `outputs\logs\tools.jsonl` — the audit log this agent hands to Day 10's tool
  registry (written next to `enterprise_agent.py`).

## 5. What to expect

**Deterministic demos** (identical every time except the `run_id`):

- `--demo direct` → `status: completed`, `answer: "Hello. I can help with policy
  questions and service requests."`, a trace of just **two** entries — one
  `Thought` and one `Final Answer`, **no tool call**.
- `--demo two-tools` → `status: completed`, **8** trace entries over 3 steps:
  `Thought → Action (lookup_internal_knowledge) → Observation` for the expense
  policy, the same for the travel policy, then a `Thought` and a `Final Answer`.
  The final text is deliberately generic ("Review the two tool observations for
  the source evidence").

**Tests:** `14 passed` in well under a second.

**Live agent — observed with `llama3.2:3b`** (one run; a live model, so expect
variation):

```text
===== Loop 1 =====
Reason:       I need to check the employee's leave balance.
Final Answer: No leave request was printed. Check the dates and leave balance.

----- Done -----
```

The model **named the right first step in its Thought but then skipped the tool
call and jumped straight to a Final Answer** — and an unhelpful one. It finished
in seconds, exit code 0, no error. This is a small model failing to follow the
ReAct format; the program handled it safely (no tool ran, nothing was
"requested"), but the *task was not done*.

By contrast `sample_thought_chain.txt` shows what a successful run looks like:
`get_festival_date` → `get_available_leave_balance` → `create_leave_request` →
Final Answer, ending
`Demo leave request printed for 2027-01-14; nothing was submitted to an HR system.`

With `qwen3:4b`, expect a much better chance of following the format and a much
longer wait.

## 6. If something goes wrong

| You see | Cause | Fix |
|---|---|---|
| Nothing for minutes | `qwen3:4b` on a CPU | `$env:OLLAMA_MODEL = "llama3.2:3b"` |
| `Could not reach Ollama model 'qwen3:4b' at http://127.0.0.1:11434` | Ollama down or model missing | Start Ollama; `ollama pull qwen3:4b` or set another model |
| It "finishes" immediately with a vague answer | The model skipped the tool call (see section 5) | Not a bug in your code. Try a stronger model; re-run |
| `Stopped after 10 loops without a final answer` | The model kept calling tools | The safeguard working; read the last Observation |
| `Invalid request: …` | Input rejected before any model call | Read the message (empty request, etc.) |
| A leave request "worked" for a past date | You edited the checks | The code should refuse; restore it |
| Pongal looks "in the past" next year | Demo dates age | Use an explicit future `YYYY-MM-DD` |
| `ModuleNotFoundError` | Wrong Python | `& $py …` |

## 7. Learn more

- **The ReAct paper** — *ReAct: Synergizing Reasoning and Acting in Language
  Models* (Yao et al., 2022).
- **Agent frameworks:** LangChain / LangGraph, LlamaIndex, OpenAI Agents SDK,
  Anthropic's "Building effective agents" article. Read it *after* you have seen
  how little is needed to build the loop by hand.
- **Planning vs reacting; memory; reflection; multi-agent systems.**
- **Evaluating agents** is much harder than evaluating answers — you must judge
  *trajectories*. (Day 15 and 16 start on this.)
- **Failure modes:** infinite loops, wrong-tool selection, argument hallucination,
  context overflow as the trace grows, prompt injection via tool results.
- **Structured tool calling** (Day 10) versus **text-parsed ReAct** (today): the
  former is more reliable when the model supports it.

## 8. What you might be missing

- **Agents are not automatically better.** The honest summary of Day 11 + Day 12:
  the agent *can* handle varied requests, but its behaviour varies run to run and
  it depends heavily on model quality. For a known task, a deterministic workflow
  (Day 12) is more reliable and far easier to test. Use an agent only when the
  next step genuinely depends on what the last one found.
- **A 3 B model is a poor agent.** What you saw in section 5 is typical. Expect to
  need a larger model — or native tool calling — for reliable results. The safety
  of the *loop* does not depend on the model; the *usefulness* does.
- **The loop is only as safe as its executor.** Everything that makes it safe is
  Python (allow-listed tool names, validation, the step cap) — none of it is the
  prompt. If you move a rule from code into the prompt, you have made it optional.
- **`create_leave_request` only prints.** No HR system is touched, nothing is saved,
  and there is no approval, authentication or persistence (the README states it).
  Day 12 adds approval, idempotency and an audit trail for exactly this reason.
- **Anyone can claim any employee ID.** The user types `E103` and the agent
  believes it. There is no identity.
- **The "balance" is demo data** — change the dictionary and the "truth" changes.
- **Text parsing is brittle.** `parse_step` tolerates minor formatting drift
  (code fences, leading bullets) because small models drift. That tolerance is a
  trade-off: it accepts sloppy output, which is also how a bad action could slip
  through a looser parser. Read the parser and the tests.
- **The prompt contains the date** (`Today's date is {today}`). Change your
  system clock or the prompt and results change. Time is an input to agents.
- **Tokens accumulate.** Each loop appends to the conversation; a long run eats
  the context window (and memory/time).
- **`evidence/` files are recorded, not live.** `enterprise_agent.py --demo` is a
  scripted replay — useful for studying structure, not for judging a model.
- **Notice the `run_id` on every record.** It lets you find one run among many —
  the idea Day 16 generalises into trace IDs.

## 9. Where this leads

Day 12 solves the *same* leave task deterministically — run both and compare
reliability. Day 13 asks when an agent is justified at all. Day 16 shows how to
see *inside* a run like this.
