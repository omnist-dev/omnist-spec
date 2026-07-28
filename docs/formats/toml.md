# TOML

## Model mapping

Tables and array-of-tables map directly onto the Document model. A table
becomes a list of edges. `[[x]]` written twice becomes the label `x` twice.

| TOML | Document |
|---|---|
| `a = 1` / `b = 2` | `[(a,1),(b,2)]` |
| `[[x]]` twice, each with `name` | `[(x,[(name,"a")]), (x,[(name,"b")])]` |

`[[x]]` is TOML's idiomatic repeated record, and it lands on the
repeated-label shape with no adjustment at all. Of the four non-native
formats, TOML is the one whose own idiom already matches the model.

**TOML has native `date`, `time`, and `datetime` literals.** All three parse to
the matching types with no schema needed, and write back the same way. TOML is
the one format with no temporal stringification in either direction.

**TOML has no `null`.** A null-valued leaf cannot be written. Implementations
MUST report this as a write-time adjustment rather than inventing a
representation.

**Top level must be a table.** A bare scalar Document cannot be written as
TOML.

**Interleaving is lost on write**, as in the rest of the JSON family.

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

The same order in TOML:

```toml
[order]
id = "A1"
status = "shipped"
total = 29.97

[order.address]
street = "1 Main"
city = "London"

[[order.items]]
sku = "W"
qty = 3
price = 9.99

[[order.items]]
sku = "G"
qty = 1
price = 9.99
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

The `[[order.items]]` blocks are the clearest statement in any format of what
`"items" [1,]: LineItem` means: the label repeats, and there is no list.
`[order.address]` — a single table, not an array-of-tables — is the `[1,1]`
case, one edge.

A `coupon` field would be a plain key inside `[order]`. Because TOML has no
`null`, an *absent* coupon is written by omitting the key, which is what
`[0,1]` cardinality already means. A `null` coupon has no TOML spelling at all
and is a write-time adjustment.

**A real-world example.** `pyproject.toml` is the canonical case of a
spec'd-open format: its core tables are specified, but `[tool.*]` is
*defined* to be open — third-party tools own those subtrees, and a schema
author doesn't get to close them. See [`pyproject.osd`](../examples/pyproject/pyproject.osd)
and its three fixtures in [`../examples/`](../examples/index.md#pyprojecttoml),
framed explicitly around where OSD's algebra can't fully capture the
format's own spec.

## Parity gaps

Chapter 9's status table ([§9.3](../09-divergence-ledger.md#93-current-status))
is the authority. As of spec v0.1, its "Codecs JSON/YAML/TOML/XML" row reads
"all four" for Python, TypeScript, and Rust alike — every implementation has
a TOML codec.

There is no TOML-specific entry in
[§9.4](../09-divergence-ledger.md#94-known-open-divergences). The `null` gap
and the table-at-top-level rule are properties of TOML, specified above, not
open questions between implementations.
