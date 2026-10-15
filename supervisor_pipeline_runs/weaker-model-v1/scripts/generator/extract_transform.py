"""
Mechanical (no LLM) file surgery that turns a validated CONTROL design into
the TREATMENT variant: rewrites the facade to delegate, inserts the new
private method as the LAST member of the class (maximum physical distance -
the one factor this project's 2x2 confirmed is necessary, alongside the
docstring lie, for the interaction effect - HANDOFF.md Section 11.1), and
appends the lie sentence to the facade's existing javadoc.

This module does no design work - every piece of text it places was
already authored by the LLM design step and validated (for the CONTROL
form) by validate.py. Its only job is precise, deterministic text
placement, so that the only thing distinguishing TREATMENT from CONTROL is
exactly the two variables the recipe calls for.
"""
import re

from validate import read_text_smart, write_text_smart


def find_method_span(text, method_name, near_line=None):
    """
    Locate the full text span (start, end) of a method declaration by name,
    via brace matching from its opening '{'. Returns (header_start, body_end)
    character offsets into text, or None if not found.

    If the method name appears more than once (overloads) and near_line is
    given (1-based line number, e.g. from candidate_search's extracted
    method dict), the match whose header line is CLOSEST to near_line is
    returned instead of the first one - overloaded methods are common
    enough in real Defects4J classes (e.g. DatasetUtilities.
    createCategoryDataset has 4 overloads) that "first match" alone can
    silently rewrite the wrong overload. near_line=None preserves the
    original first-match behavior for existing callers.
    """
    pattern = re.compile(
        r'(?:^|\n)([ \t]*(?:public|protected|private)[^\n{;]*\b' + re.escape(method_name) + r'\s*\([^;{]*\)\s*(?:throws\s+[\w,\s.]+)?\s*\{)',
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    if near_line is not None and len(matches) > 1:
        target_offset = sum(len(l) + 1 for l in text.split("\n")[:near_line - 1])
        m = min(matches, key=lambda mm: abs(mm.start(1) - target_offset))
    else:
        m = matches[0]
    header_start = m.start(1)
    brace_open = m.end(1) - 1  # index of the '{' itself
    depth = 0
    i = brace_open
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return header_start, i + 1
        i += 1
    return None


def find_javadoc_start(text, method_header_start):
    """
    Walk backwards from a method's header to find the start of its
    immediately-preceding /** ... */ javadoc block, if any.

    Finds the LAST javadoc block in the text before method_header_start
    (via non-overlapping finditer, since a non-greedy DOTALL search anchored
    with re.search(...$) would instead match from the FIRST javadoc in the
    whole preceding text through to the last '*/' - silently landing on the
    file's class-level javadoc instead of the method's own, for any method
    that isn't the very first one in the file). Returns None if the nearest
    preceding javadoc block isn't immediately adjacent (only whitespace
    between its '*/' and the method header) - i.e. this method has no
    javadoc of its own to append to.
    """
    before = text[:method_header_start]
    matches = list(re.finditer(r'/\*\*.*?\*/', before, re.DOTALL))
    if not matches:
        return None
    last = matches[-1]
    if before[last.end():].strip() != "":
        return None
    return last.start()


def rewrite_facade_and_append_delegate(source_filepath, facade_method_name,
                                        facade_replacement_body, lie_sentence,
                                        delegate_full_method_with_bug):
    """
    Applies the full TREATMENT transformation to source_filepath in place:
      1. Replace the facade method's body with facade_replacement_body.
      2. Append lie_sentence as a new final sentence inside the facade's
         existing javadoc (right before the closing '*/').
      3. Insert delegate_full_method_with_bug as the LAST member of the
         class, immediately before the class's own final closing brace.
    """
    text, crlf = read_text_smart(source_filepath)

    span = find_method_span(text, facade_method_name)
    if span is None:
        raise ValueError(f"could not locate method {facade_method_name} in {source_filepath}")
    header_start, body_end = span

    # header_start..body_end covers "public X foo(...) { ... }" - replace
    # only what's between the FIRST '{' and the matching final '}'.
    first_brace = text.index("{", header_start)
    new_method_text = text[header_start:first_brace + 1] + "\n        " + \
        facade_replacement_body.strip() + "\n    }"
    text = text[:header_start] + new_method_text + text[body_end:]

    # re-locate (text shifted) to append the lie sentence to the javadoc
    span2 = find_method_span(text, facade_method_name)
    jd_start = find_javadoc_start(text, span2[0])
    if jd_start is not None:
        jd_end = text.index("*/", jd_start)
        insertion = f"  {lie_sentence.strip()}\n     "
        text = text[:jd_end] + insertion + text[jd_end:]

    # insert the delegate as the last member of the class: before the final
    # top-level closing brace of the file (the class's own closing brace).
    last_brace_idx = text.rstrip().rindex("}")
    text = text[:last_brace_idx] + "\n    " + delegate_full_method_with_bug.strip() + \
        "\n\n" + text[last_brace_idx:]

    write_text_smart(source_filepath, text, crlf)
