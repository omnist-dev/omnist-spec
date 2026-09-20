# 5. OSD grammar

**OSD** (Omnist Schema Definition) is the text format for Schemas. The
machine-readable grammar is [`grammars/osd.abnf`](https://github.com/omnist-dev/omnist-spec/blob/master/grammars/osd.abnf). This
chapter is its normative prose companion.

## 5.1 Shape

```osd
# Service topology
record Database {
    "type":            string,
    "server":          string,
    "port":            integer,
}
record Service {
    "host":            string,          # cardinality [1,1] by default
    "port":            integer,
    "databases" [1,]:  Database,        # at least one
    "tags" [0,]:       string,          # any count, including zero
    "owner" [0,1]:     string?,         # may be absent, may be null
    "payload":         any,             # one declared opening
}
root Service
```

Declarations may appear in any order. `root` need not come last, though
canonical output places it there.

## 5.2 The quoting rule

This is the single most important disambiguation in OSD, and it has no
exceptions.

| Spelling | Means |
|---|---|
| `"quoted"` | a **data string**. In this grammar that is only ever a field label. |
| unquoted `name` | a **schema name**: a scalar keyword, `any`, or a reference to a record. |

The two are never interchangeable. A bare name in label position is an error. A
quoted string in type position is an error.

## 5.3 Tokens

The tokenizer is a single ordered alternation. Whitespace and comments are
discarded before the parser sees anything, so a comment may appear anywhere
whitespace may — between declarations, inside a record body, after a field.

`#` starts a comment that runs to end of line.

An OSD `name` is `[A-Za-z_][A-Za-z0-9_]*` — this is
[§3.3](03-schema-model.md#33-formal-definition)'s S-8 `Name` domain,
enforced here by the tokenizer itself; OSD text cannot tokenize a name
outside this set in the first place, so no separate check is needed at
the schema-construction stage the way [OSD-OML](extensions/osd-oml.md)
needs one. Note the difference from OML's `IDENT`: **OSD names do not
permit a hyphen.**

### 5.3.1 String unescaping

An OSD string's value is computed by stripping the quotes and replacing every
backslash pair `\X` with the single character `X`. There is **no named-escape
table**. `\n` becomes the letter `n`, not a newline. `\\` becomes `\` and `\"`
becomes `"`, which are the only two cases where the rule matches intuition.

**OSD-1.** This is deliberately weaker than OML's string escaping and MUST NOT be
"upgraded" by an implementation. A label like `"a\nb"` is the three-character
string `anb`. Conformance vectors cover this.

**A raw control character below `U+0020` inside an OSD string is an error**
(`parse.control-character`, [§8.3.1](08-conformance-and-errors.md#831-parse-text-to-document-stage-1)),
the same restriction OML's double-quoted strings have
([§4.5](04-oml-grammar.md#45-strings)). Weak unescaping only changes
how backslash sequences are interpreted — it says nothing about which raw
bytes are legal in the string body to begin with, and there is no reason
for OSD to be laxer than OML on that separate question.

**The ban applies to every raw byte in the string body, escape context
included.** A control character immediately after a backslash is still a
control character in the body, so `"a\<U+0001>b"` is an error exactly as
`"a<U+0001>b"` is. This was previously written as "a *literal* control
character", which invited the reading that only an unescaped one was
forbidden — and `grammars/osd.abnf`'s escape alternative was written as
`"\" %x00-10FFFF`, which admitted the escaped form. The grammar now excludes
`%x00-1F` there, so the two artifacts agree.

## 5.4 Records and fields

```
record-def = "record" name "{" [ field *( "," field ) [ "," ] ] "}"
field      = string [ cardinality ] ":" type
```

A trailing comma after the last field is legal, and is what canonical output
emits. Fields are otherwise comma-separated, with no leading comma.

An empty record body — `record R { }` — is legal. It describes a node with no
edges.

**OSD-2. A field label MUST NOT be the empty string.** `""` is a legal *value* for an
OML/OSD string generally, but a label is an identifier, not a value — an
empty label names nothing a caller could ever reference, and any real input
that produced one represents a data-quality problem, not an intentional
schema. `"": string` is rejected with `schema.empty-label`.

**OSD-3. A field label MUST NOT contain `[` or `]`.** [§3.6.1](03-schema-model.md#361-validatedocument-schema-pseudocode)'s
diagnostic-path convention appends `[i]` to a repeated label's second and
later occurrences (the first occurrence of `"a"` paths as `$.a`, the second
as `$.a[1]`). A label that itself contains a literal bracket — `"a[1]": string`
declared as its own field, alongside a repeatable `"a"` — can produce that
exact same path for a genuinely different field, making the two
indistinguishable in a diagnostic. This is rejected outright with
`schema.bracket-in-label`, the same "don't allow two different things to
collide into one spelling" principle as `schema.empty-label` above and the
`format.*` write-side fixes in [§8.3.8](08-conformance-and-errors.md#838-format-codec-adjustments) —
here applied to the label vocabulary itself rather than to a written value.

## 5.5 Cardinality

```abnf
cardinality = "[" ( int [ "," [ int ] ] / "," [ int ] ) "]"
int         = 1*DIGIT
```

Every accepted form, and what each means:

| Written | min | max |
|---|---|---|
| *(omitted)* | 1 | 1 |
| `[3]` | 3 | 3 |
| `[1,5]` | 1 | 5 |
| `[5,]` | 5 | unbounded |
| `[,5]` | 0 | 5 |
| `[,]` | 0 | unbounded |

The grammar above accepts all five bracketed rows, including the comma-first
forms. It rejects `[]`, which is the "empty cardinality" error.

**OSD-4.** Three further checks sit above the grammar, and MUST be applied:

- A bound containing `.` is rejected: cardinality must be a whole number.
- **OSD-5.** A negative minimum is rejected. This spec's `int` production above accepts
  only unsigned digits, but a conformant tokenizer's number token MAY include
  an optional leading `-` (the reference implementation's does, since the same
  token also reads negative field values elsewhere in the grammar). Either
  way, `[-1]` MUST NOT be reported as a syntax error: whether the `-` is
  rejected at the token boundary or accepted into the token and rejected one
  step later at field construction, the observable result is the same
  invalid-cardinality error, not a parse failure.
- **OSD-6.** **A leading `+` is a syntax error**, unlike `-`. `[+1]` MUST be rejected as
  `parse.unexpected-token`, never accepted and silently normalized to
  `[1,1]`. The latitude granted to `-` above exists only because a
  tokenizer's number token legitimately reads negative values elsewhere in
  the grammar; `+` has no such role, so there is nothing for a conformant
  tokenizer to accept it into. The same goes for a repeated sign such as
  `[--1]`. Stated because `-` was addressed carefully and `+` was not,
  leaving three defensible readings — reject at the token boundary, accept
  then reject at construction, or accept and normalize — of which the third
  differs *observably* from the other two.
- An inverted range, `max < min`, is rejected. `[1,0]` tokenizes fine and is
  rejected on field construction.
- **A cardinality of exactly `[0,0]` is rejected.** A field that must occur
  zero times is indistinguishable, in every observable respect, from a field
  that was never declared at all — records are closed by default, so an
  undeclared label present in a document is already an error
  ([§8.3.4](08-conformance-and-errors.md#834-validate-document-against-schema)'s
  `validate.unexpected-field`). `[0,0]` would be a second spelling for that
  same thing, which this spec does not permit anywhere else (an empty array
  and an absent label are likewise never two different things — [§4.3.1](04-oml-grammar.md#431-arrays-are-sugar)).
  `[0,0]` tokenizes fine and is rejected at field construction, the same
  `schema.invalid-cardinality` error as a negative bound or an inverted
  range.

## 5.6 Types

```
type        = scalar-type / any-type / ref-type
scalar-type = scalar-name [ "?" ]
scalar-name = string | integer | number | boolean | date | time | datetime
any-type    = any
ref-type    = name
```

**Scalars.** Exactly seven keywords. A trailing `?` makes the scalar nullable;
omitting it means non-nullable.

**OSD-7. `any`.** Reserved in its exact lowercase spelling only. `any?` MUST be
rejected: `any` already includes `null`, so the suffix is redundant rather than
meaningful. Capitalized `Any` is *not* this production — it is an ordinary
`name` and therefore a reference, which produces an unknown-type error if no
record by that name exists.

**OSD-8. References.** Any `name` that is not a scalar keyword and not `any`.
Resolution is by lookup in the schema's environment, so forward references and
mutual recursion both work. `?` MUST NOT follow a reference; the error MUST
point the author at cardinality `[0,1]` instead.

## 5.7 Reserved names

**OSD-9.** A record MUST NOT be defined with a name that is one of the seven scalar
keywords, and MUST NOT be named `any`. In both cases the reason is the same: a
bare name in type position resolves to the builtin first, so such a record could
never be referenced. Per [§3.3](03-schema-model.md#33-formal-definition) S-3,
this check is exact and case-sensitive — `record String { ... }` does not
collide with the `string` keyword.

Defining the same record name twice is an error.

## 5.8 Root

**OSD-10.** Exactly one `root` declaration MUST be present. A schema with no root is an
error (`schema.no-root`). A schema with more than one `root` declaration is
also an error (`schema.duplicate-root`): a second `root` MUST NOT silently
override the first.

## 5.9 Canonical output

**OSD-11.** An OSD writer is canonical if, for every schema **OSD text can
represent** (OSD-14 below names the one class it cannot), it emits text that
parses back to an equal schema, following the canonical form below. Two conformant
implementations parsing the *same* source and immediately writing it back
MUST produce byte-identical text — that guarantee comes from
[§3.3](03-schema-model.md#33-formal-definition)'s order principles plus
the formatting rules below, together. It does **not** extend to two
*different* texts that happen to describe the same schema (for example,
the same schema written in OSD versus [OSD-OML](extensions/osd-oml.md)) —
each preserves its own input's declaration order, so equivalent-but-different
source can legitimately produce different, still-canonical output. Canonical
form:

- record and field order per
  [§3.3's canonical serialization order](03-schema-model.md#33-formal-definition)
  invariant;
- one record per `record` block, fields one per line, four-space indent;
- a trailing comma after every field, including the last;
- `root` last;
- cardinality omitted when it is `[1,1]`;
- labels always quoted, types never quoted;
- **OSD-15.** in a quoted label, a backslash MUST be written `\\` and a
  double quote MUST be written `\"`, and no other character is escaped.

```osd
record R {
    "a" [0,3]: string?,
}
root R
```

**OSD-12.** A compact mode with no indentation is permitted and MUST round-trip:
`record R { "a": string } root R`.

**Why OSD-15's two escapes are exactly the two that are needed, and why
OSD-11 needs them.** [§5.3.1](#531-string-unescaping) computes a string's
value by stripping the quotes and replacing every backslash pair `\X` with
the single character `X`. Written the other way round, that makes the
escaping rule an exact inverse: a backslash in the value has to be doubled,
or it will consume whatever character follows it; a double quote has to be
backslashed, or it will close the string early; and **nothing else may be
escaped**, because `\X` yields `X` for any `X`, so escaping an ordinary
character is harmless on read but breaks OSD-11's byte-identical guarantee
between two writers that disagree about which characters to escape. The
grammar already admits both forms — `grammars/osd.abnf`'s `string` excludes a
raw `"` from the body and allows `"\" %x20-10FFFF` — so this adds no syntax;
it states which of the admitted spellings a canonical writer emits, which
§5.9's list did not say at all. The rule round-trips every label including
the two that break a naive writer: a label **ending** in a backslash
(`a\` is written `"a\\"`, where a single trailing backslash would escape the
closing quote) and a label made only of backslashes and quotes. Both were
verified by reading back the text this rule says to write.

**Measured: the Python reference does not do this**, and it is the more
dangerous of the two failure modes. Its `to_osd` escapes nothing, so the
label `a\b` is written `"a\b"` and reads back as `ab` — **silent
corruption**, a different schema with no diagnostic anywhere — while the
label `a"b` is written `"a"b"` and at least fails loudly with
`parse.unterminated-string`. This is exactly the collision shape OSD-14
below refuses to permit, reached by a path OSD-14 does not cover because
these labels *are* representable; they were simply never being written
correctly. Recorded as `DIV-5`.

**OSD-14. A schema OSD text cannot represent MUST fail the write, never be
approximated.** [§5.3.1](#531-string-unescaping) bans every raw byte below
`U+0020` in a string body, escape context included, and OSD's unescaping is
weak — `\X` yields `X` and nothing more — so a field label containing a C0
control character has no OSD spelling at all: written raw the byte is
rejected, and written after a backslash it is the same byte in the same body
and rejected identically. An OSD writer given such a schema MUST fail with
`write.unsupported-value`
([§8.3.9](08-conformance-and-errors.md#839-write)), unconditionally and
regardless of any `strict` setting, on the rule
[§8.3.8](08-conformance-and-errors.md#838-format-codec-adjustments)'s E-6
already applies to every writer case of this shape: a writer that cannot
represent a value fails rather than emitting something that reads back as
different data — here, text no conformant OSD reader accepts at all. This is
what OSD-11 above is scoped by.

**OSD-14's diagnostic uses the Schema path of the record, not of the
field.** [§8.4](08-conformance-and-errors.md#84-paths)'s Schema paths are
`RecordName` and `RecordName.label`, and it offers no quoting or escaping for
a label inside a path — so the field form would require putting the exact
byte that has no spelling into a path compared byte-for-byte, which is the
problem restated rather than reported. The record form is unambiguous, needs
no new path syntax, and names a unit the reader can act on: the message,
which §8.5.2 never compares, is where the label belongs.

**The class is exactly that, once OSD-15 is in force: a C0 control character
in a field label — and such a schema still travels, as
[OSD-OML](extensions/osd-oml.md).** Backslash and double quote look like the
same problem and are not: OSD-15 above gives both a spelling, and after it
every model-legal label except the C0 case round-trips, verified by reading
back the text OSD-15 says to write for labels containing a backslash, a
quote, both, `U+007F`, `U+2028`, a space, a colon and a `#`. Two shapes that
also have no OSD text are **not** part of this class because they are not
legal labels to begin with: a label containing `[` or `]` and the empty
label, which [§5.4](#54-records-and-fields)'s OSD-2 and the bracket rule
reject on read and which [§3.3](03-schema-model.md#33-formal-definition)
excludes from the model, not merely from this surface. Record
names cannot reach it, because
[§3.3](03-schema-model.md#33-formal-definition)'s S-8 confines a `Name` to
`[A-Za-z_][A-Za-z0-9_]*` on every route into a Schema — enforced by this
chapter's own tokenizer ([§5.3](#53-tokens)) on the OSD route and by §E.6's
R-3a on the OSD-OML one — and `root` names a declared record, so it cannot
either. Field labels are the asymmetry, deliberately: §E.6's R-7 leaves a
label unrestricted beyond `[`, `]` and emptiness, because a label is a
*value*, not an identifier ([§5.2](#52-the-quoting-rule)). OML can write one
where OSD cannot — [OML-15](04-oml-grammar.md#45-strings) requires `\u00XX`
for exactly these characters and OML's escaping is real rather than weak — so
a schema `write_schema` must refuse is one `write_schema_oml` round-trips,
and that is the route for it. Measured: the Python reference's `to_osd`
emits the raw byte today and its own `parse_schema` then rejects what it
wrote, the same round-trip break the Go sweep found in `osd.Write`
([omnist-go#118](https://github.com/omnist-dev/omnist-go/pull/118)).

## 5.10 Worked examples

**OSD-13.** Every row MUST hold for a conformant implementation.

| Input | Result |
|---|---|
| `record R { "a\nb": string }` | label is the literal three-character string `anb` |
| `"a" [1,5]: string` | cardinality `(1, 5)` |
| `"a" [5,]: string` | cardinality `(5, unbounded)` |
| `"a" [,5]: string` | cardinality `(0, 5)` |
| `"a" [,]: string` | cardinality `(0, unbounded)` |
| `"a" []: string` | error: empty cardinality |
| `"a" [-1]: string` | error: invalid cardinality |
| `"a" [1,0]: string` | error: invalid cardinality |
| `"a" [0,0]: string` | error: invalid cardinality (redundant with not declaring the field) |
| `"a" [1.5]: string` | error: cardinality must be a whole number |
| `"a": string?` | nullable scalar field |
| `"a": Other?` | error: `?` cannot apply to a reference; use `[0,1]` |
| `record string { "a": string }` | error: reserved scalar name |
| `record any { "a": string }` | error: reserved type name |
| `record R{"a":string}` twice | error: duplicate definition |
| `record R{"a":string}` with no `root` | error: a schema must declare a root |
| `record R{"a":string} record S{"b":string}` with two `root` declarations | error: a schema MUST NOT declare more than one root (OSD-10) |
| `record R{a:string}` | error: expected a quoted field name |
| `record R{"": string}` | error: a field label MUST NOT be empty (OSD-2) |
| `record R{"a": "string"}` | error: a quoted string cannot appear in type position |
| `record R { "a": string, }` | valid; trailing comma accepted |
| `record R { "data": any }` | field type is `any` |
| `record R { "data" [0,]: any }` | valid; cardinality is orthogonal to `any` |
| `record R { "data": any? }` | error: `any` already includes null |
| `record R { "data": Any }` with no record `Any` | error: unknown type `Any` |
