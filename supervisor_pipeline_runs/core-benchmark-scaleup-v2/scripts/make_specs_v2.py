"""Generates analysis/spec_<bug>.json for analyze_multiproject.py from each bug's pair_config.json, its rendered TREATMENT payload and the treatment source.
Observable-only markers: exact source substrings (declarations, call lines, buggy lines, contract/javadoc snippets). No LLM."""
import json, os, re, sys
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2"
BUGS = {"projects/Compress/bug-01": "Compress", "projects/Compress/bug-02": "Compress", "projects/Compress/bug-03": "Compress",
        "projects/JacksonCore/bug-04": "JacksonCore", "projects/JacksonCore/bug-05": "JacksonCore", "projects/Compress/bug-06": "Compress"}
# contract / external-evidence markers per bug (substrings that appear in tool OUTPUT when the agent reads the evidence), chosen from TARGET_SPEC external evidence
CONTRACT = {
 "projects/Compress/bug-01": {"J_unsigned_rule": "BYTE_MASK", "C_byte_mask_decl": "private static final int BYTE_MASK = 255", "W_writer_checksum": "getCheckSumOctalBytes", "P_parse_octal": "result = (result << 3)", "H_magnitude_hops": "final int magnitude", "A_accumulator_hops": "sum += IOUtils.sumPair"},
 "projects/Compress/bug-02": {"W_writer_order": "TarUtils.getCheckSumOctalBytes(chk, outbuf, csOffset, CHKSUMLEN)", "L_chksum_len": "CHKSUMLEN", "F_flag_use": "linkFlag ==", "R_reader_cursor": "offset += CHKSUMLEN", "H_widths_hops": "final int numericEnd", "D_dir_flag": "LF_DIR"},
 "projects/Compress/bug-03": {"S_shift_stride": "val = val >> 3", "P_parse_octal": "result = (result << 3)", "M_default_modes": "DEFAULT_FILE_MODE", "T_terminators": "buf[offset + idx] = (byte) ' '", "H_radix_hops": "final int radix", "D_digit_hops": "digitValue"},
 "projects/JacksonCore/bug-04": {"S_surr_constants": "SURR1_FIRST", "I_inverse_split": "(char) (0xD800 + (ch >> 10))", "L_low_mask": "ch & 0x03FF", "R_range_check": "c > 0x10FFFF", "H_weight_hops": "final int bits", "P_plane_base": "final int base = 0x10000"},
 "projects/JacksonCore/bug-05": {"J_last_processed": "location of the last processed character", "C_column_convention": "// 1-based", "T_token_offset": "_tokenInputTotal", "L_location_class": "public class JsonLocation", "H_convention_hops": "final int back", "A_accounting_hops": "final long consumed"},
 "projects/Compress/bug-06": {"R_reader_skip": "ArArchiveInputStream", "C_cpio_pad": "private void pad(", "L_length_check": "prevEntry.getLength() != entryOffset", "H_parity_hops": "final boolean unaligned", "B_boundary_hops": "final int boundary = 2", "M_magic": "!<arch>"},
}
def idents(text): return sorted({t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text)})
for bug, proj in BUGS.items():
    root = f"{S}/{bug}"; cfg = json.load(open(f"{root}/pair_config.json")); T = cfg["treatment"]; C = cfg["control"]
    fac_cls = cfg["facade_file"].split("/")[-1].replace(".java", ""); fac_meth = cfg["facade_decl"].split("(")[0].split()[-1]
    fac_decl = cfg["facade_decl"].strip(); fac_call = T["facade_call"].strip()
    hops = T["hops"]; chain = [["facade", fac_cls, fac_meth, fac_decl, fac_call]]
    for i, h in enumerate(hops):
        tag = f"H{h['n']}"; chain.append([tag, h["class"].split(".")[-1], h["method"], h["decl"].strip(), (h["calls_next"] or "").strip() or None])
    def buggy_line(block):
        lines = [l.strip() for l in block.split("\n") if l.strip()]; return lines[-1] if len(lines) > 1 else lines[0]
    arms = {cfg["control_id"]: {"arm": "CONTROL", "gold_class": C["gold_class"], "gold_method": C["gold_method"], "gold_decl": C["gold_decl"].strip(), "buggy": buggy_line(C["bug_line"])},
            cfg["treatment_id"]: {"arm": "TREATMENT", "gold_class": T["gold_class"], "gold_method": T["gold_method"], "gold_decl": T["gold_decl"].strip(), "buggy": buggy_line(T["bug_line"])}}
    payload = open(f"{root}/analysis/leakage/rendered_payload_treatment.txt", errors="replace").read()
    payload_tokens = idents(payload)
    novel = sorted({h["method"] for h in hops} | {h["class"].split(".")[-1] for h in hops} | set(idents(T["orig_line"])) | set(idents(T["bug_line"])) - set(payload_tokens))
    spec = {"project": proj, "label": f"NON-CANONICAL / CORE BENCHMARK SCALE-UP / GPT-5.6 ({cfg['pair_id']})", "src_dir": cfg["src_dir"], "chain": chain, "arms": arms,
            "contract": CONTRACT[bug], "other": {"assertion_msg": cfg["expected_signature"], "d4j_modified_class_output": "d4j.classes.modified"},
            "payload_tokens": payload_tokens, "novel_watch": novel, "gold_name_tokens": [T["gold_method"], T["gold_class"].split(".")[-1]]}
    out = f"{S}/results-gpt56/analysis/spec_{cfg['pair_id']}.json"; json.dump(spec, open(out, "w"), indent=1)
    # sanity: every chain decl / call / buggy / gold_decl string must occur in the treatment repro checkout (control buggy in the control checkout)
    def grep(co, s):
        for dp, _, fs in os.walk(os.path.join(co, cfg["src_dir"])):
            for fn in fs:
                if fn.endswith(".java") and s in open(os.path.join(dp, fn), errors="replace").read().replace("\r\n", "\n"): return True
        return False
    tco = f"{root}/repro/treatment-checkout"; cco = f"{root}/repro/control-checkout"; missing = []
    for tag, cls, meth, decl, call in chain:
        if not grep(tco, decl): missing.append(("decl", tag, decl))
        if call and not grep(tco, call): missing.append(("call", tag, call))
    if not grep(tco, arms[cfg["treatment_id"]]["buggy"]): missing.append(("buggy", "T", arms[cfg["treatment_id"]]["buggy"]))
    if not grep(cco, arms[cfg["control_id"]]["buggy"]): missing.append(("buggy", "C", arms[cfg["control_id"]]["buggy"]))
    cm = {k: v for k, v in CONTRACT[bug].items() if not (grep(tco, v) or grep(cco, v) or v in payload)}
    print(f"{cfg['pair_id']:18s} spec -> {os.path.relpath(out, S)} | payload tokens {len(payload_tokens)} | novel_watch {len(novel)} | missing anchors: {missing or 'none'} | contract markers not found in source/payload: {cm or 'none'}")
