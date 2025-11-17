import { GridOptions } from "ag-grid-community"
import { cloneDeep } from "lodash"
import { deepMap } from "../utils"
import { parseJsCodeFromPython } from "./gridUtils"
import { columnFormaters } from "../customColumns"
import { ThemeParser } from "../ThemeParser"


export function parseGridOptions(props: any){
    console.log("=============")
    console.log(props)
    let gridOptions: GridOptions = cloneDeep(props.gridOptions)

    if (props.allow_unsafe_jscode) {
        console.warn("flag allow_unsafe_jscode is on.")
        gridOptions = deepMap(gridOptions, parseJsCodeFromPython, ["rowData"])
    }

    if (!("getRowId" in gridOptions)) {
        console.warn("getRowId was not set. Auto Rows hashes will be used as row ids.")
    }

    //adds custom columnFormatters
    gridOptions.columnTypes = Object.assign(
        gridOptions.columnTypes || {},
        columnFormaters
    )

    //processTheming
    const themeParser = new ThemeParser()
    let streamlitTheme = props.theme
    let agGridTheme = props.theme
    gridOptions.theme = themeParser.parse(agGridTheme, streamlitTheme)

    return gridOptions
}

export function parseData(props: any){

    var data = props.data
    var gridOptions_rowData = props.gridOptions?.rowData 
    var rowData = []

        // Handle rowData: use data.table if available, otherwise check gridOptions.rowData
        if (data) {

          //Quick fix for bigInt serializations. Python side should avoid sending non-json-serializabe entities.
          const bigintReplacer = (key: any, value: any): any => {
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
          } catch (e) {}

          // Filter out index columns and select only data fields
          const dataFields = arrowTable?.schema?.fields
            ?.map((f: any) => f.name)
            .filter((name: string) => !indexColumns.includes(name)) || []
          console.log("+++++++", data)
          const filteredTable = arrowTable.select(dataFields)
          rowData = JSON.parse(JSON.stringify(filteredTable.toArray(), bigintReplacer))  
        } 
         // If data is null but gridOptions.rowData contains JSON string, parse it
         else if (gridOptions_rowData && typeof gridOptions_rowData === 'string') {
         
          try {
            rowData = JSON.parse(gridOptions_rowData)
          } catch (e) {
            console.error('Failed to parse gridOptions.rowData as JSON:', e)
            throw e
          }
        } 
        return rowData
}