# OML

## Model mapping

OML is not a codec in the same sense as the other four. Its syntax *is* the
Document model, so there is no mapping to describe — only a spelling. Every
Document shape round-trips with zero adjustments: any nesting, any repeated
label, any interleaving, in original order.

| OML | Document |
|---|---|
| `a: 1` / `b: 2` | `[(a,1),(b,2)]` |
| `m: A` / `x: X` / `m: B` | `[(m,A),(x,X),(m,B)]` — interleaving preserved |
| `a: { b: "hi" }` | `[(a,[(b,"hi")])]` |

There is no list syntax, because there is no list in the model. An array is a
label written more than once. There is no wrapper, no separator token between
repetitions, and no way to distinguish a one-element array from a single value
— they are the same Document.

The grammar is [chapter 4](../04-oml-grammar.md); this page does not restate
it.

**The one gap.** OML has no native temporal literal. A temporal value written
to OML text becomes a string, and reading it back requires a schema to recover
the type. On that single point TOML is more capable.

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

The same order in OML:

```oml
order: {
    id: "A1"
    status: "shipped"
    total: 29.97
    address: { street: "1 Main"; city: "London" }
    items: { sku: "W"; qty: 3; price: 9.99 }
    items: { sku: "G"; qty: 1; price: 9.99 }
}
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

The `items` label simply appears twice. That is the whole array mechanism, and
it is the one place where reading the format text and reading the edge list are
the same exercise — compare this block against the Document above line by line.

The `Root` wrapper is not needed by OML: OML carries several top-level edges
without complaint. It is kept here so the example is one Document across all
five formats rather than two ([XML](xml.md) is the constraint).

## Parity gaps

Chapter 9's status table ([§9.3](../09-divergence-ledger.md#93-current-status))
is the authority. "OML read/write" is complete in every current implementation
(Core and Extended alike on the read side). Only the *writer* restriction is
one-sided by design — a canonical writer MUST NOT emit Extended spellings even
though a reader MUST accept them.

Canonical output is not permitted to vary at all. Chapter 9's
[§9.2](../09-divergence-ledger.md#92-forbidden-variation) puts the exact bytes
an OML writer emits, and which OML texts parse, in the forbidden-variation
list. A partial writer is a gap; a writer that emits different bytes is a
conformance failure.
