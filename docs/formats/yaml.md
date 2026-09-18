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
each in turn. `<<` itself never survives as a label; it is a merge
instruction, not an edge. So `d: &d {a: 1}` / `e: {<<: *d, b: 2}` reads as
`e` carrying the two edges `a` and `b`, not an edge named `<<`. This is the
mechanism [D-18](../02-document-model.md#241-bounding-alias-expansion) means by
"flattened", and the reason a merge-key config expands one-to-one where a
plain alias multiplies; §2.4.1 states what each form contributes to the
expansion factor.

**Which is exactly why the YAML reader MUST bound alias expansion.** Fully
expanding every alias is what makes an anchor an amplifier: one written
definition materializes again at each reference, and an anchor whose
definition itself contains references multiplies. YAML's anchor/alias
mechanism is the only such construct among the five formats this spec covers,
so YAML is the only format on which
[D-18](../02-document-model.md#241-bounding-alias-expansion) currently has
anything to do — and a conformant YAML reader MUST enforce it. Compute each
anchored definition's expansion factor `E` from the anchor/alias graph
*before* expanding, reject the input with `document.limit.alias-expansion`
when any `E` exceeds the configured maximum (reference default 50), and
reject a self-referential anchor outright. §2.4.1 defines `E`, gives the
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

**Duplicate keys: last one wins**, matching JSON's policy
([§ JSON, "Duplicate keys"](json.md)) rather than the YAML 1.1 spec's own
stance — YAML 1.1 actually calls duplicate mapping keys an error, but no
mainstream implementation library enforces that, all silently resolving to
last-key-wins in practice. Omnist follows the implementations, not the
unenforced spec text, for the same reason as JSON: consistency with what
every reader is already going to do, at zero cost.

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
