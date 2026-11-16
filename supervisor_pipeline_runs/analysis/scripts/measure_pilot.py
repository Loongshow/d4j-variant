"""Deterministic, read-only measurements over the Lang seed-42 pilot pair.
CONTROL state = fresh clone of lang-1f-checkout + CONTROL patches (scratch).
TREATMENT state = real/repro-checkout (the pipeline's own fresh-checkout repro, patches applied).
Writes analysis/data/pilot_measurements.json. No supervisor file is touched."""
import json, os, re, subprocess, sys, glob
RR="/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
CONTROL=sys.argv[1]; TREAT=os.path.join(RR,"real/repro-checkout")
sys.path.insert(0, os.path.join(RR,"shim")); sys.path.insert(0, "/Users/shawnli/Desktop/Honours/thesis")
from callgraph import extract_methods_from_file
import candidate_search, host_search

def rg(root, pattern, sub="src/main/java", fixed=True):
    cmd=["grep","-rn","--include=*.java"]+(["-F"] if fixed else [])+[pattern, os.path.join(root,sub)]
    out=subprocess.run(cmd,capture_output=True,text=True).stdout.strip().splitlines()
    return [l.replace(root+"/","") for l in out]

TOKENS=[('startsWith("+")',True),('"+"',True),('+1234',True),('PositiveSigned',True),('explicit positive',True),
        ('negate',True),('radix',True),('createBigInteger',True),('resolveWholeValue',True),('decodeMagnitude',True),
        ('java.math.BigInteger',True),('BigInteger',True),('startsWith("-")',True),('scanned once',True)]
def method_line(path, name):
    for m in extract_methods_from_file(path):
        if m["name"]==name: return m["start_line"], m["end_line"]
    return None
def nlines(p): return sum(1 for _ in open(p,encoding="utf-8",errors="ignore"))
def indent_anomalies(path):
    """method headers at 8-space indent (outer members are at 4 in this codebase) and javadoc lines lacking '*'"""
    lines=open(path,encoding="utf-8",errors="ignore").read().split("\n")
    hdr8=[i+1 for i,l in enumerate(lines) if re.match(r'^ {8}(public|private|protected) ',l) and not re.match(r'^ {8}(public|private|protected) .*=',l)]
    injd=[]; injavadoc=False
    for i,l in enumerate(lines):
        s=l.strip()
        if s.startswith("/**"): injavadoc=True; continue
        if injavadoc and s.endswith("*/"): injavadoc=False; continue
        if injavadoc and s and not s.startswith("*"): injd.append(i+1)
    return {"method_headers_at_8_spaces":hdr8, "javadoc_lines_without_star":injd}

res={}
for label,root in (("CONTROL",CONTROL),("TREATMENT",TREAT)):
    r={}
    r["grep_src_main"]={t:rg(root,t) for t,_ in TOKENS}
    r["grep_src_test"]={t:rg(root,t,"src/test/java") for t in ('PositiveSigned','+1234','createBigInteger(','resolveWholeValue','decodeMagnitude','explicit positive')}
    NU=os.path.join(root,"src/main/java/org/apache/commons/lang3/math/NumberUtils.java")
    OU=os.path.join(root,"src/main/java/org/apache/commons/lang3/ObjectUtils.java")
    CB=os.path.join(root,"src/main/java/org/apache/commons/lang3/builder/CompareToBuilder.java")
    r["files"]={"NumberUtils":{"lines":nlines(NU),"methods":len(extract_methods_from_file(NU)),"createBigInteger_span":method_line(NU,"createBigInteger")},
                "ObjectUtils":{"lines":nlines(OU),"methods":len(extract_methods_from_file(OU)),"resolveWholeValue_span":method_line(OU,"resolveWholeValue")},
                "CompareToBuilder":{"lines":nlines(CB),"methods":len(extract_methods_from_file(CB)),"decodeMagnitude_span":method_line(CB,"decodeMagnitude")}}
    r["callers_src_main"]={n:[l for l in rg(root,n+"(") if not re.search(r'(public|private|protected)\s+static.*\b'+n+r'\s*\(', l)] for n in ("createBigInteger","resolveWholeValue","decodeMagnitude")}
    r["indent_anomalies"]={"ObjectUtils":indent_anomalies(OU),"CompareToBuilder":indent_anomalies(CB),"NumberUtils":indent_anomalies(NU)}
    r["fq_BigInteger_in_hosts"]={"ObjectUtils":len(rg(root,"java.math.BigInteger")) and sum(1 for l in rg(root,"java.math.BigInteger") if "ObjectUtils.java" in l),
                                 "CompareToBuilder":sum(1 for l in rg(root,"java.math.BigInteger") if "CompareToBuilder.java" in l)}
    r["git_status_modified"]=subprocess.run(["git","status","--short"],cwd=root,capture_output=True,text=True).stdout.strip().splitlines()
    res[label]=r

