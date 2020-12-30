# json-date-parser
Minimal function suitable for passing to JSON.parse to revive common date-time strings (including ISO and those weird .NET ones) into Date objects.

Implementation is cribbed straight from: [json.date-extensions](https://github.com/RickStrahl/json.date-extensions).

Differences:
* Instead of polluting the core `JSON` object, it defines a completely separate function.
* TypeScript type information is included.

## Installation

    npm install --save json-date-parser

## Usage

```ts
import { jsonDateParser } from "json-date-parser"

// Call standard JSON parser but use jsonDateParser as a "reviver"
var parsedStuff = JSON.parse(stringOfJson, jsonDateParser);
```

