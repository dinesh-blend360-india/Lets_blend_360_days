"""Day 14 local MCP capability discovery and safe lookup."""

import asyncio
from importlib.util import module_from_spec, spec_from_file_location

import streamlit as st

from config import DAY_DIRS


def render():
    st.caption("Discover Day 10's read-only lookup through a local MCP stdio server.")
    st.info("This example uses clearly labelled mock policy data and has no remote server or write capability.")
    if not st.button("Discover and call MCP tool", key="day14_run"):
        return
    try:
        path = DAY_DIRS[14] / "client.py"
        spec = spec_from_file_location("day14_hub_client", path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        result = asyncio.run(module.run())
        st.json(result)
    except ImportError:
        st.error("Install the Day 14 MCP dependency from 14_mcp/requirements.txt first.")
    except Exception as exc:
        st.error(f"MCP call failed: {type(exc).__name__}: {exc}")

