# streamlit-aggrid

AgGrid is an awsome grid for web frontend. More information in [https://www.ag-grid.com/](https://www.ag-grid.com/). Consider purchasing a license from Ag-Grid if you are going to use enterprise featrues!

Comment on [discuss.streamlit.io](https://discuss.streamlit.io/t/ag-grid-component-with-input-support/) (There is also a sponsor link below, if you prefer =))

This is just a proof of concept. Check Links below:

* [Open in Streamlit Share](https://share.streamlit.io/pablocfonseca/streamlit-aggrid/main/example.py)

* [GitHub](https://github.com/PablocFonseca/streamlit-aggrid])

* [pypi.org](https://test.pypi.org/project/streamlit-aggrid/)

* If you like it, [Buy me a beer 🍺!](https://www.paypal.com/donate?hosted_button_id=8HGLA4JZBYFPQ)


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
Version 0.1.2
* added customCurrencyFormat as column type

 Version 0.1.0:
* I worked a little bit more on making the example app functional.
* Couple configuration options for update mode (How frontend updates streamlit) and for data returns (grid should return data filtered? Sorted?)
* Some basic level of row selection
* Added some docstrings specially on gridOptionsBuilder methods
* Lacks performance for production. JS Client code is slow...