# host-selection tie-order sensitivity (pool has a 1080-line tie: Validate.java / ToStringBuilder.java)
src=os.path.join(RR,"lang-1f-checkout/src/main/java"); tgt=os.path.join(src,"org/apache/commons/lang3/math/NumberUtils.java")
orig=candidate_search.find_large_classes
def reversed_ties(source_root,min_lines=1500):
    cl=orig(source_root,min_lines); return sorted(cl,key=lambda x:(-x[1],x[0]),reverse=False) if False else sorted(cl,key=lambda x:(-x[1], x[0]))
def reversed_ties2(source_root,min_lines=1500):
    cl=orig(source_root,min_lines); return sorted(cl,key=lambda x:(-x[1], x[0]),reverse=False)[::1] and sorted(cl,key=lambda x:(-x[1]), reverse=False)[::-1][::-1]
base=[os.path.basename(f) for f,_ in orig(src,900)]
pool_ties=[n for n in set(x[1] for x in orig(src,900)) if [x[1] for x in orig(src,900)].count(n)>1]
h_default=host_search.pick_two_hosts(src,tgt,900,seed=42)[:2]
candidate_search.find_large_classes=lambda s,min_lines=1500: sorted(orig(s,min_lines),key=lambda x:(-x[1], x[0]))
h_nameasc=host_search.pick_two_hosts(src,tgt,900,seed=42)[:2]
candidate_search.find_large_classes=lambda s,min_lines=1500: sorted(orig(s,min_lines),key=lambda x:(-x[1], x[0]),reverse=False)[::-1][::-1] if False else sorted(orig(s,min_lines),key=lambda x:(-x[1], "~"+x[0]) )
candidate_search.find_large_classes=lambda s,min_lines=1500: sorted(orig(s,min_lines),key=lambda x:(-x[1]))  # stable: keeps glob order
h_globorder=host_search.pick_two_hosts(src,tgt,900,seed=42)[:2]
def tie_rev(s,min_lines=1500):
    cl=orig(s,min_lines); out=[]; i=0
    while i<len(cl):
        j=i
        while j<len(cl) and cl[j][1]==cl[i][1]: j+=1
        out+=cl[i:j][::-1]; i=j
    return out
candidate_search.find_large_classes=tie_rev
h_tierev=host_search.pick_two_hosts(src,tgt,900,seed=42)[:2]
candidate_search.find_large_classes=orig
res["host_selection_tie_sensitivity"]={"pool_order_default":base,"tied_line_counts":pool_ties,
    "hosts_default":[os.path.basename(x) for x in h_default],"hosts_ties_reversed":[os.path.basename(x) for x in h_tierev],
    "hosts_name_sorted_ties":[os.path.basename(x) for x in h_nameasc]}
# test-file selection: how many test files 'cover' createBigInteger by the pipeline's file_covers_method
tst=os.path.join(RR,"lang-1f-checkout/src/test/java")
cov=[os.path.relpath(f,tst) for f in glob.glob(f"{tst}/**/*.java",recursive=True) if candidate_search.file_covers_method(f,"createBigInteger")]
res["covering_test_files_for_createBigInteger"]=cov
# example_test truncation: does the 6000-char prefix include testCreateBigInteger?
nt=open(os.path.join(tst,"org/apache/commons/lang3/math/NumberUtilsTest.java")).read()
res["design_prompt_example_test"]={"file_chars":len(nt),"prefix_chars_sent":6000,"testCreateBigInteger_offset":nt.find("testCreateBigInteger("),"included_in_prompt":nt.find("testCreateBigInteger(")<6000}
# baseline suite failures from run.log
log=open(os.path.join(RR,"real/run.log")).read()
res["baseline_failures_reported"]= "baseline has" in log
json.dump(res,open(os.path.join(RR,"analysis/data/pilot_measurements.json"),"w"),indent=1)
print(json.dumps(res,indent=1))
