# NON-CANONICAL ADVERSARIAL VARIANT - ADV-DEPTH-01

Exploratory adversarial instance built to find what makes LLM fault localization wrong. Not a canonical Defects4J bug and
not a thesis-benchmark instance. Base Lang-1f. Gold `org.apache.commons.lang3.BitField#widen` (src/main/java/org/apache/commons/lang3/BitField.java). Trigger `org.apache.commons.lang3.ConversionTest::testLang1112`.
Attack DEP-01: non-terminal gold at H3 (mask dropped) with a deeper, correct, javadoc-loud terminal H5. Classification: ['DEPTH_PRIOR_TRAP', 'ATTRIBUTION_TRAP', 'OWNERSHIP_TRAP', 'LEXICAL_TRAP', 'ARTIFACT'].
