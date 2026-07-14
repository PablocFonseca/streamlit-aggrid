type CSSDict = { [key: string]: { [key: string]: string } }

const injectedScriptsByDocument = new WeakMap<
  Document,
  Set<string>
>()

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
 * Inject an optional JavaScript extension once per document and return a
 * lifecycle-compatible cleanup function. Script side effects cannot be undone
 * by removing the element, so content-keyed deduplication also prevents a
 * remounted or second grid from registering the same globals twice.
 *
 * CSS is deliberately rendered by React inside the component root instead of
 * being appended to document.head. Components V2 isolates styles in a shadow
 * root by default, so document-level styles cannot reach the grid.
 */
export function injectProScript(jsCode?: string): () => void {
  if (!jsCode) return () => undefined

  let scripts = injectedScriptsByDocument.get(document)
  if (!scripts) {
    scripts = new Set()
    injectedScriptsByDocument.set(document, scripts)
  }

  if (scripts.has(jsCode)) return () => undefined

  const script = document.createElement("script")
  script.textContent = jsCode
  document.body.appendChild(script)
  scripts.add(jsCode)

  return () => {
    // Removing a script element cannot undo the globals it registered. Keep
    // one content-keyed element per document so mounting a second grid (or
    // remounting the first) never executes the same extension twice.
  }
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
