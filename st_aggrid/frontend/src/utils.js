// stole from https://github.com/andfanilo/streamlit-echarts/blob/master/streamlit_echarts/frontend/src/utils.js Thanks andfanilo
function mapObject(obj, fn) {
    return Object.keys(obj).reduce((res, key) => {
        res[key] = fn(obj[key])
        return res
    }, {})
}

function deepMap(obj, fn) {
    const deepMapper = (val) =>
        val !== null && typeof val === "object" ? deepMap(val, fn) : fn(val)
    if (Array.isArray(obj)) {
        return obj.map(deepMapper)
    }
    if (typeof obj === "object") {
        return mapObject(obj, deepMapper)
    }
    return obj
}

export default deepMap
