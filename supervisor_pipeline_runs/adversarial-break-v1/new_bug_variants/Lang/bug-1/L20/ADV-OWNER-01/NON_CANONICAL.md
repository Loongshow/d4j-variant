# NON-CANONICAL ADVERSARIAL VARIANT - ADV-OWNER-01

Exploratory adversarial instance built to find what makes LLM fault localization wrong. Not a canonical Defects4J bug and
not a thesis-benchmark instance. Base Lang-1f. Gold `org.apache.commons.lang3.Conversion#longToHex` (src/main/java/org/apache/commons/lang3/Conversion.java). Trigger `org.apache.commons.lang3.ConversionTest::testLang1185`.
Attack OWN-01: round trip: producer (longToHex) emits spec-shaped but wrong upper digits; consumer (hexToLong) is correct and exposes it. Classification: ['OWNERSHIP_TRAP', 'ATTRIBUTION_TRAP', 'FAILURE_SIGNAL_TRAP'].
