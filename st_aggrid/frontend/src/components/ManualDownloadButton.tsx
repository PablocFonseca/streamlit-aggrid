import React from "react"

const ManualDownloadButton = (props: any) => {
  if (props.enabled) {
    return (
      <button onClick={props.onClick} style={{ marginLeft: 5, marginRight: 5 }}>
        Download
      </button>
    )
  }
  return <></>
}

export default ManualDownloadButton