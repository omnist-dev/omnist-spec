# 2. The Document model

## 2.1 Mental model

*Non-normative.*

Start with a fact about the formats Omnist reads. JSON, YAML, and TOML model an
object as a map from key to value, and express "many" by making that value a
list. XML does not. XML expresses "many" by repeating an element, and it lets
repeated elements interleave with other elements.

That difference is not cosmetic. Take this XML:

```xml
<order>
  <item>pen</item>
  <note>rush</note>
  <item>pad</item>
</order>
```

Read it into a map-of-arrays and you get `{"item": ["pen","pad"], "note": "rush"}`.
The note has moved. The original interleaving is gone and cannot be recovered.
Write it back out and you get a different document.

So Omnist does not use a map. A node is an **ordered list of labeled edges**:

```
[ (item, "pen"), (note, "rush"), (item, "pad") ]
```

Nothing has been reordered and nothing merged. The same three formats above read
into exactly this:

| Format | Text | Document |
|---|---|---|
| JSON | `{"item": ["pen","pad"], "note": "rush"}` | `[(item,"pen"), (item,"pad"), (note,"rush")]` |
| OML | `item: "pen"` / `note: "rush"` / `item: "pad"` | `[(item,"pen"), (note,"rush"), (item,"pad")]` |
| XML | the snippet above | `[(item,"pen"), (note,"rush"), (item,"pad")]` |

Two consequences follow, and they are the whole model.

**There is no array.** An array *is* a repeated label. `tags` appearing four
times is a four-element array of tags. Array-of-record and array-of-scalar are
the same thing, handled by the same mechanism, with no separate type to define.

**Object and array collapse into one thing.** A node is an edge list. The
object-versus-array distinction that every other data model carries does not
exist here, so no operation ever has to branch on it.

Order is preserved because a Document is a faithful record of what was read.
Order is never *checked*, because schemas count edges rather than sequencing
them. A reordered round trip stays valid.

---

## 2.2 Formal definition

A Document is a node.

```
scalar-value = string | integer | number | boolean | date | time | datetime
value        = scalar-value | null
edge         = (label, target)          ; label is a string
target       = value | node
node         = [ edge, edge, ... ]      ; ordered; labels MAY repeat
Document     = node | value             ; a bare value is a legal Document
```

### 2.2.1 Scalar kinds

Exactly seven scalar kinds exist:

| Kind | Domain |
|---|---|
| `string` | A sequence of Unicode code points |
| `integer` | An arbitrary-precision signed integer, subject to §2.4 |
| `number` | A real number, represented as IEEE 754 binary64 |
| `boolean` | `true` or `false` |
| `date` | A calendar date: year, month, day |
| `time` | A time of day, with optional sub-second precision and optional UTC offset |
| `datetime` | A date and a time of day, joined |

**D-6.** There is no `float` kind and no `decimal` kind. `number` covers
non-integral values. Implementations MUST NOT add scalar kinds; adding one changes the
Schema Algebra's subtyping lattice and therefore changes conformance results.

`null` is a value but not a kind. It has no scalar kind of its own and is
admitted only where a schema permits it (§3).

### 2.2.2 Labels

A label is a string. Any Unicode string is a legal label. Two edges in the same
node MAY carry the same label; nothing in the Document model constrains
uniqueness, ordering, or the relationship between repeated labels.

### 2.2.3 Nesting

**D-7.** A target is either a value or a node. Nothing else. In particular there is no
bare nested list: a target cannot be a list of unlabeled items, because an
unlabeled item has no edge to occupy. An input containing one (JSON
`[[1,2],[3,4]]`, for instance) MUST be rejected at read time, not silently
flattened. See [chapter 7](07-codecs-and-deserialization.md).

---

## 2.3 Structural invariants

**D-17. A conformant implementation MUST maintain all of the following for
every Document it constructs, reads, or hands back.** Each of `D-1`..`D-5` is
also a requirement in its own right, and where one states a narrower scope of
its own — `D-1` binds every reader, `D-3` binds the operations of chapters 3
and 6 — that narrower scope governs, and this rule does not widen it. Where a
rule states no scope of its own, notably `D-5`, this rule supplies it: scalar
identity holds for every Document an implementation constructs, reads, or
hands back.

