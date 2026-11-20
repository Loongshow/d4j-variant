"""Make a mechanism-search run plan. Usage: mx_plan.py <out.json> --iids A,B,C --runs 3 --seed N [--purpose TEXT]
Rounds: every variant once per round, in a seeded random order per round, so repetitions of an instance are spread over the block."""
import json, sys, random, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ct_lib as C
a = sys.argv; out = a[1]; iids = a[a.index("--iids") + 1].split(","); runs = int(a[a.index("--runs") + 1]); seed = int(a[a.index("--seed") + 1])
purpose = a[a.index("--purpose") + 1] if "--purpose" in a else ""
key = json.load(open(f"{C.V3}/review/VARIANT_KEY.json")); by_iid = {v["instance_id"]: k for k, v in key.items()}
missing = [i for i in iids if i not in by_iid]; assert not missing, f"not in key: {missing}"
rng = random.Random(seed); slots = []
for r in range(1, runs + 1):
    order = list(iids); rng.shuffle(order)
    for i in order:
        k = key[by_iid[i]]; slots.append({"instance_id": i, "condition": k.get("mechanism"), "level": k.get("tier"), "variant_id": by_iid[i], "round": r})
json.dump({"seed": seed, "purpose": purpose, "runs_per_instance": runs, "instances": iids, "slots": slots}, open(out, "w"), indent=1)
print(len(slots), "slots ->", out)
