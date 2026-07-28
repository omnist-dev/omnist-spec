# 3. The Schema model

## 3.1 Mental model

*Non-normative.*

A schema is a graph of named records. Each record lists the labels it allows,
how many times each may appear, and what shape sits at the other end of each
edge.

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

The whole order sits under a single top-level `order` key. That is deliberate:
a Document with one top-level edge is the only shape XML can carry, so a
single-rooted schema is the one that round-trips through every format
([chapter 7](07-codecs-and-deserialization.md)).

As a graph, `root Root` looks like this. An edge label carries its cardinality;
the node it points to is either a scalar kind or another record.

```mermaid
graph LR
    Root((Root)) -->|"order [1,1]"| Order((Order))
    Order -->|"id [1,1]"| string1(("string"))
    Order -->|"status [1,1]"| string2(("string"))
    Order -->|"total [1,1]"| number1((number))
    Order -->|"address [1,1]"| Address((Address))
    Order -->|"items [1,∞]"| LineItem((LineItem))
    Order -->|"coupon [0,1]"| string3(("string"))
    Address -->|"street [1,1]"| string4(("string"))
    Address -->|"city [1,1]"| string5(("string"))
    LineItem -->|"sku [1,1]"| string6(("string"))
    LineItem -->|"qty [1,1]"| integer1((integer))
    LineItem -->|"price [1,1]"| number2((number))
```

Four things are worth noticing before the formal rules.

**Every record is closed.** `Order` allows `id`, `status`, `total`, `address`,
`items`, and `coupon`, and nothing else. A stray `shipping` edge is invalid.
There is no wildcard.

**Cardinality does all the multiplicity work.** `[1,1]` is required and is the
default when you write no bracket. `[0,1]` is optional. `[1,]` is a non-empty
array. `[,1]` is at most one. There is no array type, because a repeated label
is already the array.

**Records are named and referenced.** There is no inline record body inside a
field. Reuse and recursion then work the same way as every other reference, and
the schema is a graph of named definitions rather than a nested tree.

**A field's type is exactly one thing.** One scalar kind, or one reference, or
`any`. Never a choice between candidates.

That last point is worth dwelling on, because it is the constraint that shapes
the whole model.

---

## 3.2 What this model refuses, and why

Omnist does not support structural unions (`{a} | {b}`), value enums
(`"red" | "green"`), or open/wildcard maps (`{ [string]: T }`). These are
refusals, not omissions awaiting a future release.

The reason is one sentence, and it is the same reason in all three cases:

> **The moment a value can match more than one candidate, there is no
> principled way to decide what it really is.**

Follow it through. If a field could be "an integer or the literal string
`unlimited`", then when a reader materializes a value it must pick a type, and a
value that matches both candidates — or neither cleanly — leaves it guessing.
If a record could be `{a} | {b}`, then a node matching both admits two different
answers to "which record is this," and every operation downstream inherits the
ambiguity. If a record has an open key set, the label alphabet the algebra
reasons over is no longer finite, and `compatible_with`, `normalize`, and
`extract` stop being decidable.

The rest of this specification does not repeat this argument. Where a refusal
appears below, this is the reason.

The single sanctioned opening is `any` (§3.7), which is designed to not create
this problem: it opens a value, never a label alphabet, and it is written
literally in the schema text so it can be found by grep and audited by a human.

**The closed alternative to an open map.** Refusing `{ [string]: T }` doesn't
mean open-ended key/value data is unmodelable — it means it has to be
authored as a record of entries instead of a map:

```
record Env      { "entry" [0,]: EnvEntry }
record EnvEntry { "key": string, "value": string }
root Env
```

This gives up something real, on purpose: duplicate keys now validate (two
`entry` edges can carry the same `"key"` value — nothing stops it), and data
must be authored in this entry-list shape from the start. A third party's
`{"A": "1", "B": "2"}` can't be validated as-is; it has to be restructured
into entries first, which only works when the caller owns that
restructuring step. That's exactly the case `any` exists for (§3.7) — data
whose shape isn't the caller's to restructure at all.

---

## 3.3 Formal definition

```
Schema      = (root: Ref, env: Name -> Record)

Record      = { Field, ... }                    ; CLOSED: only these labels
Field       = (label: String, type: Type, cardinality: [min, max])
Type        = Scalar | Ref | Any
Scalar      = (kind, nullable: Boolean)
              kind in { string, integer, number, boolean, date, time, datetime }
Ref         = Name                              ; resolved in env
Any         = the singleton `any` type
min         = non-negative integer
max         = non-negative integer | unbounded
```

Constraints on a well-formed schema:

- **S-1.** Exactly one root MUST be declared. The root MUST be a `Ref`, never a
  scalar and never `any`.
