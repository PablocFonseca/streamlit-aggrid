import React from "react"

const ManualUpdateButton = (props: any) => {
  if (props.manualUpdate) {
    return (
      <button onClick={props.onClick} style={{ marginLeft: 5, marginRight: 5 }}>
        Update
      </button>
    )
  }
  return <></>
}

export default ManualUpdateButton