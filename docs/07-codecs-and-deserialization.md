# 7. Codecs and deserialization

## 7.1 Two stages

Reading a document is two separate operations, and keeping them separate is
normative.

```
        text  --[ stage 1: parse ]-->  untyped Document
                                              |
                                              | schema (optional)
                                              v
                                   [ stage 2: materialize ]
                                              |
                                              v
                                       typed Document
```

**Stage 1: parse.** Turn format text into a Document. No schema is involved. The
result carries whatever types the format itself distinguishes — JSON has no date
type, so an ISO-8601 date arrives as a string. Stage 1 MUST be total with
respect to the schema: it never consults one and never fails because of one.

**Stage 2: materialize.** Walk the untyped Document together with a schema,
upgrading leaves to the declared types, and check record shape in the same pass.

Stage 2 is optional. With no schema, the Document is returned exactly as read,
untouched. There is no third mode. Implementations MUST NOT offer a `strict`
switch: either a schema is supplied and the result is guaranteed to conform, or
one is not and nothing is checked.

## 7.2 Materialization rules

Materialization upgrades a leaf **only when the conversion is value-exact.**

| From | To | Upgraded? |
|---|---|---|
| `"2024-01-01"` | `date` | Yes |
| `"12:30:00"` | `time` | Yes |
| `"2024-01-01T12:30:00"` | `datetime` | Yes |
| `1.0` | `integer` | Yes — value-exact |
| `1.5` | `integer` | No. Error. |
| `1` | `number` | Yes |
| `"1"` | `integer` | No. Error. A string is not a number. |
| `"maybe"` | `boolean` | No. Error. |

The rule is one sentence: a conversion is permitted when it loses nothing and
invents nothing. String-to-number coercion invents; float-to-int truncation
loses. Neither happens.

At an `any`-typed field, materialization stops. The subtree passes through
untouched and no leaf beneath it is upgraded.

Materialization MUST collect **every** problem it finds, not stop at the first,
and report them together. Each entry carries a path, a code, and a message. See
[chapter 8](08-conformance-and-errors.md).

> Materialization cannot be implemented as "validate, then convert."
> `validate` checks a value already in its final form and has no notion of
> upgrading. Since materialization already knows, at every node, which field and
> type the schema expects there, upgrading and shape-checking happen in one pass.

## 7.3 Writing

Writing is the reverse projection, and it is **schema-free by design**.

A writer MUST NOT accept a schema. Its job is to serialize the Document exactly
as it is. Schema awareness is one-directional, on the read side only.

**Grouping.** Edges sharing a label are grouped into one key, regardless of
position: `[(m,A),(x,X),(m,B)]` writes as `{"m":[A,B], "x":X}`. Within-label
order is preserved. Cross-label interleaving is lost, because no format in the
JSON family can express it. Only OML and XML preserve it.

**The count-1 rule.** A label appearing exactly once MUST be written as a bare
value. A label appearing more than once MUST be written as a list. This is
forced: a one-element list and a single value are the same Document — one edge —
so the Document alone cannot tell them apart, and the writer has no schema to
ask.

That asymmetry is real and worth stating outright. `{"tag": ["x"]}` reads to one
edge and writes back as `{"tag": "x"}`. The Document is unchanged; the text is
not.

## 7.4 JSON

The baseline. Objects become edge lists. A key whose value is a list becomes a
repeated label.

| JSON | Document |
|---|---|
| `{"a":1,"b":2}` | `[(a,1),(b,2)]` |
| `{"m":[A,B]}` | `[(m,A),(m,B)]` |

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
top-level edges.

## 7.5 YAML

The JSON-compatible core. Mappings and sequences behave as their JSON
counterparts.

**Aliases resolve at parse time.** `a: &x foo` / `b: *x` reads as two
independent edges both carrying `foo`. Shared identity is not preserved; the
Document model has no notion of it. This is lossless in value and lossy in
structure sharing, which is the correct trade for a model whose whole point is
the fully expanded edge list.

**YAML resolves some scalars on its own.** A bare ISO-8601-looking scalar
resolves to a `date` or `datetime` with no schema involved. This is the one
format where stage 1 can produce a temporal type.

**One sharp edge.** YAML's core schema has no standalone time type. A bare
`12:00:00` resolves to the **integer** 43200 — sexagesimal, twelve hours in
seconds. That is YAML's behavior, not a choice Omnist makes, and there is no
read-side workaround: by the time the value reaches Omnist it is already an
integer. Quote it.

## 7.6 TOML

Tables and array-of-tables map directly.

| TOML | Document |
|---|---|
| `[[x]]` twice, each with `name` | `[(x,[(name,"a")]), (x,[(name,"b")])]` |

`[[x]]` is TOML's idiomatic repeated record, and it lands on the repeated-label
shape with no adjustment at all.

**TOML has native `date`, `time`, and `datetime` literals.** All three parse to
the matching types with no schema needed, and write back the same way. TOML is
the one format with no temporal stringification in either direction.

**TOML has no `null`.** A null-valued leaf cannot be written. Implementations
MUST report this as a write-time adjustment rather than inventing a
representation.

**Top level must be a table.** A bare scalar Document cannot be written as TOML.

## 7.7 XML

XML is the format the Document model was shaped around.

**Elements become edges, and interleaving survives.** `<m/><x/><m/>` reads as
`[(m,...),(x,...),(m,...)]` in that order. A map-of-arrays model cannot
represent this; the edge list can. This is the whole reason the Document is an
ordered edge list rather than a map.

**Repeated elements are the array.** No wrapper element is invented on either
side.

**Text is untyped.** XML carries no type information, so every leaf arrives as a
string. Typing requires a schema in stage 2.

**Single document element.** An XML document has exactly one top-level element,
so its Document has exactly one top-level edge. A Document with several
top-level edges cannot be written as XML. To share one Document across all
formats, wrap the data under a single top-level key.

**Attributes and namespace prefixes are dropped.** `<a x="1"><b>hi</b></a>`
reads as `[(a,[(b,"hi")])]`; the attribute is gone. A prefixed tag `<ns:b>`
reads as the local name `b`, with the prefix and any namespace binding
discarded. There is no path from a Document edge back to an attribute, so
writing never produces one.

This is a real limitation of the current XML profile and is recorded as such in
[chapter 9](09-divergence-ledger.md). Implementations MUST behave identically
here — dropping silently in the same places — until the profile changes.

## 7.8 OML

OML is not a codec in the same sense. Its syntax *is* the Document model, so
every Document shape round-trips with zero adjustments: any nesting, any
repeated label, any interleaving.

The one gap OML shares with JSON and YAML: it has no native temporal literal, so
a temporal value written to OML text becomes a string, and reading it back
requires a schema to recover the type. See [chapter 4](04-oml-grammar.md).

## 7.9 Format reports

A reader or writer SHOULD be able to report the adjustments a given conversion
would make — a temporal value stringified, a special float substituted, a null
dropped — without performing it. This is what makes lossiness auditable ahead of
time rather than discovered afterward.

The report's contents are format-specific. Its codes belong to the
`format.adjustment.*` family in
[chapter 8](08-conformance-and-errors.md), which is new material and which no
implementation currently emits.
