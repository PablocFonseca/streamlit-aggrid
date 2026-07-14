type Mapper = (value: any) => any

function mapObject(
  obj: Record<string, any>,
  fn: Mapper,
  keysToIgnore: string[]
): Record<string, any> {
  return Object.keys(obj).reduce<Record<string, any>>((result, key) => {
    result[key] = keysToIgnore.includes(key) ? obj[key] : fn(obj[key])
    return result
  }, {})
}

function deepMap(obj: any, fn: Mapper, keysToIgnore: string[] = []): any {
  const deepMapper = (value: any): any =>
    value !== null && typeof value === "object"
      ? deepMap(value, fn, keysToIgnore)
      : fn(value)

  if (Array.isArray(obj)) return obj.map(deepMapper)
  if (obj !== null && typeof obj === "object") {
    return mapObject(obj, deepMapper, keysToIgnore)
  }
  return obj
}

export { deepMap }
