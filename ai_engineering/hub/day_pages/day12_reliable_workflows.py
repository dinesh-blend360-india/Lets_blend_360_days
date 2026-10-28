"""Day 12 deterministic leave workflow demonstration."""

from importlib.util import module_from_spec, spec_from_file_location
import json

import streamlit as st

from config import DAY_DIRS


def render():
    st.caption("Eligibility and duplicate prevention are enforced in code. All records are local simulations.")
    with st.form("day12_form"):
        user_id = st.selectbox("Demo employee", ["E104", "E101", "E102", "E103"])
        festival = st.selectbox("Festival", ["Diwali", "Pongal", "Dussehra"])
        offset = st.number_input("Days after festival", min_value=0, max_value=30, value=1)
        days = st.number_input("Leave days", min_value=1, max_value=30, value=1)
        create = st.checkbox("Record a simulated local request")
        approval = st.text_input("Type CONFIRM for the exact proposal if recording", value="")
        submitted = st.form_submit_button("Check workflow")
    if not submitted:
        return
    path = DAY_DIRS[12] / "workflow.py"
    spec = spec_from_file_location("day12_hub_workflow", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    output = DAY_DIRS[12] / "outputs"
    app = module.LeaveWorkflow(module.LeaveStore(output / "requests.json"), output / "runs.jsonl")
    result = app.run(
        user_id=user_id, festival=festival, offset_days=int(offset), leave_days=int(days),
        create=create, approve=(lambda _: approval == "CONFIRM") if create else None,
    )
    if result["status"] in {"blocked", "failed", "declined"}:
        st.warning(f"{result['status']}: {result['code']}")
    else:
        st.success(f"{result['status']}: {result['code']}")
    if result.get("audit_error"):
        st.warning("The request result was returned, but its audit record could not be written.")
    st.json(result)

