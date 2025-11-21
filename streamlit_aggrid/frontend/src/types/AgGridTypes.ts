import { GridApi, GridOptions, ColumnState } from "ag-grid-community"

export interface State {
  gridHeight: number
  gridOptions: GridOptions
  isRowDataEdited: boolean
  api?: GridApi
  enterprise_features_enabled: boolean
  debug: boolean
  editedRows: Set<any>;
  isMaximized: boolean;
  savedColumnState?: ColumnState[];
}
