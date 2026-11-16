# NON-CANONICAL ADVERSARIAL VARIANT - ADV-LEX-01

Exploratory adversarial instance built to find what makes LLM fault localization wrong. Not a canonical Defects4J bug and
not a thesis-benchmark instance. Base Lang-1f. Gold `org.apache.commons.lang3.math.NumberUtils#apply` (src/main/java/org/apache/commons/lang3/math/NumberUtils.java). Trigger `org.apache.commons.lang3.ConversionTest::testLang1112`.
Attack LEX-01: witness inversion: generic undocumented gold (`apply`) vs a loud, documented, executed decoy (`wordOffset`) whose javadoc states the correct formula and whose body computes the wrong-shaped one. Classification: ['LEXICAL_TRAP', 'ATTRIBUTION_TRAP', 'CONTEXT_TRAP', 'ARTIFACT'].
