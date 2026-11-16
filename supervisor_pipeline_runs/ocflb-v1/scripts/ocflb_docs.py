"""Generate the per-pair analysis documents from pair.json + validation.json. Usage: ocflb_docs.py <pair.json>"""
import json, sys, os
spec = json.load(open(sys.argv[1])); PD = spec["pair_dir"]; val = json.load(open(f"{PD}/validation/validation.json")); CH = spec["chain"]; A = spec["arms"]; an = f"{PD}/analysis"; os.makedirs(an, exist_ok=True)
def w(name, s): open(f"{PD}/{name}", "w").write(s)
roles = ["H1", "H2", "H3", "H4", "H5"]; rn = {"H1": "input preparation / extraction", "H2": "semantic convention / definition (DEFINER)", "H3": "adapter / transformation (ADAPTER)", "H4": "consumer / application", "H5": "final combination / output"}
w("TARGET_SPEC.md", f"""# {spec['pair_id']} target spec (NON-CANONICAL RESEARCH BENCHMARK)

Project {spec['project']}, base {spec['base_version']}, seed {spec.get('seed_variant')}. Fault family: **{spec['family']}**.
Semantic convention (H2 contract): {spec.get('convention')}
Effect of the fault: {spec.get('effect')}

| Role | Method | File |
|---|---|---|
| Facade | `{CH['facade']['class']}#{CH['facade']['method']}` | `{CH['facade']['file']}` |
""" + "\n".join(f"| {r} ({rn[r]}) | `{CH[r]['class']}#{CH[r]['method']}` | `{CH[r]['file']}` |" for r in roles) + f"""

Trigger `{spec['trigger']}` (neutral name). Expected failure text contains `{spec['expected_signature']}`.
Pin test (second caller of H2): `{spec['pin_test']}`. Production second caller: {spec.get('second_caller') or 'none (unit-test pin only)'}.

| Arm | Variant | Gold | Buggy line(s) | Correct line(s) | Declared collateral |
|---|---|---|---|---|---|
""" + "\n".join(f"| {arm} | `{a['variant_id']}` | {a['gold_role']} `{a['gold']['class']}#{a['gold']['method']}` | `{a['gold']['bug_line'].strip().replace(chr(10), ' / ')}` | `{a['gold']['orig_line'].strip().replace(chr(10), ' / ')}` | {a.get('declared_collateral') or 'none'} |" for arm, a in A.items()) + "\n")
w("analysis/LOGIC_CHAIN.md", f"""# Logic chain - {spec['pair_id']}

```
{CH['facade']['class'].split('.')[-1]}.{CH['facade']['method']}   (facade)
  -> {CH['H1']['class'].split('.')[-1]}.{CH['H1']['method']}   (H1 {rn['H1']})
       -> {CH['H2']['class'].split('.')[-1]}.{CH['H2']['method']}   (H2 {rn['H2']})   <== DEFINER_FAULT gold
       -> {CH['H3']['class'].split('.')[-1]}.{CH['H3']['method']}   (H3 {rn['H3']})   <== ADAPTER_FAULT gold
            -> {CH['H4']['class'].split('.')[-1]}.{CH['H4']['method']}   (H4 {rn['H4']})
                 -> {CH['H5']['class'].split('.')[-1]}.{CH['H5']['method']}   (H5 {rn['H5']})
second caller: {spec['pin_test']} -> H2
```

H1 obtains the semantic quantity from H2 and hands it to H3; H3 -> H4 -> H5 is a nested call chain. Dynamic participation of the
facade and all five hops under the trigger was verified by the instrumented run in gate V6 for both arms
({[g['key_output'] for g in val['gates'] if g['gate']=='V6'][:2]}). Static call edges verified in gate V10.
""")
own = {arm: val["arms"][arm] for arm in A}
w("analysis/OWNERSHIP_PROOF.md", f"""# Ownership proof - {spec['pair_id']}

Isolated repairs executed by the validator (gates V11a/V11b/V12), on the buggy arm each time:

| Arm | Gold repair (declared gold line restored) | Compensating repair at the other hop | Pin on buggy arm | Classification |
|---|---|---|---|---|
""" + "\n".join(f"| {arm} | trigger fail={own[arm]['gold_repair']['trigger_fail']}, pin fail={own[arm]['gold_repair']['pin_fail']} | target {own[arm]['compensating_repair']['target_role']}: trigger fail={own[arm]['compensating_repair']['trigger_fail']}, pin fail={own[arm]['compensating_repair']['pin_fail']} | fail={own[arm]['pin_on_buggy']['n_fail']} | **{own[arm]['ownership']}** |" for arm in A) + f"""

Reading. DEFINER_FAULT: the convention itself is wrong; repairing H2 fixes the trigger and the pin together; making H3 compensate
fixes the trigger but leaves the pin (which checks H2's documented convention) failing. ADAPTER_FAULT: H2 is independently correct
(pin passes on the buggy arm); repairing H3 fixes the trigger; making H2 absorb H3's error fixes the trigger but breaks the pin.
An upstream compensating edit to H2 therefore cannot absorb the H3 fault without collateral damage: ownership is pinned.
""")
sig = {arm: val["arms"][arm]["trigger_runs"][0]["signature"] for arm in A}
w("analysis/SEMANTIC_EQUIVALENCE.md", f"""# Semantic equivalence of the arms - {spec['pair_id']}

Both arms share the base checkout, facade, trigger, failing input, expected output, chain, names, files, documentation and test
patch (one `test.patch`, identical hash {spec['package_hashes']['DEFINER_FAULT']['test.patch'][:16]}...). The variant patches differ
only in the declared H2/H3 lines (gate V10b: {[g['key_output'] for g in val['gates'] if g['gate']=='V10b']}).

Observed failure, DEFINER_FAULT: `{sig['DEFINER_FAULT'].splitlines()[-1] if sig['DEFINER_FAULT'] else ''}`
Observed failure, ADAPTER_FAULT: `{sig['ADAPTER_FAULT'].splitlines()[-1] if sig['ADAPTER_FAULT'] else ''}`
Identical: {sig['DEFINER_FAULT'] == sig['ADAPTER_FAULT']} (gate V3d). Algebraic reason: {spec.get('equivalence_note')}
""")
lex = [g for g in val["gates"] if g["gate"].startswith("V9")]
w("analysis/LEAKAGE_AUDIT.md", f"""# Leakage audit - {spec['pair_id']}

- Trigger name `{spec['trigger'].split('::')[1]}` contains no hop method name (V9a: {lex[0]['status']}).
- Lexgate over added lines of test.patch and both variant patches for fault-identifying vocabulary: {', '.join(g['gate']+'='+g['status'] for g in lex)}.
- The pin test is named after H2's method by design (it documents H2's convention); it is the second caller, not a leak of the gold:
  it exists identically in both arms, passes on the ADAPTER arm and fails on the DEFINER arm (declared collateral, visible only to an
  agent that runs the whole test class or the pin test).
- Both arms expose the same repository structure; neither manifest, reasoning file nor patch is visible to the agent.
""")
w("analysis/LOCAL_COHERENCE.md", f"""# Local coherence - {spec['pair_id']}

H2 (`{CH['H2']['method']}`) carries a javadoc stating the convention: {spec.get('convention')}. In the DEFINER arm the body contradicts
that javadoc; in the ADAPTER arm the body matches it. H3 (`{CH['H3']['method']}`) carries a javadoc describing the transformation; in the
ADAPTER arm its body misapplies H2's value ({spec.get('adapter_fault_note')}); in the DEFINER arm it is correct. Documentation is
identical across arms, so a reader who trusts the javadoc finds the same words in both arms and must read the bodies to locate the fault.
""")
print("docs written for", spec["pair_id"])
