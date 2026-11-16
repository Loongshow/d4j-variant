#!/usr/bin/env python
"""V15/V16 evidence packets. Usage: blindness_packets.py <pair.json> <work-checkout>
For each arm: applies the arm, extracts H2 (javadoc+signature+body), H3 likewise, writes projects/<P>/bug-XX/blindness/<ARM>_{H2,H3,H2H3}.txt, resets."""
import json, sys, os, re, subprocess
spec = json.load(open(sys.argv[1])); work = sys.argv[2]; env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5")); CH = spec["chain"]
out = f"{spec['pair_dir']}/blindness"; os.makedirs(out, exist_ok=True)
def sh(c): return subprocess.run(c, cwd=work, capture_output=True, text=True, env=env)
def reset(): sh(["git", "reset", "-q", "--", "."]); sh(["git", "checkout", "--", "."]); sh(["git", "clean", "-fdq", "--", "src", "tests", "source"])
def method_block(rel, name):
    t = open(f"{work}/{rel}", "rb").read().decode("utf-8").replace("\r\n", "\n"); lines = t.split("\n")
    pat = re.compile(r"^\s*(public|protected|private|static|final|\s)*[\w<>\[\], ]+\s+" + re.escape(name) + r"\s*\(")
    idx = next(i for i, l in enumerate(lines) if pat.match(l)); s = idx
    while s > 0 and (lines[s - 1].strip().startswith(("*", "/**", "*/", "@")) or lines[s - 1].strip() == ""):
        if lines[s - 1].strip() == "" and not (s >= 2 and lines[s - 2].strip().startswith(("*", "/**"))): break
        s -= 1
    depth = 0; e = idx; started = False
    for j in range(idx, len(lines)):
        depth += lines[j].count("{") - lines[j].count("}")
        if "{" in lines[j]: started = True
        if started and depth == 0: e = j + 1; break
    return "\n".join(lines[s:e])
for arm, A in spec["arms"].items():
    reset(); sh(["git", "apply", f"{A['package_dir']}/test.patch"]); sh(["git", "apply", f"{A['package_dir']}/variant.patch"])
    h2 = method_block(CH["H2"]["file"], CH["H2"]["method"]); h3 = method_block(CH["H3"]["file"], CH["H3"]["method"])
    hdr = lambda role: f"// Packet: one production method from a Java project ({spec['project']}). Class {CH[role]['class']}.\n// Nothing else from the repository is provided.\n\n"
    open(f"{out}/{arm}_H2.txt", "w").write(hdr("H2") + h2 + "\n"); open(f"{out}/{arm}_H3.txt", "w").write(hdr("H3") + h3 + "\n")
    open(f"{out}/{arm}_H2H3.txt", "w").write(f"// Packet: two production methods from a Java project ({spec['project']}); the second consumes the value the first returns.\n// Nothing else from the repository is provided.\n\n// --- {CH['H2']['class']} ---\n{h2}\n\n// --- {CH['H3']['class']} ---\n{h3}\n")
reset(); print("packets written to", out)
