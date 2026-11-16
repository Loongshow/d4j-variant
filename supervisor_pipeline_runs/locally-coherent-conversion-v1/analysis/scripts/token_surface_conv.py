import json, os, re, subprocess
LC="/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/locally-coherent-conversion-v1"
STATES={"CONTROL-01":("c","src/main/java/org/apache/commons/lang3/Conversion.java","public static long intArrayToLong(final int[] src"),
        "TREATMENT-01":("t","src/main/java/org/apache/commons/lang3/math/Fraction.java","public static long assemble(final int[] values")}
TOKENS=["testLang1112","ConversionTest","intArrayToLong","Conversion","foldValues","assemble","ArrayUtils","Fraction","dstPos","nInts","srcPos","dstInit","0xffffffffL","<< shift","shift = ","* 32","int[]","long out","mask","bits","greather","endian","offset","0xCDF1F0C1","0x0F123456","0x0000000F12345600","0x1234CDF1F0C1DEF0","position in the result","values[i + from]","i + from","(i + at)","(i + dstPos)","import org.apache.commons.lang3.math.Fraction","subAndCheck","greatestCommonDivisor","subarray"]
def grep(root,tok,sub):
    p=subprocess.run(["grep","-rnF","--include=*.java",tok,os.path.join(root,sub)],capture_output=True,text=True); return [l.replace(root+"/","") for l in p.stdout.splitlines()]
def span(root,f,decl):
    L=open(os.path.join(root,f)).read().split("\n"); s=next((i for i,l in enumerate(L) if decl in l),None)
    if s is None: return None
    d=0;st=False
    for j in range(s,len(L)):
        d+=L[j].count("{")-L[j].count("}"); st=st or "{" in L[j]
        if st and d==0: return (s+1,j+1)
out={}
for name,(sd,gf,decl) in STATES.items():
    root=os.path.join(LC,"analysis/states",sd); gs=span(root,gf,decl); res={"gold_file":gf,"gold_span":gs,"tokens":{}}
    for tok in TOKENS:
        hm=grep(root,tok,"src/main/java"); ht=grep(root,tok,"src/test/java"); files=sorted({h.split(":")[0].split("/")[-1] for h in hm})
        ing=[h for h in hm if h.startswith(gf+":") and gs and gs[0]<=int(h.split(":")[1])<=gs[1]]
        res["tokens"][tok]={"main_hits":len(hm),"main_files":files,"test_hits":len(ht),"gold_file_hits":sum(1 for h in hm if h.startswith(gf+":")),"hits_inside_gold_method":len(ing),"scannable(<=40)":len(hm)<=40}
    out[name]=res
json.dump(out,open(os.path.join(LC,"analysis/data/token_surface.json"),"w"),indent=1)
print("| token | CONTROL-01: main hits / files / in-gold | TREATMENT-01: main hits / files / in-gold |\n|---|---|---|")
for tok in TOKENS: print(f"| `{tok}` | "+" | ".join(f"{out[n]['tokens'][tok]['main_hits']} / {len(out[n]['tokens'][tok]['main_files'])} / {out[n]['tokens'][tok]['hits_inside_gold_method']}" for n in STATES)+" |")
print("\ngold spans:",{n:out[n]["gold_span"] for n in STATES})
for n in STATES:
    t=out[n]["tokens"]; print(n,"| 0xffffffffL files:",t["0xffffffffL"]["main_files"],"| '<< shift' files:",t["<< shift"]["main_files"],"| Fraction files:",t["Fraction"]["main_files"][:8],"| foldValues:",t["foldValues"]["main_files"],"| assemble:",t["assemble"]["main_files"])
