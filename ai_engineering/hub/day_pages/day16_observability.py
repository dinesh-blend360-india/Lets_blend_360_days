"""Day 16 tracing: run a Day 15 case with a fault switched on and read the trace."""

import sys

import streamlit as st

from config import DAY_DIRS, add_day_to_path


def _load():
    """Import the Day 16 package, with Day 10 and Day 15 reachable.

    Day 16's package is `obs`, not `src`, so it does not collide with Day 10's
    `src` package on sys.path.
    """
    add_day_to_path(10)
    for day in (15, 16):
        path = str(DAY_DIRS[day])
        if path not in sys.path:
            sys.path.insert(0, path)
    from obs.faults import FAULTS, FaultConfig
    from obs.run_traced import F16_06_MESSAGE, run_case, run_message
    from obs.tracing import render_tree
    import run_baseline as day15

    return FAULTS, FaultConfig, run_case, run_message, render_tree, day15, F16_06_MESSAGE


def render():
    st.caption("Every request produces one trace. Switch on a fault and read the step where it went wrong.")
    st.info(
        "Traces are written locally as JSONL; no LangSmith account is needed. "
        "Personal data is masked before anything is stored."
    )

    try:
        FAULTS, FaultConfig, run_case, run_message, render_tree, day15, privacy_message = _load()
        cases = day15.load_cases()
    except Exception as exc:
        st.error(f"Could not load Day 16: {type(exc).__name__}: {exc}")
        return

    left, middle, right = st.columns(3)
    with left:
        case_id = st.selectbox("Day 15 case", [case["id"] for case in cases], key="day16_case")
    with middle:
        fault = st.selectbox("Fault (off by default)", ["none", *FAULTS], key="day16_fault")
    with right:
        retry = st.selectbox(
            "Retry attempts", [0, 2], index=0, key="day16_retry",
            help="0 reproduces the original behaviour; 2 is the Day 16 fix.",
        )

    privacy = st.checkbox(
        "Use the personal-data message instead (F16-06)", key="day16_privacy",
        help="Shows the masking rules working end to end.",
    )
    if privacy:
        st.code(privacy_message, language="text")

    if not st.button("Run with tracing", key="day16_run", type="primary"):
        return

    try:
        faults = FaultConfig(FaultConfig.parse(None if fault == "none" else fault))
        if privacy:
            row, tracer = run_message(privacy_message, faults=faults, retry_attempts=retry)
        else:
            case = next(item for item in cases if item["id"] == case_id)
            row, tracer = run_case(case, faults=faults, retry_attempts=retry)
    except Exception as exc:
        st.error(f"Traced run failed: {type(exc).__name__}: {exc}")
        return

    summary = row["trace"]
    columns = st.columns(4)
    columns[0].metric("Steps", summary["step_count"])
    columns[1].metric("Total", f"{summary['total_ms']} ms")
    columns[2].metric("Errored steps", len(summary["error_steps"]))
    failed = [name for name, passed in (row.get("checks") or {}).items() if not passed]
    columns[3].metric("Failed checks", len(failed) if row.get("checks") else "n/a")

    if failed:
        st.warning(f"Failed Day 15 checks: {', '.join(failed)}")
    elif row.get("checks"):
        st.success("All Day 15 checks passed for this case.")

    st.subheader("Trace")
    st.code(render_tree(tracer.records()), language="text")

    if summary["error_steps"]:
        st.subheader("Errored steps")
        st.json(summary["error_steps"])
    elif fault == "bad_retrieval":
        st.warning(
            "No step errored, yet the answer is wrong. That is the point of this fault: "
            "only the retriever run's document_count reveals it."
        )

    with st.expander("Masked inputs on the root run"):
        root = tracer.root()
        st.json(root.inputs if root else {})
    with st.expander("Full trace records"):
        st.json(tracer.records())
    with st.expander("Assistant result"):
        st.json({key: value for key, value in row.items() if key != "trace"})