- **S-2.** `min` MUST be a non-negative integer. `max`, when bounded, MUST be a
  non-negative integer with `max >= min`. A negative bound or an inverted range
  is an error.
- **S-3.** A record name MUST NOT be one of the seven scalar kind keywords, and
  MUST NOT be `any`. Type position resolves a bare name to a builtin first, so
  such a record could never be referenced.
- **S-4.** A record name MUST be unique within `env`.
- **S-5.** A field's label MUST be unique within its record. Two fields naming
  the same label is an error, not an implicit merge.
- **S-6.** A `Ref` MUST resolve to a name present in `env`. Forward references
  and mutual recursion are legal; a dangling reference is an error.
- **S-7.** `nullable` MAY be set only on a `Scalar`. A nullable `Ref` and a
  nullable `any` are both errors.

A schema MAY be recursive. `env` is finite, so every operation in
[chapter 6](06-schema-algebra.md) terminates.

---

## 3.4 Cardinality

Cardinality is a closed integer range `[min, max]` where `max` may be unbounded.
It bounds the **count** of edges carrying the field's label in a node. It says
nothing about their positions.

The OSD surface forms:

| Written | min | max | Meaning |
|---|---|---|---|
| *(omitted)* | 1 | 1 | Exactly one. The default. |
| `[n]` | n | n | Exactly n |
| `[m,n]` | m | n | Between m and n inclusive |
| `[m,]` | m | unbounded | At least m |
| `[,n]` | 0 | n | At most n |
| `[,]` | 0 | unbounded | Any count, including zero |
| `[]` | — | — | **Error.** Empty cardinality. |

Common cases in the shorthand above: `[1,1]` required, `[0,1]` optional,
`[0,]` array, `[1,]` non-empty array, `[2,5]` bounded array.

The grammar in [chapter 5](05-osd-grammar.md) accepts every row of this table
except the last, which it rejects with a specific error. In particular the
comma-first forms `[,n]` and `[,]` are legal: a minimum bound before the comma
is not required.

A field with `max = 0` is legal to write and means the label may never appear.
`prune` removes such fields (§6.5).

---

## 3.5 Nullable versus optional

These are different questions and they use different mechanisms. Conflating
them is the most common modeling error in Omnist.

| Question | Mechanism | Written |
|---|---|---|
| May the edge be missing? | cardinality `min = 0` | `"coupon" [0,1]: string` |
| May the value present be `null`? | nullable scalar | `"coupon": string?` |
| Both? | both | `"coupon" [0,1]: string?` |

`?` applies to scalars only. A reference MUST NOT take `?`; "this subtree may be
absent" is cardinality `[0,1]`. `any` MUST NOT take `?` either, since `any`
already admits `null`.

> A record-or-null field would need a type that is half scalar and half
> reference. The model has no such type, by §3.2.

---

## 3.6 Validation

A node `n` conforms to a record `R` in schema `S` if and only if all three hold.

1. **Cardinality.** For every field `(label, type, [min, max])` in `R`, let `c`
   be the number of edges in `n` whose label equals `label`. Then
   `c >= min`, and if `max` is bounded, `c <= max`.
2. **Closedness.** Every edge label in `n` is the label of some field of `R`.
3. **Targets.** For every edge in `n`, its target conforms to the type of the
   field whose label it matches.

A target conforms to a type as follows:

- to `Scalar(kind, nullable)`: the target is a value whose kind is `kind`, or
  the target is `null` and `nullable` is true. A node never conforms to a
  scalar.
- to `Ref(name)`: the target is a node conforming to `env[name]`. A value never
  conforms to a reference.
- to `any`: always. Descent stops; nothing below is checked.

A Document conforms to a schema `S` if its root node conforms to `env[S.root]`.

**Order MUST be ignored** at every step (invariant D-3). Validation counts
edges; it never sequences them.

**Validation checks, it never converts.** A value either has the declared kind
or it does not. Converting a value to match a declared type is materialization,
a separate operation defined in
[chapter 7](07-codecs-and-deserialization.md).

**Validation MUST report every failure**, not just the first. A validation
result is a list of `(path, code, message)` entries; an empty list means valid.
Codes are defined in [chapter 8](08-conformance-and-errors.md).

### 3.6.1 `validate(document, schema)` — pseudocode

