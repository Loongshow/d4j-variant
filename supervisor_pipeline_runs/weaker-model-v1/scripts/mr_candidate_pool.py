"""Main run (weaker-model-v1): build the Defects4J candidate pool for transferring the Stage B C10 recipe.
For every active Defects4J bug, at its FIXED revision (read from the local project repositories with git; Chart, whose
revisions are SVN numbers, is read from the harness's fixed checkouts or a scratch `defects4j checkout`):
  - hosts: production .java files with >= 1500 newlines that declare a public (non-interface, non-enum) class, the recipe's
    host gate (host_search.find_large_classes, --min-host-lines 1500) plus Stage B's public-class rule (AMENDMENTS W15);
  - targets: public STATIC methods of the bug's modified classes that pass the recipe's own candidate filter
    (candidate_search.score_candidate_methods(require_static=True): 4-50 body lines, not a pure delegate,
    self_containedness > 0), each with the number of test files under the test root that call it;
  - context: modified-class size, real fix shape (files/hunks), harness fixed checkout present, project suite cost.
Classifies each bug ELIGIBLE or REJECTED (reason) and ranks the eligible ones by compatibility with the Stage B recipe.
Writes main-run/DEFECTS4J_CANDIDATE_POOL.csv and main-run/candidate_pool.json. No model call, read-only on the repositories."""
import csv, json, os, re, subprocess, sys, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); WM = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "generator"))
import candidate_search  # noqa: E402  (vendored supervisor generator; uses the callgraph shim)
D4J = "/Users/shawnli/Desktop/Honours/defects4j"; FW = f"{D4J}/framework/projects"; REPOS = f"{D4J}/project_repos"
CHECKOUTS = f"{WM}/models/w55/workspaces/defects4j"; OUT = f"{WM}/main-run"; os.makedirs(OUT, exist_ok=True)
REPO = {"Lang": "commons-lang.git", "Math": "commons-math.git", "Closure": "closure-compiler.git", "Cli": "commons-cli.git",
        "Codec": "commons-codec.git", "Collections": "commons-collections.git", "Compress": "commons-compress.git", "Csv": "commons-csv.git",
        "JxPath": "commons-jxpath.git", "Gson": "gson.git", "JacksonCore": "jackson-core.git", "JacksonDatabind": "jackson-databind.git",
        "JacksonXml": "jackson-dataformat-xml.git", "Jsoup": "jsoup.git", "Mockito": "mockito.git", "Time": "joda-time.git"}
# full-suite cost class from core-benchmark-scaleup-v2/PROJECT_SELECTION.md and BUILD_PROTOCOL.md (validation runs the full suite)
SUITE = {"Lang": ("fast", 20), "Chart": ("fast", 5), "Compress": ("fast", 2), "JacksonCore": ("fast", 3), "JxPath": ("fast", 4),
         "Gson": ("fast", 3), "Jsoup": ("fast", 2), "Codec": ("fast", 3), "Cli": ("fast", 1), "Csv": ("fast", 2), "Math": ("medium", 190),
         "Closure": ("unmeasured", None), "JacksonXml": ("unmeasured", None), "Time": ("slow", 996), "Collections": ("slow", 1001),
         "JacksonDatabind": ("slow", 959), "Mockito": ("slow", 978)}
ENV = {**os.environ, "PERL5LIB": os.path.expanduser("~/perl5/lib/perl5"), "PATH": f"{D4J}/framework/bin:" + os.environ.get("PATH", "")}
CLASS_DECL = re.compile(r"^\s*public\s+(?:(?:final|abstract|strictfp)\s+)*class\s+\w+", re.M)

def git(p, *a):
    return subprocess.run(["git", "--git-dir", f"{REPOS}/{REPO[p]}", *a], capture_output=True, text=True, errors="replace").stdout

def layout(p, rev):
    for row in csv.reader(open(f"{FW}/{p}/dir-layout.csv")):
        if row and row[0] == rev: return row[1], row[2]
    return None, None

def host_ok(text):
    return text.count("\n") >= 1500 and bool(CLASS_DECL.search(text))

