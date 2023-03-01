from enum import Enum, IntEnum, IntFlag, Flag, auto, EnumMeta

class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True   
class BaseEnum(Enum, metaclass=MetaEnum):
    pass
class GridUpdateMode(Flag):
    NO_UPDATE = auto()
    MANUAL = auto()
    VALUE_CHANGED = auto()
    SELECTION_CHANGED = auto()
    FILTERING_CHANGED = auto()
    SORTING_CHANGED = auto()
    COLUMN_RESIZED = auto()
    COLUMN_MOVED = auto()
    COLUMN_PINNED = auto()
    COLUMN_VISIBLE = auto()
    MODEL_CHANGED = VALUE_CHANGED | SELECTION_CHANGED | FILTERING_CHANGED | SORTING_CHANGED 
    COLUMN_CHANGED =  COLUMN_RESIZED | COLUMN_MOVED | COLUMN_VISIBLE | COLUMN_PINNED
    GRID_CHANGED = MODEL_CHANGED | COLUMN_CHANGED

class DataReturnMode(IntEnum):
    AS_INPUT = 0
    FILTERED = 1
    FILTERED_AND_SORTED = 2

class ColumnsAutoSizeMode(IntEnum):
    NO_AUTOSIZE = 0
    FIT_ALL_COLUMNS_TO_VIEW = 1
    FIT_CONTENTS = 2

class AgGridTheme(BaseEnum):
    STREAMLIT = "streamlit"
    ALPINE = "alpine"
    BALHAM = "balham"
    MATERIAL = "material"

class ExcelExportMode(BaseEnum):
    NONE = "NONE"
    MANUAL = "MANUAL" #Add a download button to the grid
    FILE_BLOB_IN_GRID_RESPONSE = "FILE_BLOB_IN_GRID_RESPONSE" #include in grid's return an Excel Blob Property with file binary encoded as B64 String
    TRIGGER_DOWNLOAD = "TRIGGER_DOWNLOAD" #After Grid Refreshes triggers the download.
    SHEET_BLOB_IN_GRID_RESPONSE = "SHEET_BLOB_IN_GRID_RESPONSE" #include in grid's return a SheetlBlob Property with sheet binary encoded as B64 String. Meant to be used with MULTIPLE
    MULTIPLE_SHEETS = "MULTIPLE_SHEETS" #Triggers the download and add other B64 encoded sheets. Send sheets as a list using excel_export_extra_sheets parameter

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
        match_js_comment_expression = r"\/\*[\s\S]*?\*\/|([^\\:]|^)\/\/.*$"
        js_code = re.sub(re.compile(match_js_comment_expression, re.MULTILINE), r"\1", js_code)
        
        match_js_spaces = r"\s+(?=(?:[^\'\"]*[\'\"][^\'\"]*[\'\"])*[^\'\"]*$)"
        one_line_jscode = re.sub(match_js_spaces, " ", js_code, flags=re.MULTILINE)
        
        js_placeholder = "--x_x--0_0--"
        one_line_jscode = re.sub(r"\s+|\r\s*|\n+", " ", js_code, flags=re.MULTILINE)
        
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