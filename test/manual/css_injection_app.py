"""
Test CSS injection in Streamlit
This script helps verify if st.markdown CSS injection is working correctly
"""

import streamlit as st
from st_aggrid import AgGrid
import pandas as pd

st.set_page_config(page_title="CSS Injection Test", layout="wide")

st.title("CSS Injection Test")

# Test 1: Basic CSS injection on Streamlit elements
st.markdown("""
<style>
/* Test style for Streamlit elements - should work */
.test-element {
    background-color: #ffeb3b;
    padding: 20px;
    border-radius: 8px;
    border: 2px solid #f44336;
}

/* Test style for AG Grid - may NOT work due to iframe isolation */
.ag-theme-streamlit .ag-header {
    background-color: #ff0000 !important;
}

.ag-theme-streamlit .ag-row {
    background-color: #e3f2fd !important;
}

/* Custom class we'll try to apply */
.custom-grid-container {
    border: 5px solid purple !important;
    padding: 20px;
}
</style>
""", unsafe_allow_html=True)

# Test element outside the grid
st.markdown('<div class="test-element">✅ If this box has yellow background and red border, CSS injection is working for Streamlit elements</div>', unsafe_allow_html=True)

st.write("---")

# Create sample dataframe
df = pd.DataFrame({
    'A': [1, 2, 3, 4, 5],
    'B': [10, 20, 30, 40, 50],
    'C': ['foo', 'bar', 'baz', 'qux', 'quux']
})

st.subheader("AG Grid Test")
st.markdown("**Expected behavior:**")
st.markdown("- ❌ Grid header will likely NOT be red (iframe isolation)")
st.markdown("- ❌ Grid rows will likely NOT be light blue (iframe isolation)")

# Try with a wrapper div
st.markdown('<div class="custom-grid-container">', unsafe_allow_html=True)

result = AgGrid(
    df,
    key="css_test_grid",
    height=300,
    theme="streamlit"
)

st.markdown('</div>', unsafe_allow_html=True)

st.write("---")

# Instructions for testing
st.subheader("How to verify:")
st.markdown("""
1. **Open browser DevTools** (F12 or Right-click → Inspect)
2. **Check the Elements tab**:
   - Look for `<style>` tags in the `<head>` section
   - Your custom CSS should be there
3. **Inspect the AG Grid component**:
   - Look for `<iframe>` tags
   - If AG Grid is inside an iframe, your CSS won't affect it
   - Click into the iframe to inspect its internal structure
4. **Check the Console** for any errors

**Alternative solutions if CSS doesn't work:**
- Use the `custom_css` parameter in AgGrid (if available)
- Inject CSS directly in the component's frontend code
- Use JavaScript to inject styles: `JsCode` with style manipulation
""")

st.write("---")
st.subheader("Component Info")
st.write(f"Grid return data shape: {result.data.shape}")

# Add JavaScript injection test
st.subheader("JavaScript CSS Injection Test")
st.markdown("This attempts to inject CSS via JavaScript in the component:")

from st_aggrid import JsCode

# Try injecting CSS via JavaScript after grid loads
js_css_injection = JsCode("""
function(params) {
    // Try to inject CSS via JavaScript
    const style = document.createElement('style');
    style.textContent = `
        .ag-header {
            background-color: green !important;
        }
    `;
    document.head.appendChild(style);
    console.log('CSS injection via JS attempted');
}
""")

AgGrid(
    df,
    key="js_css_test_grid",
    height=300,
    theme="streamlit",
    gridOptions={
        "onGridReady": js_css_injection
    },
    allow_unsafe_jscode=True
)

st.info("Check browser console for 'CSS injection via JS attempted' message")