class Tree:
    """Read access to one fixed revision, from git or from a checkout directory."""
    def __init__(self, p, rev, src, test, checkout=None):
        self.p, self.rev, self.src, self.test, self.co = p, rev, src, test, checkout
    def read(self, rel):
        if self.co:
            f = os.path.join(self.co, rel); return open(f, errors="replace").read() if os.path.exists(f) else None
        out = subprocess.run(["git", "--git-dir", f"{REPOS}/{REPO[self.p]}", "show", f"{self.rev}:{rel}"], capture_output=True, text=True, errors="replace")
        return out.stdout if out.returncode == 0 else None
    def hosts(self):
        res = []
        if self.co:
            for root, _, fs in os.walk(os.path.join(self.co, self.src)):
                for f in fs:
                    if f.endswith(".java"):
                        path = os.path.join(root, f)
                        if os.path.getsize(path) < 30000: continue
                        t = open(path, errors="replace").read()
                        if host_ok(t): res.append(os.path.relpath(path, self.co))
            return sorted(res)
        for line in git(self.p, "ls-tree", "-r", "-l", self.rev, "--", self.src).splitlines():
            parts = line.split(None, 4)
            if len(parts) < 5 or not parts[4].endswith(".java") or parts[3] == "-" or int(parts[3]) < 30000: continue
            t = subprocess.run(["git", "--git-dir", f"{REPOS}/{REPO[self.p]}", "cat-file", "-p", parts[2]], capture_output=True, text=True, errors="replace").stdout
            if host_ok(t): res.append(parts[4])
        return sorted(res)
    def test_files_calling(self, name):
        pat = r"\b" + re.escape(name) + r"\s*\("
        if self.co:
            n = 0
            for root, _, fs in os.walk(os.path.join(self.co, self.test)):
                for f in fs:
                    if f.endswith(".java") and re.search(pat, open(os.path.join(root, f), errors="replace").read()): n += 1
            return n
        out = git(self.p, "grep", "-l", "-E", r"(^|[^A-Za-z0-9_])" + name + r"[[:space:]]*\(", self.rev, "--", self.test)
        return len([l for l in out.splitlines() if l.endswith(".java")])

def fix_shape(p, bid):
    f = f"{FW}/{p}/patches/{bid}.src.patch"
    if not os.path.exists(f): return None, None
    t = open(f, errors="ignore").read()
    files = set(re.findall(r"^\+\+\+ [ab]/(\S+)", t, re.M)) or set(re.findall(r"^Index: (\S+)", t, re.M))
    return len(files), len(re.findall(r"^@@", t, re.M))

def chart_checkout(bid, scratch):
    co = f"{CHECKOUTS}/Chart-{bid}/fixed"
    if os.path.isdir(co): return co
    d = f"{scratch}/Chart-{bid}"
    if not os.path.isdir(d):
        subprocess.run(["defects4j", "checkout", "-p", "Chart", "-v", f"{bid}f", "-w", d], capture_output=True, env=ENV, timeout=600)
    return d if os.path.isdir(d) else None

