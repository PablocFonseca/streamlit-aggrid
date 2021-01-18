import streamlit as st
import pandas as pd 
import numpy as np
import altair as alt

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

np.random.seed(42)

@st.cache(allow_output_mutation=True)
def fetch_data(samples, include_date_time):

    dummy_data = {
        "date":pd.date_range('2020-01-01', periods=samples),
        "date_tz_aware":pd.date_range('2020-01-01', periods=samples, tz="Asia/Katmandu"),
        "apple":np.random.randint(0,100,samples) / 3.0,
        "banana":np.random.randint(0,100,samples) / 5.0,
        "chocolate":np.random.randint(0,100,samples),
        "group": np.random.choice(['A','B'], size=samples) ,
    }
    if not include_date_time:
        dummy_data.pop("date_tz_aware", None)

    return pd.DataFrame(dummy_data)

#Example controlers
st.sidebar.subheader("St-AgGrid example options")

sample_size = st.sidebar.number_input("rows", min_value=10, value=10)
grid_height = st.sidebar.number_input("Grid height", min_value=200, max_value=800, value=200)

return_mode = st.sidebar.selectbox("Return Mode", list(DataReturnMode.__members__), index=0)
return_mode_value = DataReturnMode.__members__[return_mode]

update_mode = st.sidebar.selectbox("Update Mode", list(GridUpdateMode.__members__), index=6)
update_mode_value = GridUpdateMode.__members__[update_mode]

#TZ aware DT handling
include_date_time = st.sidebar.checkbox("Include tz aware date column", value=False)
if include_date_time:
    custom_format_string = st.sidebar.text_input("date column format string", value='yyyy-MM-dd HH:mm zzz')
    st.sidebar.text("___")

#enterprise modules
enable_enterprise_modules = st.sidebar.checkbox("Enable Enterprise Modules")
if enable_enterprise_modules:
    enable_sidebar =st.sidebar.checkbox("Enable grid sidebar", value=False)
else:
    enable_sidebar = False

#features
fit_columns_on_grid_load = st.sidebar.checkbox("Fit Grid Columns on Load")

enable_selection=st.sidebar.checkbox("Enable row selection", value=False)
if enable_selection:
    st.sidebar.subheader("Selection options")
    selection_mode = st.sidebar.radio("Selection Mode", ['single','multiple'])
    
    use_checkbox = st.sidebar.checkbox("Use check box for selection")
    if use_checkbox:
        groupSelectsChildren = st.sidebar.checkbox("Group checkbox select children", value=True)
        groupSelectsFiltered = st.sidebar.checkbox("Group checkbox includes filtered", value=True)

    if ((selection_mode == 'multiple') & (not use_checkbox)):
        rowMultiSelectWithClick = st.sidebar.checkbox("Multiselect with click (instead of holding CTRL)", value=False)
        if not rowMultiSelectWithClick:
            suppressRowDeselection = st.sidebar.checkbox("Suppress deselection (while holding CTRL)", value=False)
        else:
            suppressRowDeselection=False
    st.sidebar.text("___")

enable_pagination = st.sidebar.checkbox("Enable pagination", value=False)
if enable_pagination:
    st.sidebar.subheader("Pagination options")
    paginationAutoSize = st.sidebar.checkbox("Auto pagination size", value=True)
    if not paginationAutoSize:
        paginationPageSize = st.sidebar.number_input("Page size", value=5, min_value=0, max_value=sample_size)
    st.sidebar.text("___")

df = fetch_data(sample_size, include_date_time)

#Infer basic colDefs from dataframe types
gb = GridOptionsBuilder.from_dataframe(df)

#customize gridOptions
gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)

if include_date_time:
    gb.configure_column("date_tz_aware", type=["dateColumnFilter","customDateTimeFormat"], custom_format_string=custom_format_string, pivot=True)

gb.configure_column("apple", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2, aggFunc='sum')
gb.configure_column("banana", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=1, aggFunc='avg')
gb.configure_column("chocolate", type=["numericColumn", "numberColumnFilter", "customCurrencyFormat"], custom_currency_symbol="R$", aggFunc='max')

#configures last row to use custom styles based on cell's value, injecting JsCode on components front end
cellsytle_jscode = JsCode("""
function(params) {
    if (params.value == 'A') {
        return {
            'color': 'white',
            'backgroundColor': 'darkred'
        }
    } else {
        return {
            'color': 'black',
            'backgroundColor': 'white'
        }
    }
};
""")
gb.configure_column("group", cellStyle=cellsytle_jscode)

if enable_sidebar:
    gb.configure_side_bar()

if enable_selection:
    gb.configure_selection(selection_mode)
    if use_checkbox:
        gb.configure_selection(selection_mode, use_checkbox=True, groupSelectsChildren=groupSelectsChildren, groupSelectsFiltered=groupSelectsFiltered)
    if ((selection_mode == 'multiple') & (not use_checkbox)):
        gb.configure_selection(selection_mode, use_checkbox=False, rowMultiSelectWithClick=rowMultiSelectWithClick, suppressRowDeselection=suppressRowDeselection)

if enable_pagination:
    if paginationAutoSize:
        gb.configure_pagination(paginationAutoPageSize=True)
    else:
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=paginationPageSize)

gb.configure_grid_options(domLayout='normal')
gridOptions = gb.build()

#Display the grid
with st.spinner("Loading Grid..."):
    st.header("Streamlit Ag-Grid")
    grid_response = AgGrid(
        df, 
        gridOptions=gridOptions,
        height=grid_height, 
        width='100%',
        data_return_mode=return_mode_value, 
        update_mode=update_mode_value,
        fit_columns_on_grid_load=fit_columns_on_grid_load,
        allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
        enable_enterprise_modules=enable_enterprise_modules,
        )

df = grid_response['data']
selected = grid_response['selected_rows']
selected_df = pd.DataFrame(selected)

with st.spinner("Displaying results..."):
    #displays the chart
    chart_data = df.loc[:,['date','apple','banana','chocolate']].assign(source='total')

    if not selected_df.empty:
        selected_data = selected_df.loc[:,['date','apple','banana','chocolate']].assign(source='selection')
        chart_data = pd.concat([chart_data, selected_data])

    chart_data = pd.melt(chart_data, id_vars=['date','source'], var_name="item", value_name="quantity")
    #st.dataframe(chart_data)
    chart = alt.Chart(data=chart_data).mark_bar().encode(
        x=alt.X("item:O"),
        y=alt.Y("sum(quantity):Q", stack=False),
        color='source:N',
    )

    st.header("Example chart")
    st.markdown("""
    This chart is built with data returned from the grid. Experiment selecting rows, group and filtering.
    """)

    st.altair_chart(chart, use_container_width=True)

    st.header("Component Outputs")
    st.subheader("Returned grid data:")
    st.dataframe(grid_response['data'])

    st.subheader("grid selection:")
    st.write(grid_response['selected_rows'])

    st.header("Generated gridOptions")
    st.write(gridOptions)
