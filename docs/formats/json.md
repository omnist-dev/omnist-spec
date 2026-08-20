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
| `{"m":[]}` | zero `m` edges — the label is simply absent from the result |

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

**An empty array is a legitimate zero-edge encoding, not an error.**
`{"m":[]}` reads to zero `m` edges: the label simply doesn't appear in the
result, the same as if the key were absent entirely. This is JSON-specific
and does not extend to OML's `[...]` array sugar — a bare `m: []` in OML MUST
be rejected (verified live: `empty array is not allowed`), because OML's
array syntax is sugar for a *run* of same-label edges and a zero-length run
is indistinguishable from no sugar being used at all. JSON has no such
ambiguity: its arrays are a real container independent of the Document
model's edge-repetition mechanism, so an empty one is just as meaningful as
a non-empty one.

**Top level.** A JSON document may have many top-level keys, which becomes many
top-level edges. That is legal, and it is also the shape XML cannot carry.

**Duplicate keys: last one wins.** `{"a":1,"a":2}` reads as `[(a,2)]` — one
edge, not two. The JSON grammar itself is silent on duplicate names (RFC 8259
permits but discourages them and does not define a resolution), so this is an
Omnist policy choice, not a JSON requirement — chosen because it is already
the de facto behavior of essentially every mainstream JSON parser (a later
key overwriting an earlier one when built into a map), so codifying it costs
nothing across ports and avoids inventing divergent behavior where none
currently exists in practice. This is unrelated to a **repeated** label
becoming a repeated edge (`{"m":[A,B]}` → `[(m,A),(m,B)]`, see above) — that
is JSON's own array syntax, not a duplicate-key situation. Duplicate keys
collapse to one edge; a JSON array under a single key does not.

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

**A real-world example.** The running Order schema is clean by design — it
has no unions and no open key sets, so it never has to confront JSON's actual
worst case. `package.json` does: its `author`/`bugs`/`repository` fields can
each be either a string or an object, and `scripts`/`dependencies` are
genuinely open key sets. Modeling it is exactly the kind of case `any` (§3.7)
exists for — see [`package.osd`](../examples/package-json/package.osd) and
its two fixtures in [`../examples/`](../examples/index.md#packagejson).

## Parity gaps

Chapter 9's status table ([§9.3](../09-divergence-ledger.md#93-current-status))
is the authority. As of spec v0.1, its "Codecs JSON/YAML/TOML/XML" row reads
"all four" for Python, TypeScript, and Rust alike — every implementation has
every codec.

There is no JSON-specific entry in
[§9.4](../09-divergence-ledger.md#94-known-open-divergences). The general
divergences that also apply here are D-1 (resource caps unverified outside
Python) and D-4 (no implementation emits §8.3 error codes yet), neither of
which is about JSON.
