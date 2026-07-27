# JSON

## Model mapping

JSON is the baseline. An object becomes a list of edges, in the order its keys
appear. A key whose value is an array becomes a **repeated label**: the array
is not a value in the model, it is the same label occurring more than once.

| JSON | Document |
|---|---|
| `{"a":1,"b":2}` | `[(a,1),(b,2)]` |
| `{"m":[A,B]}` | `[(m,A),(m,B)]` |
| `{"m":[A]}` | `[(m,A)]` — one edge, indistinguishable from `{"m":A}` |

**No temporal types.** JSON has none, so a reader MUST NOT produce `date`,
`time`, or `datetime` on its own. A date-looking string stays a string unless a
schema upgrades it in stage 2. A writer MUST stringify a temporal leaf to
ISO-8601.

**No `NaN` or `Infinity`.** Those tokens are not valid JSON. A writer MUST NOT
emit them. The default behavior is to substitute `null` at the leaf so the
output is always valid JSON, and to report the substitution as an
error-severity adjustment in the format report. A strict mode MAY instead fail.

**Bare nested arrays are rejected.** `[[1,2],[3,4]]` has inner elements with no
label and therefore no edge to occupy. A reader MUST reject it rather than
flatten it.

**Top level.** A JSON document may have many top-level keys, which becomes many
top-level edges. That is legal, and it is also the shape XML cannot carry.

**Interleaving is lost on write.** Edges sharing a label are grouped into one
key regardless of position, because a JSON object cannot express
`[(m,A),(x,X),(m,B)]`. See [§7.3](../07-codecs-and-deserialization.md#73-writing).

### Worked example

The schema:

```
record Address  { "street": string, "city": string }
record LineItem { "sku": string, "qty": integer, "price": number }

record Order {
    "id":           string,
    "status":       string,
    "total":        number,
    "address":      Address,
    "items" [1,]:   LineItem,
    "coupon" [0,1]: string,
}

record Root { "order": Order }
root Root
```

The same order in JSON:

```json
{"order": {"id": "A1", "status": "shipped", "total": 29.97,
  "address": {"street": "1 Main", "city": "London"},
  "items": [{"sku": "W", "qty": 3, "price": 9.99},
            {"sku": "G", "qty": 1, "price": 9.99}]}}
```

reads to:

```
[ (order, [ (id,      "A1"),
            (status,  "shipped"),
            (total,   29.97),
            (address, [ (street, "1 Main"), (city, "London") ]),
            (items,   [ (sku, "W"), (qty, 3), (price, 9.99) ]),
            (items,   [ (sku, "G"), (qty, 1), (price, 9.99) ]) ]) ]
```

The two `items` objects arrive as two edges sharing the label `items`, which is
exactly what `"items" [1,]: LineItem` counts. Writing back reverses it: two
`items` edges regroup into one JSON array. Had there been one line item, the
writer would emit a bare object rather than a one-element array, by the count-1
rule in [§7.3](../07-codecs-and-deserialization.md#73-writing).

`total` is `29.97` and reads as a `number` with no schema involved. `qty` reads
as an integer. Neither needs materialization; the schema's role here is to
check shape, not to convert. A JSON leaf that did need conversion — a
`datetime` field carrying `"2024-01-01T12:30:00"` — would stay a string after
stage 1 and only become a `datetime` in stage 2.

## Parity gaps

Chapter 9's status table ([§9.3](../09-divergence-ledger.md#93-current-status))
is the authority. As of spec v0.1, its "Codecs JSON/YAML/TOML/XML" row reads
Python "all four", TypeScript "JSON", Rust "JSON".

For JSON specifically, that means all three implementations have the codec. It
is the only format with no implementation gap.

There is no JSON-specific entry in
[§9.4](../09-divergence-ledger.md#94-known-open-divergences). The general
divergences that also apply here are D-1 (resource caps unverified outside
Python) and D-4 (no implementation emits §8.3 error codes yet), neither of
which is about JSON.
