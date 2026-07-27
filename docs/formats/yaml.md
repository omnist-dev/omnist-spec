# YAML

## Model mapping

YAML maps through its JSON-compatible core. A mapping becomes a list of edges;
a key whose value is a sequence becomes a repeated label. On those two shapes
YAML and JSON are the same codec.

| YAML | Document |
|---|---|
| `a: 1` / `b: 2` | `[(a,1),(b,2)]` |
| `m:` with a two-item sequence | `[(m,A),(m,B)]` |

**Aliases resolve at parse time.** `a: &x foo` / `b: *x` reads as two
independent edges both carrying `foo`. Shared identity is not preserved; the
Document model has no notion of it. This is lossless in value and lossy in
structure sharing, which is the correct trade for a model whose whole point is
the fully expanded edge list.

**YAML resolves some scalars on its own.** A bare ISO-8601-looking scalar
resolves to a `date` or `datetime` with no schema involved. This is the one
format where stage 1 can produce a temporal type without a schema.

**One sharp edge.** YAML's core schema has no standalone time type. A bare
`12:00:00` resolves to the **integer** 43200 — sexagesimal, twelve hours in
seconds. That is YAML's behavior, not a choice Omnist makes, and there is no
read-side workaround: by the time the value reaches Omnist it is already an
integer. Quote it.

**Interleaving is lost on write**, as in JSON: same-label edges group into one
key regardless of position.

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

The same order in YAML:

```yaml
order:
  id: A1
  status: shipped
  total: 29.97
  address: {street: 1 Main, city: London}
  items:
    - {sku: W, qty: 3, price: 9.99}
    - {sku: G, qty: 1, price: 9.99}
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

Byte-for-byte identical to the Document JSON produces. The sequence under
`items` becomes two `items` edges, not one edge holding a list.

Two YAML-only notes on this example. `status: shipped` is an unquoted scalar
and resolves to the string `"shipped"`, which is what `"status": string`
wants — but an unquoted `status: no` would resolve to the boolean `false`, and
the schema would then report a type mismatch rather than silently coercing. And
if the order carried a `placed: 2024-01-01` field typed `date`, YAML would
resolve it to a `date` during stage 1, where JSON would hand stage 2 a string
to upgrade. Same schema, same final Document, different stage.

## Parity gaps

Chapter 9's status table ([§9.3](../09-divergence-ledger.md#93-current-status))
is the authority. As of spec v0.1, its "Codecs JSON/YAML/TOML/XML" row reads
Python "all four", TypeScript "JSON", Rust "JSON".

For YAML specifically, that means **Python only**. Neither TypeScript nor Rust
ships a YAML codec yet, so YAML input is not portable across implementations
today. This is a completeness gap, not a behavioral divergence: there is no
second YAML implementation to disagree with the first.

There is no YAML-specific entry in
[§9.4](../09-divergence-ledger.md#94-known-open-divergences). The resolver
behavior above — dates, and `12:00:00` as an integer — is YAML's own, and is
specified rather than divergent.
