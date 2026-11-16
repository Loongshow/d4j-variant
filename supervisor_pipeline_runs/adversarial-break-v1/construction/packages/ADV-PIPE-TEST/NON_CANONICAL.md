# NON-CANONICAL ADVERSARIAL VARIANT - ADV-PIPE-TEST

Exploratory adversarial instance built to find what makes LLM fault localization wrong. Not a canonical Defects4J bug and
not a thesis-benchmark instance. Base Lang-1f. Gold `org.apache.commons.lang3.math.NumberUtils#overlay` (src/main/java/org/apache/commons/lang3/math/NumberUtils.java). Trigger `org.apache.commons.lang3.ConversionTest::testLang1112`.
Attack PIPE-TEST: pipeline dry run (historical five-hop chain). Classification: ['CLEAN'].
