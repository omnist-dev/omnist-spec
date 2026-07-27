# 10. Governance and versioning

## 10.1 The spec is upstream

The specification is upstream of every implementation. A behavior is correct
because the spec says so, not because the reference implementation does it.

In practice that means:

- A new feature is written into the spec first, with test vectors, and
  implemented second.
- A bug is a disagreement between an implementation and the spec. If the spec is
  silent, that silence is itself the bug and gets fixed first.
- The Python implementation is the **reference**, which means it is usually
  first to implement. It does not mean it is the authority. When Python
  disagrees with the spec, Python is wrong until the spec is changed.

This inversion is the point of having a spec at all. Without it, "what Omnist
does" is whatever the oldest implementation happens to do, and the other two
inherit its accidents as requirements.

## 10.2 Spec-TDD: the vector comes first

Every normative change follows the same order. It is red-before-green applied to
prose.

1. **Write the failing vector.** Add a test vector to `test-suite/` describing
   the behavior you want. Every current implementation fails it, or skips it.
   That failure is the proof the change is not already in effect.
2. **Write the prose.** Change the chapter that governs the behavior. The vector
   MUST cite the section it pins, via its `spec` field.
3. **Review both together.** A prose change with no vector is not reviewable —
   there is no way to tell whether an implementation satisfies it. A vector with
   no prose is a test of an unspecified behavior, which is how accidents become
   requirements.
4. **Implement.** Each implementation lands the change and turns the vector
   green on its own schedule.
5. **Update the ledger.** [Chapter 9](09-divergence-ledger.md) records who
   passes and who does not.

**A prose-only change is accepted only when it is genuinely non-normative** — a
clarification, an example, a typo — and only when it is stated in the change
description that no behavior is affected. If reasonable implementers could read
the before and after differently, it is normative and needs a vector.

Characterization vectors are the tool for the common case of documenting
behavior that already exists but was never written down. Write the vector so it
passes on the reference implementation, confirm it passes, then write the prose.
The vector is still first; it is just green on arrival, and its job is to catch
a future regression rather than to drive a change.

## 10.3 Versioning

The spec carries its own SemVer, independent of every implementation.

| Change | Bump |
|---|---|
| A document valid before is now invalid, or the reverse | **major** |
| An algebra result changes for some input | **major** |
| A canonical output's bytes change | **major** |
| A code is removed or its meaning changes | **major** |
| New optional capability that no existing input triggers | **minor** |
| New error code for a case previously reported generically | **minor** |
| New vectors covering existing behavior | **minor** |
| Clarification, example, typo, formatting | **patch** |

Implementations version independently. An implementation states which spec
version it targets. There is no requirement that implementation and spec version
numbers ever align, and no attempt should be made to make them align — that
coupling is exactly what the split is for.

Every implementation SHOULD publish the spec version it targets and its
conformance run's pass/fail/skip counts alongside each release.

## 10.4 Discrepancy resolution

When two implementations disagree, the sequence is fixed. Do not skip to step 4.

**Step 1: Reduce it to a vector.** Write the smallest input reproducing the
disagreement, in the format of
[§8.5](08-conformance-and-errors.md#85-conformance-harness-protocol). Verbal
descriptions of disagreements do not survive contact with a second reader.

**Step 2: Ask what the spec says.** Three outcomes:

- *The spec is clear.* The implementation that disagrees has a bug. File it,
  cite the section, done. No spec change.
- *The spec is silent.* This is a spec defect. Go to step 3.
- *The spec is ambiguous.* Also a spec defect, and a worse one, because both
  implementations were reading it in good faith. Go to step 3.

**Step 3: Decide, then write it down.** Choose the behavior on the merits, not
on which implementation already does it. The three questions, in order:

1. Does it keep every operation in [chapter 6](06-schema-algebra.md) decidable
   and total?
2. Does it keep the model closed, or does it open something without saying so?
3. Which behavior is easier to explain to someone who has read only the spec?

Prior implementation is a tiebreaker, not an argument. A behavior three
implementations share can still be wrong; that just means it is expensive to
fix, which is a scheduling fact, not a correctness one.

**Step 4: Land it in spec order.** Vector, prose, implementations, ledger — §10.2
in full. The implementation that was already right does nothing. The one that
was wrong files a bug against itself.

**Cross-implementation bug filing.** A bug found in one implementation MUST be
checked against the other two. A parser bug is usually a spec ambiguity wearing
a disguise, and a spec ambiguity is a bug in all three whether or not they
happen to have tripped over it yet.

## 10.5 Changing a refusal

[§3.2](03-schema-model.md#32-what-this-model-refuses-and-why) refuses unions,
enums, and open maps. Those refusals have a higher bar than an ordinary spec
change, because the whole termination table in
[§6.12](06-schema-algebra.md#612-termination) rests on them.

A proposal to add one MUST include:

1. A proof or clear argument that every operation in chapter 6 stays decidable
   and total.
2. The exact rule that resolves ambiguity when a value matches more than one
   candidate — the specific problem
   [§3.2](03-schema-model.md#32-what-this-model-refuses-and-why) names.
3. The effect on `normalize`'s canonical form, which is the operation most
   sensitive to model changes.
4. Vectors covering the new behavior and, separately, vectors demonstrating
   every existing result is unchanged.

Absent all four, the answer is no, and the proposal is closed rather than
deferred. A refusal that keeps being reopened without new argument costs more
than it saves.

## 10.6 Editorial standards

Small rules, applied to every file in this repository.

- **Encoding is UTF-8, without a byte-order mark.** Em-dashes, arrows, and
  non-ASCII characters are written literally. A file containing replacement
  characters or mojibake is a defect, however cosmetic it looks.
- **No tab characters** in prose, paths, or tables. Indentation in code blocks
  is spaces.
- **Line endings are LF.**
- **Every claimed constant, limit, or error code traces to something.** Either a
  named source location in an implementation, or an explicit statement that the
  content is new to the spec. There is no third category, and "presumably"
  is not a citation.
- **Short sentences.** A rule an implementer has to parse twice is a rule two
  implementers will parse differently.

## 10.7 Before you open the implementation PR

A scannable version of §10.2, for a contributor or an agent about to write
code rather than read policy:

- [ ] The behavior is written in a chapter, not just in this checklist's memory.
- [ ] A test vector for it exists in `test-suite/` and its `spec` field cites
      the section.
- [ ] The vector fails (or skips) against every implementation that doesn't
      have the behavior yet — that failure is what proves the change is real.
- [ ] The implementation PR links the spec section or vector it satisfies.
- [ ] The conformance harness (§8.5) passes on the changed vectors before merge.
- [ ] If the change touches §3.2's refusals, §10.5's four requirements are
      answered in the PR description, not assumed.

If any box is unchecked, stop and go back to §10.2 rather than negotiating an
exception in review.
