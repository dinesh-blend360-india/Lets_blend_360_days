# Day 01 — Simple GenAI: a chat box over a local model

| | |
|---|---|
| **Folder** | `01_simple_genAI/` — `app.py`, `results.txt` |
| **Command** | `& $py -m streamlit run 01_simple_genAI\app.py` (from `$ai`) |
| **Needs** | Ollama running + one model pulled. No internet after that. |
| **Time** | 30–45 minutes |
| **Depends on** | Nothing. This is the starting point. |

Run the three variables from the [shared setup](README.md#22-three-variables-used-in-every-guide) first.

---

## 1. What you are learning

- **A language model is a function.** Messages go in, text comes out. Everything
  later in this course — RAG, agents, tools — is that same call wrapped in
  more code.
- **Ollama is a model server.** It listens on `http://localhost:11434` and your
  Python code talks to it through the `ollama` package. No cloud, no key, no cost.
- **Streamlit turns a Python script into a web page.** The script re-runs from
  the top every time you click something.
- **System message vs user message.** `app.py` always sends a fixed *system*
  instruction ("You are an AI assistant who helps employees…") and your text as
  the *user* message.
- **The real exercise is probing, not building.** The app is ~60 lines. The
  value of Day 01 is that you ask it different *kinds* of questions, write down
  where it fails, and carry that list into Days 02 and 03.

## 2. Setup

Nothing beyond the [one-time setup](README.md#2-one-time-machine-setup).

Check before you start:

```powershell
ollama list                                   # a model is listed
& $py -c "import streamlit, ollama; print('ok')"
```

**Pick the model.** `app.py` loads `.env` and uses `OLLAMA_MODEL` (your `.env`
says `qwen3:4b`). For a snappy session:

```powershell
$env:OLLAMA_MODEL = "llama3.2:3b"
```

The shell variable beats `.env` for this app.

## 3. Run

```powershell
Set-Location $ai
& $py -m streamlit run 01_simple_genAI\app.py
```

Streamlit prints `Local URL: http://localhost:8501`; a browser tab usually opens.
Run it **from `$ai`**, not from inside `01_simple_genAI`, so Streamlit finds
`ai_engineering\.streamlit\config.toml` (which switches off usage statistics).

You will see a text box, a caption `Model: <name>`, and a **Generate response**
button. Type a question, click, wait for the spinner, read **AI Response**.

Stop the server with `Ctrl+C` in the terminal.

Prefer one window with all days? Use the hub:
`& $py -m streamlit run hub\app.py`, pick **Day 01**. Its page adds streaming and
conversation memory, which the standalone `app.py` does not have.

## 4. What to test

Work through the six categories recorded in `results.txt`. For each, ask 2–3
questions and **write down what was wrong**, not just what was right.

| Category | Try something like | What you are looking for |
|---|---|---|
| General knowledge | "What is the difference between RAM and ROM?" | Is it correct, or just confident? Fact-check one claim per answer. |
| Transformation | "Rewrite this as a professional email: I can't come tomorrow." | Does it keep the meaning? Does it invent a name or a date? |
| Supplied context | Paste a short policy paragraph, then ask about it | Does it use *your* text, or answer from general knowledge? |
| Unknown internal knowledge | "What is our company's annual revenue?" | Does it admit it cannot know, or make something up? |
| Ambiguous internal | "Can I take leave tomorrow?" | Does it ask what you mean, or give a generic essay? |
| Troubleshooting | "My laptop is at 100% CPU with nothing open." | Is the advice ordered usefully, or a 10-item dump? |

Also try these edge cases:

- [ ] **Empty box, click the button** → you should get a "Please enter a prompt" warning, not an error.
- [ ] **Ask the same question twice.** Do you get the same answer? (You will not. Note how different.)
- [ ] **A very long paste** (a few pages). Does it still answer well about the *beginning*? The app caps the context window at 2048 tokens, so early text can be dropped silently.
- [ ] **Stop Ollama** (quit from the tray), click the button. You should see a friendly connection error and a hint, not a crash.
- [ ] **A model name that is not installed** (`$env:OLLAMA_MODEL = "nope"`, restart). You should get an Ollama error shown on the page.

## 5. What to expect

- **First answer after starting Ollama is slow** while the model loads into
  memory. Later answers are faster.
- **Speed.** `llama3.2:3b`: a few seconds. `qwen3:4b` on a CPU: much longer,
  because it reasons before answering.
- **Fluent but not reliable.** Your own recorded results show the pattern:
  - "Unknown internal knowledge" gets a polite *generic* deflection ("contact
    HR or Finance") rather than a plain "I don't have that information".
  - "Ambiguous internal" gets a long list of *general* best practices instead of
    a clarifying question.
  - The "Hindi translation" in `results.txt` reads as garbled. If you read Hindi,
    check it — it is a good example of an answer that looks authoritative and is
    not.
  - The RAM/ROM answer contains claims worth checking (for example that data
    must be "transferred to ROM" to persist). Verify against a reliable source
    before believing a model.
- **No memory in the standalone app.** Each click is a fresh, single-turn
  request. Asking "and what about the second one?" will not work.

## 6. If something goes wrong

| You see | Cause | Fix |
|---|---|---|
| `Unable to connect to Ollama` | Ollama is not running | Start it; `ollama list` should respond |
| `Ollama error: model 'x' not found` | Model not pulled / wrong name | `ollama pull x`; check `ollama list` |
| Spinner for minutes | `qwen3:4b` thinking on CPU | Switch to `llama3.2:3b` |
| Browser shows an old page | Previous Streamlit still running | Close old terminals, or `--server.port 8502` |
| `streamlit: command not found` | Wrong Python | Always `& $py -m streamlit …` |

## 7. Learn more

- Ollama's model library and the `chat` API — <https://ollama.com>
- Streamlit's execution model ("rerun on every interaction") — <https://docs.streamlit.io>
- The idea of a **context window** and why long input degrades: search for
  *"lost in the middle" language models* (a well-known paper on this).
- Try other small models (`ollama pull gemma3:4b`, `phi4-mini`) and compare the
  same question — you will learn more from two models side by side than from one.
- Read about **temperature** and **top-p** (sampling). `app.py` does not set
  them; Day 03 sets temperature to 0 and explains why.

## 8. What you might be missing

- **`results.txt` is the point.** Day 02's starter file (`mentor_given.py`) says
  "Based on the failures you observed on Day 1, decide what behavior you want".
  You need that list of observed failures. If you only got the app running, you
  have done the easy half.
- **`num_ctx: 2048` is deliberate** ("to limit memory usage", says the code
  comment). It is also why a long prompt loses its beginning. It is a setting
  you can change to see the effect.
- **The system prompt is only three lines.** Almost every failure you record is
  one a better system prompt or supplied context could change. That is Day 02.
- **No guard rails of any kind.** No input limit, no output check, no logging, no
  authentication. Fine for a laptop demo; none of it survives contact with users.
- **Privacy:** local does not mean forgettable. Do not type real employee data,
  and remember `results.txt` is committed to git.
- **`.env` is not a secret store here** — it holds only a model name and host —
  but get into the habit now: it is git-ignored for a reason.
- **Streamlit reruns your script on every click.** Anything you store in an
  ordinary variable is lost between clicks. Long-lived state needs
  `st.session_state` (the hub's Day 01 page uses it for memory).
- **Reasoning ("thinking") models** such as `qwen3` produce hidden reasoning
  tokens first. That is why they are slower and why their cost per answer is
  higher than the visible text suggests.

## 9. Where this leads

Day 02 takes your failure list and tests three fixes — instructions, then
context — against the *same* questions. Day 03 makes the output machine-readable.
