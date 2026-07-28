# XML

## Model mapping

XML is the format the Document model was shaped around.

**Elements become edges, and interleaving survives.** `<m/><x/><m/>` reads as
`[(m,...),(x,...),(m,...)]` in that order. A map-of-arrays model cannot
represent this; the edge list can. This is the whole reason the Document is an
ordered edge list rather than a map.

**Repeated elements are the array.** No wrapper element is invented on either
side. Two `<items>` elements are two `items` edges, full stop.

**Text is untyped.** XML carries no type information, so every leaf arrives as
a string. Typing requires a schema in stage 2. XML is the format that leans
hardest on materialization.

**Single document element.** An XML document has exactly one top-level element,
so its Document has exactly one top-level edge. A Document with several
top-level edges cannot be written as XML. To share one Document across all
formats, wrap the data under a single top-level key.

**Attributes and namespace prefixes are dropped.** `<a x="1"><b>hi</b></a>`
reads as `[(a,[(b,"hi")])]`; the attribute is gone. A prefixed tag `<ns:b>`
reads as the local name `b`, with the prefix and any namespace binding
discarded. There is no path from a Document edge back to an attribute, so
writing never produces one.

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

The same order in XML:

```xml
<order>
  <id>A1</id>
  <status>shipped</status>
  <total>29.97</total>
  <address><street>1 Main</street><city>London</city></address>
  <items><sku>W</sku><qty>3</qty><price>9.99</price></items>
  <items><sku>G</sku><qty>1</qty><price>9.99</price></items>
</order>
```

reads, after stage 2 against the schema, to:

```
[ (order, [ (id,      "A1"),
            (status,  "shipped"),
            (total,   29.97),
            (address, [ (street, "1 Main"), (city, "London") ]),
            (items,   [ (sku, "W"), (qty, 3), (price, 9.99) ]),
            (items,   [ (sku, "G"), (qty, 1), (price, 9.99) ]) ]) ]
```

Two things about this example are XML-specific.

**The single-rooted design is for XML's sake.** `record Root { "order": Order }`
exists so that the Document has exactly one top-level edge. Without it, JSON,
YAML, and TOML would all still round-trip and XML alone would fail. Every other
format tolerates the wrapper; XML requires it.

**Stage 1 output differs here, stage 2 output does not.** Parsing that XML
yields `total` as the string `"29.97"` and `qty` as the string `"3"`, because
XML text is untyped. It is materialization against `"total": number` and
`"qty": integer` that produces the numbers shown above. Read the same order
from JSON and stage 1 already has them typed. The two paths converge only after
stage 2 — which is precisely why the schema is applied on the read side and
never on the write side.

Note also that `<items>` elements do not sit inside an `<items>` wrapper. There
is no wrapper element in this profile, on either side.

**A real-world example.** `sitemap.xml` is the cleanest of the four examples
in [`../examples/`](../examples/index.md#sitemapxml), because it isolates a
gap category none of the others do: **value refinement**. The schema
([`sitemap.osd`](../examples/sitemap/sitemap.osd)) types `changefreq` as
`string` and `priority` as `number` — OSD has no enum or range constraint —
so `changefreq: sometimes` and `priority: 1.5` both validate cleanly under
OSD despite violating the sitemaps.org spec (which restricts `changefreq`
to a fixed set of values and `priority` to `[0.0, 1.0]`), demonstrated
directly by [`invalid-values.xml`](../examples/sitemap/invalid-values.xml).
No union, no open key set, nothing else is at play — it's a clean
demonstration of exactly one limitation (see also
[§6.3](../06-schema-algebra.md#63-scalar-subtyping)).

## Parity gaps

Chapter 9's status table ([§9.3](../09-divergence-ledger.md#93-current-status))
is the authority. As of spec v0.1, its "Codecs JSON/YAML/TOML/XML" row reads
"all four" for Python, TypeScript, and Rust alike — every implementation has
an XML codec.

XML is also the one format with its own open divergence.
[D-3](../09-divergence-ledger.md#94-known-open-divergences) records that
attributes and namespace prefixes are dropped *silently*, with no adjustment
reported — the information loss described above is not surfaced in a format
report at all, so a caller has no way to learn it happened.
[§8.3.8](../08-conformance-and-errors.md#838-format--codec-adjustments) already
defines codes for reporting it; emitting them is a behavior change and needs a
conformance vector first. Until that lands, implementations MUST behave
identically here: dropping, silently, in the same places.
