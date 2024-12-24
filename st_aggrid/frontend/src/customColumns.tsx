import { compareAsc, format, parseISO } from "date-fns"

import { duration } from "moment"


//TODO: mover formaters to gridOptionsBuilder options
function dateFormatter(isoString: string, formaterString: string): String {
  try {
    let date = parseISO(isoString)
    return format(date, formaterString)
  } catch {
    return isoString
  } finally {
  }
}

function currencyFormatter(number: any, currencySymbol: string): String {
  let n = Number.parseFloat(number)
  if (!Number.isNaN(n)) {
    return currencySymbol + n.toFixed(2)
  } else {
    return number
  }
}

function numberFormatter(number: any, precision: number): String {
  let n = Number.parseFloat(number)
  if (!Number.isNaN(n)) {
    return n.toFixed(precision)
  } else {
    return number
  }
}

const columnFormaters = {
  dateColumnFilter: {
    filter: "agDateColumnFilter",
    filterParams: {
      comparator: (filterValue: any, cellValue: string) =>
        compareAsc(parseISO(cellValue), filterValue),
    },
  },
  numberColumnFilter: {
    filter: "agNumberColumnFilter",
  },
  shortDateTimeFormat: {
    valueFormatter: (params: any) =>
      dateFormatter(params.value, "dd/MM/yyyy HH:mm"),
  },
  customDateTimeFormat: {
    valueFormatter: (params: any) =>
      dateFormatter(params.value, params.column.colDef.custom_format_string),
  },
  customNumericFormat: {
    valueFormatter: (params: any) =>
      numberFormatter(params.value, params.column.colDef.precision ?? 2),
  },
  customCurrencyFormat: {
    valueFormatter: (params: any) =>
      currencyFormatter(
        params.value,
        params.column.colDef.custom_currency_symbol
      ),
  },
  timedeltaFormat: {
    valueFormatter: (params: any) => duration(params.value).humanize(true),
  },
}

export {columnFormaters}