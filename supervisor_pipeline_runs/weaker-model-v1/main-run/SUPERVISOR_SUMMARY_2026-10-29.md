Dear Hong Jin,

The "run all Defects4J bugs" extension has finished its runs (29 October).

**Final count: 223 instances fully run (5 runs each), in 13 Defects4J projects; 146 of them shifted at least once (520 of 1,114 answered runs had the gold below rank 1).**

| Instance type | Facade | Hosts | Instances | With ≥ 1 shift | Shifted runs |
|---|---|---|---|---|---|
| C10 | static method | five classes of ≥ 1,500 lines | 67 | 50 | 194/335 |
| C10f | static method | the five largest classes | 38 | 30 | 108/190 |
| C10i | instance method | either rule, by project | 118 | 66 | 218/589 |
| **Total** | | | **223** | **146** | **520/1,114** |

Main findings:
- The effect is strongest on the bugs the recipe was designed for and weakens on the later tiers (share of instances with a shift: 0.75 and
  0.79 for the static facades, 0.62 and 0.41 for the last two instance-facade tiers, whose facades are mostly thin wrappers).
- Host size and facade kind do not explain this: fallback hosts shift as often as large ones, and on the same bug with the same hosts a static
  and an instance facade shift equally often (14 distinct pairs, 6 up / 5 down).
- Projects differ consistently: Collections shifts in almost every instance (20 of 22), JacksonDatabind (5 of 22) and Jsoup (8 of 20) rarely.
- When a run shifts, the model nearly always ranks the facade (the method the test calls) first.

Not attempted: Mockito (cannot be scored on the frozen evaluation server) and Csv (no public host classes).

**Credits.** Total OpenAI spend about **$562** (gpt-5.5, including estimated probe cost). Nothing more is needed for these experiments.

Best regards,
[Your name]
