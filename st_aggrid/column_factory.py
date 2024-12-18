
from streamlit.elements.lib.column_types import Column, NumberColumn
from st_aggrid.grid_options import ColumnDefinition
from st_aggrid import JsCode


def convert_st_column(field: str, st_column: Column) -> ColumnDefinition:
    c : ColumnDefinition = {}
    c['field'] = field

    if (label := st_column.get('label', None)) is not None:
        c['headerName'] = label

    if (width := st_column.get("width", None)) is not None:
        #l 432, m 232, s 107
        match width:
            case 'large':
                c['width'] = 400
            case "medium":
                c["width"] = 200
            case 'small':
                c['width'] = 75
            case _:
                pass
    
    if help := st_column.get("help", None) is not None:
          c['tooltipValueGetter'] = JsCode(f"function(){{return `{help}`}}")

    if (disabled := st_column.get("disabled", None)) is not None:
        c["editable"] = not disabled

    if (required := st_column.get("required", None)) is not None:
        # TODO:implement requiredCellEditor https://plnkr.co/edit/qT2fOz7L5mzG846K?preview
        # or handle in cellEditionEvents
        pass

    return c

def convert_st_NumberColumn(field, st_numberColumn: NumberColumn) -> ColumnDefinition:
    c = convert_st_column(field, st_numberColumn)

    if (default := st_numberColumn.get("default", None)) is not None:
        # TODO: implement behavior for when num_rows = dynamic https://blog.ag-grid.com/add-new-rows-using-a-pinned-row-at-the-top-of-the-grid/ 
        pass

    if (type_config := st_numberColumn.get("type_config", None)) is not None:
       
        
        if (format := type_config.get("format", None)) is not None:
            format_fn = JsCode("""
            function numberFormatter(val){
                function pythonFormat(value, formatString) {
                    // Match the format specifier within {}
                    const match = formatString.match(/{(.*?):([\d\.\,]*)([a-zA-Z%]*)}/);
                    if (!match) {
                        throw new Error("Invalid format string");
                    }

                    // Extract parts of the format string
                    const [, variable, precision, specifier] = match;

                    // Ensure the input value is a number
                    if (typeof value !== "number") {
                        throw new TypeError("Value must be a number");
                    }

                    let result = value;

                    // Apply precision or fixed-point formatting
                    if (precision && precision.includes(".")) {
                        const [, digits] = precision.split(".");
                        result = result.toFixed(Number(digits));
                    }

                    // Apply specifiers
                    switch (specifier) {
                        case "f":
                            result = parseFloat(result); // Ensure no extra zeros
                            break;
                        case "%":
                            result = (result * 100).toFixed(precision ? Number(precision.split(".")[1]) : 0) + "%";
                            break;
                        case ",":
                            result = Number(result).toLocaleString();
                            break;
                        default:
                            if (specifier) {
                                throw new Error(`Unknown format specifier: ${specifier}`);
                            }
                    }

                    // Handle thousand separators (with or without specifier)
                    if (precision && precision.includes(",") && !specifier) {
                        result = Number(result).toLocaleString();
                    }

                    return result.toString();
                };
            return pythonFormat(Number(val.value), "{:.2f}");
            }
           """)

            c["valueFormatter"] = format_fn
        

        if (min_value := type_config.get("min_value", None)) is not None:
            # TODO: implement behavior for when num_rows = dynamic https://blog.ag-grid.com/add-new-rows-using-a-pinned-row-at-the-top-of-the-grid/ 
            pass

        if (max_value := type_config.get("max_value", None)) is not None:
            # TODO: implement behavior for when num_rows = dynamic https://blog.ag-grid.com/add-new-rows-using-a-pinned-row-at-the-top-of-the-grid/
            pass

        if (step := type_config.get("step", None)) is not None:
            # TODO: implement behavior for when num_rows = dynamic https://blog.ag-grid.com/add-new-rows-using-a-pinned-row-at-the-top-of-the-grid/
            pass

    return c