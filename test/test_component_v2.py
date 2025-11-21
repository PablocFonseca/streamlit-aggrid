import streamlit as st
import pandas as pd

# from st_aggrid import AgGrid
from streamlit.components.v2.manifest_scanner import (
    _is_likely_streamlit_component_package,
    _find_package_pyproject_toml,
    _load_pyproject,
    _extract_components,
    _normalize_package_name,
    _resolve_package_root,
    _derive_project_metadata,
    ComponentConfig,
    ComponentManifest,
    _pyproject_via_read_text,
    _process_single_package,
    scan_component_manifests

)



import importlib

all_distributions = list(importlib.metadata.distributions())
#st.write([_normalize_package_name(d.name) for d in all_distributions])

candidate_distributions = [
    dist for dist in all_distributions if _is_likely_streamlit_component_package(dist)
]

manifests =[_process_single_package(dist) for dist in candidate_distributions]


st.write(scan_component_manifests())


from streamlit.runtime import Runtime

Runtime.instance().bidi_component_registry.discover_and_register_components()

Runtime.instance().bidi_component_registry._registry._components


from st_aggrid import AgGrid

df = pd.DataFrame([[1,2,3], [4,5,6]], columns=list('abc'))


st.subheader("Header above the grid")
result = AgGrid(df, key="test_grid", show_toolbar=True)

st.subheader("Grid Return Value")
st.write(result.data)
