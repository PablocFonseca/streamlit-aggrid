
var reISO = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2}(?:\.{0,1}\d*))(?:Z|(\+|-)([\d|:]*))?$/;
var reMsAjax = /^\/Date\((d|-|.*)\)[\/|\\]$/;

export function jsonDateParser(_: string, value: any) {
    
    var parsedValue = value;
    if (typeof value === 'string') {
        var a = reISO.exec(value);
        if (a) {
            parsedValue = new Date(value);
        } else {
            a = reMsAjax.exec(value);
            if (a) {
                var b = a[1].split(/[-+,.]/);
                parsedValue = new Date(b[0] ? +b[0] : 0 - +b[1]);
            }
        }
    }
    
    return parsedValue;
}
