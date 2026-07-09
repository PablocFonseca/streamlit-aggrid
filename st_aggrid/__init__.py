"""Backwards-compatibility shim: the package was historically imported as
``st_aggrid``. The real implementation lives in ``streamlit_aggrid``."""

import sys

from streamlit_aggrid import *  # noqa: F401,F403
from streamlit_aggrid import __all__  # noqa: F401

# Alias submodules so imports like ``from st_aggrid.shared import JsCode``
# or ``import st_aggrid.grid_options_builder`` keep working.
import streamlit_aggrid.AgGrid  # noqa: F401
import streamlit_aggrid.AgGridReturn  # noqa: F401
import streamlit_aggrid.aggrid_utils  # noqa: F401
import streamlit_aggrid.grid_options_builder  # noqa: F401
import streamlit_aggrid.shared  # noqa: F401
import streamlit_aggrid.styles  # noqa: F401

for _name in (
    "AgGrid",
    "AgGridReturn",
    "aggrid_utils",
    "grid_options_builder",
    "shared",
    "styles",
):
    sys.modules[f"{__name__}.{_name}"] = getattr(
        sys.modules["streamlit_aggrid"], _name
    )
