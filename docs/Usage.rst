Usage
########

This section lists the most common use cases of AgGrid. Many are based on questions asked at 
`Streamlit Forums <https://discuss.streamlit.io/t/ag-grid-component-with-input-support>`_.


Simple use
==========
The most straight-forward way to use the component is to use AgGrid call direclty from st_aggrid module.

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

The default settings for AgGrid read-only cells. The fastest way to make cells editable is to use `editable=True` on ag-grid call.
edited dataframe is returned as a dataframe inside `data` key in returned dictionary.
By default AgGrid will try to cast edited values to original types.

.. code-block::  python
    :caption: app.py
    :emphasize-lines: 6,7
    
    import streamlit as st
    import pandas as pd
    from st_aggrid import AgGrid
    
    df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
    grid_return = AgGrid(df, editable=True)
    new_df = grid_return['data']

in the previous example `new_df` variable will contain the updated dataframe.


Grid Customization
==================

AgGrid is very flexible and may be customized in many ways, most options can be set using the `grid_options` parameter.
`grid_options` is a dictionary used as a "one stop shop" to configure the grid.
 Extensive documentation  is available at `AgGrid documentation <https://www.ag-grid.com/javascript-data-grid/grid-properties/>`_

.. note::
    Not all `grid_options` are suppoerted by streamlit-aggrid. Current implementation cover most common scenarios.

if `grid_options` is not set, AgGrid will try to infer default options from the dataframe using 
:doc:`GridOptionsBuilder.from_dataframe` internally. 
if it's set, at least `columnDefs` key must be set. 

Code below is equivalent to first example, but makes only the first column editable.

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
                "headerName": "col1,
                "field": "col1",
                "editable": True,
            },
            {
                "headerName": "col2",
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

Manually writing grid options for large dataframes can be very verbose.
If not much Customization is needed, it's better to use :doc:`GridOptionsBuilder` to define grid options.
By using this builder you can generate the `grid_options` dictionary by calling :doc:`GridOptionsBuilder.build`.	

The next example builds a Grid excatly as the example above, using the helper class.
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
    grid_options = options_builder.build()

    grid_return = AgGrid(df, grid_options)
    selected_rows = grid_return["selected_rows"]

    st.write(selected_rows)

