"""
Mechanical (no LLM) file surgery for the TWO-FILE-CROSSING chain recipe:
rewrites the facade to call hop1 (in host1), inserts hop1's plumbing method
into host1 at an ANONYMOUS interior point (never file-end - HANDOFF.md
Section 11.21 found relocating a delegate away from a conspicuous position
is itself part of what makes the recipe work), inserts hop2's real-logic
method into host2 at another anonymous interior point, and appends the
narrative lie to the facade's existing javadoc.

This module does no design work - every piece of text it places was already
authored by chain_design.py and (for the CONTROL form, hop2's correct body)
validated by validate.py. Its only job is precise, deterministic, three-file
text placement.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_transform import find_method_span, find_javadoc_start
from validate import read_text_smart, write_text_smart
import host_search


def insert_method_at_anonymous_point(filepath, method_text, seed):
    """
    Inserts method_text as a new member of the class in filepath, at an
    anonymous interior point (after a randomly-chosen existing method that
    is neither the first nor the last in the file) - falling back to
    "just before the class's final closing brace" only if the file doesn't
    have enough methods to pick an interior anchor from.

    Returns the anchor method name used (or None if the file-end fallback
    was used), so callers can record it for the manifest's audit trail.
    """
    text, crlf = read_text_smart(filepath)
    line_idx, anchor_name = host_search.pick_insertion_anchor(filepath, seed)

    lines = text.split("\n")
    indented = "\n".join("    " + l if l.strip() else l for l in method_text.strip().split("\n"))

    if line_idx is not None:
        new_lines = lines[:line_idx] + ["", indented, ""] + lines[line_idx:]
        write_text_smart(filepath, "\n".join(new_lines), crlf)
        return anchor_name

    # fallback: before the class's final closing brace
    last_brace_idx = text.rstrip().rindex("}")
    text = text[:last_brace_idx] + "\n    " + indented + "\n\n" + text[last_brace_idx:]
    write_text_smart(filepath, text, crlf)
    return None


def rewrite_facade(source_filepath, facade_method_name, facade_replacement_body, lie_sentence,
                    near_line=None):
    """
    Applies only the facade-side transformation: replace the facade
    method's body, and append lie_sentence to its existing javadoc. Does
    NOT touch host1/host2 - call insert_method_at_anonymous_point for those
    separately, so each of the three files is a single, independently
    diff-able change (needed for the multi-file variant.patch).

    near_line should be the candidate's own start_line (from
    candidate_search's extracted method dict) whenever the facade method
    name might be overloaded - see extract_transform.find_method_span.
    """
    text, crlf = read_text_smart(source_filepath)

    span = find_method_span(text, facade_method_name, near_line=near_line)
    if span is None:
        raise ValueError(f"could not locate method {facade_method_name} in {source_filepath}")
    header_start, body_end = span

    first_brace = text.index("{", header_start)
    new_method_text = text[header_start:first_brace + 1] + "\n        " + \
        facade_replacement_body.strip() + "\n    }"
    text = text[:header_start] + new_method_text + text[body_end:]

    # header_start is still valid in the new text: the splice only replaced
    # [header_start:body_end], so everything before header_start - including
    # any earlier, unrelated overloads of the same method name - is
    # untouched. Look up the javadoc directly from header_start rather than
    # re-searching by name, which would find the WRONG overload's javadoc
    # if an earlier-positioned overload of the same name exists.
    jd_start = find_javadoc_start(text, header_start)
    if jd_start is not None:
        jd_end = text.index("*/", jd_start)
        insertion = f"  {lie_sentence.strip()}\n     "
        text = text[:jd_end] + insertion + text[jd_end:]

    write_text_smart(source_filepath, text, crlf)


def apply_chain_transform(source_filepath, facade_method_name, host1_path, host2_path,
                           design, anchor_seed1, anchor_seed2, facade_near_line=None):
    """
    Full TREATMENT transformation across three files:
      1. facade file: replace body with a call into host1's hop1, append
         the narrative lie to the javadoc.
      2. host1 file: insert hop1_full_method (pure plumbing into host2) at
         an anonymous interior point.
      3. host2 file: insert hop2_full_method (the CORRECT logic - the bug
         is applied to it separately afterward, by the same substring
         substitution used throughout this project) at another anonymous
         interior point.
    facade_near_line should be the candidate's own start_line, to
    disambiguate an overloaded facade method name - see rewrite_facade.
    Returns (anchor1_name, anchor2_name) for the manifest's audit trail.
    """
    rewrite_facade(source_filepath, facade_method_name, design.facade_replacement_body,
                    design.lie_sentence, near_line=facade_near_line)
    anchor1 = insert_method_at_anonymous_point(host1_path, design.hop1_full_method, anchor_seed1)
    anchor2 = insert_method_at_anonymous_point(host2_path, design.hop2_full_method, anchor_seed2)
    return anchor1, anchor2
