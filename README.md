# streamlit-aggrid

This is just a proof of concept. Links below:

* [Open in Streamlit Share](https://share.streamlit.io/pablocfonseca/streamlit-aggrid/main/example.py])

* [GitHub](https://github.com/PablocFonseca/streamlit-aggrid])

* [pypi.org](https://test.pypi.org/project/streamlit-aggrid/)



This just a proof of concept. <br>
AgGrid is an awsome grid for web frontend. More information in [https://www.ag-grid.com/](https://www.ag-grid.com/)

Comment on [discuss.streamlit.io](https://discuss.streamlit.io/t/ag-grid-component-with-input-support/) if you like this!

Pablo Fonseca
<br><br>

# Install
```
pip install -i https://test.pypi.org/simple/ streamlit-aggrid

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

![example image](https://github.com/PablocFonseca/streamlit-aggrid/raw/main/example.gif)
