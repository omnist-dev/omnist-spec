# Extensions

## What Core is

Everything in chapters 1–10 is **Core**: the Document model, the Schema model,
OML, OSD, the Schema Algebra, the format codecs (JSON/YAML/TOML/XML), and the
conformance protocol. Core is what "Omnist" means on its own. Every
implementation that claims any conformance at all MUST implement all of Core.
There is no partial-Core conformance level.

## What an Extension is

An **Extension** is an optional capability built entirely on top of Core,
using Core's existing models and machinery without modifying them. An
extension:

- MUST NOT change the meaning of any Core construct, grammar production, or
  error code.
- MUST NOT be required for Core conformance. An implementation that supports
  zero extensions is fully conformant.
- MUST be implementable using only Core's public surface (the Document model,
  the Schema model, OML's reader/writer, the Schema Algebra) — an extension
  that needs a new primitive at the Document or Schema level is not an
  extension; it is a Core change, and belongs in chapters 1–10 instead.
- gets its own chapter under this section, its own conformance vectors (tagged
  by extension name in the test suite), and its own entry in the divergence
  ledger (chapter 9) tracking which implementations support it.

This mirrors the Format Codecs relationship to Core: JSON/YAML/TOML/XML are
already "optional" in the sense that an implementation could in principle
support only OML and still be Core-conformant, but in practice every port
implements all of them. Extensions make that same relationship explicit for
capabilities that are more clearly separable — most implementations may
choose to support some but not all extensions.

## Conformance and versioning

- Extension support is reported independently of Core conformance. "Port X
  supports Core + OSD-OML" and "Port X supports Core only" are both valid,
  reportable conformance statements.
- Each extension carries its own version, independent of both the Core spec
  version and of other extensions — the same independence Core grants each
  implementation in [§10.3](../10-governance-and-versioning.md#103-versioning).
- Extension changes follow the same spec-TDD process as Core changes
  ([§10.2](../10-governance-and-versioning.md#102-spec-tdd-the-vector-comes-first)):
  vector first, then prose, implemented against the vector.
- An extension MAY be promoted into Core in a future major version if it
  becomes universal and foundational enough that treating it as optional no
  longer makes sense. That decision is deliberately not pre-committed for any
  currently-listed extension.

## Current extensions

| Extension | Summary |
|---|---|
| [OSD-OML](osd-oml.md) | A Document-shaped representation of a Schema, written in OML instead of OSD text. |
