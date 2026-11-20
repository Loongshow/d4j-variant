"""Refuse a paid block while any Defects4J checkout or construction leftover is reachable under /private/tmp (agents run
`find /private/tmp`; AMENDMENTS X2/X7). Allowed: the active server's empty external workspace roots (d4jws-*) and the session's
own claude-<uid> directory. Exit 0 = clean, 1 = leftovers listed. Read-only."""
import os, sys, re
bad = []
for e in sorted(os.listdir("/private/tmp")):
    p = os.path.join("/private/tmp", e)
    if e.startswith("claude-") or not os.path.isdir(p) and not e.endswith(".log"): continue
    if e.startswith("d4jws-"):
        if os.listdir(p): bad.append(f"{p} (workspace root not empty)")
        continue
    if re.match(r"^(mxb-|mxm-|mxmark-|mxchk-|mxd-|mxrh-|ct3ws-|n?r\d+m\d+)", e): bad.append(p); continue
    for root, dirs, files in os.walk(p):
        if root.count(os.sep) - p.count(os.sep) > 3: dirs[:] = []; continue
        if "defects4j.build.properties" in files: bad.append(f"{p} (Defects4J checkout at {root})"); break
print("CLEAN" if not bad else "LEFTOVERS:\n  " + "\n  ".join(bad)); sys.exit(1 if bad else 0)
