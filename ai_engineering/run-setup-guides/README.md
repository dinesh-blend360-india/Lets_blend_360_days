# AI Engineering — Learner's Guides, Days 01–16

One guide per day. Each tells you what you are learning, how to set up, how to
run, what to test, what you should see, where people get stuck, what to read
next, and what is easy to miss.

**Read this page once, then go day by day.** It holds everything that is the
same for every day, so the day guides do not repeat it.

Every command and every "what to expect" block in these guides was run on this
repository (Windows 11, Python 3.11.9, CPU only, Ollama with `llama3.2:3b` and
`qwen3:4b`). Where output comes from a live model it says so, because a model
can answer differently for you.

---

## 1. The map

| Day | Guide | You build / study | Needs Ollama? | Needs Day 06 index? |
|---|---|---|---|---|
| 01 | [day-01-simple-genai.md](day-01-simple-genai.md) | A chat box over a local model | Yes | No |
| 02 | [day-02-context-levels.md](day-02-context-levels.md) | Same question, three levels of context | Yes | No |
| 03 | [day-03-structured-output.md](day-03-structured-output.md) | Validated JSON output with bounded retry | Yes (app) / No (tests) | No |
| 04 | [day-04-task-api.md](day-04-task-api.md) | A REST API with a database, built with an AI assistant | No | No |
| 05 | [day-05-document-chunking.md](day-05-document-chunking.md) | Parsing and chunking documents | No | No |
| 06 | [day-06-embeddings-retrieval.md](day-06-embeddings-retrieval.md) | Embeddings, vector search, retrieval metrics | No (local BGE) | **Builds it** |
| 07 | [day-07-rag.md](day-07-rag.md) | Retrieval-augmented generation with citations | Live runs only | Live runs only |
| 08 | [day-08-rag-evaluation.md](day-08-rag-evaluation.md) | Evaluating RAG stage by stage | Yes | Yes |
| 09 | [day-09-architecture-decisions.md](day-09-architecture-decisions.md) | Prompt vs RAG vs fine-tuning vs no LLM | No | No |
| 10 | [day-10-tool-calling.md](day-10-tool-calling.md) | Tools, permissions, human confirmation | Live runs only | Optional (`mock` works) |
| 11 | [day-11-agents.md](day-11-agents.md) | A bounded ReAct agent loop | Live runs only | No |
| 12 | [day-12-reliable-workflows.md](day-12-reliable-workflows.md) | A deterministic, auditable workflow | No | No |
| 13 | [day-13-agentic-engineering.md](day-13-agentic-engineering.md) | A pilot design card and reflection | No | No |
| 14 | [day-14-mcp.md](day-14-mcp.md) | A local MCP server and client | No | No |
| 15 | [day-15-evaluations.md](day-15-evaluations.md) | Golden cases, hard gates, an LLM judge | Live / judge only | No |
| 16 | [day-16-observability.md](day-16-observability.md) | Tracing, faults, masking, one diagnosed fix | Live diagnosis only | No |

**How the days depend on each other**

```text
05 chunk ─► 06 embed + index ─► 07 RAG ─► 08 evaluate RAG
                                 │
10 tools ──┬─► 11 agents ─► 12 reliable workflow ─► 13 design card
           ├─► 14 MCP
           └─► 15 evaluations ─► 16 observability
```

Days 01–04, 09, 12 and 13 stand alone. Do 05 → 06 → 07 → 08 in order the first
time: Days 07 and 08 cannot run live until Day 06's index exists, and that index
is deliberately **not** in git.

Longer, older walkthroughs for Days 04–07 are kept in this folder
(`day_4 …`, `day_5 …`, `day_6 …`, `day_7 …`). The day guides above are the
current, consistent ones; the older files go deeper on Days 05–07 if you want a
slower, screenshot-style read.

---

## 2. One-time machine setup

Do this once. About 15–30 minutes, mostly downloads.

