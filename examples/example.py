import streamlit as st
import os

root = os.path.join(os.path.dirname(__file__))

dashboards = {
    "Main Example": os.path.join(root, "main_example.py"),
    "Fixed Key Parameter": os.path.join(root, "fixed_key_example.py"),
    "License Key": os.path.join(root, "licensing_example.py"),
    "Two grids in page": os.path.join(root, "two_grids_example.py"),
    "Virtual Columns": os.path.join(root, "virtual_columns.py"),
    "Highlight Editions": os.path.join(root, "example_highlight_change.py")
}

choice = st.sidebar.radio("Examples", list(dashboards.keys()))

path = dashboards[choice]
with open(path, encoding="utf-8") as code:
    exec(code.read(), globals())