Uses the notation of [§6.2](06-schema-algebra.md#62-notation-used-in-the-pseudocode):
`S.resolve(t)`, `R.field(label)`, `f.min`/`f.max`.

```
function validate(document, S):
    result = ValidationResult()               # a list of (path, code, message)
    conform(document.root, S, S.root, "$", result)
    return result

function conform(node, S, t, path, result):
    d = S.resolve(t)
    if d is Any:
        return                                 # descent stops; accepted unchecked
    if d is Scalar:
        conform_scalar(node, d, path, result)
    else:                                       # d is Record
        conform_record(node, S, d, path, result)

function conform_scalar(node, s, path, result):
    if node is a node (not a leaf):
        result.add(path, "shape-mismatch", "expected a scalar value, got an object")
        return
    if node.value is null:
        if not s.nullable:
            result.add(path, "null-not-allowed", "null not allowed here")
        return                                  # null never checked against kind
    if not matches_kind(node.value, s.kind):
        result.add(path, "type-mismatch", "value does not match declared kind")

function conform_record(node, S, rec, path, result):
    if node is a leaf (not a node):
        result.add(path, "shape-mismatch", "expected an object, got a value")
        return
    counts = {}
    for (label, child) in node.edges:            # in edge order; order not otherwise used
        i = counts.get(label, 0)
        counts[label] = i + 1
        child_path = path + "." + label + (("[" + i + "]") if i > 0 else "")
        f = rec.field(label)
        if f is none:
            result.add(child_path, "unexpected-field", "field not declared on this record")
            # no further descent: an undeclared field has no type to check against
        else:
            conform(child, S, f.type, child_path, result)
    for f in rec.fields:
        c = counts.get(f.label, 0)
        if c < f.min or not le(c, f.max):
            result.add(path, "cardinality",
                        "field " + f.label + " occurs " + c + " time(s), "
                        + "expected [" + f.min + "," + f.max + "]")
```

Two details that are easy to miss and change the result if skipped:

- **An undeclared field's target is never descended into.** It is reported and
  left alone; conformance of its subtree is meaningless once the field itself is
  invalid.
- **The cardinality error's path is the parent node, not the field's edges.**
  "This record is missing a required field" has no single edge to point at when
  the count is zero, so the path is always the record's own path, even when the
  count is nonzero-but-wrong.

`validate` MUST run within the depth limit of [§2.4](02-document-model.md#24-safety-limits).
Exceeding it is a resource-cap error, not a validation finding, and is defined
there, not in this section.

---

## 3.7 The `any` type

`any` is the model's one sanctioned opening. It accepts every legal Document
value: any scalar of any kind, `null`, and any node of any shape.

Its scope is deliberately narrow.

**What `any` buys: one schema for a variant payload.** A common shape in
practice — webhooks, message-queue events, CloudEvents — is a rigorously
typed envelope wrapping a payload whose shape depends on a sibling field.
Without unions, that payload is out of reach entirely; `any` makes it
reachable:

```
record Event {
    "id":      string,
    "type":    string,
    "created": datetime,
    "data":    any,
}
root Event
```

Both of these validate against that one schema:

```json
{"id": "evt_1", "type": "user.created",
 "created": "2026-07-01T09:30:00",
 "data": {"name": "Ann", "email": "ann@example.com"}}
```

```json
{"id": "evt_2", "type": "payment.settled",
 "created": "2026-07-01T09:31:00",
 "data": {"amount_cents": 1250, "currency": "EUR"}}
```

This does not smuggle a union back in. The schema never chooses between
candidates — application code dispatches on `type` explicitly, then
validates `data` against a per-event-type schema of its own, also closed.
The choice lives in code, where it's visible and debuggable, never in the
algebra.

**What `any` opens.** The value at one declared field, and everything beneath
it.

**What `any` does not open.** The record's label alphabet. A field typed `any`
still has a label and still has a cardinality; the record remains closed. Adding
an `any` field does not let unknown labels through anywhere.

Semantics of `any` in each operation:

| Operation | Behavior at an `any` boundary |
|---|---|
| validate | Descent stops. The subtree is accepted unchecked. |
| `compatible_with` | If the right-hand type is `any`, the answer is true — `any` absorbs everything. If the left-hand type is `any` and the right-hand type is not, the answer is false. |
| materialize | The subtree passes through untouched. No leaf upgrades happen inside it. |
| `infer` | `infer` MUST NOT emit `any` unless explicitly requested. When requested, every opening it introduces MUST be reported. |
| `lint` | Every `any` field is reported as an informational finding, so a human can audit the schema's openings. |

Restrictions:

- `any?` MUST be rejected. `any` already includes `null`.
- A record MUST NOT be named `any`.
- Only the exact lowercase spelling is reserved. `Any` is an ordinary name and
  therefore a reference.
- Cardinality is orthogonal to `any`: `"data" [0,]: any` is legal.

> The cost of `any` is stated plainly in §6.2: compatibility checking is
> vacuous inside an `any` boundary, so a change made beneath one is invisible to
> `compatible_with`. That is the trade the escape hatch buys, and it is why
> `lint` inventories every occurrence.
