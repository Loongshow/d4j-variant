"""Main run, batch 5 on: add fixed Defects4J checkouts to the shared harness store (new directories only, as in W29/W34).
For each key <P>-<id> given on the command line, if <store>/defects4j/<P>-<id>/fixed does not exist, runs
`defects4j checkout -p <P> -v <id>f -w <that dir>` and appends one line to main-run/<log>:
    <key> OK|FAIL <git short head or -> <D4J_<P>_<id>_FIXED_VERSION tag or -> <size>
Existing checkouts are never touched. Usage: mr_checkouts.py <log-name> <key> [<key> ...]"""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); WM = os.path.dirname(HERE)
STORE = "/Users/shawnli/Desktop/Honours/defects4j/workspaces/defects4j"
D4J = "/Users/shawnli/Desktop/Honours/defects4j"
ENV = {**os.environ, "PERL5LIB": os.path.expanduser("~/perl5/lib/perl5"), "PATH": f"{D4J}/framework/bin:" + os.environ.get("PATH", "")}
log = open(f"{WM}/main-run/{sys.argv[1]}", "a")
for key in sys.argv[2:]:
    p, b = key.rsplit("-", 1); dst = f"{STORE}/{key}/fixed"
    if os.path.isdir(dst):
        print(f"{key} exists, skipped", flush=True); continue
    t0 = time.time()
    r = subprocess.run(["defects4j", "checkout", "-p", p, "-v", f"{b}f", "-w", dst], env=ENV, capture_output=True, text=True)
    ok = r.returncode == 0 and os.path.isdir(dst)
    head = subprocess.run(["git", "-C", dst, "rev-parse", "--short=9", "HEAD"], capture_output=True, text=True).stdout.strip() if ok else "-"
    tag = subprocess.run(["git", "-C", dst, "describe", "--tags", "--exact-match"], capture_output=True, text=True).stdout.strip() if ok else "-"
    size = subprocess.run(["du", "-sh", dst], capture_output=True, text=True).stdout.split()[0] if ok else "-"
    line = f"{key} {'OK' if ok else 'FAIL'} {head} {tag or '-'} {size}  ({time.time() - t0:.0f}s)"
    print(line, flush=True); log.write(line + "\n"); log.flush()
    if not ok: print(r.stderr[-800:], flush=True)
