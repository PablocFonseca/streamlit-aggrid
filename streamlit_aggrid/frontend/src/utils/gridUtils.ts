type CSSDict = { [key: string]: { [key: string]: string } }

export function getCSS(styles: CSSDict): string {
  const css: string[] = []
  for (const selector in styles) {
    let style = `${selector} {`
    for (const prop in styles[selector]) {
      style += `${prop}: ${styles[selector][prop]};`
    }
    style += "}"
    css.push(style)
  }
  return css.join("\n")
}

/**
 * Inject an optional JavaScript extension and return a cleanup function.
 *
 * CSS is deliberately rendered by React inside the component root instead of
 * being appended to document.head. Components V2 isolates styles in a shadow
 * root by default, so document-level styles cannot reach the grid.
 */
export function injectProScript(jsCode?: string): () => void {
  if (!jsCode) return () => undefined

  const script = document.createElement("script")
  script.textContent = jsCode
  document.body.appendChild(script)

  return () => script.remove()
}

export function parseJsCodeFromPython(v: string) {
  const JS_PLACEHOLDER = "::JSCODE::"
  const funcReg = new RegExp(`${JS_PLACEHOLDER}(.*?)${JS_PLACEHOLDER}`, "s")
  let match = funcReg.exec(v)
  if (match) {
    const funcStr = match[1]
    // eslint-disable-next-line
    return new Function("return " + funcStr)()
  } else {
    return v
  }
}
