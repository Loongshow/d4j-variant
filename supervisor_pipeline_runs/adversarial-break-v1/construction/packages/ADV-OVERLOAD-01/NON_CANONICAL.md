# NON-CANONICAL ADVERSARIAL VARIANT - ADV-OVERLOAD-01

Exploratory adversarial instance built to find what makes LLM fault localization wrong. Not a canonical Defects4J bug and
not a thesis-benchmark instance. Base Lang-1f. Gold `org.apache.commons.lang3.Conversion#hexToLong` (src/main/java/org/apache/commons/lang3/Conversion.java). Trigger `org.apache.commons.lang3.ConversionTest::testLang1180`.
Attack OVL-01: 18 sibling conversions executed by one boolean-only test; fault in one. Classification: ['CANDIDATE_OVERLOAD', 'FAILURE_SIGNAL_TRAP'].
