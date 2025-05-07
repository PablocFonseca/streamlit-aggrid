import React from "react"

const GridToolBar = (props: any) => {
  if (props.enabled) {
    return (
      <div id="gridToolBar">
        <div className="ag-row-odd ag-row-no-focus ag-row ag-row-level-0 ag-row-position-absolute">
          <div className="">
            <div className="ag-cell-wrapper">{props.children}</div>
          </div>
        </div>
      </div>
    )
  }
  return <></>
}

export default GridToolBar