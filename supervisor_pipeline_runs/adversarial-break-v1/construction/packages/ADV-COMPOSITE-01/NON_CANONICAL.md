# NON-CANONICAL ADVERSARIAL VARIANT - ADV-COMPOSITE-01

Exploratory adversarial instance built to find what makes LLM fault localization wrong. Not a canonical Defects4J bug and
not a thesis-benchmark instance. Base Chart-1f. Gold `org.jfree.chart.plot.Plot#resolve` (source/org/jfree/chart/plot/Plot.java). Trigger `org.jfree.chart.plot.junit.PiePlotTests::test2986548`.
Attack MAX-01: maximum-difficulty composite: pinned pure definer + non-terminal generic undocumented guard-padded gold + loud correct terminal + boolean-only failure. Classification: ['ATTRIBUTION_TRAP', 'OWNERSHIP_TRAP', 'DEPTH_PRIOR_TRAP', 'LEXICAL_TRAP', 'TOOL_BEHAVIOR_TRAP', 'FAILURE_SIGNAL_TRAP', 'CONTEXT_TRAP', 'ARTIFACT'].
