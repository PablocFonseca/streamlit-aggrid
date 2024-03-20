# streamlit-aggrid

[![Open in Streamlit][share_badge]][share_link] [![GitHub][github_badge]][github_link] [![PyPI][pypi_badge]][pypi_link]

---

**Note** (feb 2024 update)

(feb 2024 update)   
I had to stop the development during last year, for things outside of my control... Many people had 
reached me stating how Streamlit AgGrid devlivered value to them. I'll dedicate some more time over the next months
with focus on (on this priority):
    - Stability and dependency updates.
    - Compatibility with late streamlit versions
    - PR review and merges to main trunk.
    - More examples (if you write a PR, please include a simple Streamlit app demonstrating how it works, if possible)


If you want to sponsor or support this project you can <a href="javascript:window.location.href=atob('cGFibG9mb25zZWNhQGdtYWlsLmNvbQ==')">email me</a>.
if like the project [Buy me a beer 🍺!](https://www.paypal.com/donate?hosted_button_id=8HGLA4JZBYFPQ)

---

**AgGrid** is an awesome grid for web frontend. More information in [https://www.ag-grid.com/](https://www.ag-grid.com/). Consider purchasing a license from Ag-Grid if you are going to use enterprise features!



<br>
Live example [on Streamlit Cloud](https://pablocfonseca-streamlit-aggrid-examples-example-jyosi3.streamlitapp.com/). Some basic documentation is available: https://streamlit-aggrid.readthedocs.io

# Install

```
pip install streamlit-aggrid

```

# Quick Use

Create an example.py file

```python
from st_aggrid import AgGrid
import pandas as pd

df = pd.read_csv('https://raw.githubusercontent.com/fivethirtyeight/data/master/airline-safety/airline-safety.csv')
AgGrid(df)
```

Run :

```shell
streamlit run example.py
```

# Demo

Grid data is sent back to streamlit and can be reused in other components. In the example below a chart is updated on grid edition.

![example image](https://github.com/PablocFonseca/streamlit-aggrid/raw/main/group_selection_example.gif)

# Development Notes
Version 0.3.5
 - Merged many PR, thanks everybody.
 - Grid State can be saved and retrieved. Many people requested this one. Live Example [Here](https://staggrid-examples.streamlit.app/?example=%27Grid%20State%27) 


Version 0.3.4

- Added quickfilter
- Added Excel Export Module
- Bugfixes (an probably introduced new ones :/)
- Code cleanup
- Updated Ag-Grit to 29.1.0 (including ag-grid-react) which will cause direct HTML returns to stop rendering ([#198](https://github.com/PablocFonseca/streamlit-aggrid/issues/198)). Use a [cellRenderer](https://www.ag-grid.com/javascript-data-grid/component-cell-renderer/) instead.

Version 0.3.3

- Fixes [#132](https://github.com/PablocFonseca/streamlit-aggrid/issues/132)
- Fixes [#131](https://github.com/PablocFonseca/streamlit-aggrid/issues/131) and [#130](https://github.com/PablocFonseca/streamlit-aggrid/issues/130)
- Added Sparklines [#118](https://github.com/PablocFonseca/streamlit-aggrid/issues/118)
- Changed Grid Return to support [#117](https://github.com/PablocFonseca/streamlit-aggrid/issues/117)
- Rebuilt streamlit theme

Version 0.3.0

- Merged some PR (Thanks everybody!) check PR at github!
- Added class parsing in React Side, so more advanced CellRenderers can be used. (Thanks [kjakaitis](https://github.com/kjakaitis))
- Added gridOptionsBuilder.configure_first_column_as_index() to, well, style the first columns as an index (MultiIndex to come!)
- Improved serialization performance by using simpler pandas to_json method (PR #62, #85)
- Added option to render plain json instead of pd.dataframes
- gridOptions may be loaded from file paths or strings
- gridReturn is now a @dataclass with rowIndex added to selected_rows, (previous version returned only the selected data, now you can know which row was selected)
- Changed GridReturnMode behavior. Now update_on accepts a list of gridEvents that will trigger a streamlit refresh, making it possible to subscribe to any [gridEvent](https://www.ag-grid.com/javascript-data-grid/grid-events/).
- Removed dot-env and simplejson dependencies.
- Other smaller fixes and typos corrections.

Version 0.2.3

- small fixes
- Merged PR #44 and #25 (thanks [msabramo](https://github.com/msabramo) and [ljnsn](https://github.com/ljnsn))
- Merged PR #58 - allow nesting dataframes. Included an example in exampes folder.

Version 0.2.2

- Updated frontend dependencies to latest version
- Corrected text color for better viz when using streamlit theme (thanks [jasonpmcculloch](https://github.com/jasonpmcculloch))
- Switched default theme to Balham Light ('light'), if you want to use streamlit theme set `theme='streamlit'` on agGrid call

Version 0.2.0

- Support Themes
- Incorporated Pull Requests with fixes and pre-select rows (Thanks [randomseed42](https://github.com/randomseed42) and [msabramo](https://github.com/msabramo))
- You can use strings instead of importing GridUpdateMode and DataReturnMode enumerators
- it works fine with st.forms!
- new theme example in example folder

Version 0.1.9

- Small fixes
- Organized examples folder

Version 0.1.8

- Fixes a bug that breaks the grid when NaN or Inf values are present in the data

Version 0.1.7

- Fixes a bug that happened when converting data back from the grid with only one row
- Added license_key parameter on AgGrid call.

Version 0.1.6

- Fixes issue [#3](https://github.com/PablocFonseca/streamlit-aggrid/issues/3)
- Adds support for timedelta columns check [example][share_link]

Version 0.1.5

- small bug fixes
- there is an option to avoid grid re-initialization on app update (check fixed_key_example.py on examples folder or [here](https://share.streamlit.io/pablocfonseca/streamlit-aggrid/main/examples/fixed_key_example.py))

Version 0.1.3

- Fixed bug where cell was blank after edition.
- Added enable_enterprise_modules argument to AgGrid call for enabling/disabling [enterprise features](https://www.ag-grid.com/documentation/javascript/licensing/)
- It is now possible to inject js functions on gridOptions. Enabling advanced customizations such as conditional formatting (check 4<sup>th</sup> column on the [example](share_link))

Version 0.1.2

- added customCurrencyFormat as column type

Version 0.1.0:

- I worked a little bit more on making the example app functional.
- Couple configuration options for update mode (How frontend updates streamlit) and for data returns (grid should return data filtered? Sorted?)
- Some basic level of row selection
- Added some docstrings specially on gridOptionsBuilder methods
- Lacks performance for production. JS Client code is slow...

[share_badge]: https://static.streamlit.io/badges/streamlit_badge_black_white.svg
[share_link]: https://share.streamlit.io/pablocfonseca/streamlit-aggrid/main/examples/example.py
[github_badge]: https://badgen.net/badge/icon/GitHub?icon=github&color=black&label
[github_link]: https://github.com/PablocFonseca/streamlit-aggrid
[pypi_badge]: https://badgen.net/pypi/v/streamlit-aggrid?icon=pypi&color=black&label?
[pypi_link]: https://www.pypi.org/project/streamlit-aggrid/
