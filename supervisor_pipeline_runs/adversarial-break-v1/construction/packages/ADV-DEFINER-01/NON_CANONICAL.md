# NON-CANONICAL ADVERSARIAL VARIANT - ADV-DEFINER-01

Exploratory adversarial instance built to find what makes LLM fault localization wrong. Not a canonical Defects4J bug and
not a thesis-benchmark instance. Base Chart-1f. Gold `org.jfree.chart.plot.Plot#nudge` (source/org/jfree/chart/plot/Plot.java). Trigger `org.jfree.chart.plot.junit.PiePlotTests::test2986548`.
Attack CMB-01: CHART-PIE-03 rebuilt: pure definer (drift, pinned by its own unit test) + NON-TERMINAL gold (nudge drops the negation) + correct textbook terminal (shift). Classification: ['ATTRIBUTION_TRAP', 'OWNERSHIP_TRAP', 'DEPTH_PRIOR_TRAP', 'CONTEXT_TRAP'].
