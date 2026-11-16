"""Render the agent-visible payload (failing test id, failing test source, failure text) for lexgate from a PATCHED checkout that has run the
trigger (its failing_tests file holds the assertion and stack). Usage: render_payload.py <config.json> <patched_checkout> <out.txt>"""
import json, os, re, sys
cfg, co, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
trig = cfg["trigger"]; tcls, tm = trig.split("::"); tf = os.path.join(co, cfg["test_file"]); t = open(tf, "rb").read().decode("utf-8").replace("\r\n", "\n")
i = t.find(f"public void {tm}("); assert i > 0, tm
j = t.rfind("\n", 0, t.rfind("/**", 0, i)) if "/**" in t[max(0, i - 400):i] else t.rfind("\n", 0, t.rfind("@Test", 0, i)) if "@Test" in t[max(0, i - 200):i] else t.rfind("\n", 0, i)
k = i; d = 0; st = False
while k < len(t):
    d += (t[k] == "{") - (t[k] == "}"); st = st or t[k] == "{"
    if st and d == 0: break
    k += 1
src = t[j + 1:k + 1]
ft = open(os.path.join(co, "failing_tests")).read() if os.path.exists(os.path.join(co, "failing_tests")) else ""
payload = f"Failing test identifier: {trig}\n\nFailing test source:\n{src}\n\nFailure stack trace:\nFailing tests: 1\n  - {trig}\n{ft}"
open(out, "w").write(payload); print(out, len(payload), "bytes;", ft.count("\n"), "failing_tests lines")
