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

An OSD `name` is `[A-Za-z_][A-Za-z0-9_]*`. Note the difference from OML's
`IDENT`: **OSD names do not permit a hyphen.**

### 5.3.1 String unescaping

An OSD string's value is computed by stripping the quotes and replacing every
backslash pair `\X` with the single character `X`. There is **no named-escape
table**. `\n` becomes the letter `n`, not a newline. `\\` becomes `\` and `\"`
becomes `"`, which are the only two cases where the rule matches intuition.

This is deliberately weaker than OML's string escaping and MUST NOT be
"upgraded" by an implementation. A label like `"a\nb"` is the three-character
string `anb`. Conformance vectors cover this.

**A literal control character below `U+0020` inside an OSD string is an
error** (`parse.control-character`, [§8.3.1](08-conformance-and-errors.md#831-parse-text-to-document-stage-1)),
the same restriction OML's double-quoted strings have
([§4.5](04-oml-grammar.md#45-strings)). Weak unescaping only changes
how backslash sequences are interpreted — it says nothing about which raw
bytes are legal in the string body to begin with, and there is no reason
for OSD to be laxer than OML on that separate question.

## 5.4 Records and fields

```
record-def = "record" name "{" [ field *( "," field ) [ "," ] ] "}"
field      = string [ cardinality ] ":" type
```

A trailing comma after the last field is legal, and is what canonical output
emits. Fields are otherwise comma-separated, with no leading comma.

An empty record body — `record R { }` — is legal. It describes a node with no
edges.

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

Three further checks sit above the grammar, and MUST be applied:

- A bound containing `.` is rejected: cardinality must be a whole number.
- A negative minimum is rejected. This spec's `int` production above accepts
  only unsigned digits, but a conformant tokenizer's number token MAY include
  an optional leading `-` (the reference implementation's does, since the same
  token also reads negative field values elsewhere in the grammar). Either
  way, `[-1]` MUST NOT be reported as a syntax error: whether the `-` is
  rejected at the token boundary or accepted into the token and rejected one
  step later at field construction, the observable result is the same
  invalid-cardinality error, not a parse failure.
- An inverted range, `max < min`, is rejected. `[1,0]` tokenizes fine and is
  rejected on field construction.

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

**`any`.** Reserved in its exact lowercase spelling only. `any?` MUST be
rejected: `any` already includes `null`, so the suffix is redundant rather than
meaningful. Capitalized `Any` is *not* this production — it is an ordinary
`name` and therefore a reference, which produces an unknown-type error if no
record by that name exists.

**References.** Any `name` that is not a scalar keyword and not `any`.
Resolution is by lookup in the schema's environment, so forward references and
mutual recursion both work. `?` MUST NOT follow a reference; the error MUST
point the author at cardinality `[0,1]` instead.

## 5.7 Reserved names

A record MUST NOT be defined with a name that is one of the seven scalar
keywords, and MUST NOT be named `any`. In both cases the reason is the same: a
bare name in type position resolves to the builtin first, so such a record could
never be referenced.

Defining the same record name twice is an error.

## 5.8 Root

Exactly one `root` declaration MUST be present. A schema with no root is an
error.

> Implementations currently differ on a second `root` declaration: the Python
> reference silently lets the later one win. This spec does not bless that. See
> [chapter 9](09-divergence-ledger.md); the resolution proposed there is to
> make a duplicate root an error, which is a spec-level change requiring a test
> vector first.

## 5.9 Canonical output

An OSD writer is canonical if, for every schema, it emits text that parses back
to an equal schema, and the emitted text is byte-identical across conformant
implementations. Canonical form:

- one record per `record` block, fields one per line, four-space indent;
- a trailing comma after every field, including the last;
- `root` last;
- cardinality omitted when it is `[1,1]`;
- labels always quoted, types never quoted.

```osd
record R {
    "a" [0,3]: string?,
}
root R
```

A compact mode with no indentation is permitted and MUST round-trip:
`record R { "a": string } root R`.

## 5.10 Worked examples

Every row MUST hold for a conformant implementation.

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
| `"a" [1.5]: string` | error: cardinality must be a whole number |
| `"a": string?` | nullable scalar field |
| `"a": Other?` | error: `?` cannot apply to a reference; use `[0,1]` |
| `record string { "a": string }` | error: reserved scalar name |
| `record any { "a": string }` | error: reserved type name |
| `record R{"a":string}` twice | error: duplicate definition |
| `record R{"a":string}` with no `root` | error: a schema must declare a root |
| `record R{a:string}` | error: expected a quoted field name |
| `record R{"a": "string"}` | error: a quoted string cannot appear in type position |
| `record R { "a": string, }` | valid; trailing comma accepted |
| `record R { "data": any }` | field type is `any` |
| `record R { "data" [0,]: any }` | valid; cardinality is orthogonal to `any` |
| `record R { "data": any? }` | error: `any` already includes null |
| `record R { "data": Any }` with no record `Any` | error: unknown type `Any` |
