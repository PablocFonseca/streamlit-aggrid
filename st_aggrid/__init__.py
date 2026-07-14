"""Backwards-compatibility shim: the package was historically imported as
``st_aggrid``. The real implementation lives in ``streamlit_aggrid``."""

import importlib
import sys

from streamlit_aggrid import *  # noqa: F401,F403
from streamlit_aggrid import __all__  # noqa: F401

# Alias submodules so imports like ``from st_aggrid.shared import JsCode``
# or ``import st_aggrid.grid_options_builder`` keep working.
for _name in (
    "AgGrid",
    "AgGridReturn",
    "aggrid_utils",
    "grid_options_builder",
    "shared",
    "styles",
):
    # Package attributes such as ``streamlit_aggrid.AgGrid`` intentionally
    # export a callable.  Looking them up with ``getattr`` therefore installs a
    # function in ``sys.modules`` instead of the corresponding module.  Import
    # the module explicitly so legacy submodule imports remain valid.
    sys.modules[f"{__name__}.{_name}"] = importlib.import_module(
        f"streamlit_aggrid.{_name}"
    )
