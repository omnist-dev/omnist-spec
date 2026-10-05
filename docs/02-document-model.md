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
MAY be unbounded on any of them.** Two further quantities, the alias expansion
factor (D-18) and the expanded size (D-22), both in §2.4.1, bound a format
mechanism rather than the Document itself, so they bind only the codecs that
have such a mechanism; where they apply, each is a safety limit in this
section's sense like the other three, and D-10 and D-11 below govern them
identically. A sixth quantity, the size of the input in bytes, bounds what is
read rather than what is built; it is a SHOULD with no reference default, and
is stated in [§2.4.2](#242-resource-bounds-beyond-the-document).

**What is fixed, and what is not.** The *existence* and *meaning* of the
limits is normative — the three universal ones, and the expansion factor and
expanded size wherever D-18 and D-22 apply. The specific *numbers* are not: this
is a deliberate
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
| Maximum alias expansion factor | 50 | The materialized-to-written value-slot ratio of any one anchored definition, any other mapping or sequence, and the document root, in a format that has an anchor/reference mechanism (D-18) |
| Maximum expanded size | 1 000 000 | The value slots one input materializes, `W` of the document root, for an input that contains an alias or a merge key (D-22) |
| Maximum input size | none (D-24) | Bytes of one input, any format (D-23, a SHOULD) |

**The fourth and fifth rows are conditional; the first three are not.** Depth, node
count and integer digits bound every Document on every route into the model, so
every implementation enforces all three. The expansion factor and the expanded
size bound one specific mechanism — a format construct that is written once and
materializes many times — and are therefore requirements on the codecs that have
such a mechanism, not on implementations generally (D-18 and D-22 below, and
[§9.2](09-divergence-ledger.md#92-forbidden-variation)). The input size row
is the only one that bounds bytes, and the only one that is a SHOULD. A
Document built programmatically from native objects has no anchors and is
unaffected.

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
  expansion factor of D-18 or the expanded size of D-22 wherever those rules
  apply. The one exception is the input size of D-23, which is a SHOULD: an
  implementation MAY enforce none, but one that enforces a maximum MUST make
  it finite.
- **D-11.** They MUST be documented, in the same place a user would look for the rest of
  the implementation's conformance profile. This too covers every limit in
  this section, the alias expansion factor included: an implementation that
  ships a YAML codec MUST state the maximum expansion factor and the maximum
  expanded size it enforces.
- **D-12.** The depth limit MUST match between the Document builder and the OML parser
  within one implementation (§2.4 note below) — a document that parses MUST
  NOT then fail to build.

**Where this stands today.** Rust, Go and Java expose a configuration
surface for the depth, node-count and integer-digit limits (a `Limits`
struct, struct or record passed to the readers; checked 2026-10-05, see
[§9.3](09-divergence-ledger.md#93-current-status)). Python and TypeScript do
not: Python's `_MAX_DEPTH`, `_MAX_NODES`, and `_MAX_INT_DIGITS` are
hardcoded module constants and TypeScript's are compile-time constants, with no
constructor argument, function parameter, or environment variable that lets a
caller change them. That is permitted ("MAY set any of these limits"), and it
is why those two ports skip the six `document-model/limits` vectors, which
need a runtime-configurable limit to declare
([`DIV-28`](09-divergence-ledger.md#94-known-open-divergences)). All five ports
do expose the maximum input size of D-23 (§2.4.2).

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
maximum **expansion factor** on every **candidate node** in its input, and
MUST reject input that exceeds it with `document.limit.alias-expansion`
([§8.3.2](08-conformance-and-errors.md#832-document-building-and-limits)).
A candidate node is every anchored definition, **and** every mapping and
sequence in the input whether or not it is anchored, **including the document
root** when it is a container and including a mapping written inline as a
merge source. Bounding only anchored nodes leaves the limit one keystroke from
void: an input that omits the anchor on the amplifying node is never checked.
For a candidate node `a`:

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

**What is, and is not, a candidate.**

- A **scalar** is never checked: `W = S = 1`, so `E = 1.00` trivially. A
  scalar anchor is a candidate in name only.
- The **document root** is a candidate when it is a mapping or a sequence.
  `S(root)` counts the whole document as written and `W(root)` the whole
  document as materialized.
- An **unanchored container that merely contains aliases** is a candidate
  like any other. `S` counts each alias it holds as one slot and `W` adds what
  each alias materializes, exactly as for an anchored node; the absence of an
  anchor changes nothing about its `E`.
- A **mapping written inline as a merge source** (YAML `<<: {a: 1}`) is a
  candidate. In the referrer's `S`, the `<<` entry's value counts as one slot,
  exactly as an alias there does, and the inline mapping's own written values
  add their slots on top; the inline container is that one slot, not a second.
  In `W` the inline container is flattened away like any merge source's, so
  the inline mapping contributes `W - 1`. Worked, for
  `t: {<<: {a: 1}, z: 1}`:

  ```
  W(t) = 1 + 1 + 1 = 3     S(t) = 4  (t, the << slot, a, z)     E(t) = 0.75
  ```

  The inline mapping's own `E` is computed like any candidate's, over its own
  subtree (`W = S = 2` for `{a: 1}`): it is 1.00 only when it contains no
  aliases. Aliases written inside it add to its `W` and count one slot each in
  its `S`, so it can exceed the maximum on its own.
  The sequence carrying a merge key's aliases is not a candidate: it is a
  syntactic carrier and holds no slot (below).
- A container nested inside another candidate is checked on its own **and**
  counted within the outer one: each candidate is measured over its own
  subtree, so one amplifying subtree is rejected where it sits, not diluted by
  the rest of a large document.

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
- **A merge key whose value is a *sequence* of aliases** — YAML 1.1's
  `<<: [*p, *q, ...]` form, which the reference accepts — is the single-alias
  case repeated, and nothing more. **Each** alias in the sequence contributes
  its target's edges flattened in, `W(target) - 1` apiece, exactly as the
  single-alias form does; **none** of them contributes its target's full `W`.
  The sequence holding the aliases is a syntactic carrier for the merge, not a
  materialized container, so it contributes **no slot of its own** to `W`. And
  the `<<` entry counts as exactly **one** written slot in `S`, whether its
  value is a single alias or a sequence of any length. Worked, given
  `p: &p {k: 1}`, `q: &q {j: 2}` and `z: &z {<<: [*p, *q], m: 3}`:

  ```
  W(z) = 1 + (W(p) - 1) + (W(q) - 1) + 1 = 4     S(z) = 3     E(z) = 1.33
  ```

  `S(z)` is 3 — `z`'s own container, the single `<<` entry, and `m` — not 5.
  Reading the plain-alias rule onto each element instead, and counting the
  sequence as a slot, would give `W = 7` over `S = 5`; that reading is wrong.
  Confirmed against the reference: `z` materializes `{j: 2, k: 1, m: 3}`, four
  slots.

  **D-18a. The carrier is a carrier whether or not it is anchored, and whether
  it is written in place or referred to.** A sequence in merge-value position is
  not a materialized container, and a codec MUST NOT let how it is spelled
  change that (D-18):

  - An **anchored** carrier, `<<: &s [*p, *q]`, is the unanchored carrier with
    a name attached. It holds no slot in `W` and none in `S`, the `<<` entry is
    still exactly one written slot, and the carrier is **not a candidate
    node**. Adding the anchor changes no verdict on the mapping that holds it.
  - An **alias to** a sequence in merge-value position, `<<: *s`, contributes
    exactly what the same members written inline would: the sum over the
    sequence's members of `W(member) - 1`, and no slot for the sequence
    itself. It does **not** contribute `W(s) - 1`, which would count each
    member's container slot that the merge flattens away. In `S` it adds one
    slot, the `<<` entry, and nothing for the members. Their written slots are
    counted once, where `s` was written: for an ordinary sequence value, as
    part of `S` of the container that holds it; for a merge-position carrier,
    as the `<<` slot plus the written slots of any inline or newly anchored
    mapping members (below).
  - A sequence written as an ordinary value and anchored there,
    `s: &s [*p, *q]`, is an ordinary sequence at that site: a candidate node,
    with
    `W(s) = 1 + W(p) + W(q)`. Only a reference to it from merge-value position
    flattens it. A plain alias to an anchored carrier, `t: *s` where `s` was
    written as `<<: &s [*p, *q]`, materializes the list and contributes
    `1 + W(p) + W(q)`.

  - An **empty** merge sequence, `<<: []`, is a well-formed carrier with no
    members, never an error. Its `W` contribution is 0, because a carrier
    holds no slot and there is no member to flatten, and in `S` the `<<` entry
    is still one slot. An **alias to an empty sequence** in merge position,
    `s: &s []` followed by `<<: *s`, is likewise a well-formed carrier
    contributing 0 (the sum over zero members). It merges nothing, so
    `config: {<<: []}` is an empty mapping. An empty sequence **not** in
    merge position, `k: []`, is an ordinary sequence node with `W = S = 1`.
    The input still contains a merge key, so it is subject to D-22. Worked,
    for `t: {<<: [], c: 3}`:

    ```
    W(t) = 1 + 0 + 1 = 2     S(t) = 3  (t, the << slot, c)     E(t) = 0.67
    ```

    and for `config: {<<: []}`, `W = 1`, `S = 2`, `E = 0.50`. An empty
    sequence satisfies "a sequence of mappings" vacuously, which is why it is
    not among the malformed shapes below.

  **Members of a merge MUST be mappings.** YAML 1.1's merge type takes a
  mapping or a sequence of mappings, and nothing in this specification
  admitted anything else; it is pinned here. A merge value that is a scalar, a
  merge sequence with a scalar member, a sequence inside a merge sequence
  (`<<: [*s]` where `s` is a sequence, or `<<: [[{a: 1}]]`), and `<<: *s` where
  `s` holds scalars are malformed input: the codec MUST reject them with
  `parse.codec-syntax`
  ([§8.3.1](08-conformance-and-errors.md#831-parse-text-to-document-stage-1)),
  the code for input that is not well formed in its source format, before D-18
  or D-22 counts anything. Merge-shape validation is part of reading the
  document, a syntax error, and it wins over every `document.limit.*` code
  when both are present, because D-18 and D-22 count a well-formed graph; a
  malformed document need not be counted at all. A carrier is therefore one
  level deep, and what remains to be counted is:

  - An **inline mapping** inside a carrier, `<<: [{x: 1}, *p]`, counts as a
    standalone inline merge source does: its own written slots, less its
    container, add to `S` of the referrer, and it contributes `W - 1`.
  - An **anchored mapping first defined inside a carrier**,
    `<<: [&m {y: 2}, *m]`, is a candidate node, with `W` and `S` counted where
    it is defined. A later alias to it, in a merge or anywhere else, uses its
    `W`; in a merge that is `W(m) - 1`.

  Worked, given nothing else in the document:

  ```
  z: {<<: [{x: 1}, &m {y: 2}, *m], k: 3} gives W(z) = 1 + 1 + 1 + 1 + 1 = 5,
  S(z) = 1 + 1 + 1 + 1 + 1 = 5, E(z) = 1.00
  ```

  The five slots of `S(z)` are `z`, the `<<` entry, `x`, `y` and `k`; the three
  merge members contribute `W - 1 = 1` each to `W(z)` and nothing but their
  written entries to `S(z)`.

  Worked, given `p: &p {k: 1}` and `q: &q {j: 2}` (`W = S = 2` for each):

  ```
  z: {<<: &s [*p, *q], m: 3} gives W(z) = 1 + 1 + 1 + 1 = 4, S(z) = 3, E(z) =
  1.33
  s: &s [*p, *q] gives W(s) = 1 + 2 + 2 = 5, S(s) = 3, E(s) = 1.67
  y: {<<: *s, m: 3} gives W(y) = 1 + 1 + 1 + 1 = 4, S(y) = 3, E(y) = 1.33
  ```

  `z` reads the same with or without the anchor on its sequence. `y` is 4, not
  `1 + (W(s) - 1) + 1 = 6`: the alias to `s` flattens its members, it does not
  flatten `s` as if `s` were a mapping.

The general rule is the first sentence; the three cases are what it comes to
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
the configured maximum for any candidate node `a` in it. The reference
default is **50**. A worked unanchored case, given `b: &b {k1: 1, k2: 2, k3: 3}`
and `t: {<<: [*b, *b, *b, *b]}`, where `t` has no anchor:

```
W(b) = 4   S(b) = 4   E(b) = 1.00
W(t) = 1 + 4*(W(b) - 1) = 13   S(t) = 2   E(t) = 6.50
```

`t` is a candidate although nothing refers to it, and it is rejected at a
maximum of 6 for exactly the reason an anchored `t` would be.

- **D-19.** The check MUST be performed **before** the expansion is
  materialized. `W` and `S` are computable in time linear in the size of the
  input from the raw anchor/reference graph alone, without walking the
  expanded tree, so a conformant implementation refuses an over-limit input
  without ever paying for the expansion it describes. An implementation that
  discovers the violation only after expanding does not satisfy this rule
  even if it reports the right code.

  **`W` is a conservative upper bound, not the exact materialized count.**
  Computing `W` from the reference graph — each reference contributing its
  target's full structural contribution, per the rules above — is what makes
  the check linear and pre-materialization, and it is deliberately blind to
  key-collision resolution. Where a merged key is overridden by a local key of
  the same name, the bound exceeds what is actually materialized. Given
  `p: &p {k: 1}` and `q: &q {<<: *p, k: 9}`, the rule computes
  `W(q) = 1 + (W(p) - 1) + 1 = 3`, while the reference in fact materializes
  `{k: 9}` — two slots — because `q`'s own `k` displaces the merged one. This
  overestimate is intentional and conformant: resolving which keys survive a
  collision requires walking the expanded tree, which is precisely the work
  D-19 exists to avoid paying before the input has been accepted. An
  implementation MUST NOT refine `W` downward by performing collision
  resolution during the check. The bound errs toward rejection, never toward
  acceptance, so no input that the exact count would refuse is admitted by the
  bound. Where §2.4.1 says `W(a)` is the number of value slots *materialized*,
  read it as the structural count defined by these rules; the two coincide
  except under key override.

  **The check is one pass.** `W` and `S` for every candidate node MUST be
  computed in a single traversal of the input with each anchored definition's
  `W` and `S` memoized, so the work stays linear in the size of the input no
  matter how many times a definition is referred to: a reference reads the
  target's stored `W`, it does not re-walk the target. Counting each candidate
  by re-expanding the aliases inside it is the quadratic or exponential
  behaviour D-19 forbids.

  **D-19's bound holds only if the check is made as it goes.** An
  implementation SHOULD evaluate `E(a)` per candidate node as it computes
  it and reject on the first `E(a)` over the maximum, rather than computing
  every `W` in the input and checking afterwards. Checking as it goes keeps
  every `W` it ever holds bounded by `max × S(a)` for the anchor in hand.
  Deferring the check lets the very input D-18 exists to refuse drive a `W` to
  arbitrary magnitude first — on a fixed-width integer that is an overflow,
  and a wrapped `W` can compare *under* the maximum, turning the attack input
  into an accept. `W` accumulation MUST be saturating (or arbitrary-precision)
  regardless of when the check runs, because an unanchored container can carry
  a `W` as large as an anchored one. An implementation that does defer the
  check MUST otherwise guard against that overflow, with a checked or
  saturating accumulation or an arbitrary-precision `W`.

  **Merge shapes are validated first.** A merge value that is not a mapping or
  a sequence of mappings (D-18a) is a syntax error, `parse.codec-syntax`. An
  implementation validates merge shapes in the same pass as the count or
  before it, need not count anything for a document that is malformed, and
  reports the syntax error rather than a limit code if the document has both
  a bomb and a malformed merge.
- **D-20.** An anchored definition that refers to itself, directly or through
  a cycle of other definitions, has unbounded `W` and MUST be rejected under
  this limit, with `document.limit.alias-expansion` — the same code as any
  other D-18 rejection. A codec MUST NOT attempt to compute a finite `E` for
  it, and MUST NOT materialize a cyclic or infinite structure instead.

  All five implementations satisfy this as of the Python adoption in
  omnist#352; before it, the reference rejected a directly self-referential
  mapping anchor with an uncoded `DocumentError` and accepted the self-merging
  form `a: &a {<<: *a, k: 1}`, materializing `{k: 1}`.

- **D-22.** A codec for a format with an anchor/reference mechanism MUST also
  enforce a finite maximum **expanded size** on the input as a whole: the
  number of value slots it materializes, which is `W(root)` as defined above,
  computed by the same single memoized pass. **D-22 applies only to an input
  that contains at least one alias or merge key.** An input with neither is not
  subject to it: its `W(root)` is its written size, `S(root)`, which D-9's node
  limit and D-23's input-size bound, where one is enforced, govern, and a
  plain YAML file is treated as a JSON or OML file of the same size is. A
  **merge key** here is a
  `<<` key as [§ YAML](formats/yaml.md) uses the term; that page says nothing
  of a quoted or explicitly tagged `<<`, and this rule does not decide it. A
  codec subject to D-22
  MUST reject the input with
  `document.limit.expanded-size`
  ([§8.3.2](08-conformance-and-errors.md#832-document-building-and-limits))
  when `W(root)` is **greater than** the maximum, and MUST accept it when
  `W(root)` is **equal to** the maximum. The reference default is
  **1 000 000** slots. The check is made at the root, after every candidate
  node has been measured against D-18 and before the expansion is materialized
  (D-19), with the same saturating or arbitrary-precision `W`; a saturated
  `W(root)` exceeds every maximum. Its `path` is `$`, as for D-18.

  **When both limits are crossed, D-18 is reported.** If any candidate node's
  `E` exceeds the maximum expansion factor, the input is rejected with
  `document.limit.alias-expansion` whether or not `W(root)` also exceeds the
  expanded-size maximum. Neither limit implies the other: an input can pass
  the ratio and fail the size, or pass the size and fail the ratio.

  **Why a second limit.** D-18 bounds amplification, not absolute size. A
  large document in which every container sits just under the maximum `E` is
  accepted by D-18 and can still allocate gigabytes. Measured in Go, an input
  of 30 000 containers (1.5 MB of text, `W` about 3.2 million slots, every `E`
  under 50) was accepted in 16 to 22 seconds with 2.5 GB allocated. The node
  limit does not catch it, because it counts mappings, not the scalars that make
  up most of that `W`. This is omnist-spec#125. The cliff is deliberate: a plain
  file of two million slots passes, and adding one alias makes it subject to
  the cap. D-22 bounds amplification; input size is bounded by D-23, which
  an implementation enforces or leaves to its caller.

  **The default.** It is chosen from measured `W(root)` of realistic aliased
  documents, which it must never refuse, and from the measured memory cost of
  the documents it must refuse. Compose files of 100 services merging a 20-key
  block and of 100 merging a 60-key block measure 2 223 and 6 263 slots; 1 000
  services merging a 60-key block, 62 063; a GitLab file of 200 jobs, 5 828; a
  Kubernetes file of 500 objects, 15 009. The largest of these is 16 times under
  the default. The measured memory bomb, 3.2 million slots at 2.5 GB in Go, is
  over three times above it. An implementation MAY
  configure another finite value (D-10) and MUST document it (D-11). It
  SHOULD NOT configure one above **10 000 000** without measuring its own
  memory per slot: the Go measurement above is about 780 bytes per slot, so
  10 000 000 slots is roughly 8 GB there, and other runtimes differ.

  **`W` is the conservative structural count (D-19)**, so a document whose
  merged keys are overridden can be refused by this limit though it
  materializes fewer slots; the limit errs toward rejection, as D-18 does.

**Scope, stated explicitly.** D-18 binds a codec *that has such a mechanism*.
It is not a fourth universal limit: §2.4's first three rows apply to every
Document however it was built, and D-18 and D-22 apply to a parse of a format
with anchors. Of the five formats this spec covers, **only YAML has one today**
([§ YAML](formats/yaml.md)); JSON, TOML, XML and OML have no construct that
materializes more than once from a single written definition, so the rule is
vacuous for them and they need not compute anything. It binds any future
format or extension that adds one. Nothing in D-18 refers to input byte
length, so there is no ratio-to-bytes to be undefined on a programmatic
construction route, and no denominator to disagree about. D-22 is likewise a
count of materialized slots, not of input bytes. It is also not a cap on plain
document size: a YAML input with no alias and no merge key is outside it, as a
JSON or OML input of the same size is. Bytes are bounded by D-23, not here.

**XML's entity expansion is the same class of problem and is already
handled.** A DTD's internal entities have exactly this shape — the "billion
laughs" attack is an XML attack first — but the data-XML profile in
[§ XML](formats/xml.md) rejects a DTD outright, so the mechanism never
reaches the Document builder. That is a stronger rule than this one, not a
gap in it, and it is deliberately not restated here: one refusal per hazard.

**On the reference default of 50.** It was first calibrated against `E` as
measured on anchored nodes only, where legitimate YAML read far below it: a
merge-key configuration of the `<<: *defaults` kind that docker-compose and
GitLab CI use reads `E = 1.00` for the *anchored defaults block* at every size
tested, up to 36 KB, because a merge key flattens into the referring mapping
rather than nesting under it; anchor-to-anchor chains and scalar-constant
reuse read at most 5.75. That is no longer the whole picture, because the
container rule also measures the mappings that do the merging.

**A mapping that merges a large anchor does not read 1.00, anchored or not.**
Its `E` is about `(keys + 2) / 3`: `job: {<<: *base, script: x}` writes three
slots (the container, `<<`, `script`) and materializes `keys + 2`. Measured
under the container rule:

- 100 services each merging a 20-key defaults block: worst `E = 7.33`.
- 100 services each merging a 60-key defaults block: worst `E = 20.67`.
- a `job` merging a 150-key base and writing one key of its own: `E = 50.67`,
  rejected at the default.
- a 100-key block aliased 100 times at the document root: `E = 50.50`,
  rejected at the default.

So realistic merges reach 20 and beyond, and the largest shapes reach the
limit. That is intended: a mapping that writes almost nothing of its own while
pulling in a large block is exactly the ratio D-18 bounds, and the earlier
"1.00 at every size" reading held only because unanchored referrers were never
measured. A workload that legitimately needs more MAY raise the maximum; that
is the documented escape hatch under D-10 and D-11, not a defect.

The amplifying shape — nested anchors, each level referring to the previous
one several times — crosses into dangerous territory around `E = 170` and
climbs steeply from there. 50 sits roughly 3.4× below the weakest dangerous
shape measured, and it fires well before the input grows large enough to
reach the node cap. An implementation MAY configure a different value,
subject to D-10 and D-11 like any other limit in §2.4: finite, and
documented.

### 2.4.2 Resource bounds beyond the Document

Every limit above bounds the Document an input builds, or the amplification of
one format mechanism. None bounds how many bytes an implementation will read,
and none bounds what a codec's parsing library spends on them. The 2026-10-04
audit measured the cost of that gap, so this section states what an
implementation does about it.

- **D-23. An implementation SHOULD enforce a finite maximum input size, in
  bytes, on every read of a Document from text or bytes, in every format, and
  SHOULD document it (D-11).** An implementation that enforces one MUST refuse
  an input larger than the maximum with `document.limit.input-size`
  ([§8.3.2](08-conformance-and-errors.md#832-document-building-and-limits)),
  at path `$`, and MUST accept an input equal to the maximum. An
  implementation that enforces none SHOULD say so where it documents its other
  limits. The size is **bytes, not characters**: it is the length of the input
  as received, so `é` counts as two, and a leading byte-order mark is counted
  (three bytes) because the length is taken before the mark is stripped (D-15)
  and before the input is decoded. The check comes first. It runs before
  decoding and before any parsing, so this code takes precedence over D-14's
  `parse.invalid-encoding` and over every other diagnostic: an oversized input
  is refused with it even if it is also invalid UTF-8 or malformed. An
  implementation reading from a stream, or any input of unknown length, SHOULD
  stop reading as soon as more than the maximum has been seen and then refuse
  the input, rather than buffer the rest. The rule applies to OML, JSON, YAML,
  TOML and XML alike, a YAML input with no alias included, which D-22 does not
  reach; the vectors sample JSON, YAML and OML, and the rule is the same for
  the other two. It cannot arise from a programmatic construction, which has no
  input bytes.
- **D-24. The maximum is configurable and has no reference default.** An
  implementation MAY set it to any finite value (D-10), MUST document the value
  it chooses (D-11), and SHOULD measure its slowest codec on a worst-case input
  of that size before raising it. This specification names no number, because
  the safe one depends on the codec library and the hardware.

  *Note (non-normative).* Parse cost can be superlinear in a codec library, and
  a byte cap bounds it: no input above the cap is parsed at all. A cap does not
  make any parse fast. Two measurements in the audit's record show the
  spread, and each is a single point. TypeScript's `yaml` library took 194.8 s
  on a 1.19 MB block mapping of 50 000 keys, on that one library
  ([DIV-12](09-divergence-ledger.md#94-known-open-divergences),
  omnist-ts#157), so a cap of 1.19 MB would still admit that input. PyYAML took
  about 4 s on a 1.1 MB, 50 000-key mapping, one point that was not re-run.
- **D-25. An implementation SHOULD also bound the length of a string scalar,
  the length of a label, and the size of a schema, and SHOULD document each
  bound (D-11).** Schema size means the bytes of OSD text it reads and the
  number of records and fields it will hold. This specification gives these no
  code and no vector: a refusal for one is implementation-defined and is not
  pinned by the conformance suite. They matter where D-23 does not reach: a
  Document or Schema built programmatically has no input bytes, and a
  deployment may want a per-string or per-schema bound tighter than its
  whole-input maximum. Where D-23 is enforced it already bounds every string,
  label and OSD text read from an input, so these three add nothing for that
  route.
- **D-26. What the existing limits do not bound.** D-9's node count counts
  nodes, not the scalars beneath them or the bytes they were written in: a
  flat document of a million scalars is within it. D-9's integer-digit limit
  bounds one literal. D-18 and D-22 bound only the amplification and expanded
  size of input that has an alias or a merge key, and **a plain alias-free
  input is exempt from D-22 by design**: D-22 bounds amplification, not size,
  and says the cliff is deliberate. D-23 is where a size bound is now stated.
  None of them bounds the cost of a codec's parsing library, and
  [§6.12](06-schema-algebra.md#612-termination) guarantees that the algebra
  terminates, not that it is cheap. D-23 is the only rule in this
  specification that bounds parse cost, and only through the size of the
  input.

---

## 2.5 Encoding

These rules apply to every text surface — OML, OSD, and every codec's input.
They are stated because each one is a place two implementations can build
*different Documents from identical bytes* while both believing they are
correct, which is the most dangerous class of divergence a data format has:
one system validates the reading it sees, another acts on a different one.

**D-14. Input MUST be valid UTF-8.** A malformed byte sequence is an error,
reported as `parse.invalid-encoding` ([§8.3.1](08-conformance-and-errors.md#831-parse-text-to-document-stage-1))
at text position `1:1`.
An implementation MUST NOT substitute `U+FFFD` or otherwise repair the input
and continue: silent repair is exactly how two readers end up with different
Documents, since what a replacement character stands in for is not
recoverable.

**The path is `1:1` always: a fixed value, not a computed position.** Every
other `parse.*` path is a `line:col` position in the decoded text, its column
counted in code points for OML and OSD ([§8.4](08-conformance-and-errors.md#84-paths), E-28).
D-14's is not, because what failed is the decoding of the input *as a whole* —
the diagnostic is raised before any position in the decoded text exists to be
computed. Taking the offending byte's own position instead would require this
spec to say which byte of an ill-formed sequence is *the* failing one.
Unicode answers that question with its substitution-of-maximal-subparts
rule, whose purpose is to tell a *replacing* decoder how many `U+FFFD` to
emit for a run of bad bytes — and D-14 forbids replacing, so **this spec
adopts no maximal-subpart convention and no substitute for one**. `1:1` is
the name this spec already gives a whole-input text refusal; D-21 reports
there too. One consequence is normative: a conformant implementation MUST
emit **at most one** `parse.invalid-encoding` diagnostic for one input,
however many malformed sequences it contains.

**Which entry points D-14 binds.** The test is whether the entry point ever
sees bytes:

- **D-14 binds every byte-oriented entry point, and it MUST validate** —
  one taking a byte array, a file path, standard input, or a byte stream. It
  MUST reject malformed input with `parse.invalid-encoding` at `1:1`.
- **A string-typed entry point MAY treat its input as already decoded — in
  every language.** D-14 is a rule about *bytes*: a byte sequence that is not
  well-formed UTF-8. Once a value is the language's text type, whatever it
  holds got there through a decode this implementation did not perform, and
  D-14 does not reach back through that decode to audit it.
- **An entry point that decodes bytes into a string on the caller's behalf
  is byte-oriented for D-14**, whatever its reader's signature says. A CLI, a
  file-reading convenience function, or a stdin wrapper MUST NOT decode with
  replacement and hand the result on: that is the silent repair the
  paragraph above forbids, moved one call earlier, and it is the likelier
  place to commit it, because the repair is usually a default argument on a
  decode call rather than anything the parser does. Such an entry point MUST
  fail the read per the first bullet.

**What is out of D-14's scope.** Two things resemble this rule and are not
it, both of them properties of an already-decoded string rather than of
bytes. A **UTF-16 lone surrogate** — which a JavaScript or Java string
admits — is ill-formed UTF-16, not an ill-formed UTF-8 byte sequence. A
**surrogate-escape artefact** — a code point in `U+DC80`..`U+DCFF` that a
lossy-but-reversible decode such as Python's `errors="surrogateescape"` put
into a string to stand for a byte it could not decode — is likewise a
property of the string handed in. A string-typed entry point that accepts
either is conformant under D-14. That is not a statement that either is
harmless: a surface's own grammar may reject a value on its own terms, and
OML's rule against an unpaired `\uXXXX` escape is about escape syntax in
source text and is a different rule from this one.

**What a writer does with such a string is not out of scope.** Accepting a
lone surrogate is conformant for a reader; emitting one is not for a writer.
A Document built from such a string, by a string-typed reader or
programmatically, MUST NOT be written: every writer fails with
`write.unsupported-value`, per
[C-9](07-codecs-and-deserialization.md#73-writing). The two rules do not
conflict, because they bind different steps: D-14 binds the bytes a reader
sees, C-9 binds the bytes a writer would emit.

**The one string type that is itself bytes, and what D-14 asks of it.** Go's
`string` is a byte sequence rather than decoded text — `utf8.ValidString` can return `false`
for one — so a Go reader taking a `string` is a byte-oriented entry point in
the sense of the first bullet. Concretely, and testably: **a conformant Go
implementation MUST reject any reader input `s` for which
`utf8.ValidString(s)` is `false`, with `parse.invalid-encoding` at `1:1`**,
rather than building a Document from its bytes. Rust's `&str` is the
opposite case — validity is the type's own invariant, so a reader taking one
has nothing left to check and the second bullet applies unchanged.

**This is also what makes D-14 conformance-checkable.** The vectors for it
give their input as bytes
([E-27](08-conformance-and-errors.md#853-operation-drivers)), and a runner
MUST present those bytes to a byte-oriented entry point if the
implementation has one **anywhere** — a CLI, or any library function that
reads a file, standard input or a byte stream, is one, whatever the
signature of the reader sitting behind it. Only an implementation offering
no byte-oriented entry point at all reports these vectors as a skip, under
[E-21](08-conformance-and-errors.md#855-reporting) with its own
[§9.4](09-divergence-ledger.md#94-known-open-divergences) ledger entry; a runner that
has merely not learned the `bytes_hex` input form yet reports E-20, "not yet
implemented". What no runner may do is decode the bytes with replacement and
run the result as though it were the vector's input, which would report a
pass for the one behaviour D-14 forbids.

**Where D-14 sits in the read order.** D-14 runs first, on the bytes, before
any text exists. Only then does D-15 strip a leading `U+FEFF` from the
decoded text, D-21 reject a second mark still standing at offset zero, and
the surface's own grammar or codec begin parsing.
[E-24](08-conformance-and-errors.md#831-parse-text-to-document-stage-1)
states the same order from the error-code side. The ordering is not
cosmetic: a BOM is `EF BB BF`, so a truncated one is malformed UTF-8 and
D-14 — not D-15 — is the rule that fires on it.

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

**D-21. Exactly one leading mark is consumed, and a second MUST be
rejected.** D-15 strips the mark at offset zero and stops there. A reader
MUST then reject a `U+FEFF` still standing at offset zero of the remaining
text, on every surface, reporting it at text position `1:1` — computed on
the text that remains after the strip, not on the original input — with
`parse.unexpected-token` on OML and OSD and `parse.codec-syntax` on JSON,
TOML, YAML and XML
([§8.3.1](08-conformance-and-errors.md#831-parse-text-to-document-stage-1)).
**An implementation MUST NOT silently consume the second mark, whatever its
parsing library does.**

**This is a rule Omnist imposes, not one derived from each format.** That
distinction matters, because on three of the six surfaces the remaining text
is perfectly well-formed in its own right: YAML 1.2 and XML 1.0 both admit a
leading byte-order mark at offset zero, which is exactly why their common
libraries discard one before any grammar sees it, and RFC 8259 §8.1 permits
a JSON parser to ignore *a* byte order mark without saying anything about how
many. Only OML, OSD and TOML reject the second mark on their own grammar's
terms. So the requirement above cannot be read off the formats; it has to be
stated, and on YAML and XML a conformant reader has to **pre-check** the text
it is about to hand its library rather than relying on the library to fail.

**The reason is D-15's own.** A library that quietly strips one more mark
under D-15's strip is performing a *second, undeclared* strip: two inputs
differing in bytes build one Document, with nothing in the result recording
which byte was discarded. That is precisely the outcome D-15 exists to
prevent, and permitting it on the two surfaces whose libraries happen to do
it would reopen the divergence D-15 closed, one layer down. Uniformity is
worth the pre-check.

**What it costs, stated plainly: YAML loses one document shape.** A YAML file
whose very first key is an *unquoted* key beginning with `U+FEFF` becomes
unreadable under this rule, because after D-15's strip that key's leading
mark is exactly the byte D-21 rejects. Measured, the loss is narrow: a
`U+FEFF` anywhere else in that key (`a` + mark + `bc`) reads fine, a key in
any position other than the first reads fine, and quoting the key
(`"` + mark + `abc":`) reads fine — so the shape has a workaround and only
the unquoted-first-key case has none. JSON, TOML and XML lose nothing at all,
since their first significant character can only be `{`, `[`, a bare key
character or `<`. That is the price, and it is worth naming rather than
leaving for a port to discover: the alternative is the silent-swallow
outcome, where the same file reads as two different Documents depending on
which YAML library the reader was built on, and nothing reports it.

**A `U+FEFF` that is not at offset zero MUST be preserved (D-21).** D-15
already says the mark is ordinary content anywhere but offset zero; this is
the part a pre-check can get wrong. A reader that strips or rejects every
`U+FEFF` it finds, rather than exactly the one at offset zero of the text
remaining after D-15, corrupts labels and values while passing every
doubled-BOM vector in the suite. The mark is an ordinary codepoint in a label
and in a scalar, it compares byte-wise like any other (D-16), and
`formats-json/encoding/interior-bom-is-ordinary-content` exists to catch a
pre-check written one character too wide.

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
