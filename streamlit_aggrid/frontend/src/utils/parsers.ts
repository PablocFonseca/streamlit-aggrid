import { GridOptions } from "ag-grid-community"
import { cloneDeep } from "lodash"
import { deepMap } from "../utils"
import { parseJsCodeFromPython } from "./gridUtils"
import { columnFormaters } from "../customColumns"
import { ThemeParser, type StAggridThemeOptions } from "../ThemeParser"


export function parseGridOptions(
    gridOptions: GridOptions,
    allowUnsafeJscode: boolean,
    theme?: StAggridThemeOptions
): GridOptions {
    // gridOptions crosses the Python -> host -> JS boundary; it can arrive as a
    // JSON string (or missing) rather than a plain object.
    const raw = typeof gridOptions === "string" ? JSON.parse(gridOptions) : gridOptions
    let parsedGridOptions: GridOptions =
        raw && typeof raw === "object" ? cloneDeep(raw) : {}

    if (allowUnsafeJscode) {
        console.warn("flag allow_unsafe_jscode is on.")
        parsedGridOptions = deepMap(parsedGridOptions, parseJsCodeFromPython, ["rowData"])
    }

    if (!("getRowId" in parsedGridOptions)) {
        // The renderer installs its positional ::auto_unique_id:: callback
        // after parsing ordinary Python data. Keep this diagnostic out of the
        // production warning channel because it is expected for normal grids.
        console.debug("getRowId was not set; checking for generated row IDs.")
    }

    //adds custom columnFormatters
    parsedGridOptions.columnTypes = Object.assign(
        parsedGridOptions.columnTypes || {},
        columnFormaters
    )

    //processTheming
    const themeParser = new ThemeParser()
    parsedGridOptions.theme = themeParser.parse(theme)

    return parsedGridOptions
}

export function parseData(
    data: any,
    gridOptionsRowData?: any
): any[] {

    var rowData: any[] = []

    // Handle rowData: use data.table if available, otherwise check gridOptions.rowData
    if (data) {

        //Quick fix for bigInt serializations. Python side should avoid sending non-json-serializabe entities.
        const bigintReplacer = (_key: any, value: any): any => {
            if (typeof value === "bigint") {
                return Number(value)
            }
            if (Array.isArray(value)) {
                return value.map((item: any) => bigintReplacer(null, item))
            }
            if (value && typeof value === "object") {
                // Recursively handle object properties
                const replacedObj: any = {}
                for (const prop in value) {
                    if (Object.prototype.hasOwnProperty.call(value, prop)) {
                        replacedObj[prop] = bigintReplacer(prop, value[prop])
                    }
                }
                return replacedObj
            }
            return value
        }
        const arrowTable = data //.dataTable || data.table

        // Extract index column names from pandas metadata
        let indexColumns: string[] = []
        try {
            const pandasMeta = JSON.parse(arrowTable?.schema?.metadata?.get('pandas') || '{}')
            indexColumns = pandasMeta.index_columns || []
        } catch {}

        // Filter out index columns and select only data fields
        const dataFields = arrowTable?.schema?.fields
            ?.map((f: any) => f.name)
            .filter((name: string) => !indexColumns.includes(name)) || []
            
        const filteredTable = arrowTable.select(dataFields)
        rowData = JSON.parse(JSON.stringify(filteredTable.toArray(), bigintReplacer))
    }
    // If data is null but gridOptions.rowData contains JSON string, parse it
    else if (gridOptionsRowData && typeof gridOptionsRowData === 'string') {

        try {
            rowData = JSON.parse(gridOptionsRowData)
        } catch (e) {
            console.error('Failed to parse gridOptions.rowData as JSON:', e)
            throw e
        }
    }
    return rowData
}
