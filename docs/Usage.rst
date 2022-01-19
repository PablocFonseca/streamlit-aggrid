Usage
########

This section lists the most common use cases of AgGrid. Many are based on questions asked at 
`Streamlit Forums <https://discuss.streamlit.io/t/ag-grid-component-with-input-support>`_.


Simple use
==========
The most straight-forward way to use AgGrid in an streamlit application is to use AgGrid call direclty from st_aggrid module's root.

Code below will create a simple two column DataFrame and use AgGrid to render a read-only representation using default options for 
AgGrid.

.. code-block::  python
    :caption: app.py
    :name: app.py
    
    import streamlit as st
    import pandas as pd
    from st_aggrid import AgGrid
    
    df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
    AgGrid(df)

The example can be run with the following command:

>>> streamlit run app.py


Making Cells Editable
=====================

The default settings for AgGrid renders a nice read-only datagrid interface. However, it is also possible to use AgGrid in Editable mode.
Allowing users to feed tabular back to pyhon code running within Streamlit application. To use it, just modify the previous `app.py` as below:

.. code-block::  python
    :caption: app.py
    :emphasize-lines: 6,7
    
    import streamlit as st
    import pandas as pd
    from st_aggrid import AgGrid
    
    df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
    grid_return = AgGrid(df, editable=True)
    new_df = grid_return['data']

this will make all the cells in the grid editable and the `new_df` variable will contain the updated dataframe.


Grid Customization
==================
AgGrid can be customized in many ways, many options can be set using the `grid_options` parameter.
`grid_options` is a dictionary used as a one-stop-shop to configure the grid. Extensive documentation  is available at
`AgGrid documentation <https://www.ag-grid.com/javascript-data-grid/grid-properties/>`_

.. note::
    Not all `grid_options` are fully suppoerted by streamlit-aggrid. Not all use cases have been tested current implementation
    cover most common scenarios.

if `grid_options` is not set, AgGrid call will infer default options from the dataframe. However if it is set, at least `columnDefs` key must be 
set. 

Code below is equivalent to first example, but changes columns headers and makes only first column editable.

.. _grid-customization-code:

.. code-block::  python
    :caption: app.py
    :emphasize-lines: 7,8,9,10,11,12,13,14,15,16,17,18,19,20
    
    import streamlit as st
    import pandas as pd
    from st_aggrid import AgGrid

    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})

    grid_options = {
        "columnDefs": [
            {
                "headerName": "First Column",
                "field": "col1",
                "editable": True,
            },
            {
                "headerName": "Second Column",
                "field": "col2",
                "editable": False,
            },
        ],
    }

    grid_return = AgGrid(df, grid_options)
    new_df = grid_return["data"]

    st.write(new_df)


Helper class to define grid_options - GridOptionsBuilder 
=========================================================
Defining grid options for large dataframes can be very verbose. 
Streamlit-aggrid provides a helper class to simplify the process - :doc:`GridOptionsBuilder`
By using the builder you can generate the `grid_options` dictionary by calling its methods, 
which could be less error prone.

The example below configures the grid like the :ref:`previous example <grid-customization-code>`, and 
also enables single row selection. Selection result  returns as a list of selected rows.

.. code-block::  python
    :caption: app.py
    :emphasize-lines: 7,8,9,10
    
    import streamlit as st
    import pandas as pd
    from st_aggrid import AgGrid, GridOptionsBuilder

    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})

    options_builder = GridOptionsBuilder.from_dataframe(df)
    options_builder.configure_column('col1', editable=True)
    options_builder.configure_selection("single")
    options_builder.
    grid_options = options_builder.build()

    grid_return = AgGrid(df, grid_options)
    selected_rows = grid_return["selected_rows"]

    st.write(selected_rows)

