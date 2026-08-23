# 4. OML grammar

**OML** (Omnist Markup Language) is the native text format for Documents. It is
the only format whose syntax *is* the Document model rather than a projection
onto it, so every Document shape round-trips through OML exactly.

Two levels are defined:

- **OML-Core** — what the canonical writer emits. Every conformant reader MUST
  accept all of it.
- **OML-Extended** — additional read-only spellings. Every conformant reader
  MUST accept them; a canonical writer MUST NOT emit them.

The machine-readable grammar is [`grammars/oml.abnf`](https://github.com/omnist-dev/omnist-spec/blob/master/grammars/oml.abnf),
written in ABNF ([RFC 5234](https://www.rfc-editor.org/rfc/rfc5234)). This
chapter is its normative prose companion; where the two disagree, that is a
defect to be fixed, not a choice.

## 4.1 Shape

OML nesting is **brace-delimited**. Indentation is insignificant. Newlines and
semicolons are both edge separators and are interchangeable.

```oml
# a comment runs to end of line
name: "Ann"
address: {
  city: "Zurich"
  postcode: "8001"
}
tag: "x"
tag: "y"
```

That document is:

```
[ (name,"Ann"),
  (address, [(city,"Zurich"), (postcode,"8001")]),
  (tag,"x"),
  (tag,"y") ]
```

The same thing on one line, which is what the compact writer emits:

```oml
name: "Ann"; address: { city: "Zurich"; postcode: "8001" }; tag: "x"; tag: "y"
```

## 4.2 Tokenization

A conformant tokenizer MUST scan with **maximal munch under a fixed priority
order**. At each position it tries rules in this order and the first that
matches wins, consuming the longest match for that rule. There is no backtracking
between rules.

1. STRING family, pinned to a leading `"` or `'`
2. Punctuation: `{` `}` `[` `]` `:` `,`
3. `DATETIME`
4. `DATE`, only when not followed by `T` plus a TIME-shaped lookahead
5. `TIME`
6. `NUMBER` (decimal or exponent form)
7. The reserved float spellings `nan`, `inf`, `-inf`, emitted as `NUMBER`
8. `INTEGER`
9. `IDENT`

Anything matching none of these is an error.

Two consequences of the order are normative and MUST be reproduced.

**`nan` and `inf` can never be bare labels.** They are claimed by rule 7 before
`IDENT` is reached, so `nan: 1` is an error. `"nan": 1` is fine, since quoting
routes it to rule 1.

**DATE versus DATETIME needs one lookahead.** At a position where `DATE`
matches, the tokenizer MUST check whether the next character is `T` and the text
after it matches `TIME`. If so, it emits `DATETIME`. If not, it emits `DATE`,
and whatever follows is tokenized independently. So `2024-01-01T10:30` is one
`DATETIME`, while `2024-01-01T99` is a `DATE` followed by the `IDENT` `T99` —
which then fails as trailing content.

### 4.2.1 Separators

Horizontal space and comments are skipped and emit no token. A run containing at
least one newline or `;` collapses into a single separator token. A separator is
required between adjacent edges and is otherwise insignificant.

### 4.2.2 Reserved words

`null`, `true`, and `false` tokenize as ordinary `IDENT`. They are excluded from
label position by the **parser**, not the tokenizer. This differs from
`nan`/`inf`/`-inf`, which are excluded by the tokenizer. The difference matters
if you write a tokenizer-only consumer.

## 4.3 Values

```
value = scalar | "{" node-edges "}" | array
```

`{}` is a legal value: the empty edge list.

A bare identifier that is not `null`, `true`, or `false` is **not** a string. It
is an error. OML has no implicit string-from-identifier coercion anywhere.

### 4.3.1 Arrays are sugar

`[...]` in value position is expanded at **parse time** into repeated edges at
that exact position:

```oml
b: [1, 2, 3]
```

produces `[(b,1), (b,2), (b,3)]` — indistinguishable from three separate `b:`
edges. An array is not a value in the Document model, which is why array
elements MUST NOT themselves be arrays: there is nothing to nest into.

Rules:

- Comma is the only element separator. A newline or `;` inside `[...]` is an
  error.
- A trailing comma before `]` is legal.
- `[]` is an error, not a zero-edge expansion. An empty array and an absent
  label are the same Document, and OML does not offer two spellings for one
  thing.
- Separators and comments are otherwise insignificant inside `[...]`.

## 4.4 Labels

A label is written either as a `STRING` or as a bare `IDENT`. A bare label MUST
NOT be `null`, `true`, or `false`; those three, and only those three, are
rejected in bare-label position. That is the complete reserved set at the parser
level.

The canonical writer MUST emit a bare label only when the label text matches
`IDENT` **and** is not one of `null`, `true`, `false`, `nan`, `inf`. It MUST
quote otherwise. `nan` and `inf` are in the writer's quote list even though they
are not parser-level reserved words, because emitting them bare would produce
text the tokenizer reads back as a number.

## 4.5 Strings

Three spellings.

**Double-quoted (Core).** Recognized escapes are exactly `\"`, `\\`, `\/`, `\b`,
`\f`, `\n`, `\r`, `\t`, and `\uXXXX` with four hex digits. A `\uXXXX` in the
high-surrogate range `D800`–`DBFF` MUST be immediately followed by a second
`\uXXXX` in the low-surrogate range `DC00`–`DFFF`; the pair combines into one
code point. Any other escape, and any unpaired surrogate escape, is an error. A
literal control character below `U+0020` is an error.

**Raw (Extended, read-only).** `'...'` performs no escape processing at all. A
backslash inside is a literal backslash. There is no way to include a `'`; the
first one closes the string.

**Multiline (Extended, read-only).** `"""..."""`. An optional newline
immediately after the opening delimiter is consumed and is not part of the
value. The string closes at the **first** run of three or more `"` characters;
only the first three are consumed as the terminator, and any further quotes in
that run are returned to the scanner. A run of one or two quotes is literal
content. Tab and newline are legal inside; other control characters are not.

The canonical writer MUST emit only `\"`, `\\`, `\n`, `\r`, `\t`, and `\u00XX`
for other control characters. It MUST NOT emit `\/`, `\b`, `\f`, surrogate
pairs, raw strings, or multiline strings. Non-ASCII characters are emitted
literally.

## 4.6 Document shapes

An OML document is exactly one node. Unlike most formats there is no requirement
of a single root object. Three shapes are legal:

- a single top-level scalar — `42`, `"hello"`, `null`. The document *is* that
  leaf.
- zero or more top-level edges, repeats permitted, with no implicit wrapper.
- the empty document, which is the empty edge list.

Anything else — two bare scalars in a row, for instance — is an error.

### 4.6.1 Top-level disambiguation

The grammar is ambiguous on paper: a leading `IDENT` or `STRING` could begin
either a scalar or an edge. A conformant parser MUST resolve it with **one token
of lookahead** before committing. If the current token is a `STRING`, or an
`IDENT` that is not `null`/`true`/`false`, and the next token is `:`, parse as
an edge list. Otherwise parse as a single scalar.

This lookahead fires only at the start of a document and at the start of each
value inside `{ }`.

One sharp edge follows from it. At top level, `null: 1` is not the reserved-word
error: `null` fails the lookahead test, so the parser takes the scalar branch,
consumes `null`, and then fails on the leftover `:` as trailing content. Written
inside a node — `a: { null: 1 }` — label position is unambiguous and the
specific reserved-word error is produced instead. Both are errors; conformance
vectors distinguish them by code.

## 4.7 Limits

| Limit | Value | Enforced at |
|---|---|---|
| Integer literal digits, sign excluded | 4300 | tokenize time |
| Nesting depth, `{` levels | 200 | parse time |

Both match the Document model's caps (§2.4), deliberately: a document that
parses MUST NOT then fail to build. Both MUST raise a parse error rather than
letting a pathological input exhaust stack or memory.

Boundary behavior is normative and covered by conformance vectors: 4300 digits
and 200 levels parse; 4301 digits and 201 levels do not.

## 4.8 Worked examples

Every row below MUST hold for a conformant implementation, and the ABNF in
`grammars/oml.abnf` accepts every accepted input shown.

| Input | Result |
|---|---|
| `2024-01-01T10:30` | one `DATETIME` value |
| `2024-01-01T99` | `DATE` then `IDENT` `T99`, then a trailing-content error |
| `a: 'C:\no\escapes'` | raw string; value is that literal text, backslashes intact |
| `a: """` + newline + `hello` + newline + `world"""` | value `hello\nworld`; the leading newline is stripped |
| `a: """` + newline + `says ""hi"" there"""` | two-quote runs are literal content |
| `a: """` + newline + `x""""` (four closing quotes) | first three close the string; the fourth opens an unterminated string, error |
| `nan: 1` | error; `nan` is a `NUMBER` token and never reaches label position |
| `"nan": 1` | valid; the edge `(nan, 1)` |
| `null: 1` at top level | error on the leftover `:` as trailing content |
| `a: { null: 1 }` | reserved-word error naming `null` |
| `tag: "x"` newline `tag: "y"` | `[(tag,"x"), (tag,"y")]` |
| `b: [1, 2, 3]` | `[(b,1), (b,2), (b,3)]` |
| `[]` in value position | error, empty array |
| `a: {}` | `[(a, [])]` |
| `"hello"` alone | the document is the single scalar `hello` |
