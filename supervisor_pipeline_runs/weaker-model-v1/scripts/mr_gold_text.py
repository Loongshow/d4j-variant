"""Main run: print ONLY the gold method as it reads in the variant (javadoc + signature + body), for blind trace checks
(construction/mainrun/TRACE_CHECK_BRIEF.md). The text is taken from the instance's own build/variant.patch: the added lines of the
gold's file, from the gold's javadoc to the end of its body (brace-matched). Nothing else is printed.
Usage: mr_gold_text.py MR-<key>            -> gold text on stdout
       mr_gold_text.py --anon-retro OUT MAP -> write the 18 batch-1/2 golds under shuffled anonymous labels (OUT) and the label map (MAP)"""
import json, os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__)); WM = os.path.dirname(HERE)

def gold_text(iid):
    s = json.load(open(f"{WM}/construction/mainrun/specs/{iid}.json")); G = s["gold"]
    added, cur = [], None
    for l in open(f"{WM}/instances/{iid}/build/variant.patch").read().splitlines():
        if l.startswith("+++ "): cur = l[6:] if l.startswith("+++ b/") else l[4:]
        elif cur == G["file"] and l.startswith("+") and not l.startswith("+++"): added.append(l[1:])
    txt = "\n".join(added)
    i = txt.find(f" {G['method']}(")
    assert i >= 0, f"{iid}: gold {G['method']} not among the added lines of {G['file']}"
    sig = max(txt.rfind("public static", 0, i), 0)
    decl = txt[sig:txt.index("{", i)]
    assert f" {G['method']}(" in decl and "\n\n" not in decl.strip(), f"{iid}: extracted declaration does not belong to {G['method']}"
    js = txt.rfind("/**", 0, sig); start = js if js >= 0 and "*/" in txt[js:sig] else sig
    depth, j, opened = 0, txt.index("{", i), False
    while j < len(txt):
        if txt[j] == "{": depth += 1; opened = True
        elif txt[j] == "}":
            depth -= 1
            if opened and depth == 0: break
        j += 1
    out = txt[start:j + 1]
    lines = out.splitlines(); ind = min((len(x) - len(x.lstrip()) for x in lines[1:] if x.strip()), default=0)
    return "\n".join([lines[0].strip()] + [x[ind:] if len(x) >= ind else x for x in lines[1:]])

if __name__ == "__main__":
    if sys.argv[1] == "--anon-retro":
        out, mp = sys.argv[2], sys.argv[3]
        iids = sorted(f"MR-{t['key']}" for b in ("batch1", "batch2") for t in json.load(open(f"{WM}/main-run/{b}_tasks.json"))
                      if os.path.exists(f"{WM}/construction/mainrun/specs/MR-{t['key']}.json"))   # the 18 built batch-1/2 instances only
        rng = random.Random(20261017); order = iids[:]; rng.shuffle(order)
        labels = {iid: f"G{n + 1:02d}" for n, iid in enumerate(order)}
        json.dump([{"label": labels[i], "gold_text": gold_text(i)} for i in order], open(out, "w"), indent=1)
        json.dump(labels, open(mp, "w"), indent=1, sort_keys=True)
        print(len(order), "golds written to", out)
    else:
        print(gold_text(sys.argv[1]))
