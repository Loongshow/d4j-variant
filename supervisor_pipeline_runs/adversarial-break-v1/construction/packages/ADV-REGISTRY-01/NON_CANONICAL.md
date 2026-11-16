# NON-CANONICAL ADVERSARIAL VARIANT - ADV-REGISTRY-01

Exploratory adversarial instance built to find what makes LLM fault localization wrong. Not a canonical Defects4J bug and
not a thesis-benchmark instance. Base Lang-1f. Gold `org.apache.commons.lang3.Packer32#pack` (src/main/java/org/apache/commons/lang3/Packer32.java). Trigger `org.apache.commons.lang3.ConversionTest::testLang1112`.
Attack NAV-01: runtime-type registry over five real `pack` implementations; fault in the selected one, odd-looking correct sibling registered first. Classification: ['SEARCH_TRAP', 'TOOL_BEHAVIOR_TRAP', 'CANDIDATE_OVERLOAD', 'MODEL_SPECIFIC', 'ARTIFACT'].
