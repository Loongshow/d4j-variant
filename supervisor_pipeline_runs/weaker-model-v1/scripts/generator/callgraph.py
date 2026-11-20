"""
STAND-IN for the supervisor's `trajectory-analysis/callgraph.py`, which was
NOT included in the handoff (candidate_search.py does
`sys.path.insert(0, "<thesis>/../trajectory-analysis"); from callgraph import
extract_methods_from_file`). Written 2026-09-20 by Claude solely so the
pipeline can be exercised end-to-end; it is loaded via PYTHONPATH and does
not touch any supervisor file.

Only extract_methods_from_file() is provided. Its interface is inferred from
how candidate_search.py and host_search.py consume it:

    [{"name": str,
      "start_line": int,   # 1-based line number of the method header line
      "end_line": int,     # 1-based line number of the closing '}' line
      "body": str},        # header line through closing brace, verbatim
     ...]                  # in file order

REPLACE THIS FILE with the supervisor's real callgraph.py as soon as it is
available: candidate scoring, host anchor choice, and therefore the exact
seed-determined target/host draw depend on its precise behaviour.
"""
import re

_HEADER_RE = re.compile(
    r'^[ \t]*'
    r'(?:(?:public|protected|private|static|final|synchronized|abstract|native|strictfp|default)\s+)*'
    r'(?:<[^>{;]*>\s+)?'                              # generic type params <T>
    r'([\w.$<>\[\],?]+(?:\s*<[^{;()]*>)?(?:\s*\[\s*\])*)\s+'  # return type
    r'([A-Za-z_$][\w$]*)\s*'                           # method name
    r'\((?:[^;{}()]|\([^;{}()]*\))*\)\s*'              # parameter list
    r'(?:throws\s+[\w.$,\s]+?)?\s*\{',
    re.MULTILINE,
)
_NOT_METHOD_NAMES = {"if", "for", "while", "switch", "catch", "synchronized",
                     "return", "new", "else", "do", "try", "throw"}
_NOT_TYPE_TOKENS = {"new", "return", "throw", "else", "if", "case"}


def _match_brace(text, open_idx):
    """Index of the '}' matching text[open_idx] == '{', skipping braces inside
    string/char literals and comments. Returns None if unbalanced."""
    depth = 0
    i = open_idx
    n = len(text)
    state = None  # None | 'str' | 'chr' | 'line' | 'block'
    while i < n:
        ch = text[i]
        if state is None:
            if ch == '"':
                state = 'str'
            elif ch == "'":
                state = 'chr'
            elif ch == '/' and i + 1 < n and text[i + 1] == '/':
                state = 'line'; i += 1
            elif ch == '/' and i + 1 < n and text[i + 1] == '*':
                state = 'block'; i += 1
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return i
        elif state == 'str':
            if ch == '\\':
                i += 1
            elif ch == '"':
                state = None
        elif state == 'chr':
            if ch == '\\':
                i += 1
            elif ch == "'":
                state = None
        elif state == 'line':
            if ch == '\n':
                state = None
        elif state == 'block':
            if ch == '*' and i + 1 < n and text[i + 1] == '/':
                state = None; i += 1
        i += 1
    return None


def extract_methods_from_file(filepath):
    text = open(filepath, encoding="utf-8", errors="ignore").read()
    methods = []
    for m in _HEADER_RE.finditer(text):
        name = m.group(2)
        if name in _NOT_METHOD_NAMES:
            continue
        if m.group(1).split()[0] in _NOT_TYPE_TOKENS:
            continue
        open_idx = m.end() - 1
        close_idx = _match_brace(text, open_idx)
        if close_idx is None:
            continue
        start_line = text.count("\n", 0, m.start()) + 1
        end_line = text.count("\n", 0, close_idx) + 1
        methods.append({
            "name": name,
            "start_line": start_line,
            "end_line": end_line,
            "body": text[m.start():close_idx + 1].lstrip(),
        })
    return methods
