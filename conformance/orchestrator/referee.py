"""The comparison referee -- docs/conformance-harness.md Sec4.

Uses the Python `omnist` library itself to parse OML/OSD text and judge
structural equality. This module is deliberately small: it does no CLI
invocation and no fixture-format parsing -- see orchestrator.py and
self_test.py for those.
"""
from __future__ import annotations

from omnist import read_oml, parse_schema


def compare_document(actual_oml_text: str, expected_oml_text: str) -> bool:
    """Structural, order-sensitive equality (Doc.__eq__ already provides
    this -- see the conformance-harness spec Sec4, no new library code
    needed for Document comparison)."""
    actual = read_oml(actual_oml_text)
    expected = read_oml(expected_oml_text)
    return actual == expected


def compare_schema(actual_osd_text: str, expected_osd_text: str, mode: str) -> bool:
    """Sec4/6.2: two legitimate meanings, chosen per operation.

    mode="exact": every record name and every field's label/type/cardinality
    must match (normalize/prune/extract -- output naming is spec-determined).
    mode="isomorphic": same structure up to a renaming of records (infer --
    generated record names are implementation-derived, never canonical).
    """
    actual = parse_schema(actual_osd_text)
    expected = parse_schema(expected_osd_text)
    if mode == "exact":
        return actual == expected
    if mode == "isomorphic":
        return actual.isomorphic_to(expected)
    raise ValueError(f"unknown comparison mode {mode!r}; expected 'exact' or 'isomorphic'")
