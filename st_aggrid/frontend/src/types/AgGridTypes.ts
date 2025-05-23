import { GridApi, GridOptions } from "ag-grid-community"

export interface State {
  gridHeight: number
  gridOptions: GridOptions
  isRowDataEdited: boolean
  api?: GridApi
  enterprise_features_enabled: boolean
  debug: boolean
}
