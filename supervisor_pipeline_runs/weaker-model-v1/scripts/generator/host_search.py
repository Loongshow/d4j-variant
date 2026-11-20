"""
Selects the two "host" classes a chain-recipe variant will route its
delegate chain through, and picks an anonymous, natural-looking insertion
point inside each one.

This encodes the confirmed generalization-study recipe (HANDOFF.md Section
11.22/11.23): the delegate chain must cross into TWO separate, genuinely
unrelated, already-large existing classes - never a new purpose-built class,
never padding within the target's own file - with every hop embedded
anonymously among each host's other real methods (not conspicuously at the
end of the file, which is how the single-file recipe in extract_transform.py
places its one delegate).

"Genuinely unrelated" is approximated mechanically here as "not the same
class, and preferably not in the same immediate package directory" - a real
proxy for the mined mechanism's actual mechanism (dispatcher-pair path
disruption), not a semantic judgment. When the candidate pool is too small
to satisfy the directory constraint, it is relaxed and the relaxation is
returned in the result so callers can disclose it (matching this project's
established disclosed-redraw discipline - HANDOFF.md Section 9).
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import candidate_search

MIN_METHODS_FOR_ANCHOR_CHOICE = 3


def _package_dir(filepath, source_root):
    rel = os.path.relpath(filepath, source_root)
    return os.path.dirname(rel)


def pick_two_hosts(source_root, target_filepath, min_host_lines, seed, exclude_files=None):
    """
    Returns (host1_path, host2_path, note) where note discloses whether the
    different-package-directory preference was satisfied or relaxed.

    exclude_files (absolute paths) lets a caller keep hosts distinct from
    classes already used elsewhere in the project (e.g. as a facade or
    host in an earlier variant) - the same spirit as generate_chain.py's
    --exclude-class for target selection, so an already-analyzed class
    doesn't keep coming back as a host purely because it's large. Also
    keeps a host from being a class with real, independently-known,
    pre-existing test flakiness from showing up as "new" collateral
    confusingly often (e.g. Commons Lang's DateUtils).

    Draw is seeded and deterministic given the same checkout + seed, same
    reproducibility contract as candidate_search/generate.py's pick_target.
    """
    exclude_files = {os.path.abspath(f) for f in (exclude_files or [])}
    classes = candidate_search.find_large_classes(source_root, min_lines=min_host_lines)
    target_abs = os.path.abspath(target_filepath)
    pool = [(f, n) for f, n in classes
            if os.path.abspath(f) != target_abs and os.path.abspath(f) not in exclude_files]
    if len(pool) < 2:
        raise RuntimeError(
            f"only {len(pool)} candidate host class(es) >= {min_host_lines} lines "
            f"(excluding the target's own file) - lower --min-host-lines or widen the checkout"
        )

    target_pkg = _package_dir(target_filepath, source_root)
    rng = random.Random(seed)
    order = list(range(len(pool)))
    rng.shuffle(order)

    # Preferred: host1 and host2 in different package dirs from each other
    # AND from the target. Fall back progressively if the pool can't satisfy
    # that - always disclosing the relaxation actually used.
    for require_diff_from_target in (True, False):
        chosen = []
        seen_pkgs = set()
        for idx in order:
            f, n = pool[idx]
            pkg = _package_dir(f, source_root)
            if require_diff_from_target and pkg == target_pkg:
                continue
            if pkg in seen_pkgs:
                continue
            chosen.append(f)
            seen_pkgs.add(pkg)
            if len(chosen) == 2:
                note = (
                    f"host1/host2 drawn via seed={seed}, both in package dirs distinct from each "
                    f"other{' and from the target' if require_diff_from_target else ''}."
                )
                if not require_diff_from_target:
                    note += (
                        " NOTE: relaxed the 'distinct from target package' constraint - the "
                        "candidate pool for this checkout did not have >=2 other-package classes "
                        f"above {min_host_lines} lines."
                    )
                return chosen[0], chosen[1], note

    # Last resort: just take the first two distinct files in shuffle order,
    # even if they share a package dir with each other/the target.
    chosen = [pool[order[0]][0], pool[order[1]][0]]
    note = (
        f"host1/host2 drawn via seed={seed}. NOTE: relaxed BOTH package-distinctness "
        f"constraints - pool too small ({len(pool)} candidates). Hosts are still two distinct, "
        f"already-large classes, but the 'genuinely unrelated' package heuristic could not be "
        f"satisfied for this checkout."
    )
    return chosen[0], chosen[1], note


def pick_insertion_anchor(host_filepath, seed, prefer_visibility="public"):
    """
    Picks a natural, anonymous insertion offset inside host_filepath: right
    after the closing brace of an EXISTING method drawn from the interior of
    the class's method list (never the first or last method, so the new hop
    doesn't read as conspicuously appended at a boundary).

    prefer_visibility, when given, restricts the draw to interior methods
    whose own header uses that visibility keyword first (falling back to
    the full interior list if none match) - since the chain recipe's hops
    are always 'public static' (private would not compile across classes),
    anchoring next to another public method keeps the insertion blending
    into the host's real mix of public API, not its private internals.

    Returns (line_index, anchor_method_name) - line_index is the 0-based
    line number in the file's text (split on "\\n") immediately after which
    the new method's text should be inserted. Falls back to "just before the
    class's final closing brace" (line_index = None) if the class doesn't
    have enough methods to pick an interior anchor.
    """
    methods = candidate_search.extract_methods_from_file(host_filepath) if hasattr(
        candidate_search, "extract_methods_from_file"
    ) else _extract_methods_fallback(host_filepath)

    # extract_methods_from_file is a flat regex scanner with no class-
    # nesting awareness - it returns methods of inner/nested classes (e.g.
    # a private Rule implementation nested inside a formatter class)
    # exactly like true outer-class methods. Anchoring a new 'public
    # static' hop next to one and inserting after its closing brace would
    # silently nest the hop INSIDE that inner class too, producing a real
    # "cannot find symbol" compile error at the call site (confirmed live
    # against FastDatePrinter.java) - the identical nested-class bug
    # already found and fixed in pad_class.py (HANDOFF.md Section 11.3).
    # Filter to methods whose header is indented exactly 4 spaces - the
    # convention for a direct (outer-class) member in every codebase this
    # project has used; anything more indented is nested and must be
    # skipped.
    text_lines = open(host_filepath, encoding="utf-8", errors="ignore").read().split("\n")

    def _is_outer_class_member(m):
        header_line = text_lines[m["start_line"] - 1]
        indent = len(header_line) - len(header_line.lstrip(" "))
        return indent == 4

    methods = [m for m in methods if _is_outer_class_member(m)]

    if len(methods) < MIN_METHODS_FOR_ANCHOR_CHOICE:
        return None, None

    # never the first or last method in the file
    interior = methods[1:-1]
    if not interior:
        return None, None

    if prefer_visibility:
        matching = [m for m in interior if prefer_visibility in m["body"].split("\n")[0]]
        if matching:
            interior = matching

    rng = random.Random(seed)
    anchor = rng.choice(interior)
    return anchor["end_line"], anchor["name"]


def _extract_methods_fallback(filepath):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "trajectory-analysis"))
    from callgraph import extract_methods_from_file
    return extract_methods_from_file(filepath)


def host_class_dotted_name(host_filepath, source_root):
    rel = os.path.relpath(host_filepath, source_root)
    return rel[:-5].replace("/", ".").replace(os.sep, ".") if rel.endswith(".java") else rel.replace("/", ".")


if __name__ == "__main__":
    src_root, target = sys.argv[1], sys.argv[2]
    h1, h2, note = pick_two_hosts(src_root, target, min_host_lines=1500, seed=42)
    print("host1:", h1)
    print("host2:", h2)
    print("note:", note)
    a1 = pick_insertion_anchor(h1, seed=42)
    a2 = pick_insertion_anchor(h2, seed=43)
    print("anchor1:", a1)
    print("anchor2:", a2)
