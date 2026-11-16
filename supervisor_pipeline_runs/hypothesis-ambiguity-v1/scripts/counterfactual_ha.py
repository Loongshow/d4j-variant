"""Counterfactual repair audit (Phase 6). Usage: counterfactual_ha.py <low|high> <checkout_in_buggy_state> <out_json>
For each candidate: apply ONE locally plausible repair (exact asserted edit), compile, run the trigger, run the full suite (Lang: ~20 s), record, restore.
Classification: FIX = trigger passes and no new full-suite failure; COMPENSATING_BREAKS = trigger passes but new failures; NON_REPAIR = trigger still fails
(no new failures); BREAKS = trigger fails and new failures. Nothing is pre-written; every status comes from an executed command."""
import json, os, re, subprocess, sys, time, shutil
arm, work, out = sys.argv[1], sys.argv[2], sys.argv[3]
env = dict(os.environ, PERL5LIB=os.path.expanduser("~/perl5/lib/perl5")); TRIG = "org.apache.commons.lang3.ConversionTest::testLang1140"
J = lambda *p: os.path.join(work, "src/main/java/org/apache/commons/lang3", *p)
AU, BF, NU, CONV = J("ArrayUtils.java"), J("BitField.java"), J("math", "NumberUtils.java"), J("Conversion.java")
def sh(cmd, timeout=900):
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, env=env, timeout=timeout); return p.returncode, p.stdout + p.stderr
def compile_():
    rc, o = sh(["defects4j", "compile"]); return rc == 0 and "BUILD FAILED" not in o, o
def trigger():
    rc, o = sh(["defects4j", "test", "-t", TRIG], timeout=600); m = re.search(r"Failing tests:\s*(\d+)", o); n = int(m.group(1)) if m else None
    ft = open(os.path.join(work, "failing_tests")).read() if os.path.exists(os.path.join(work, "failing_tests")) else ""; return n, "\n".join(ft.splitlines()[:2])
def suite():
    rc, o = sh(["defects4j", "test"], timeout=1800); m = re.search(r"Failing tests:\s*(\d+)", o); return (int(m.group(1)) if m else None), sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o, re.M)))
GOLD = ("        return (at + Integer.SIZE - 1) / Integer.SIZE;", "        return at / Integer.SIZE;")
if arm == "high":
    REPAIRS = [
     ("BitField#lane (GOLD)", BF, GOLD[0], GOLD[1], "lane containing the position (floor) instead of lanes needed to cover it (ceiling)"),
     ("ArrayUtils#pack", AU, "            out = NumberUtils.deposit(out, array[startIndex + index], advance(lane, index), offset);", "            out = NumberUtils.deposit(out, array[startIndex + index], advance(lane - 1, index), offset);", "treat the lane as a 1-based count and step back one lane before advancing"),
     ("ArrayUtils#advance", AU, "        return lane + index;", "        return lane + index - 1;", "element lane computed from a 1-based lane"),
     ("NumberUtils#deposit", NU, "        final int shift = lane * Integer.SIZE + offset;", "        final int shift = (lane - 1) * Integer.SIZE + offset;", "recompose from a 1-based lane"),
     ("BitField#offset", BF, "        return at % Integer.SIZE;", "        return at % Long.SIZE;", "offset taken modulo the holder width instead of the lane width (non-compensating)"),
     ("Conversion#intArrayToLong (facade)", CONV, "        return ArrayUtils.pack(src, srcPos, nInts, dstInit, dstPos);", "        return ArrayUtils.pack(src, srcPos, nInts, dstInit, dstPos - Integer.SIZE);", "pass the position one lane lower (the only single-line facade edit that could compensate)")]
else:
    REPAIRS = [
     ("BitField#lane (GOLD)", BF, GOLD[0], GOLD[1], "lane containing the position (floor) instead of lanes needed to cover it (ceiling)"),
     ("ArrayUtils#pack", AU, "            final int shift = (lane + index) * Integer.SIZE + offset;", "            final int shift = (lane + index - 1) * Integer.SIZE + offset;", "treat the lane as a 1-based count in the inline recomposition"),
     ("ArrayUtils#gather", AU, "        System.arraycopy(array, startIndex, run, 0, count);", "        System.arraycopy(array, startIndex + 1, run, 0, count);", "off-by-one on the run start (wrong element hypothesis)"),
     ("BitField#widen", BF, "        return 0xffffffffL & value;", "        return value;", "sign-extend instead of masking (value hypothesis)"),
     ("NumberUtils#merge", NU, "        return (holder & ~field) | (value << shift);", "        return (holder & ~field) | ((value << shift) & field);", "mask the shifted value to the field (merge hypothesis)"),
     ("Conversion#intArrayToLong (facade)", CONV, "        return ArrayUtils.pack(src, srcPos, nInts, dstInit, dstPos);", "        return ArrayUtils.pack(src, srcPos, nInts, dstInit, dstPos - Integer.SIZE);", "pass the position one lane lower")]
R = {"arm": arm.upper(), "checkout": work, "trigger": TRIG, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "baseline_buggy": {}, "repairs": []}
ok, o = compile_(); n, sig = trigger(); sn, sfails = suite(); R["baseline_buggy"] = {"compiled": ok, "trigger_fail_count": n, "signature": sig, "suite_failures": sfails}
base = set(sfails)
for name, path, old, new, hyp in REPAIRS:
    t = open(path).read(); assert t.count(old) == 1, (name, t.count(old))
    open(path, "w").write(t.replace(old, new, 1))
    cok, co = compile_(); rec = {"candidate": name, "file": os.path.relpath(path, work), "repair": {"old": old.strip(), "new": new.strip()}, "hypothesis": hyp, "compiled": cok}
    if cok:
        n2, sig2 = trigger(); s2n, s2fails = suite(); newf = [f for f in s2fails if f not in base and f != TRIG]
        rec.update({"trigger_fail_count": n2, "trigger_signature": sig2, "suite_failures": s2fails, "new_failures_vs_buggy_baseline": newf,
                    "classification": ("FIX" if n2 == 0 and not newf else "COMPENSATING_BREAKS" if n2 == 0 else "NON_REPAIR" if not newf else "BREAKS")})
    else: rec.update({"classification": "DOES_NOT_COMPILE", "compile_output": co[-800:]})
    open(path, "w").write(t)  # restore
    R["repairs"].append(rec); json.dump(R, open(out, "w"), indent=1); print(name, "->", rec["classification"], "| trigger fails:", rec.get("trigger_fail_count"), "| new failures:", rec.get("new_failures_vs_buggy_baseline"), flush=True)
cok, co = compile_(); n, sig = trigger(); R["restored_state"] = {"compiled": cok, "trigger_fail_count": n, "signature": sig}; R["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
json.dump(R, open(out, "w"), indent=1); print("restored:", R["restored_state"])
