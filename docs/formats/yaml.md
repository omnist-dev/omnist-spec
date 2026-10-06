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

**The merge key, `<<`, is the one alias form that does not nest.** An entry
`<<: *x` in a mapping flattens the referenced mapping's *own* entries into the
referring mapping — one level up — rather than nesting a copy of it under the
key `<<`. YAML 1.1 also permits a sequence of aliases, `<<: [*x, *y]`, merging
each in turn; an empty sequence, `<<: []`, merges nothing and is not an
error. `<<` itself never survives as a label; it is a merge
instruction, not an edge. So `d: &d {a: 1}` / `e: {<<: *d, b: 2}` reads as
`e` carrying the two edges `a` and `b`, not an edge named `<<`. This is the
mechanism [D-18](../02-document-model.md#241-bounding-alias-expansion) means by
"flattened", and the reason a merge-key config expands one-to-one where a
plain alias multiplies; §2.4.1 states what each form contributes to the
expansion factor.

**Merged entries come first, in source order.** A Document is an ordered edge
list ([D-1](../02-document-model.md#23-structural-invariants)), so a codec
cannot leave this to chance the way YAML can: a YAML mapping is unordered and
YAML 1.1's merge type says nothing about the resulting order, but an Omnist
Document is ordered and conformance vectors compare that order byte for byte.
The normative order is:

- for `<<: *x`, the entries of `x` in `x`'s own written order, then the
  referring mapping's own entries in theirs;
- for `<<: [*a, *b]`, `a`'s entries, then `b`'s, then the referring mapping's
  own — **sequence order**, the order the aliases are written in, with no
  reversal at any level.

So:

```yaml
base: &base
  region: eu-west-1
limits: &limits
  retries: 3
svc:
  <<: [*base, *limits]
  name: api
```

reads `svc` as the three edges `region`, `retries`, `name`, in that order.
Source order is normative because it is the only order the written text
explains. Some YAML libraries flatten a merge sequence in *reverse* —
PyYAML's constructor does, which is how the reference implementation came to
produce `retries, region, name` — and a codec built on one of those MUST
reorder rather than pass the artifact through. See
[omnist-spec#98](https://github.com/omnist-dev/omnist-spec/issues/98). All five
implementations pass the vectors that pin source order as of v0.21.0-beta.

**Key collisions resolve to one edge, at the earliest position.** A key
supplied by more than one of the merged sources, or by a merged source and
the referring mapping both, produces exactly **one** edge. It sits at the
position of its first occurrence in the order above, and it carries the
referring mapping's *own* value when the mapping writes one, otherwise the
value from the **earliest** alias in the sequence that supplies it. Over
`d: &d {a: 1, b: 2}`, the mapping `e: {<<: *d, a: 99}` reads as `a = 99` then
`b = 2` — the local value in the merged key's position — and this holds
whether the local `a:` is written before or after the `<<:`. Over
`p: &p {a: 1}` and `q: &q {a: 2}`, the mapping `r: {<<: [*p, *q]}` reads as
the single edge `a = 1`: the earlier alias wins. Both rules were verified
against two independent YAML implementations — PyYAML 6.0.3 and the
JavaScript `yaml` library 2.9.0 — which produce the same **values** on every
shape tested. They agree on **order** too except where PyYAML's reversed
sequence flattening shows through, which is the artifact this section rules
out: given `p: &p {a: 1, b: 5}` and `q: &q {b: 2, c: 3}`, the mapping
`r: {<<: [*p, *q], c: 99}` reads as `a = 1`, `b = 5`, `c = 99` under this
rule and in the JavaScript library, while PyYAML returns the same three
values in the order `b, c, a`.

**A merge nests.** An aliased mapping that itself contains a `<<` is merged
recursively, and the grandparent's entries arrive first: for
`g: &g {a: 1}`, `m: &m {<<: *g, b: 2}` and `n: {<<: *m, c: 3}`, `n` reads as
`a`, `b`, `c`. **A repeated alias in one sequence contributes once.**
`<<: [*p, *p]` yields exactly one copy of `p`'s entries, not two — the second
occurrence supplies only keys the first already supplied, and the collision
rule above collapses them. Both were measured in PyYAML 6.0.3 and
`yaml` 2.9.0, which agree on both.

This is also the case §2.4.1's D-19 flags when it calls `W` a *conservative*
bound: the expansion check runs before materialization and is deliberately
blind to collision resolution, so it counts a collided key twice where the
reader materializes it once. Erring high there is intended, and nothing here
changes it.

**Which is exactly why the YAML reader MUST bound alias expansion.** Fully
expanding every alias is what makes an anchor an amplifier: one written
definition materializes again at each reference, and an anchor whose
definition itself contains references multiplies. YAML's anchor/alias
mechanism is the only such construct among the five formats this spec covers,
so YAML is the only format on which
[D-18](../02-document-model.md#241-bounding-alias-expansion) currently has
anything to do — and a conformant YAML reader MUST enforce it. Compute the
expansion factor `E` of every anchored definition, every other mapping and
sequence, and the root, from the anchor/alias graph
*before* expanding, reject the input with `document.limit.alias-expansion`
when any `E` exceeds the configured maximum (reference default 50), and
reject a self-referential anchor outright. It MUST also reject an input
containing an alias or merge key whose total expansion `W` of the root exceeds
the configured maximum expanded size (reference default 1 000 000 slots) with
`document.limit.expanded-size`
([D-22](../02-document-model.md#241-bounding-alias-expansion)); a YAML input
with neither is outside that limit, though
[D-23](../02-document-model.md#242-resource-bounds-beyond-the-document)'s input
size applies to it. A merge value that is not a mapping or a
sequence of mappings is a syntax error, `parse.codec-syntax`; a sequence with
no members is a sequence of mappings and merges nothing. An alias with no
preceding anchor is also a syntax error, a redefined anchor shadows the earlier
one for the aliases that follow it, and a quoted `<<` is an ordinary key, not a
merge key; so is a `<<` tagged `!!str`, while one tagged `!!merge` is a merge key
([D-27](../02-document-model.md#241-bounding-alias-expansion)). §2.4.1 defines
`E`, gives the
reasoning behind the default, and explains why ordinary anchored YAML — merge
keys, shared constants, anchor chains — sits far below it. Nothing here
changes the value-fidelity rule above: an alias that is expanded still reads
as an independent edge carrying the value.

**YAML resolves some scalars on its own.** A bare ISO-8601-looking scalar
resolves to a `date` or `datetime` with no schema involved. YAML is one of two
formats whose native parser can do this without a schema — TOML is the
other, and covers all three temporal kinds (date, time, and datetime) where
YAML only resolves date and datetime; a bare time-of-day resolves to an
integer instead, not a `time` (see the sharp edge below).

**One sharp edge.** YAML's core schema has no standalone time type. A bare
`12:00:00` resolves to the **integer** 43200 — sexagesimal, twelve hours in
seconds. That is YAML's behavior, not a choice Omnist makes, and there is no
read-side workaround: by the time the value reaches Omnist it is already an
integer. Quote it.

**A second sharp edge, real enough to have a name: the "Norway problem."**
YAML 1.1's core schema resolves `on`/`off`/`yes`/`no`/`true`/`false` (in
various cases) as booleans, not strings — the classic case is `NO` parsing
as `false`, and `on` is a less-famous instance of the same rule. A bare `on:`
key parses to the boolean `true`, not the string `"on"`. Since a label MUST
be a string (§2.2.2), a reader MUST refuse to build a Document from a
boolean-keyed mapping rather than silently coercing it — this is correct
behavior given what the YAML parser handed it, but it collides with the one
top-level key almost every real GitHub Actions workflow file needs (`on:`
starting the trigger block), and almost no one quotes it. Quoting the key
(`"on":`) sidesteps the problem entirely; there is no read-side workaround
once an unquoted `on:` has already resolved to a boolean. See
[`test.yml`](../examples/github-actions/test.yml) (a real workflow that
fails at exactly this point) and
[`test-quoted-on.yml`](../examples/github-actions/test-quoted-on.yml) (the
same file with the key quoted, which reads and validates cleanly) in
[`../examples/`](../examples/index.md#github-actions-workflow).

**This alias set is exactly these six words, not the raw YAML 1.1
specification's fuller list.** The YAML 1.1 spec itself also resolves bare
`y`/`Y`/`n`/`N` as booleans; the reference implementation's resolver
deliberately does not (matching PyYAML's own default `SafeLoader`, which
omits the single-letter forms specifically because they collide too easily
with ordinary short keys and values). A bare `n:` or `y:` key stays an ordinary string label here, not a
Norway-problem case — confirmed live for `n`/`N`/`y`/`Y` in both key and
value position. Don't assume the full YAML 1.1 alias list transfers; only
`on`/`off`/`yes`/`no`/`true`/`false` (case variants included) resolve as
booleans.

**Interleaving is lost on write**, as in JSON: same-label edges group into one
key regardless of position.

**Duplicate keys are rejected**
([C-12](../07-codecs-and-deserialization.md#71-two-stages)). A mapping that
holds the same key twice, in block or flow style and at any depth, fails the
read with `parse.codec-syntax`: `a: 1` / `b: 2` / `a: 3` is an error, not the
edges `a = 3, b = 2`. YAML 1.1 and YAML 1.2 both require the keys of a mapping
to be unique, and the mainstream libraries that enforce it (the JavaScript
`yaml` package, `go-yaml` v3) are the ones that read the specification
literally; the ones that let the last key win are the lenient exception, not
the consensus. This is not JSON's policy
([§ JSON, "Duplicate keys"](json.md)): RFC 8259 only advises that names be
unique, so a JSON reader has a result to choose and Omnist chooses the one every
mainstream JSON parser already gives. A key a merge key supplies is not a
duplicate of the same key written in the mapping; the merge section above
states that collision. `a` and `"a"` are one key.

**`!!pairs`, `!!omap` and `!!set` are rejected**
([C-13](../07-codecs-and-deserialization.md#71-two-stages)) with
`parse.codec-syntax`. They name ordered-pair and set collections the Document
model has no single reading for; write the plain sequence of single-key
mappings, or the plain mapping, instead.

**A number literal too large for binary64 reads as an infinity**
([D-29](../02-document-model.md#221-scalar-kinds)): `a: 1.0e+999` reads as the
`number` `+Infinity` with no diagnostic. Which spellings YAML resolves as a float
is the resolver's own business; the rule is about what a float literal beyond
the range means. For an integer literal D-9's digit limit counts the digits of
the **value**, not of the spelling
([D-28](../02-document-model.md#24-safety-limits)): `0x` followed by 3 600 `F`
is a value of 4 335 decimal digits and is refused with
`document.limit.int-digits`, and `1_000` has four digits, not five.


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
is the authority on which implementations ship a YAML codec. This page states
no per-port status of its own: a copy here can only go stale relative to the
ledger.

There is no YAML-specific entry in
[§9.4](../09-divergence-ledger.md#94-known-open-divergences). The resolver
behavior above — dates, and `12:00:00` as an integer — is YAML's own, and is
specified rather than divergent.
