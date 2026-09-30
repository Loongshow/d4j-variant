# NON-CANONICAL ADVERSARIAL VARIANT - ADV-MASK-01

Exploratory adversarial instance built to find what makes LLM fault localization wrong. Not a canonical Defects4J bug and
not a thesis-benchmark instance. Base Lang-1f. Gold `org.apache.commons.lang3.EnumUtils#compose` (src/main/java/org/apache/commons/lang3/EnumUtils.java). Trigger `org.apache.commons.lang3.ConversionTest::testLang1112`.
Attack CTX-01: pre-positioned field contract: unpositioned field built at H2 with the template's verbatim line; H5's field/word shift asymmetry reads as the bug; a second real consumer pins H5. Classification: ['DEPTH_PRIOR_TRAP', 'CONTEXT_TRAP', 'ATTRIBUTION_TRAP', 'OWNERSHIP_TRAP'].