### 2.1 What you need

| Need | Detail |
|---|---|
| Windows 11 + PowerShell | The commands in these guides are PowerShell. Bash users: swap `$env:NAME = "x"` for `export NAME=x` and `\` for `/`. |
| Python **3.11 or newer** | Check with `python --version`. This repo was verified on 3.11.9. Day 04's `run.bat` refuses anything older. |
| Ollama | Local model server. Download from <https://ollama.com/download>. |
| Disk | ~5 GB free: the shared virtual environment (PyTorch is large), `llama3.2:3b` ≈ 2.0 GB, `qwen3:4b` ≈ 2.5 GB, the BGE embedding model ≈ 130 MB. |
| RAM | 8 GB works for the 3–4 B models; 16 GB is more comfortable. No GPU is needed, but without one every model call is slow (see 2.6). |
| Internet | Only to install packages and download models. Afterwards everything runs offline. |
| Git | You are in a git repository. `.env` is ignored, so your configuration is never committed. |

### 2.2 Three variables used in every guide

Open PowerShell and run these first in **every new window** (they do not
persist). Change `$repo` if your clone lives somewhere else.

```powershell
$repo = "C:\workspace\IDC-on-boarding-training\Lets_blend_360_days"
$ai   = "$repo\ai_engineering"
$py   = "$repo\venv\Scripts\python.exe"
```

From now on `& $py` means "run the shared Python", and `$ai` is the folder that
contains `01_…` to `16_…`. Using absolute paths means a command works no matter
which folder you are in, which removes the most common beginner error
("No such file or directory").

> **Why `& $py` and not just `python`?** Plain `python` may be a different
> Python from the one holding your packages. That produces
> `ModuleNotFoundError` even though you "already installed it". The shared
> interpreter is the only one these guides rely on.

### 2.3 Create the shared virtual environment

There is **one** `venv` at the repository root, shared by all 16 days.

```powershell
Set-Location $repo
python -m venv venv
& $py -m pip install --upgrade pip
& $py -m pip install -r "$ai\requirements.txt"
```

If the folder already exists and `& $py --version` works, skip this and just run
the `pip install` line — it is safe to repeat.

Check it:

```powershell
& $py --version                       # Python 3.11.x
& $py -c "import streamlit, ollama, pydantic, fastapi, sentence_transformers, mcp, openai; print('imports OK')"
```

If a command reports `Activate.ps1 cannot be loaded because running scripts is
disabled`, you do not need activation at all — `& $py` works without it.

### 2.4 Install Ollama and pull two models

After installing Ollama it runs in the background (look for the llama icon in
the system tray). Then:

```powershell
ollama pull llama3.2:3b      # ~2.0 GB. Fast on CPU. Use this to get days finished.
ollama pull qwen3:4b         # ~2.5 GB. The repository default, but a "thinking" model: slow on CPU.
ollama list                  # both should be listed
```

Confirm the server answers:

```powershell
& $py -c "import ollama; print([m.model for m in ollama.Client(host='http://localhost:11434').list().models])"
```

Expected: `['llama3.2:3b', 'qwen3:4b']`.

**Which model should you use?** `qwen3:4b` is set as the default in `.env`, but
it "thinks" before answering. On a CPU a single question can take several
minutes, and the multi-step days (11, 12, 15, 16) look frozen. Pick
`llama3.2:3b` while learning and switch to `qwen3:4b` when you want to compare:

```powershell
$env:OLLAMA_MODEL = "llama3.2:3b"     # affects only this PowerShell window
```

A model name in a shell variable **beats** the one in `.env`.

### 2.5 The `.env` file

Create `ai_engineering\.env`. It is git-ignored; never commit it and never paste
real secrets into it. It is plain `NAME=value` lines.

```ini
# Which local model the apps use, and where Ollama is listening
OLLAMA_MODEL="qwen3:4b"
OLLAMA_HOST="http://localhost:11434"

