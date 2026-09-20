# 4. OML grammar

**OML** (Omnist Markup Language) is the native text format for Documents. It is
the only format whose syntax *is* the Document model rather than a projection
onto it, so every Document shape round-trips through OML exactly.

Two levels are defined:

- **OML-1. OML-Core.** — what the canonical writer emits. Every conformant reader MUST
  accept all of it.
- **OML-2. OML-Extended.** — additional read-only spellings. Every conformant reader
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

**OML-3.** A conformant tokenizer MUST scan with **maximal munch under a fixed priority
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

**OML-4.** Two consequences of the order are normative and MUST be reproduced.

**`nan` and `inf` can never be bare labels.** They are claimed by rule 7 before
`IDENT` is reached, so `nan: 1` is an error — specifically the scalar-then-
leftover error of [OML-25](#461-top-level-disambiguation), not a label error:
the parser consumes `nan` as the document's single `NUMBER` and fails on the
leftover `:`. `"nan": 1` is fine, since quoting routes it to rule 1.

**OML-5. DATE versus DATETIME needs one lookahead.** At a position where `DATE`
matches, the tokenizer MUST check whether the next character is `T` and the text
after it matches `TIME`. If so, it emits `DATETIME`. If not, it emits `DATE`,
and whatever follows is tokenized independently. So `2024-01-01T10:30` is one
`DATETIME`, while `2024-01-01T99` is a `DATE` followed by the `IDENT` `T99` —
which then fails as trailing content, `parse.trailing-content` at the `T99`
per [OML-26](#461-top-level-disambiguation).

### 4.2.1 Separators

Horizontal space and comments are skipped and emit no token. A run containing at
least one newline or `;` collapses into a single separator token. A separator is
required between adjacent edges and is otherwise insignificant.

### 4.2.2 Reserved words

`null`, `true`, and `false` tokenize as ordinary `IDENT`. They are excluded from
label position by the **parser**, not the tokenizer. This differs from
`nan`/`inf`/`-inf`, which are excluded by the tokenizer. The difference matters
if you write a tokenizer-only consumer.

### 4.2.3 NUMBER and INTEGER

```abnf
INTEGER  = ["-"] int-part
int-part = "0" / (%x31-39 *DIGIT)
NUMBER   = ["-"] int-part "." 1*DIGIT [exponent]
         / ["-"] int-part exponent
         / %s"nan" / %s"inf" / "-" %s"inf"
exponent = ("e" / "E") ["+" / "-"] 1*DIGIT
```

**OML-6. A numeric literal's integer part MUST NOT have a leading zero.** `int-part`
only permits a single `0`, or a nonzero digit followed by any digits — never a
`0` followed by more digits. `01` and `00` are errors
(`parse.leading-zero`); `0`, `0.5`, and `-0` are fine. This matches every
target format OML round-trips through (JSON, TOML) forbidding the same thing,
and closes what was previously undefined behavior — nothing in this spec
constrained `NUMBER`/`INTEGER` lexically before this section existed, so a
leading zero silently tokenized as if it were not there, with no normative
text saying whether that was required or merely one implementation's choice.

`int-part` alone (no `.`, no exponent) is not itself sufficient to choose
between `NUMBER` and `INTEGER` — that distinction is entirely rule priority
(§4.2's ordered list): `NUMBER` requires a fraction or exponent to match at
all, so a bare `int-part` only ever falls through to `INTEGER`.

### 4.2.4 DATE, TIME, and DATETIME value ranges

**OML-7.** ABNF constrains `DATE`/`TIME`/`DATETIME` (§4's grammar) to digit *counts*
only — it cannot express that a month digit pair must be `01`–`12`, for
instance. That range checking is still normative and MUST be enforced, at
parse time, as part of tokenizing these three rules, not deferred to some
later validation pass:

- **OML-8. `DATE`.** MUST be a valid proleptic Gregorian calendar date: month `01`–`12`;
  day valid for that month and year, including leap years (`2000-02-29` is
  valid, `1900-02-29` is not — 1900 is not a leap year).
- **OML-9. `TIME`.** and the time portion of `DATETIME` MUST have hour `00`–`23`,
  minute `00`–`59`, and second `00`–`59`. OML has no leap-second spelling:
  `23:59:60` is an error, not a valid 61st second.
- **OML-10. `tz-offset`.** MUST have the same hour and minute ranges as `TIME` —
  `00`–`23` and `00`–`59` respectively. This is the same rule as `TIME`'s,
  applied to the same two digit pairs; an implementation MUST NOT accept a
  wider range for the offset than it accepts for `TIME` itself. (This is
  called out explicitly because it is easy to implement the offset as a
  separate code path from `TIME` and let the two drift apart — an
  implementation that does that can end up with `+00:60` normalizing to a
  1-hour offset instead of being rejected, which is wrong twice over: `:60`
  is out of range the same way it is in `TIME`, and even where a normalizing
  interpretation might seem convenient, silently folding it to `+01:00`
  makes two different, both out-of-spec author inputs collide into one
  written form with no diagnostic — the same failure shape §8.3.8 already
  rejects for codec writers, here on the read side instead.)

Any of these out-of-range values is `parse.invalid-date` (for `DATE` and the
date portion of `DATETIME`) or `parse.invalid-time` (for `TIME`, the time
portion of `DATETIME`, and `tz-offset`).

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

**OML-11.** produces `[(b,1), (b,2), (b,3)]` — indistinguishable from three separate `b:`
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

**OML-12.** A label is written either as a `STRING` or as a bare `IDENT`. A bare label MUST
NOT be `null`, `true`, or `false`; those three, and only those three, are
rejected in bare-label position. That is the complete reserved set at the parser
level.

**OML-13.** The canonical writer MUST emit a bare label only when the label text matches
`IDENT` **and** is not one of `null`, `true`, `false`, `nan`, `inf`. It MUST
quote otherwise. `nan` and `inf` are in the writer's quote list even though they
are not parser-level reserved words, because emitting them bare would produce
text the tokenizer reads back as a number.

## 4.5 Strings

Three spellings.

**OML-14. Double-quoted (Core).** Recognized escapes are exactly `\"`, `\\`, `\/`, `\b`,
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

**OML-15.** The canonical writer MUST emit only `\"`, `\\`, `\n`, `\r`, `\t`, and `\u00XX`
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

**OML-16.** The grammar is ambiguous on paper: a leading `IDENT` or `STRING` could begin
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

**OML-25. When the lookahead takes the scalar branch, anything left after
the scalar is `parse.trailing-content`.** §8.3.1 states the general form —
content remaining after the document's single node is trailing content,
whatever that node was — and OML-25 is this section's case of it: the node is
a bare scalar, reached because the lookahead above declined the edge branch.
An implementation MUST report it at the text position of the first leftover
**significant** token, and MUST do so regardless of which tokenizer rule
produced the scalar. `null: 1`, `true: 1`, `nan: 1`, `inf: 1` and `5: 1`
therefore all fail identically, at `1:5`, `1:5`, `1:4`, `1:4` and `1:2`
respectively. That `nan` and `inf` are kept out of label position by the
**tokenizer** (§4.2.2) while `null`/`true`/`false` are kept out by the
**parser** is a real distinction, but it is spent before the scalar branch is
taken and MUST NOT change the code. `parse.unexpected-token` is for a token
appearing where the grammar does not allow it; a complete document body
followed by more text is not that, and reporting it that way sends a reader
looking for a bad token rather than for the second document they accidentally
wrote.

**"First leftover significant token" is §4.2.1's sense of significant.**
Horizontal space, newlines, `;` and comments are skipped or collapse into a
separator and are not themselves leftover content, so the reported position
is the first *real* token after the scalar, not the whitespace in front of
it: `1` newline `2` reports `2:1`, the `2`, not `1:2`. A **trailing comment
is not leftover content at all** — `1 # done` is the valid single-scalar
document `1`, because §4.2.1 skips comments before the parser can see them.
One case sits outside this rule entirely: a top-level bare sequence such as
`[1, 2] 3` never reaches it, because `[` in value position is not a document
body to begin with ([§4.3.1](#431-arrays-are-sugar)) and the read fails on
the `[` itself — measured against the reference as `parse.unexpected-token`
at `1:1`.

**OML-26. Leftover content after a complete *top-level edge* is
`parse.trailing-content` as well.** OML-25 covers the scalar branch of the
lookahead above; this covers the edge branch, and the two state one
principle together: **`parse.trailing-content` means content after the
document has ended.** At top level a complete edge can end the document —
§4.6's second legal shape is a list of edges and nothing further is owed —
so a significant token standing there with no separator in front of it is a
second document the author accidentally wrote. An implementation MUST report
`parse.trailing-content` at the text position of the first leftover
significant token, in the same §4.2.1 sense OML-25's paragraph above
defines, which applies here unchanged. `a: 1 b: 2` therefore fails at `1:6`,
the `b`; `a: 2024-01-01T99` fails at `1:14`, the `IDENT` `T99` that
[OML-5](#42-tokenization) produces, which is the row §4.8's table has always
carried.

**OML-27. Inside `{...}` or `[...]` the same missing separator is
`parse.unexpected-token`.** Nothing has ended there: a closing `}` or `]` is
still owed, so a token appearing where a separator or that delimiter belongs
is precisely §8.3.1's "a token appears where the grammar does not allow it",
and an implementation MUST report `parse.unexpected-token` at that token.
`a: { b: 1 c: 2 }` fails at `1:11`, the `c`; `a: [1 2]` fails at `1:7`, the
`2` — [§4.3.1](#431-arrays-are-sugar) makes the comma the only element
separator, so the `2` stands where a `,` or `]` was owed. **The deciding
fact is the enclosing delimiter, not the missing separator**, which is
absent in all four of these inputs. Reporting them all one way would either
send a reader inside a brace looking for a second document, or send a reader
who has written one document too many looking for a bad token.

## 4.7 Limits

| Limit | Value | Enforced at |
|---|---|---|
| Integer literal digits, sign excluded | 4300 | tokenize time |
| Nesting depth, `{` levels | 200 | parse time |

**OML-17.** Both match the Document model's caps (§2.4), deliberately: a document that
parses MUST NOT then fail to build. Both MUST raise a parse error rather than
letting a pathological input exhaust stack or memory.

Boundary behavior is normative and covered by conformance vectors: 4300 digits
and 200 levels parse; 4301 digits and 201 levels do not.

## 4.8 Worked examples

**OML-18.** Every row below MUST hold for a conformant implementation, and the ABNF in
`grammars/oml.abnf` accepts every accepted input shown.

| Input | Result |
|---|---|
| `2024-01-01T10:30` | one `DATETIME` value |
| `2024-01-01T99` | `DATE` then `IDENT` `T99`, then a trailing-content error — `parse.trailing-content` at `1:14` (OML-26) |
| `a: 'C:\no\escapes'` | raw string; value is that literal text, backslashes intact |
| `a: """` + newline + `hello` + newline + `world"""` | value `hello\nworld`; the leading newline is stripped |
| `a: """` + newline + `says ""hi"" there"""` | two-quote runs are literal content |
| `a: """` + newline + `x""""` (four closing quotes) | first three close the string; the fourth opens an unterminated string, error |
| `nan: 1` | error; `nan` is a `NUMBER` token and never reaches label position, so the parser consumes it as a scalar and fails on the leftover `:` — `parse.trailing-content` at `1:4` (OML-25) |
| `inf: 1` | error, identical to `nan: 1` — `parse.trailing-content` at `1:4` |
| `5: 1` | error; `INTEGER` is a scalar and the lookahead never routes it to label position — `parse.trailing-content` at `1:2` |
| `"nan": 1` | valid; the edge `(nan, 1)` |
| `null: 1` at top level | error on the leftover `:` as trailing content — `parse.trailing-content` at `1:5`, the same rule |
| `a: { null: 1 }` | reserved-word error naming `null` |
| `tag: "x"` newline `tag: "y"` | `[(tag,"x"), (tag,"y")]` |
| `b: [1, 2, 3]` | `[(b,1), (b,2), (b,3)]` |
| `[]` in value position | error, empty array |
| `a: {}` | `[(a, [])]` |
| `"hello"` alone | the document is the single scalar `hello` |

## 4.9 Canonical output

An OML writer is canonical if, for every Document, it emits text that parses
back to an equal Document, following the canonical form below.

**OML-19.** **Two conformant implementations writing the *same* Document MUST produce
byte-identical text.** This guarantee is stronger than
[OSD's](05-osd-grammar.md#59-canonical-output), for a structural reason: OML's
syntax *is* the Document model, and edge order is data
([§2.3](02-document-model.md#23-structural-invariants) D-1), so there is no
separate source-declaration order to preserve. Two different OML texts
denoting the same Document — array sugar versus repeated labels, compact
versus expanded — therefore canonicalise to the same bytes, where the
corresponding OSD case legitimately does not.

Canonical form:

- **OML-20. OML-Core only.** A canonical writer MUST NOT emit OML-Extended spellings,
  though every reader MUST accept them — restating the Core/Extended split
  defined in this chapter's opening.
- **Edges in Document order**, always. Order is data and is never rearranged.
- **OML-21. Repeated labels, never array sugar.** `[(b,1), (b,2), (b,3)]` MUST be
  written as three `b:` edges, not as `b: [1, 2, 3]`. Both parse to the same
  Document (§4.3.1), so a canonical form has to pick one, and this is it.
  Emitting array sugar is a permitted non-canonical writer option, not
  canonical output.
- **One edge per line.** A node value opens with `{` on the edge's own line,
  its edges indented by two spaces, and a closing `}` at the parent's
  indentation.
- **Labels** bare only where §4.4 permits, quoted otherwise.
- **String escapes** restricted to the set §4.5 allows.

```oml
name: "Ann"
adr: {
  city: "Z"
  pc: "8001"
}
tag: "x"
tag: "y"
```

**OML-22.** A **compact mode** is permitted: the whole Document on one line, edges
separated by `;` rather than newlines. "Compact" means single-line, not
merely unindented — a writer that keeps newlines but drops indentation is
producing a third layout, which this section does not define and which a
canonical writer MUST NOT emit.

```oml
name: "Ann"; adr: { city: "Z"; pc: "8001" }; tag: "x"; tag: "y"
```

**OML-23.** Compact output MUST round-trip in both of the senses that matter, and they
are different claims:

- **Parsing it yields an equal Document** — the same Document the expanded
  form above denotes. Compact mode changes layout, never content.
- **OML-24. Re-writing that Document in compact mode reproduces the same bytes.**
  Compact mode is itself canonical within its own layout, so two conformant
  implementations emitting compact output for one Document MUST agree byte
  for byte, exactly as they must for the expanded form.

What it does *not* claim is that compact and expanded output are
interchangeable byte sequences: they are two canonical layouts of one
Document, each stable under its own round-trip.
