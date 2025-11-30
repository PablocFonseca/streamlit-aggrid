"""
CSS utility functions for styling AG Grid components.

These functions return CSS strings that can be injected using:
    st.markdown(css_string, unsafe_allow_html=True)

Since Streamlit AgGrid uses Components V2, CSS injected via st.markdown()
will directly affect the grid without needing the deprecated custom_css parameter.
"""


def get_hide_expanders_css() -> str:
    """
    CSS to hide column and row group expand/collapse icons until hover.

    Creates a cleaner UI by only showing expander icons on hover.
    Works with both column groups (MultiIndex columns) and row groups (MultiIndex index).

    Returns:
        str: CSS string ready for st.markdown(css, unsafe_allow_html=True)

    Example:
        >>> import streamlit as st
        >>> from streamlit_aggrid import AgGrid, GridOptionsBuilder, get_hide_expanders_css
        >>>
        >>> # Inject the CSS
        >>> st.markdown(get_hide_expanders_css(), unsafe_allow_html=True)
        >>>
        >>> # Create and display grid
        >>> gb = GridOptionsBuilder.from_dataframe(df, parse_multi_index=True)
        >>> AgGrid(df, gridOptions=gb.build())
    """
    return """
<style>
/* Hide column group expand/collapse icons */
.ag-header-group-cell .ag-header-expand-icon {
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.3s ease, visibility 0.3s ease;
}

.ag-header-group-cell:hover .ag-header-expand-icon {
  opacity: 1;
  visibility: visible;
}

/* Hide row group expand/collapse icons */
.ag-row-group .ag-group-expanded,
.ag-row-group .ag-group-contracted {
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.3s ease, visibility 0.3s ease;
}

.ag-row:hover .ag-group-expanded,
.ag-row:hover .ag-group-contracted {
  opacity: 1;
  visibility: visible;
}
</style>
"""


def get_compact_grid_css(row_height: int = 28, header_height: int = 32) -> str:
    """
    CSS for a more compact grid with tighter spacing.

    Args:
        row_height: Height of data rows in pixels (default: 28)
        header_height: Height of header rows in pixels (default: 32)

    Returns:
        str: CSS string for compact mode

    Example:
        >>> import streamlit as st
        >>> from streamlit_aggrid import get_compact_grid_css
        >>>
        >>> st.markdown(get_compact_grid_css(row_height=25), unsafe_allow_html=True)
    """
    return f"""
<style>
.ag-theme-streamlit .ag-row,
.ag-theme-alpine .ag-row,
.ag-theme-balham .ag-row {{
  min-height: {row_height}px !important;
  height: {row_height}px !important;
}}

.ag-theme-streamlit .ag-header-row,
.ag-theme-alpine .ag-header-row,
.ag-theme-balham .ag-header-row {{
  min-height: {header_height}px !important;
  height: {header_height}px !important;
}}

.ag-theme-streamlit .ag-cell,
.ag-theme-alpine .ag-cell,
.ag-theme-balham .ag-cell {{
  padding-left: 8px !important;
  padding-right: 8px !important;
}}
</style>
"""


def get_zebra_stripes_css(even_color: str = "#f9f9f9", odd_color: str = "#ffffff") -> str:
    """
    CSS for alternating row colors (zebra striping).

    Args:
        even_color: Background color for even rows (default: light gray)
        odd_color: Background color for odd rows (default: white)

    Returns:
        str: CSS string for zebra striping

    Example:
        >>> import streamlit as st
        >>> from streamlit_aggrid import get_zebra_stripes_css
        >>>
        >>> st.markdown(get_zebra_stripes_css(even_color="#f0f0f0"), unsafe_allow_html=True)
    """
    return f"""
<style>
.ag-row-even {{
  background-color: {even_color} !important;
}}

.ag-row-odd {{
  background-color: {odd_color} !important;
}}
</style>
"""
