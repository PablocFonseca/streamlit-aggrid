from enum import IntEnum, IntFlag
class GridUpdateMode(IntFlag):
    NO_UPDATE = 0b0000
    MANUAL = 0b0001
    VALUE_CHANGED = 0b0010
    SELECTION_CHANGED = 0b0100
    FILTERING_CHANGED = 0b1000
    SORTING_CHANGED = 0b10000
    MODEL_CHANGED = 0b11111

class DataReturnMode(IntEnum):
    AS_INPUT = 0
    FILTERED = 1
    FILTERED_AND_SORTED = 2

# stole from https://github.com/andfanilo/streamlit-echarts/blob/master/streamlit_echarts/frontend/src/utils.js Thanks andfanilo
class JsCode:
    def __init__(self, js_code: str):
        """Wrapper around a js function to be injected on gridOptions.
        code is not checked at all. 
        set allow_unsafe_jscode=True on AgGrid call to use it.
        Code is rebuilt on client using new Function Syntax (https://javascript.info/new-function)
        
        Args:
            js_code (str): javascript function code as str
        """        
        import re
        js_placeholder = "--x_x--0_0--"
        one_line_jscode = re.sub(r"\s+|\n+", " ", js_code)
        self.js_code = f"{js_placeholder}{one_line_jscode}{js_placeholder}"

def walk_gridOptions(go, func):
    """Recursively walk grid options applying func at each leaf node

    Args:
        go (dict): gridOptions dictionary
        func (callable): a function to apply at leaf nodes
    """        
    from collections.abc import Mapping

    if isinstance(go, (Mapping, list)):
        for i, k in enumerate(go):

            if isinstance(go[k], Mapping):
                walk_gridOptions(go[k], func)
            elif isinstance(go[k], list):
                for j in go[k]:
                    walk_gridOptions(j, func)
            else:
                go[k] = func(go[k])