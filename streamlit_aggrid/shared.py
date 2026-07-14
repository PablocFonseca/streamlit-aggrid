from enum import Enum, IntEnum, Flag, auto, EnumMeta
import json
import pathlib
from typing import Any, Literal, Mapping, Optional, TypedDict

DEFAULT_COLUMN_PROPS = [
    "cellDataType",
    "checkboxSelection",
    "suppressNavigable",
    "editable",
    "cellEditorPopupPosition",
    "singleClickEdit",
    "useValueParserForImport",
    "autoHeaderHeight",
    "suppressHeaderMenuButton",
    "suppressHeaderFilterButton",
    "suppressHeaderContextMenu",
    "headerCheckboxSelectionFilteredOnly",
    "headerCheckboxSelectionCurrentPageOnly",
    "lockPinned",
    "enablePivot",
    "autoHeight",
    "wrapText",
    "enableCellChangeFlash",
    "rowDrag",
    "rowGroup",
    "enableRowGroup",
    "enableValue",
    "defaultAggFunc",
    "sortable",
    "unSortIcon",
    "resizable",
    "suppressSizeToFit",
    "suppressAutoSize",
    "marryChildren",
    "suppressStickyLabel",
    "openByDefault",
    "suppressColumnsToolPanel",
    "suppressFiltersToolPanel",
    "suppressSpanHeaderHeight",
    "filter",
]


def getAllGridOptions():
    jsonRoot = pathlib.Path(__file__).parent / "json"
    allOptions = json.load(open(jsonRoot / "gridOptions.json"))
    return allOptions


def getAllColumnProps():
    jsonRoot = pathlib.Path(__file__).parent / "json"
    allProps = json.load(open(jsonRoot / "columnProps.json"))
    return allProps


def getAllGridEvents():
    jsonRoot = pathlib.Path(__file__).parent / "json"
    allGridEvents = json.load(open(jsonRoot / "gridEvents.json"))
    return allGridEvents


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
    MODEL_CHANGED = (
        VALUE_CHANGED | SELECTION_CHANGED | FILTERING_CHANGED | SORTING_CHANGED
    )
    COLUMN_CHANGED = COLUMN_RESIZED | COLUMN_MOVED | COLUMN_VISIBLE | COLUMN_PINNED
    GRID_CHANGED = MODEL_CHANGED | COLUMN_CHANGED


class DataReturnMode(str, Enum):
    AS_INPUT = "AS_INPUT"
    FILTERED = "FILTERED"
    FILTERED_AND_SORTED = "FILTERED_AND_SORTED"
    MINIMAL = "MINIMAL"
    CUSTOM = "CUSTOM"


class ColumnsAutoSizeMode(IntEnum):
    NO_AUTOSIZE = 0
    FIT_ALL_COLUMNS_TO_VIEW = 1
    FIT_CONTENTS = 2


class ExcelExportMode(BaseEnum):
    NONE = "NONE"
    MANUAL = "MANUAL"  # Add a download button to the grid
    FILE_BLOB_IN_GRID_RESPONSE = "FILE_BLOB_IN_GRID_RESPONSE"  # include in grid's return an Excel Blob Property with file binary encoded as B64 String
    TRIGGER_DOWNLOAD = "TRIGGER_DOWNLOAD"  # After Grid Refreshes triggers the download.
    SHEET_BLOB_IN_GRID_RESPONSE = "SHEET_BLOB_IN_GRID_RESPONSE"  # include in grid's return a SheetlBlob Property with sheet binary encoded as B64 String. Meant to be used with MULTIPLE
    MULTIPLE_SHEETS = "MULTIPLE_SHEETS"  # Triggers the download and add other B64 encoded sheets. Send sheets as a list using excel_export_extra_sheets parameter


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
        js_code = re.sub(
            re.compile(match_js_comment_expression, re.MULTILINE), r"\1", js_code
        )

        js_placeholder = "::JSCODE::"
        one_line_jscode = re.sub(r"\s+|\r\s*|\n+", " ", js_code, flags=re.MULTILINE)

        self.js_code = f"{js_placeholder}{one_line_jscode}{js_placeholder}"


class JsCodeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, JsCode):
            return o.js_code

        return super().default(o)


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


# add deprecation note
class AgGridTheme(BaseEnum):
    STREAMLIT = "streamlit"
    ALPINE = "alpine"
    BALHAM = "balham"
    MATERIAL = "material"


_CUSTOM_THEME_BASES = ("alpine", "balham", "quartz")
_CUSTOM_THEME_PARTS = (
    "colorSchemeLight",
    "colorSchemeLightWarm",
    "colorSchemeLightCold",
    "colorSchemeDark",
    "colorSchemeDarkWarm",
    "colorSchemeDarkBlue",
    "iconSetQuartz",
    "iconSetQuartzLight",
    "iconSetQuartzBold",
    "iconSetAlpine",
    "iconSetMaterial",
    "iconSetQuartzRegular",
)


class StAggridThemeType(TypedDict, total=False):
    themeName: Literal["custom"]
    base: Literal["alpine", "balham", "quartz"]
    params: Mapping[str, Any]
    parts: list[str]


# Subclassing a dict keeps the theme directly JSON serializable.
class StAggridTheme(dict):
    def __init__(self, base: Optional[Literal["alpine", "balham", "quartz"]] = None):
        super()
        self["themeName"] = "custom"
        self["params"] = {}
        self["parts"] = []
        if base is not None:
            self.base(base)

    def base(
        self, base: Literal["alpine", "balham", "quartz"]
    ) -> "StAggridTheme":
        if base not in _CUSTOM_THEME_BASES:
            raise ValueError(
                f"{base!r} is not a valid custom theme base. Expected one of: "
                f"{', '.join(_CUSTOM_THEME_BASES)}."
            )
        self["themeName"] = "custom"
        self["base"] = base
        return self

    def withParams(self, **params: Any) -> "StAggridTheme":
        self["themeName"] = "custom"
        self["params"].update(params)
        return self

    def withParts(self, *parts: str) -> "StAggridTheme":
        invalid_types = [part for part in parts if not isinstance(part, str)]
        if invalid_types:
            raise TypeError(
                "Theme parts must be passed as separate string arguments, for "
                "example withParts('colorSchemeDark', 'iconSetMaterial')."
            )

        invalid_parts = [part for part in parts if part not in _CUSTOM_THEME_PARTS]
        if invalid_parts:
            raise ValueError(
                f"Unsupported custom theme part(s): {', '.join(invalid_parts)}. "
                f"Expected one of: {', '.join(_CUSTOM_THEME_PARTS)}."
            )

        # AG Grid resolves competing parts of the same feature by using the
        # last one. Preserve caller order and move re-added parts to the end so
        # this behavior is deterministic across Python processes.
        ordered_parts = list(self["parts"])
        for part in parts:
            if part in ordered_parts:
                ordered_parts.remove(part)
            ordered_parts.append(part)

        self["themeName"] = "custom"
        self["parts"] = ordered_parts
        return self
