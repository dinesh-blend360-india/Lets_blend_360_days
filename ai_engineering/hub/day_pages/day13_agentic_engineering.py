"""Day 13 proposed production design card."""

import json

import streamlit as st

from config import DAY_DIRS


def render():
    card = json.loads((DAY_DIRS[13] / "design_card.json").read_text(encoding="utf-8"))
    st.warning("Design hypothesis only. This is not a deployed or customer-approved system.")
    st.subheader(card["title"])
    st.write(card["current_prototype"]["summary"])
    st.markdown("### Proposed architecture")
    st.write(card["architecture"]["workflow"])
    st.markdown("### Lifecycle owners and evidence")
    st.dataframe(card["lifecycle"], width="stretch")
    st.markdown("### Proposed golden cases")
    st.dataframe(card["golden_cases"], width="stretch")
    with st.expander("Unknowns, pilot conditions, and trade-off"):
        st.json({key: card[key] for key in ("unknowns", "pilot_conditions", "alternative", "top_risks")})

