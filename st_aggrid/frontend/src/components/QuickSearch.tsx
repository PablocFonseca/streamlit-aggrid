import React from "react"

const QuickSearch = (props: any) => {
  if (props.enableQuickSearch) {
    return (
      <input
        className="ag-cell-value"
        type="text"
        onChange={props.onChange}
        onKeyUp={props.showOverlay}
        placeholder="quickfilter..."
        style={{ marginLeft: 5, marginRight: 5 }}
      />
    )
  }
  return <></>
}

export default QuickSearch