# Day 02 mentor_given.py talks to Ollama through its OpenAI-compatible address.
# Ollama ignores the key but the client library insists on a non-empty one.
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL="qwen3:4b"

# Day 06 embeddings
EMBEDDING_MODEL_ID=BAAI/bge-small-en-v1.5
EMBEDDING_BATCH_SIZE=32
EMBEDDING_NORMALIZE=true
EMBEDDING_USE_QUERY_INSTRUCTION=true

# Day 07 / 08 / 10: where Day 06 put the index (relative to 07_rag etc.)
DAY06_INDEX_DIR=..\06_embedding_and_retrieval\outputs\embeddings\employee_policy_md_structure
```

**This is the most common silent problem in the repository: only some code
reads `.env`.** Verified by searching the code for `load_dotenv()`:

| Reads `ai_engineering\.env` itself | Reads **only real shell variables** (ignores `.env`) |
|---|---|
| Day 01 app, Day 02 `context_experiments.py`, Day 03 app, Day 04 assignment copy, the Streamlit hub | Day 02 `mentor_given.py`, Day 06, Day 07, Day 08, Day 10, Day 11 `main.py`, Day 16 |

So `OLLAMA_MODEL="qwen3:4b"` in `.env` is honoured by the Streamlit apps and the
hub, but **ignored** when you run `python -m src.assistant` (Day 10) or
`python main.py` (Day 11) from a terminal. Those fall back to a default baked
into the code, and the defaults are not the same everywhere:

| Run from a terminal with no `OLLAMA_MODEL` set | Falls back to | Installed here? |
|---|---|---|
| Day 07 `rag.pipeline`, Day 08 evaluator | `llama3.2:3b` (temperature 0, 256-token cap) | yes |
| Day 11 `main.py` | `qwen3:4b` | yes (slow) |
| **Day 10 `src.assistant`** | **`qwen2.5:3b`** | **no — fails with `MODEL_UNAVAILABLE`** |
| Day 15 `run_live.py`, Day 16 live runner | none — `--model` is required | — |

**The fix is one line per PowerShell window**, before any live run:

```powershell
$env:OLLAMA_MODEL = "llama3.2:3b"
```

Other things that catch people:

- **A variable already set in your shell wins** over `.env` (for the code that
  does read it).
- **Quotes** around values are stripped by some code and not others. When in
  doubt, no quotes.
- Each day that needs more has a `.env.example` (Days 06, 07, 08, 10) listing
  its own variables. Copy it to `.env` only if you want those values; the paths
  inside were corrected to the zero-padded folder names (`06_…`, `07_…`).

### 2.6 Prove everything works

Run the whole test sweep once. It uses mocks, so it needs no model and no
network, and takes about a minute.

```powershell
$days = "03_structured_output","04_enhanced_dev_codex","06_embedding_and_retrieval","07_rag",
        "08_rag_evaluation","09_fine_tuning","10_tool_calling","11_agents",
        "12_reliable_agentic_workflows","13_agentic_engineering","14_mcp","15_evaluations","16_observability"
