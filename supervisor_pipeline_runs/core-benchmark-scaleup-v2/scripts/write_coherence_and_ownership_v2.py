"""Writes the per-bug LOCAL_COHERENCE_AUDIT.md and appends the contractual-ownership judgement to OWNERSHIP_UNIQUENESS_AUDIT.md.
The behavioural verdict comes from the measured counterfactuals; the contractual verdict is the author's judgement of whether another
stage's own documented responsibility would make it a defensible owner of the wrong quantity (the property that CHART-PIE-03 exposed).
NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6."""
import json, os
S = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2"
BUGS = {
 "projects/Compress/bug-01": {
   "gold_body": "    public static int magnitudeOf(final byte raw) {\n        final int magnitude = raw;          // correct: raw & 0xFF\n        return magnitude;\n    }",
   "local_suggests": "a byte being widened to an int, which is what the method's name and javadoc promise (\"the magnitude of a single byte\"); the assignment is a complete, idiomatic Java widening conversion",
   "not_inferable": "that Java's `byte` is signed and that a record byte above 0x7f must therefore be masked; nothing inside the method mentions a width, a mask or a range",
   "external": "the USTAR rule that the checksum sums **unsigned** byte values, the `BYTE_MASK = 255` constant in the original `TarUtils`, and the inverse `parseOctal`, which yields a non-negative number",
   "obviously_wrong": "no: the buggy body contains no unused variable, no dangling parameter and no arithmetic that looks incomplete",
   "contractual": "UNIQUE",
   "contractual_reason": "the two stages that are behaviourally equivalent repair sites document different jobs — H4 `widen` promises a widening to the accumulator type and H3 `byteValue` promises element access with bounds validation; masking a byte to eight bits is neither of those, so neither stage is a defensible owner of the signedness decision. The facade candidate is a bypass of the chain, not a repair of a stage."},
 "projects/Compress/bug-02": {
   "gold_body": "    public static int flagOffset(final int numericEnd) {\n        final int afterChecksum = numericEnd;   // correct: numericEnd + CHKSUMLEN\n        return afterChecksum;\n    }",
   "local_suggests": "that the type flag begins exactly where the numeric fields end; the local name `afterChecksum` reads as a label for that position rather than as a claim that has to be computed",
   "not_inferable": "that a checksum field of eight bytes sits between the numeric fields and the type flag; the width `CHKSUMLEN` is not referenced in the buggy body",
   "external": "the USTAR layout (checksum at 148, type flag at 156), `TarArchiveEntry.writeEntryHeader`, which writes the checksum field before the type flag, and `TarConstants.CHKSUMLEN`",
   "obviously_wrong": "borderline: a reader who notices that the local is called `afterChecksum` while nothing about a checksum is added may become suspicious — this is recorded as the weakest local-coherence point of the six new bugs",
   "contractual": "MOSTLY_UNIQUE",
   "contractual_reason": "H4 is named `checksumBoundary` and documents that it hands the numeric end \"to the field that follows\", so an agent could defensibly argue that adding the checksum width is H4's job; the measured equivalent repairs at H4/H3 are therefore not purely mechanical. The gold remains the only stage that states where the type flag is."},
 "projects/Compress/bug-03": {
   "gold_body": "    public static int octalDigit(final long magnitude) {\n        final int radix = 16;                   // correct: 8\n        return (int) (magnitude & (radix - 1));\n    }",
   "local_suggests": "a digit being masked out of a value for a radix that is stated one line above; the mask is derived from the radix, so the body is internally consistent for any radix",
   "not_inferable": "which radix a tar numeric field uses; the shift that consumes the digit (`val >> 3`) lives in the facade, not here",
   "external": "the USTAR rule that numeric fields are octal, the `>> 3` stride in the caller, `TarUtils.parseOctal`'s `<< 3`, and the octal default modes `0644`/`0755`",
   "obviously_wrong": "no: the radix is a plausible constant and the mask is correctly derived from it",
   "contractual": "MOSTLY_UNIQUE",
   "contractual_reason": "H4 `maskDigit` documents \"masks out the lowest digit\", which makes a three-bit mask there arguable; the specific claim \"this field is octal\" is only in the gold, so the gold is the primary owner but not the only defensible one."},
 "projects/JacksonCore/bug-04": {
   "gold_body": "    public static int highSurrogateWeight(final int hiOffset) {\n        final int bits = 11;                    // correct: 10\n        return hiOffset << bits;\n    }",
   "local_suggests": "an offset being shifted by the number of bits the low surrogate holds, exactly as the javadoc says; the shift amount is a named constant, so the body is self-consistent",
   "not_inferable": "that a surrogate block is 1024 values wide and therefore carries ten bits; the block boundaries are not visible in this method",
   "external": "the Unicode UTF-16 decoding rule, the `SURR*` constants in `UTF8Writer`, and the inverse split in `UTF32Reader` (`>> 10`, `& 0x03FF`)",
   "obviously_wrong": "no: nothing in the body is unused or inconsistent; only the value of the constant is wrong",
   "contractual": "UNIQUE",
   "contractual_reason": "although a halving at H3/H4 is behaviourally equivalent, both stages document different jobs (combining the three contributions; validating the surrogate offset). No stage but the gold claims to know how wide a surrogate block is."},
 "projects/JacksonCore/bug-05": {
   "gold_body": "    public static long lastProcessed(final long nextPosition) {\n        final int back = 0;                     // correct: 1\n        return nextPosition - back;\n    }",
   "local_suggests": "a position being converted by stepping back a fixed amount; with `back = 0` the body reads as \"the next position is already the position we want\"",
   "not_inferable": "whether the caller's quantity is a count of consumed characters or an index of the next character, i.e. whether a step back is required at all",
   "external": "the javadoc of `ParserBase.getCurrentLocation` (\"location of the last processed character\"), the `+ 1 // 1-based` column convention on the adjacent line, and `getTokenLocation`, which reports an offset captured before the token was consumed",
   "obviously_wrong": "a reader may find `- back` with `back = 0` odd, but a zero adjustment is a common way to keep a conversion explicit; the wrongness is the convention, not the shape",
   "contractual": "AMBIGUOUS",
   "contractual_reason": "every stage of this chain documents the same output — \"the offset of the last processed character\" — so the convention is, by documentation, the responsibility of each of them. This is the closest analogue in the new set to CHART-PIE-03 and is flagged as such before the paid block."},
 "projects/Compress/bug-06": {
   "gold_body": "    public static int padNeeded(final long remainder) {\n        final boolean unaligned = remainder == 0;   // correct: remainder != 0\n        return unaligned ? 1 : 0;\n    }",
   "local_suggests": "a parity test naming the unaligned case and a pad count of one byte for it, which is coherent for any two-byte aligned format",
   "not_inferable": "which side of the parity means \"unaligned\"; the method receives only a remainder, and both directions are syntactically identical",
   "external": "the AR rule that a member header starts on an even offset, `ArArchiveInputStream`'s matching skip of the pad byte, and `CpioArchiveOutputStream.pad`, which pads up to the boundary",
   "obviously_wrong": "no: the comparison is well formed and the local name is consistent with its use",
   "contractual": "MOSTLY_UNIQUE",
   "contractual_reason": "the upstream stages document counts and boundaries, and only the gold decides the parity; an inverted count at H4 is behaviourally equivalent but contradicts H4's documented job (checking that the boundary is supported)."},
}
for bug, d in BUGS.items():
    D = f"{S}/{bug}"; cfg = json.load(open(f"{D}/pair_config.json")); T = cfg["treatment"]
    L = [f"# LOCAL_COHERENCE_AUDIT — {cfg['pair_id']} (gold `{T['gold_class'].split('.')[-1]}#{T['gold_method']}`, TREATMENT) · NON-CANONICAL · CORE BENCHMARK SCALE-UP V2", "",
         "Question: read in isolation, does the buggy gold look like plausible, self-consistent code, while the fault remains a real contract violation visible from the caller's contract and the trigger?", "",
         "```java", d["gold_body"], "```", "",
         "| Check | Finding |", "|---|---|",
         f"| What the local code suggests | {d['local_suggests']} |",
         f"| What cannot be inferred locally | {d['not_inferable']} |",
         f"| External evidence required | {d['external']} |",
         f"| Does the mutation look obviously wrong? | {d['obviously_wrong']} |",
         f"| CONTROL twin | the same semantic fault in `{cfg['control']['gold_class'].split('.')[-1]}#{cfg['control']['gold_method']}`: `{cfg['control']['bug_line'].strip()[:90]}` |",
         f"| Trigger visibility | `{cfg['trigger'].split('::')[-1]}` fails with `{cfg['expected_signature']}`, which names the quantity the gold computes |", "",
         "Verdict: PASS — locally coherent, globally wrong."]
    open(f"{D}/analysis/LOCAL_COHERENCE_AUDIT.md", "w").write("\n".join(L) + "\n")
    own = f"{D}/analysis/OWNERSHIP_UNIQUENESS_AUDIT.md"
    ow = json.load(open(f"{D}/analysis/ownership_counterfactual.json"))
    if os.path.exists(own) and "Contractual (judged)" not in open(own).read():
        app = ["", "## Two-dimensional classification (v2)", "",
               f"* **Behavioural (measured): {ow['classification']}** — equivalent repair sites: {ow['equivalent_repair_sites'] or 'none'}; compensating: {ow['compensating_repair_sites'] or 'none'}.",
               f"* **Contractual (judged): {d['contractual']}** — {d['contractual_reason']}", "",
               "Why both are reported: in a chain whose stages each have exactly one caller, an inverse edit at an adjacent stage is almost always behaviourally equivalent, so the behavioural dimension mostly measures a property of five-hop chains rather than of the fault. The contractual dimension asks whether another stage's *documented responsibility* would make it a defensible owner, which is the property that produced the stable rank-6 attribution of CHART-PIE-03. Benchmark-level ownership grouping uses the contractual verdict, with the behavioural measurement always shown next to it."]
        open(own, "a").write("\n".join(app) + "\n")
    print(f"{cfg['pair_id']}: coherence written | ownership behavioural {ow['classification']} / contractual {d['contractual']}")
