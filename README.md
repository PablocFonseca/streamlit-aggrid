# streamlit-aggrid

[![Open in Streamlit][share_badge]][share_link] [![GitHub][github_badge]][github_link] [![PyPI][pypi_badge]][pypi_link] 

AgGrid is an awsome grid for web frontend. More information in [https://www.ag-grid.com/](https://www.ag-grid.com/). Consider purchasing a license from Ag-Grid if you are going to use enterprise featrues!

Comment on [discuss.streamlit.io](https://discuss.streamlit.io/t/ag-grid-component-with-input-support/) If you like it or [Buy me a beer 🍺!](https://www.paypal.com/donate?hosted_button_id=8HGLA4JZBYFPQ)

<br>

# Install
```
pip install streamlit-aggrid

```

# Quick Use
Create an example.py file
```python
from st_aggrid import AgGrid

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

# Develpoment Notes
Version 0.1.3
* Fixed bug where cell was blank after edition.
* Added enable_enterprise_modules argument to AgGrid call for enabling/disabling [enterprise features](https://www.ag-grid.com/documentation/javascript/licensing/)
* It is now possible to inject js functions on gridOptions. Enabling advanced customizations such as conditional formating (check 4<sup>th</sup> column on the [example](share_link))

Version 0.1.2
* added customCurrencyFormat as column type

 Version 0.1.0:
* I worked a little bit more on making the example app functional.
* Couple configuration options for update mode (How frontend updates streamlit) and for data returns (grid should return data filtered? Sorted?)
* Some basic level of row selection
* Added some docstrings specially on gridOptionsBuilder methods
* Lacks performance for production. JS Client code is slow...


[share_badge]: https://static.streamlit.io/badges/streamlit_badge_black_white.svg
[share_link]: https://share.streamlit.io/pablocfonseca/streamlit-aggrid/main/example.py

[github_badge]: https://badgen.net/badge/icon/GitHub?icon=github&color=black&label
[github_link]: https://github.com/PablocFonseca/streamlit-aggrid

[pypi_badge]: https://badgen.net/pypi/v/streamlit-aggrid?icon=pypi&color=black&label
[pypi_link]: hhttps://test.pypi.org/project/streamlit-aggrid/