def main():
    scratch = tempfile.mkdtemp(prefix="mr-pool-", dir="/private/tmp"); rows = []
    host_cache = {}
    try:
        for p in sorted(os.listdir(FW)):
            ab = f"{FW}/{p}/active-bugs.csv"
            if not os.path.exists(ab): continue
            for r in csv.DictReader(open(ab)):
                bid = r["bug.id"]; rev = r["revision.id.fixed"]; src, test = layout(p, rev)
                row = {"project": p, "bug_id": int(bid), "instance": f"{p}-{bid}", "fixed_revision": rev, "src_root": src, "test_root": test,
                       "harness_checkout": os.path.isdir(f"{CHECKOUTS}/{p}-{bid}/fixed"), "suite_class": SUITE[p][0], "suite_s": SUITE[p][1]}
                row["fix_files"], row["fix_hunks"] = fix_shape(p, bid)
                mods = [l.strip() for l in open(f"{FW}/{p}/modified_classes/{bid}.src") if l.strip()] if os.path.exists(f"{FW}/{p}/modified_classes/{bid}.src") else []
                row["modified_classes"] = ";".join(mods)
                if p == "Chart":
                    co = chart_checkout(bid, scratch); T = Tree(p, rev, src, test, checkout=co) if co else None
                else:
                    T = Tree(p, rev, src, test) if src else None
                if T is None:
                    row.update(status="REJECTED", reason="revision or layout unavailable"); rows.append(row); continue
                hk = (p, rev)
                if hk not in host_cache: host_cache[hk] = T.hosts()
                hosts = host_cache[hk]; row["n_hosts"] = len(hosts)
                row["host_packages"] = len({os.path.dirname(h) for h in hosts})
                cands = []
                for cls in mods:
                    rel = f"{src}/" + cls.split("$")[0].replace(".", "/") + ".java"; text = T.read(rel)
                    if text is None: continue
                    tmp = os.path.join(scratch, "cls.java"); open(tmp, "w").write(text)
                    for m in candidate_search.score_candidate_methods(tmp, require_static=True):
                        if m["self_containedness"] <= 0: continue
                        cands.append({"class": cls, "file": rel, "class_lines": text.count("\n"), "method": m["name"], "n_lines": m["n_lines"],
                                      "self_containedness": m["self_containedness"], "test_files": T.test_files_calling(m["name"])})
                tested = [c for c in cands if c["test_files"] > 0]
                row["n_static_candidates"] = len(cands); row["n_tested_candidates"] = len(tested)
                row["candidates"] = json.dumps(sorted(tested, key=lambda c: -c["self_containedness"])[:6])
                reasons = []
                if SUITE[p][0] == "slow": reasons.append(f"full suite {SUITE[p][1]} s makes validation impractical")
                if len(hosts) < 5: reasons.append(f"{len(hosts)} host classes of >=1500 lines (5 needed)")
                if not cands: reasons.append("no public static self-contained method in the modified classes")
                elif not tested: reasons.append("no test calls any static candidate")
                if reasons:
                    row.update(status="REJECTED", reason="; ".join(reasons))
                else:
                    best = max(c["self_containedness"] for c in tested)
                    score = {"fast": 3, "medium": 1.5, "unmeasured": 0.5}[SUITE[p][0]] + min(len(hosts), 20) / 10 + min(best, 40) / 20 \
                            + min(len(tested), 5) / 5 + (0.5 if row["harness_checkout"] else 0) + (0.3 if row["fix_files"] == 1 else 0)
                    row.update(status="ELIGIBLE", reason="", score=round(score, 2))
                rows.append(row)
                print(f"{row['instance']:20s} {row['status']:9s} hosts={row.get('n_hosts')} tested={row.get('n_tested_candidates')} {row.get('reason','')[:70]}", flush=True)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    elig = sorted([r for r in rows if r["status"] == "ELIGIBLE"], key=lambda r: -r["score"])
    for i, r in enumerate(elig, 1): r["rank"] = i
    cols = ["rank", "instance", "project", "bug_id", "status", "reason", "score", "suite_class", "suite_s", "n_hosts", "host_packages", "n_static_candidates",
            "n_tested_candidates", "harness_checkout", "fix_files", "fix_hunks", "fixed_revision", "src_root", "test_root", "modified_classes", "candidates"]
    with open(f"{OUT}/DEFECTS4J_CANDIDATE_POOL.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for r in sorted(rows, key=lambda r: (r.get("rank") or 10**6, r["project"], r["bug_id"])): w.writerow(r)
    json.dump(rows, open(f"{OUT}/candidate_pool.json", "w"), indent=1)
    by = {}
    for r in rows: by.setdefault(r["project"], [0, 0])[0 if r["status"] == "ELIGIBLE" else 1] += 1
    print("\nELIGIBLE", len(elig), "of", len(rows)); print({k: f"{v[0]} eligible / {v[0]+v[1]}" for k, v in sorted(by.items())})

if __name__ == "__main__":
    main()
