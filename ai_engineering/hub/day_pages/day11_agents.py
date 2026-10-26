"""Day 11: inspect a bounded ReAct agent loop and its observations."""

from contextlib import redirect_stdout
from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import streamlit as st

from config import DAY_DIRS, get_ollama_client


SAMPLE_QUESTION = "My user ID is E103. Request leave for Pongal."
SAMPLE_STEPS = [
    'Thought: Find the named festival date.\nAction: get_festival_date\nAction Input: {"festival_name": "Pongal"}',
    'Thought: Check the employee balance.\nAction: get_available_leave_balance\nAction Input: {"user_id": "E103"}',
    'Thought: Print the demo request.\nAction: create_leave_request\nAction Input: {"user": "E103", "date": "2027-01-14"}',
    "Thought: The checks are complete.\nFinal Answer: The demo request was printed.",
]


class ScriptedClient:
    """Fixed model responses for a clearly labelled offline walkthrough."""

    def __init__(self):
        self.steps = iter(SAMPLE_STEPS)

    def chat(self, **_kwargs):
        return SimpleNamespace(message=SimpleNamespace(content=next(self.steps)))


def _load_agent():
    path = Path(DAY_DIRS[11]) / "main.py"
    spec = spec_from_file_location("day11_agent", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render():
    st.caption("See how a model proposes one action, receives its observation, and repeats.")
    st.info("Leave balances and festival dates are demo data. A request is printed only; nothing is submitted to an HR system.")

    scripted = st.checkbox("Use scripted walkthrough (no Ollama)", value=True, key="day11_scripted")
    if scripted:
        st.caption("The walkthrough uses fixed responses and assumes 2026-10-26 so the example date is in the future.")
        st.code(SAMPLE_QUESTION)
        question = SAMPLE_QUESTION
    else:
        question = st.text_area("Request", value=SAMPLE_QUESTION, key="day11_question")

    if st.button("Run agent", type="primary", key="day11_run"):
        if not question.strip():
            st.error("Enter a request.")
            return
        try:
            agent = _load_agent()
            trace = StringIO()
            if scripted:
                model_client = ScriptedClient()
                run_date = date(2026, 10, 26)
                model_name = "scripted walkthrough"
            else:
                host = st.session_state.get("ollama_host")
                model_name = st.session_state.get("ollama_model")
                model_client = get_ollama_client(host)
                run_date = date.today()
            with redirect_stdout(trace):
                answer = agent.run_agent(question, model_client=model_client, model=model_name, today=run_date)
            st.success(answer)
            with st.expander("Thought, action, and observation trace", expanded=True):
                st.code(trace.getvalue(), language="text")
        except Exception as exc:
            st.error(f"Agent could not finish: {exc}")
