"""Day 15 scripted control baseline, clearly separated from live model evaluation."""

from importlib.util import module_from_spec, spec_from_file_location

import streamlit as st

from config import DAY_DIRS, add_day_to_path


def render():
    st.caption("Run the reproducible scripted baseline and inspect case-ID-keyed control results.")
    st.warning("Scripted fixtures check application controls. They do not measure live model quality. Blind human labels and judge calibration remain separate steps.")
    if not st.button("Run 22-case control baseline", key="day15_run"):
        return
    try:
        add_day_to_path(10)
        path = DAY_DIRS[15] / "run_baseline.py"
        spec = spec_from_file_location("day15_hub_baseline", path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        rows = module.run_all()
        failures = [(row["id"], key) for row in rows for key, passed in row["checks"].items() if not passed]
        st.metric("Cases", len(rows))
        st.metric("Deterministic check failures", len(failures))
        st.dataframe([{
            "id": row["id"], "category": row["category"], "risk": row["risk"],
            "checks_pass": all(row["checks"].values()), "actions": row["persisted_actions"],
        } for row in rows], width="stretch")
        with st.expander("Full baseline"):
            st.json(rows)
    except Exception as exc:
        st.error(f"Baseline failed: {type(exc).__name__}: {exc}")

