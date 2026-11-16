"""Make a run plan. Usage: ct_plan.py <out.json> --instances A,B,C --levels C0,CG,CD --runs 3 --seed 20261008 [--wording-start 1]
Cue conditions CG and CD alternate their two wordings across runs (W1, W2, W1 ... starting from --wording-start), so no single
phrasing carries a condition. The order is randomised with a fixed seed and interleaved: each round contains one run of every
(instance, condition) cell in shuffled order, so no condition is run as one contiguous block."""
import json, sys, random, argparse, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--instances", required=True); ap.add_argument("--levels", default="C0,CG,CD")
ap.add_argument("--runs", type=int, default=3); ap.add_argument("--seed", type=int, default=20261008); ap.add_argument("--wording-start", type=int, default=1)
a = ap.parse_args(); key = json.load(open(f"{C.V3}/review/VARIANT_KEY.json")); rng = random.Random(a.seed)
by = {}
for vid, k in key.items(): by[(k["instance_id"], k["level"])] = vid
cells = [(i, c) for i in a.instances.split(",") for c in a.levels.split(",")]
rounds = []
for r in range(a.runs):
    order = cells[:]; rng.shuffle(order); rnd = []
    for inst, cond in order:
        if cond == "C0": level = "C0"
        else: w = ((r + a.wording_start - 1) % 2) + 1; level = f"{cond}{w}"
        rnd.append({"instance_id": inst, "condition": cond, "level": level, "variant_id": by[(inst, level)], "round": r + 1})
    rounds += rnd
json.dump({"seed": a.seed, "instances": a.instances.split(","), "levels": a.levels.split(","), "runs_per_cell": a.runs, "slots": rounds}, open(a.out, "w"), indent=1)
print(f"{len(rounds)} slots -> {a.out}")
for s in rounds: print(s["round"], s["instance_id"], s["level"], s["variant_id"])
