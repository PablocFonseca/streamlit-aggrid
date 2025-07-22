import _ from "lodash"
import { IRowNode, DetailGridInfo, GridApi } from "ag-grid-community"
import { eventDataWhiteList } from "../constants"

export async function getGridReturnValue(
  api: GridApi | undefined,
  enterprise_features_enabled: boolean,
  gridOptions: any,
  props: any,
  e: any,
  streamlitRerunEventTriggerName: string
) {
  function fetch_node_props(n: IRowNode | null): any {
    if (n == null) {
      return null
    }
    return {
      id: n.id,
      data: n.data,
      rowIndex: n.rowIndex,
      rowTop: n.rowTop,
      displayed: n.displayed,
      isHovered: n.isHovered(),
      //isFullWidthCell: n.isFullWidthCell(),
      expanded: n.expanded,
      isExpandable: n.expanded,
      group: n.group,
      groupData: n.groupData,
      aggData: n.aggData,
      key: n.key,
      field: n.field,
      rowGroupColumn: n.rowGroupColumn?.getColId(),
      rowGroupIndex: n.rowIndex,
      footer: n.footer,
      parent: fetch_node_props(n.parent),
      firstChild: n.firstChild,
      lastChild: n.lastChild,
      childIndex: n.childIndex,
      level: n.level,
      uiLevel: n.uiLevel,
      allChildrenCount: n.allChildrenCount,
      leafGroup: n.leafGroup,
      //sibling: fetch_node_props(n.sibling), //this is causing stack overvlow errors TODO: revisit what needs to be returned on grid events.
      rowHeight: n.rowHeight,
      master: n.master,
      detail: n.detail,
      rowPinned: n.rowPinned,
      isRowPinned: n.isRowPinned(),
      selectable: n.selectable,
      isSelected: n.isSelected(),
    }
  }

  let nodes: any[] = []
  api?.forEachNode((n: any) => {
    nodes.push(fetch_node_props(n))
  })

  let rowsAfterFilter: any[] = []
  api?.forEachNodeAfterFilter((row: { group: any; id: any }) => {
    if (!row.group) {
      rowsAfterFilter.push(row.id)
    }
  })

  let rowsAfterSortAndFilter: any[] = []
  api?.forEachNodeAfterFilterAndSort((row: { group: any; id: any }) => {
    if (!row.group) {
      rowsAfterSortAndFilter.push(row.id)
    }
  })

  let selected: any = []
  if (enterprise_features_enabled) {
    api?.forEachDetailGridInfo((d: DetailGridInfo) => {
      d.api?.forEachNode((n: { isSelected: () => any; id: any }) => {
        if (n.isSelected()) {
          selected.push(n.id)
        }
      })
    })
  } else {
    api?.forEachNode((n: { isSelected: () => any; id: any }) => {
      if (n.isSelected()) {
        selected.push(n.id)
      }
    })
  }

  function cleanEventKeys(obj: any, root = "", level = 0) {
    if (Array.isArray(obj)) {
      obj.forEach((v) => {
        return cleanEventKeys(v, root, level + 1)
      })
    } else if (typeof obj === "object") {
      Object.keys(obj).forEach(function (key) {
        if (level > 3) return
        if (key === "data") return
        let fullKey = [root, key].filter((v) => v !== "").join(".")

        if (!eventDataWhiteList.includes(fullKey)) {
          delete obj[key]
        } else if (typeof obj[key] === "object" && obj[key] !== null) {
          cleanEventKeys(obj[key], fullKey, level + 1)
        }
      })
    }
    return obj
  }

  let cleanEventData = cleanEventKeys(_.cloneDeep(e))
  cleanEventData["streamlitRerunEventTriggerName"] =
    streamlitRerunEventTriggerName

  let returnValue = {
    originalDtypes: props.args.frame_dtypes,
    nodes: nodes,
    selectedItems: api?.getSelectedRows(),
    gridState: api?.getState(),
    columnsState: api?.getColumnState(),
    gridOptions: JSON.stringify(gridOptions), //performance bottleneck
    rowIdsAfterFilter: rowsAfterFilter,
    rowIdsAfterSortAndFilter: rowsAfterSortAndFilter,
    eventData: cleanEventData,
  }
  return returnValue
}
