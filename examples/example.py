from multiprocessing.sharedctypes import Value
import streamlit as st
import os

st.set_page_config(layout="wide")
root = os.path.join(os.path.dirname(__file__))

dashboards = {
    "Main Example": os.path.join(root, "main_example.py"),
    "Adding your License Key": os.path.join(root, "licensing_example.py"),
    "Controling AgGrid redraw": os.path.join(root, "fixed_key_example.py"),
    "Using Custom Cell Renderer": os.path.join(root, "cell_renderer_class_example.py"),
    "Adding Two grids to one page": os.path.join(root, "two_grids_example.py"),
    "Create Virtual Columns": os.path.join(root, "virtual_columns.py"),
    "Highlight Editions": os.path.join(root, "example_highlight_change.py"),
    "Use it inside st.form": os.path.join(root, "forms.py"),
    "Set Pinned Rows": os.path.join(root, "pinned_rows.py"),
    "Theming & Pre-Selection": os.path.join(root, "themes_and_pre_selection.py"),
    "Nested Grids" : os.path.join(root, "nested_grids.py"), 
    "Rich Cell Editor" : os.path.join(root, "rich_cell_editor.py") 
}

choice_from_url = query_params = st.experimental_get_query_params().get("example", ["Main Example"])[0]
index = list(dashboards.keys()).index(choice_from_url)

choice = st.sidebar.radio("Examples", list(dashboards.keys()), index=index)

path = dashboards[choice]

with open(path, encoding="utf-8") as code:
    c = code.read()
    exec(c, globals())

    with st.expander('Code for this example:'):
        st.markdown(f"""``` python
{c}```""")