**D-1. Edge order is preserved.** The order of edges within a node MUST be the
order they appeared in the source, for every reader. Implementations MUST NOT
sort, group, or stabilize edge order at read time.

**D-2. Repeated labels are not merged.** Two edges with the same label remain
two edges. An implementation MUST NOT collapse them into a single edge carrying
a list.

**D-3. Order is never a schema constraint.** No operation in
[chapter 6](06-schema-algebra.md) and no validation rule in §3 may consult edge
order. A permutation of a node's edges MUST produce identical validation and
identical algebra results. Concretely: `[(a,1),(b,2)]` and `[(b,2),(a,1)]` are
different Documents (edge order is data, preserved faithfully) but validate
identically against any schema that accepts one of them — the schema counts
how many `a` edges and how many `b` edges exist, never which comes first.

**D-4. A target is a value or a node.** No third case exists. Implementations
MUST NOT introduce a list-valued target as an internal representation that can
escape into user-visible Documents.

**D-5. Scalar identity is by kind and value.** Two scalars are equal when their
kinds and values are equal. An `integer` and a `number` of the same magnitude
are distinct scalars in the Document model, even though `integer` is a subtype
of `number` in the Schema model (§6).

**D-8.** This invariant is unconditional for the model itself — it is not weakened by
what any particular host language can represent. An implementation targeting
a language with no native `integer`/`number` distinction (e.g. JavaScript's
single `number` type) MAY be structurally unable to preserve this distinction
independent of a schema. That is a real, accepted implementation constraint,
not a reason to relax the model: such an implementation MUST still document
the gap plainly as a numbered entry in
[§9.4](09-divergence-ledger.md#94-known-open-divergences) and MUST report
any conformance vector whose outcome depends on this distinction as
*skipped*, never as passing — a vector cannot be honestly satisfied by an
implementation that cannot construct its input.

> D-3 is the invariant most likely to be violated by accident, usually by an
> implementation that validates a node by zipping it against a field list. Zip
> against counts, not positions.

---

## 2.4 Safety limits

**D-9.** A Document is built from untrusted input. Three quantities bound the work an
implementation will do before refusing to continue: nesting depth, total node
count, and the digit length of an `integer` literal. Every conformant
implementation MUST enforce a finite limit on all three. **No implementation
MAY be unbounded on any of them.** A fourth quantity, the alias expansion
factor (D-18, §2.4.1), bounds a format mechanism rather than the Document
itself, so it binds only the codecs that have such a mechanism; where it
applies, it is a safety limit in this section's sense like the other three,
and D-10 and D-11 below govern it identically.

**What is fixed, and what is not.** The *existence* and *meaning* of the three
limits is normative. The specific *numbers* are not: this is a deliberate
change from an earlier draft of this spec, which wrongly treated one platform's
numbers as universal constants. A limit exists to bound work against untrusted
input on the hardware actually running the implementation, and that varies
legitimately by two orders of magnitude between an embedded parser and a
big-data ingestion engine.

| Limit | Reference default | Applies to |
|---|---|---|
| Maximum nesting depth | 200 | Levels of node nesting, counted from the Document root |
| Maximum node count | 1 000 000 | Nodes materialized while building one Document |
| Maximum integer digits | 4 300 | Decimal digits in an `integer` literal, sign excluded |
| Maximum alias expansion factor | 50 | The materialized-to-written value-slot ratio of any one anchored definition, in a format that has an anchor/reference mechanism (D-18) |

**The fourth row is conditional; the first three are not.** Depth, node count
and integer digits bound every Document on every route into the model, so
every implementation enforces all three. The expansion factor bounds one
specific mechanism — a format construct that is written once and materializes
many times — and is therefore a requirement on the codecs that have such a
mechanism, not on implementations generally (D-18 below, and
[§9.2](09-divergence-ledger.md#92-forbidden-variation)). A Document built
programmatically from native objects has no anchors and is unaffected.

The reference defaults are what the Python implementation uses today, and what
a new implementation SHOULD adopt absent a specific reason to deviate. 4 300
matches CPython's own default for `sys.set_int_max_str_digits` — conversion
between an arbitrarily long digit string and a big integer is superlinear, so
an unbounded literal is a denial-of-service vector regardless of language.

**Choosing different values.** An implementation MAY set any of these limits
lower or higher than the reference default, to fit its deployment target —
for example a lower depth limit on a mobile or embedded runtime with a small
call stack, or a higher node count on a system built to ingest large batch
documents. Whatever values an implementation chooses:

- **D-10.** They MUST be finite. "No limit" is not a legal choice for any
  limit in this section — the three universal ones above, or the alias
  expansion factor of D-18 wherever that rule applies.
- **D-11.** They MUST be documented, in the same place a user would look for the rest of
  the implementation's conformance profile. This too covers every limit in
  this section, the alias expansion factor included: an implementation that
  ships a YAML codec MUST state the maximum expansion factor it enforces.
- **D-12.** The depth limit MUST match between the Document builder and the OML parser
  within one implementation (§2.4 note below) — a document that parses MUST
  NOT then fail to build.

**Where this stands today.** No implementation currently exposes a public
configuration surface for any of these limits. Python's `_MAX_DEPTH`,
`_MAX_NODES`, and `_MAX_INT_DIGITS` are hardcoded module constants with no
constructor argument, function parameter, or environment variable that lets a
caller change them — the only place they vary at all is inside Python's own
test suite, via direct monkeypatching of the private module attribute, which
is a test technique, not a configuration surface a real caller can use. "MAY
set any of these limits" is written for an implementation that chooses to expose
one — an embedded or big-data target with an actual reason to deviate — not a
capability any implementation ships today. A future implementation is free to
be the first.

**D-13. What is fixed regardless of the chosen value: how exceeding it is reported.**
Exceeding a declared limit — whatever number the implementation chose — MUST
produce the corresponding standardized error from the `document.limit.*`
family defined in [chapter 8](08-conformance-and-errors.md), MUST NOT be
truncated, clamped, or silently accepted, and MUST NOT be reported as any other
error category. A conformance test comparing two implementations with
different configured limits is expected to see different pass/fail points on a
depth- or size-scaling test; it MUST see the same error code at whichever point
each of them draws its own line.

**On the node cap.** The node count bounds total materialized nodes, not depth.
It exists because a shallow document can still be enormous — a million sibling
edges is depth 1.

**On depth (D-12, elaborated).** Within one implementation, the Document builder's depth limit and
the OML parser's nesting limit MUST be the same number. A document that the
parser accepts MUST NOT then fail while the builder walks it. In Python this
isn't an active synchronization an implementer has to maintain — the builder
and the parser both import the same module-level constant, so there is
exactly one number, not two kept equal by discipline. The MUST here is aimed
at an implementation whose architecture genuinely has two separate places a
depth limit could be configured; where a single shared constant is the
natural design, as in Python, the requirement is satisfied automatically.

### 2.4.1 Bounding alias expansion

The three limits above bound the *result*. None of them bounds the *ratio*
between what an input writes and what reading it materializes. Some formats
let one written construct be referred to elsewhere and materialize again at
every reference — YAML's anchors and aliases are the case Omnist meets today
— and nesting those references multiplies. An input well under the node cap
can still expand by several hundred times, be accepted with no diagnostic,
and be replayed indefinitely at the reader's expense.

**D-18.** A codec for a format with an anchor/reference mechanism — one in
which a construct may be defined once and referred to from elsewhere, so that
a single definition materializes more than once — MUST enforce a finite
maximum **expansion factor** on every anchored definition in its input, and
MUST reject input that exceeds it with `document.limit.alias-expansion`
([§8.3.2](08-conformance-and-errors.md#832-document-building-and-limits)).
For an anchored definition `a`:

- `W(a)` is the number of **value slots materialized** when `a` is expanded. A
  container counts as one slot, a scalar leaf counts as one slot, and a
  reference to an anchored definition `b` appearing inside `a` contributes
  whatever that reference itself materializes, recursively.
- `S(a)` is the number of **value slots written in `a`'s own definition**,
  where a reference appearing inside it counts as exactly **one** slot,
  regardless of the size of what it points at.
- **The anchored node `a` itself counts as one slot, in both `W(a)` and
  `S(a)`.** `W` and `S` are counts over the same tree, one expanded and one
  as written, and both are rooted at `a` inclusively. An anchor on a mapping
  of three scalars has `S = 4`, not 3; an anchor on a bare scalar has
  `S = W = 1`, so `E = 1.00`. Counting `a` in one and not the other would
  make `E` depend on which side the reader chose, and a solitary scalar
  anchor would have a zero denominator.
- `E(a) = W(a) / S(a)`.

**What a reference contributes to `W`.** A reference contributes exactly what
it materializes — no more, and no less:

- A **plain alias** in value position (YAML `*b`) materializes a copy of `b`
  as a nested value. It contributes `W(b)` in full, including `b`'s own
  container slot, because that container is reproduced at the point of use.
- A **merge-key reference** (YAML `<<: *b`, [§ YAML](formats/yaml.md)) does
  not materialize `b`'s container at all: it flattens `b`'s own edges into
  the referring mapping, one level up. It therefore contributes `W(b) - 1` —
  everything `b` materializes except the container slot that is not
  reproduced. The `<<` entry still counts as exactly one written slot in `S`,
  like any other reference.

The general rule is the first sentence; the two cases are what it comes to
for the one format that has the mechanism today. A worked nested case, since
no vector exercises one yet — given `p: &p {k: 1}`, `q: &q {<<: *p, m: 2}`,
and `r: &r {n: *q}`:

```
W(p) = 2  (p's container + the scalar 1)          S(p) = 2   E(p) = 1.00
W(q) = 1 + (W(p) - 1) + 1 = 3                     S(q) = 3   E(q) = 1.00
W(r) = 1 + W(q) = 4                               S(r) = 2   E(r) = 2.00
```

`q`'s merge of `p` contributes 1, not 2, because `p`'s container is flattened
away; `r`'s plain alias of `q` contributes all 3 of `q`'s slots, because
`q`'s container *is* reproduced under `n`.

D-18 is violated, and the codec MUST reject the input, when `E(a)` exceeds
the configured maximum for any anchored definition `a` in it. The reference
default is **50**.

- **D-19.** The check MUST be performed **before** the expansion is
  materialized. `W` and `S` are computable in time linear in the size of the
  input from the raw anchor/reference graph alone, without walking the
  expanded tree, so a conformant implementation refuses an over-limit input
  without ever paying for the expansion it describes. An implementation that
  discovers the violation only after expanding does not satisfy this rule
  even if it reports the right code.
- **D-20.** An anchored definition that refers to itself, directly or through
  a cycle of other definitions, has unbounded `W` and MUST be rejected under
  this limit. A codec MUST NOT attempt to compute a finite `E` for it, and
  MUST NOT materialize a cyclic or infinite structure instead.

**Scope, stated explicitly.** D-18 binds a codec *that has such a mechanism*.
It is not a fourth universal limit: §2.4's first three rows apply to every
Document however it was built, and D-18 applies to a parse of a format with
anchors. Of the five formats this spec covers, **only YAML has one today**
([§ YAML](formats/yaml.md)); JSON, TOML, XML and OML have no construct that
materializes more than once from a single written definition, so the rule is
vacuous for them and they need not compute anything. It binds any future
format or extension that adds one. Nothing in D-18 refers to input byte
length, so there is no ratio-to-bytes to be undefined on a programmatic
construction route, and no denominator to disagree about.

**XML's entity expansion is the same class of problem and is already
handled.** A DTD's internal entities have exactly this shape — the "billion
laughs" attack is an XML attack first — but the data-XML profile in
[§ XML](formats/xml.md) rejects a DTD outright, so the mechanism never
reaches the Document builder. That is a stronger rule than this one, not a
gap in it, and it is deliberately not restated here: one refusal per hazard.

**On the reference default of 50.** It is calibrated against `E` as defined
above, measured on real documents. Legitimate anchored YAML clusters far
below it: a merge-key configuration of the `<<: *defaults` kind that
docker-compose and GitLab CI use reads `E = 1.00` at every size tested, up to
36 KB, because a merge key flattens into the referring mapping rather than
nesting under it; anchor-to-anchor chains and scalar-constant reuse read at
most 5.75. The amplifying shape — nested anchors, each level referring to the
previous one several times — crosses into dangerous territory around
`E = 170` and climbs steeply from there. 50 sits roughly 9× above the worst
legitimate document measured and roughly 3.4× below the weakest dangerous
one, and it fires well before the input grows large enough to reach the node
cap. An implementation MAY configure a different value, subject to D-10 and
D-11 like any other limit in §2.4: finite, and documented.

---

## 2.5 Encoding

These rules apply to every text surface — OML, OSD, and every codec's input.
They are stated because each one is a place two implementations can build
*different Documents from identical bytes* while both believing they are
correct, which is the most dangerous class of divergence a data format has:
one system validates the reading it sees, another acts on a different one.

**D-14. Input MUST be valid UTF-8.** A malformed byte sequence is an error,
reported as `parse.invalid-encoding` ([§8.3.1](08-conformance-and-errors.md#831-parse-text-to-document-stage-1)).
An implementation MUST NOT substitute `U+FFFD` or otherwise repair the input
and continue: silent repair is exactly how two readers end up with different
Documents, since what a replacement character stands in for is not
recoverable.

**D-15. A leading byte-order mark MUST be stripped, on every surface.**
`U+FEFF` at offset zero is consumed and contributes nothing to the Document.
Anywhere else it is ordinary content with no special meaning. Both ABNF
grammars admit it at that position and nowhere else.

The rule is uniform across OML, OSD and every codec deliberately. A BOM
carries no data — it is meaningless for UTF-8, which has no byte-order
ambiguity to mark — so treating it as content on any surface would be wrong,
and treating it as content on *some* surfaces is how two implementations
build different Documents from the same file.

**Where this sits relative to each format's own specification.** For JSON it
overrides nothing: RFC 8259 §8.1 explicitly permits it — implementations
parsing JSON "MAY ignore the presence of a byte order mark rather than
treating it as an error". XML 1.0 and YAML 1.2 both permit a leading BOM
outright, so stripping it is the ordinary reading there too. **TOML is the
one case where this rule goes beyond what the format requires.** TOML v1.0.0
has no BOM provision at all: it says only that a TOML file must be a valid
UTF-8 encoded document, and its ABNF gives `U+FEFF` no position anywhere,
leading or otherwise — which is why the reference's `tomllib` rejects a
BOM-prefixed document. Stripping it for TOML is therefore a deliberate
Omnist choice, made for uniformity across surfaces, not an application of
TOML's own rules; a TOML parser that rejects the byte is not violating TOML,
it is failing this spec. The pragmatic case is the same either way:
BOM-prefixed files are routine from Windows tooling, and refusing them would
reject well-formed data over a byte the author never sees and usually cannot
see.

**On writers (D-15).** A conformant Omnist writer MUST NOT emit a leading
byte-order mark on any surface — OML, OSD, or any codec's output. This
mirrors RFC 8259 §8.1's own writer guidance and is what keeps the rule from
producing byte-level divergence: if stripping on read were paired with a
free choice on write, two conformant implementations could emit different
bytes for the same Document while both read either back correctly.

Measured before this rule existed, the reference stripped a BOM for OML and
XML and rejected it for JSON, TOML and OSD — the divergence this closes.
OSD was the third rejecting surface, not a second stripping one:
`parse_schema` on BOM-prefixed OSD text raised `parse.unexpected-token`.

**D-16. Labels and names compare byte-wise, never by Unicode normalization.** Two
labels are the same label when their UTF-8 bytes are identical. `café`
written as `U+0063 U+0061 U+0066 U+00E9` and as `U+0063 U+0061 U+0066 U+0065
U+0301` are **two distinct labels**, and a node carrying both has two edges.
An implementation MUST NOT normalize to NFC, NFD, or anything else, on read
or on comparison.

That last rule is the one most likely to be violated by accident, because
some platforms normalize filenames and text input by default. It is stated
the way it is for consistency: [§3.3](03-schema-model.md#33-formal-definition)
S-3 already requires exact, case-sensitive matching for reserved names, and
[§3.3](03-schema-model.md#33-formal-definition)'s canonical ordering compares
by Unicode codepoint rather than by locale. Byte-wise label identity is the
same discipline applied to the Document model — no hidden text transformation
anywhere, so what an author writes is what round-trips.
