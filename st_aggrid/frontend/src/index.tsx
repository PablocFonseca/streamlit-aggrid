import React from "react"
import { createRoot } from 'react-dom/client';
import AgGrid from "./AgGrid"

const domNode = document.getElementById("root")
if (domNode) {
   const root = createRoot(domNode)
   root.render(<AgGrid />)
  }