foreach ($d in $days) {
  Push-Location "$ai\$d"
  Write-Host "== $d" -ForegroundColor Cyan
  & $py -m pytest -q --no-header -p no:cacheprovider
  Pop-Location
}
```

Expected: every folder ends with `N passed`; three report `1 skipped`
(Days 07, 08, 10 — those are the live-model tests, off on purpose). Day 03 also
prints one `PydanticDeprecatedSince20` warning, which is harmless. In total:
**299 passed, 3 skipped**.

If any folder fails here, fix it before starting that day — the cause is usually
a missing package, and the day guide's "If something goes wrong" will not help
if the environment itself is broken.

### 2.7 How slow is "slow"?

Measured on this machine, CPU only:

| Task | llama3.2:3b | qwen3:4b |
|---|---|---|
| One short answer (Day 01) | a few seconds | tens of seconds to minutes |
| One agent run (Day 11) | seconds | minutes — can exceed 5 |
| One live RAG question (Day 07) | ~10–35 s including embedding model load | slower |
| The first embedding build (Day 06) | downloads ~130 MB, then seconds | — |

Hitting a timeout is not a bug in your code. Lower the cost: use the 3B model,
shorten prompts, or raise a `--timeout` where one exists.

---

## 3. How each guide is laid out

1. **At a glance** — folder, command, whether it needs Ollama, how long.
2. **What you are learning** — the idea, in plain words.
3. **Setup** — anything beyond the one-time setup above.
4. **Run** — the exact commands.
5. **What to test** — a checklist of things to *try*, not just run.
6. **What to expect** — real output, so you can tell "working" from "broken".
7. **If something goes wrong** — the failures we actually hit.
8. **Learn more** — what to read or build next.
9. **What you might be missing** — gaps, traps and honest limits. Read this one.
10. **Where this leads** — how the day feeds later days.

---

## 4. Habits that will save you

- **A model answer is data, not truth.** Run important questions more than once;
  small models give different answers on different runs and sometimes the same
  wrong answer every run (Day 07 shows this).
- **Read the whole output, not the last line.** Several days report success in
  the last line while an earlier field says otherwise.
- **Keep evidence.** Several days ask you to submit outputs. Save the JSON, not
  a screenshot. The Day 11–16 documents refer to specific `evidence/` files.
- **Run the tests before you change code, and after.** A passing suite before
  your change is what makes a failing one after it meaningful.
- **Know which files a command overwrites.** Some commands rewrite files that git
  tracks (Day 15's `run_baseline.py` changes a request ID every run). Check
  `git status` after you run things; revert noise with
  `git checkout -- <path>`.
- **Use only fake data.** Every dataset here is invented. Do not paste real
  employee, customer or credential data into any prompt, trace or evidence file.
- **Commit often, small.** Never commit `.env`, a `venv`, or an API key.

---

## 5. Glossary

| Term | Meaning here |
|---|---|
| **LLM** | A large language model that predicts text. Here, a small one running locally via Ollama. |
| **Token** | A piece of text (~¾ of a word). Models read and are limited by tokens, not characters. |
| **Context window** | How many tokens a model can consider at once. Day 01–03 cap it at 2048 (`num_ctx`) to save memory. Text beyond it is silently dropped. |
| **System / user message** | The system message sets rules for the model; the user message is the request. |
| **Temperature** | Randomness. `0` is as repeatable as a model gets. Day 03 uses 0. |
| **Hallucination** | A fluent, confident answer that is not true or not supported. |
| **Structured output** | Making a model return data in a fixed shape (JSON) instead of free text. |
| **Schema / validation** | A written contract for data, and the code that rejects data that breaks it. |
| **Chunk** | A slice of a document sized for search and prompting. |
| **Embedding** | A list of numbers (here 384) representing meaning, so similar text lands close together. |
| **Cosine similarity** | How close two embeddings point. 1.0 is identical direction. |
| **Top-k** | "Return the k best matches." |
| **Recall@k / MRR** | Did the right chunk appear in the top k? / How high did it rank, on average. |
| **RAG** | Retrieve relevant text first, then make the model answer *from it*. |
| **Grounded / citation** | An answer tied to specific source text it came from. |
| **Abstain** | Saying "I don't have enough evidence" instead of guessing. |
| **Prompt injection** | Text in a document or message that tries to give the model orders. |
| **Tool call** | The model asks the *application* to run a named function. The model never runs it. |
| **ReAct** | A loop of Thought → Action → Observation, repeated until a Final Answer. |
| **Idempotent** | Doing it twice has the same effect as doing it once. Essential for retries. |
| **Audit log** | An append-only record of what was done and by whom. |
| **MCP** | Model Context Protocol: a standard way for an app to discover and call tools on a server. |
| **Golden case** | A saved test question with a known expected behaviour. |
| **Hard gate** | A check that blocks a release if it fails — no partial credit. |
| **LLM-as-judge** | Using a model to grade another model's output. Needs human calibration. |
| **Trace / span (run)** | One request's record, as a tree of timed steps. |
| **PII masking** | Replacing personal data with placeholders *before* it is stored. |
| **FDE** | Forward-Deployed Engineer: the person who makes this work for a real customer. The "FDE lens" in several days asks what you would check before shipping. |

---

## 6. Problems that appear on any day

| Symptom | Cause and fix |
|---|---|
| `ModuleNotFoundError: No module named 'x'` | You are not using the shared interpreter. Run `& $py …`, and re-run `& $py -m pip install -r "$ai\requirements.txt"`. |
| `❌ Ollama not reachable` / `Unable to connect to Ollama` | Start Ollama (tray icon, or `ollama serve`). Check `OLLAMA_HOST` matches `http://localhost:11434`. |
| `model 'x' not found` | `ollama pull x`, then `ollama list`. Check the exact name, including the tag after `:`. |
| A run seems frozen | Probably `qwen3:4b` thinking on a CPU. Wait, or `$env:OLLAMA_MODEL = "llama3.2:3b"`. |
| `No such file or directory` / `can't open file` | You are in the wrong folder or used a relative path. Use `Set-Location "$ai\<day folder>"` first. |
| `Activate.ps1 cannot be loaded…` | Skip activation. `& $py` needs none. |
| A test says `skipped` when you expected it to run | It is gated by an environment variable (Days 07, 08, 10 — see their guides). |
| `UnicodeEncodeError` printing JSON in the terminal | `$env:PYTHONIOENCODING = "utf-8"` in that window. |
| `Port 8501 is already in use` | An earlier Streamlit is still running. Close it, or add `--server.port 8502`. |
| The browser page did not open | Streamlit prints a `Local URL:` — open it manually (usually <http://localhost:8501>). |
| Hugging Face prints `unauthenticated requests` | A warning, not an error. Downloads still work, only more slowly. |
| Hugging Face `FutureWarning` lines | Harmless noise from the library version. |
| `git status` shows files you did not edit | A command rewrote a tracked output. Review with `git diff`, revert with `git checkout -- <file>`. |
| Pasting a command breaks on the second line | In PowerShell the line-continuation character is a backtick `` ` ``, not `\`. It must be the **last** character on the line. |

---

## 7. Gaps that apply to the whole repository

None of these are mistakes — they are the honest limits of a training project.
A learner who knows them avoids over-claiming.

- **The knowledge base is tiny and fake.** One expense-and-travel policy
  (11 chunks). Leave, parental leave and sick leave questions are *absent* from
  it — Days 07 and 08 show what that does.
- **Mock data stands in for real systems.** Day 10's knowledge can be a mock
  file, Days 11–12 use hard-coded leave balances and festival dates, and "service
  requests" are JSON files on disk. No HR or ticketing system is ever called.
- **There is no real identity or authorization anywhere.** "Permission" is a
  flag an operator sets (`--allow-write`). Day 13 names this as the biggest
  unvalidated assumption.
- **Small models make mistakes you will see.** Treat results as illustrations of
  *method*, not as quality benchmarks. One run is an anecdote.
- **Everything runs on one machine, one user.** No concurrency, scaling,
  deployment, monitoring or cost work — the days that mention these say so.
- **Scoring in Days 08, 09 and 15 is largely keyword-based.** It is transparent
  and reproducible, but it can fail a correct answer and pass a weak one.
- **Dates in demo data age.** Festival dates fall into the past; use an explicit
  future `YYYY-MM-DD` when a day allows it.
- **No CI, no pre-commit hooks, no lint config.** Quality depends on you running
  the tests.

If you only remember one thing: **a passing test, a valid citation and a
confident answer are three different claims, and none of them proves the answer
is true.**
