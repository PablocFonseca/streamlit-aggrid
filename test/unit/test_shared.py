"""Unit tests for shared helpers (JsCode, walk_gridOptions, themes, enums)."""

import pytest

from streamlit_aggrid.shared import (
    DataReturnMode,
    GridUpdateMode,
    JsCode,
    StAggridTheme,
    walk_gridOptions,
)


class TestJsCode:
    def test_wraps_with_placeholder(self):
        code = JsCode("function() { return 1; }")
        assert code.js_code.startswith("::JSCODE::")
        assert code.js_code.endswith("::JSCODE::")

    def test_collapses_to_one_line(self):
        code = JsCode(
            """
            function(params) {
                return params.value;
            }
            """
        )
        assert "\n" not in code.js_code

    def test_strips_line_comments(self):
        code = JsCode(
            """
            function() {
                // a comment
                return 1;
            }
            """
        )
        assert "a comment" not in code.js_code

    def test_strips_block_comments(self):
        code = JsCode("function() { /* block */ return 1; }")
        assert "block" not in code.js_code

    def test_preserves_urls_with_double_slash(self):
        code = JsCode("function() { return 'http://example.com'; }")
        assert "http://example.com" in code.js_code


class TestWalkGridOptions:
    def test_applies_function_to_leaves(self):
        go = {"a": 1, "nested": {"b": 2}, "list": [{"c": 3}]}
        walk_gridOptions(go, lambda v: v * 10 if isinstance(v, int) else v)
        assert go["a"] == 10
        assert go["nested"]["b"] == 20
        assert go["list"][0]["c"] == 30

    def test_replaces_jscode_leaves(self):
        code = JsCode("function() {}")
        go = {"columnDefs": [{"cellRenderer": code}]}
        walk_gridOptions(go, lambda v: v.js_code if isinstance(v, JsCode) else v)
        assert go["columnDefs"][0]["cellRenderer"] == code.js_code


class TestStAggridTheme:
    def test_default_theme_is_a_valid_custom_theme(self):
        theme = StAggridTheme().withParams(fontSize=12)

        assert theme["themeName"] == "custom"
        assert theme["params"] == {"fontSize": 12}

    def test_base_sets_custom_theme(self):
        theme = StAggridTheme(base="quartz")
        assert theme["themeName"] == "custom"
        assert theme["base"] == "quartz"

    def test_base_is_fluent(self):
        theme = StAggridTheme()

        assert theme.base("balham") is theme
        assert theme["base"] == "balham"

    def test_fluent_params_and_parts(self):
        theme = (
            StAggridTheme(base="alpine")
            .withParams(fontSize=12)
            .withParams(accentColor="#ff0000")
            .withParts("iconSetQuartz")
        )
        assert theme["params"] == {"fontSize": 12, "accentColor": "#ff0000"}
        assert theme["parts"] == ["iconSetQuartz"]

    def test_parts_preserve_order_and_readded_part_moves_last(self):
        theme = StAggridTheme(base="quartz").withParts(
            "iconSetAlpine",
            "colorSchemeDark",
            "iconSetMaterial",
        )

        theme.withParts("iconSetAlpine")

        assert theme["parts"] == [
            "colorSchemeDark",
            "iconSetMaterial",
            "iconSetAlpine",
        ]

    @pytest.mark.parametrize("base", ["material", "typo", ""])
    def test_invalid_base_is_rejected(self, base):
        with pytest.raises(ValueError, match="not a valid custom theme base"):
            StAggridTheme(base=base)

    def test_invalid_part_is_rejected_without_mutating_theme(self):
        theme = StAggridTheme(base="quartz").withParts("colorSchemeDark")

        with pytest.raises(ValueError, match="Unsupported custom theme part"):
            theme.withParts("notAThemePart")

        assert theme["parts"] == ["colorSchemeDark"]

    def test_parts_must_be_separate_strings(self):
        with pytest.raises(TypeError, match="separate string arguments"):
            StAggridTheme().withParts(["colorSchemeDark"])

    def test_is_json_serializable(self):
        import json

        theme = StAggridTheme(base="balham").withParams(
            fontSize=10,
            focusShadow={"radius": 2, "color": "#ff0000"},
        )
        encoded = json.loads(json.dumps(theme))
        assert encoded["base"] == "balham"
        assert encoded["params"]["focusShadow"]["radius"] == 2


class TestEnums:
    def test_data_return_mode_from_string(self):
        assert DataReturnMode("FILTERED") is DataReturnMode.FILTERED

    def test_grid_update_mode_flags(self):
        assert GridUpdateMode.MODEL_CHANGED & GridUpdateMode.VALUE_CHANGED
        assert GridUpdateMode.GRID_CHANGED & GridUpdateMode.COLUMN_MOVED
        assert not (GridUpdateMode.MODEL_CHANGED & GridUpdateMode.COLUMN_RESIZED)
