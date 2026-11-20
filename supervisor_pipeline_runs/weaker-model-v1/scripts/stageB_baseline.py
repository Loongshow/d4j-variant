"""Baseline full-suite failure set per fixture (collateral gate reference). Throwaway copies under /private/tmp."""
import sys, os, time, shutil, json
import stageB_lib as L
for P in sys.argv[1:]:
    work = f"/private/tmp/d4j-stageB-baseline-{P}"
    shutil.rmtree(work, ignore_errors=True)
    L.prepare_work(P, work)
    t0 = time.time(); ok, log = L.compile_ok(work); tc = time.time() - t0
    assert ok, log
    t0 = time.time(); n, ids, tail = L.full_suite(work); ts = time.time() - t0
    rec = {"project": P, "fixture": L.FIXTURES[P], "compile_s": round(tc, 1), "suite_s": round(ts, 1), "n_failing": n, "failing": sorted(ids)}
    L.save_json(os.path.join(L.ROOT, f"construction/stageB/validation/baseline_{P}.json"), rec)
    print(json.dumps({k: v for k, v in rec.items() if k != "fixture"}), flush=True)
    shutil.rmtree(work, ignore_errors=True)
