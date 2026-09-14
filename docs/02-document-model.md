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

There is no `float` kind and no `decimal` kind. `number` covers non-integral
values. Implementations MUST NOT add scalar kinds; adding one changes the
Schema Algebra's subtyping lattice and therefore changes conformance results.

`null` is a value but not a kind. It has no scalar kind of its own and is
admitted only where a schema permits it (§3).

### 2.2.2 Labels

A label is a string. Any Unicode string is a legal label. Two edges in the same
node MAY carry the same label; nothing in the Document model constrains
uniqueness, ordering, or the relationship between repeated labels.

### 2.2.3 Nesting

A target is either a value or a node. Nothing else. In particular there is no
bare nested list: a target cannot be a list of unlabeled items, because an
unlabeled item has no edge to occupy. An input containing one (JSON
`[[1,2],[3,4]]`, for instance) MUST be rejected at read time, not silently
flattened. See [chapter 7](07-codecs-and-deserialization.md).

---

## 2.3 Structural invariants

A conformant implementation MUST maintain all of the following for every
Document it constructs, reads, or hands back.

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

This invariant is unconditional for the model itself — it is not weakened by
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

A Document is built from untrusted input. Four quantities bound the work an
implementation will do before refusing to continue: nesting depth, total node
count, the digit length of an `integer` literal, and the ratio of nodes
materialized to input size. Every conformant implementation MUST enforce a
finite limit on all four. **No implementation MAY be unbounded on any of
them.**

**What is fixed, and what is not.** The *existence* and *meaning* of the four
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
| Maximum expansion ratio | 10 | Nodes materialized per byte of input, for any format with a reference or alias mechanism |

The reference defaults are what the Python implementation uses today, and what
a new implementation SHOULD adopt absent a specific reason to deviate. 4 300
matches CPython's own default for `sys.set_int_max_str_digits` — conversion
between an arbitrarily long digit string and a big integer is superlinear, so
an unbounded literal is a denial-of-service vector regardless of language.

**On the expansion ratio.** A format with an alias or reference mechanism —
YAML anchors today, anything similar later — can describe a document
exponentially larger than its own source text. The node-count limit bounds
the *result* but not the *ratio*, and that gap is exploitable in a way the
other three limits are not: an attacker sizes the input to land just under
the node cap, and every request is then **accepted**, with no diagnostic,
while costing the reader orders of magnitude more than it cost to send. No
limit is exceeded, so nothing anywhere reports a problem.

The default of 10 comes from measurement rather than intuition. Legitimate
documents sit near 0.1–0.2 nodes per input byte — a dense flat document of a
thousand short edges measures 0.10, a fifty-level nested document 0.20, an
ordinary small YAML config 0.14 — because every node needs a label and a
separator to exist in the source at all. A ten-level YAML anchor chain
measures **362**. A cap of 10 leaves roughly fifty times headroom above the
densest legitimate input while sitting far below any amplification worth
mounting.

A reader MUST reject input exceeding its configured ratio with the matching
`document.limit.*` code (§8.3.2), and the check MUST fire during
materialization rather than after, since firing afterwards would mean doing
the work the limit exists to prevent.

**Choosing different values.** An implementation MAY set any of the four
lower or higher than the reference default, to fit its deployment target —
for example a lower depth limit on a mobile or embedded runtime with a small
call stack, or a higher node count on a system built to ingest large batch
documents. Whatever values an implementation chooses:

- They MUST be finite. "No limit" is not a legal choice for any of the four.
- They MUST be documented, in the same place a user would look for the rest of
  the implementation's conformance profile.
- The depth limit MUST match between the Document builder and the OML parser
  within one implementation (§2.4 note below) — a document that parses MUST
  NOT then fail to build.

**Where this stands today.** No implementation currently exposes a public
configuration surface for any of the four limits. Python's `_MAX_DEPTH`,
`_MAX_NODES`, and `_MAX_INT_DIGITS` are hardcoded module constants with no
constructor argument, function parameter, or environment variable that lets a
caller change them — the only place they vary at all is inside Python's own
test suite, via direct monkeypatching of the private module attribute, which
is a test technique, not a configuration surface a real caller can use. "MAY
set any of the four" is written for an implementation that chooses to expose
one — an embedded or big-data target with an actual reason to deviate — not a
capability any implementation ships today. A future implementation is free to
be the first.

**What is fixed regardless of the chosen value: how exceeding it is reported.**
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

**On depth.** Within one implementation, the Document builder's depth limit and
the OML parser's nesting limit MUST be the same number. A document that the
parser accepts MUST NOT then fail while the builder walks it. In Python this
isn't an active synchronization an implementer has to maintain — the builder
and the parser both import the same module-level constant, so there is
exactly one number, not two kept equal by discipline. The MUST here is aimed
at an implementation whose architecture genuinely has two separate places a
depth limit could be configured; where a single shared constant is the
natural design, as in Python, the requirement is satisfied automatically.

---

## 2.5 Encoding

These rules apply to every text surface — OML, OSD, and every codec's input.
They are stated because each one is a place two implementations can build
*different Documents from identical bytes* while both believing they are
correct, which is the most dangerous class of divergence a data format has:
one system validates the reading it sees, another acts on a different one.

**Input MUST be valid UTF-8.** A malformed byte sequence is an error,
reported as `parse.invalid-encoding` ([§8.3.1](08-conformance-and-errors.md#831-parse-text-to-document-stage-1)).
An implementation MUST NOT substitute `U+FFFD` or otherwise repair the input
and continue: silent repair is exactly how two readers end up with different
Documents, since what a replacement character stands in for is not
recoverable.

**A leading byte-order mark MUST be stripped.** `U+FEFF` at the very start of
input is consumed and contributes nothing to the Document. A BOM anywhere
else is ordinary content, with no special meaning. Stripping rather than
rejecting is the pragmatic choice — BOM-prefixed files are entirely routine
from Windows tooling, and refusing them would reject well-formed data for a
byte the author never sees.

**Labels and names compare byte-wise, never by Unicode normalization.** Two
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
