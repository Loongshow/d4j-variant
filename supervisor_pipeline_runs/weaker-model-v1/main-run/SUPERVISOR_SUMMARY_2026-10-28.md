Dear Hong Jin,

A short status update on the "run all Defects4J bugs" extension (as of 28 October).

**Done so far: 187 instances fully run (5 runs each, 935 runs); 130 of them shifted at least once (466 of 935 runs had the gold below rank 1).**

| Instance type | Facade | Hosts | Instances | With ≥ 1 shift | Shifted runs |
|---|---|---|---|---|---|
| C10 | static method | five classes of ≥ 1,500 lines | 67 | 50 | 194/335 |
| C10f | static method | the five largest classes (projects without five 1,500-line classes) | 38 | 30 | 108/190 |
| C10i | instance method | either rule, by project | 82 | 50 | 164/410 |
| **Total** | | | **187** | **130** | **466/935** |

The instances cover 13 Defects4J projects. Three findings so far:
- Host size does not explain the result: the fallback-host instances shift as often as the large-host ones.
- On the same bug with the same hosts, a static and an instance-method facade shift equally often (17 paired instances).
- Two projects rarely shift in any type: JacksonDatabind (4 of 18) and Jsoup (4 of 11). On bugs that never had a static facade, the rate is lower (37 of 60).

**Still to run: 38 instances (36 counted, 2 flagged as ambiguous and reported separately), about 186 runs.** They are the last tier
of the plan: instance-method facades whose object is passed down (the receiver variant), plus the Closure bugs. All of them are
already built, independently audited, blind-checked and frozen; only the paid runs remain. Fifteen of them were prioritised because
their project had few or no instance-method instances (Closure, Cli, Collections, Compress, Codec, JacksonCore); they include the
first Cli instances of this type. When they finish the programme will have
about **223 instances** in 13 projects. Mockito and Csv are not attempted: Mockito cannot be scored on the frozen evaluation server,
and Csv has no usable public host classes.

**Credits.** Spent so far: about **$472** of OpenAI credit (gpt-5.5; $462 recorded plus about $10 of estimated probe cost). The
remaining 186 runs need about **$80** (at about $0.43 per run), bringing the total to about **$552**. The account ran out three
times during the runs; it needs a top-up of about **$100** (the $80 plus a margin for replacement runs) before the last runs can
start. Once topped up, they take about 4.5 hours.

Best regards,
[Your name]
