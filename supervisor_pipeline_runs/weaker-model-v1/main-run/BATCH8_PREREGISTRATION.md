# Main run, batch 8 (cell C10i on bugs without a static facade): pre-registration

Written before any batch-8 design, build or run, after the batch-8 checkouts and host confirmation. The sha256 of this file is recorded in
`AMENDMENTS.md` (W56). Batch 8 is the fourth tier of the "all Defects4J bugs" extension (W42, W45): the C10i recipe (instance-method
facade, batch 7) applied to bugs that **have no static facade** in their modified classes (pool v2 `facade_class_basis = no_tested_static`
or no strictly tested static target). These instances are reported in the C10i cell (`mr3_report.py`, tier `MAIN_RUN_C10I`), with batch
`batch8`, and are never pooled with C10/C10f in a headline without the composition (W42).

## Authorisation

W45 (the user's standing instruction of 25 October) and the user's instruction of 26 October to continue toward about 200 instances
("充值好了，继续跑试验", given in reply to the 200-instance projection of the same day, which projected a cumulative of about $490 and
recommended raising the guard cap to $550–600), and the 23-October instruction that cost is not a limit ("不需要考虑 cost limit"). **The
guard cap for batch 8 is $600** (it was $500 for batches 5–7, W45); the per-block checks of W45 are unchanged. The cap stays a sanity stop:
if the guard's worst case exceeds it, the launcher stops and the coordinator reports.

## Everything from batches 3 to 7, unchanged

`BATCH3_…BATCH7_PREREGISTRATION.md` apply unless this document says otherwise: the C10 recipe (`BUILD_BRIEF.md`, sha256
`cc565d61c221…`), the C10i addendum (`BUILD_BRIEF_C10I_ADDENDUM.md`, `3be3eafbfcd8…`),
the C10f host section (`BUILD_BRIEF_C10F_ADDENDUM.md`, `f50c479a7abe…`), the no-local-trace
HARD rule (`NO_LOCAL_TRACE_CHECKLIST.md`, `487a966a09f9…`), `TRACE_CHECK_BRIEF.md` and `AUDIT_BRIEF.md`
(with the batch-7 audit item `g_c10i_rules`), the pipeline (builder → auditor + blind checker → one redesign → disposition table), the frozen
protocol on w55 (gpt-5.5, medium, 50 tool calls, 5 tests, 300 s; 5 runs per instance), the KPI (SHIFT = gold rank > 1; INSTANCE_SUCCESS =
at least one shift in 5 valid runs), the 16 gates, packaging and the key, the robustness raters (secondary), facade reuse as a recorded
alternative with distinctness preferred, the per-block launcher `scripts/mr_run_blocks.sh` (cap $600 from batch 8, see Authorisation). No completed instance is redesigned, rebuilt or re-run.

## What defines batch 8

**1. Unit.** A bug not used in batches 1–7 whose modified classes offer a strictly tested public instance method (the 23-October profile:
`instance_facade_oct23/profile/candidates.csv`; variant V0–V2 feasible, public top-level class, strict test caller, at least 8 body lines or
self-containedness ≥ 5, no unknown-effects risk) and whose best candidate is V0 or V1 (the plan's "C10i-V0/V1" tier; V2-best bugs are
deferred, 62 of them). Mockito (unscorable on the frozen server), Csv (package-private hosts) and Closure (13 bugs;
224-MB fixtures, disk) are deferred. Selection script `main-run/batch8_prep/make_tasks.py` (`dd6acb068cd5…`).

**2. Facade and hosts.** `construction/mainrun/BUILD_BRIEF_C10I_B8_NOTE.md` (`b993d4bee1ea…`): no static pair
(addendum §2 void); hosts by `host_mode` with every allowed candidate's file excluded — `1500`: the recipe's seeded draw at build time;
`largest5`: the five largest public classes confirmed on the checkout (`batch8_prep/confirm_hosts.py`, `8cc77d85eceb…`;
a 1500-regime task with fewer than five such classes on the checkout is moved to largest5 and marked); distinctness preferred via
`facade_planned_by`. Reachability probe mandatory. Labels and paths are batch 7's (`mr3_spec.py`, `MI-<key>`, `designs/<key>__i.py`).

**3. Records.** `scripts/mr3_build_records.py` (`1170d9a68eea…`) now also reads `batch8_tasks.json` and
`analysis/batch8_dispositions.json`; `scripts/mr_integrity.py` (`9419bfdbdb89…`) resolves C10i ids by `fixture_key` and
knows `MR_batch8_*` plans; `scripts/mr3_report.py` (`e7e1fd85af27…`) reports the cell with a `batch` column.
Dispositions by `batch8_prep/make_dispositions.py` (a copy of batch 7's with the batch-8 file names).

**4. KPI and reading (descriptive; the batch-3 thresholds are reported as a secondary reading as in batches 4–6).** Primary: ACCEPTED
batch-8 instances with at least one shift in 5 valid runs, over instances with a distinct facade (effective reuse recorded on the facade
chosen). Secondary: all ACCEPTED; per project; per host regime; per facade variant; and the C10i cell as a whole (batches 7 + 8) beside
C10 and C10f. Comparison with the static cells is descriptive (different bugs); the paired comparison stays batch 7's.

## Candidates (97)

Batch-8 order = ranks 210–306, by project and bug id. 62 have a planned-distinct facade; 35 plan a facade already planned by an
earlier task (recorded; the builder may choose another allowed candidate). Best-candidate variants: {'V1': 84, 'V0': 13}. Host regimes:
{'1500': 48, 'largest5': 49}; the smallest largest5 fifth host has 286 lines, the median 725. Task file `main-run/batch8_tasks.json`
(sha256 `2057de7498a5…`); construction in two interleaved halves (`half` a/b) only if disk requires it.

| Project | Candidates | of which largest5 |
|---|---|---|
| Chart | 8 | 0 |
| Cli | 5 | 5 |
| Collections | 7 | 7 |
| Compress | 10 | 10 |
| Gson | 3 | 3 |
| JacksonCore | 3 | 0 |
| JacksonDatabind | 13 | 1 |
| JacksonXml | 2 | 2 |
| Jsoup | 14 | 14 |
| Lang | 7 | 0 |
| Math | 24 | 7 |
| Time | 1 | 0 |

| Rank | Task | Regime | Host lines (hop 1 → 5) | Allowed instance facades | Planned reuse of |
|---|---|---|---|---|---|
| 210 | Chart-5__i | 1500 | seeded draw | XYSeries.indexOf (V1, 13 lines) / XYSeries.add (V2, 48 lines) / XYSeries.addOrUpdate (V2, 40 lines) | — |
| 211 | Chart-8__i | 1500 | seeded draw | Week.next (V1, 25 lines) / Week.previous (V1, 21 lines) | — |
| 212 | Chart-14__i | 1500 | seeded draw | CategoryPlot.getRendererForDataset (V1, 9 lines) / XYPlot.getLegendItems (V2, 29 lines) / CategoryPlot.getLegendItems (V2, 24 lines) | — |
| 213 | Chart-16__i | 1500 | seeded draw | DefaultIntervalCategoryDataset.getSeriesIndex (V1, 9 lines) / DefaultIntervalCategoryDataset.getCategoryIndex (V1, 9 lines) / DefaultIntervalCategoryDataset.getColumnKeys (V1, 10 lines) | — |
| 214 | Chart-18__i | 1500 | seeded draw | DefaultKeyedValues2D.getValue (V1, 13 lines) / DefaultKeyedValues.getIndex (V1, 9 lines) / DefaultKeyedValues2D.removeColumn (V1, 16 lines) | — |
| 215 | Chart-19__i | 1500 | seeded draw | CategoryPlot.getRendererForDataset (V1, 9 lines) / CategoryPlot.getLegendItems (V2, 24 lines) / CategoryPlot.addDomainMarker (V2, 28 lines) | Chart-14__i |
| 216 | Chart-21__i | 1500 | seeded draw | DefaultBoxAndWhiskerCategoryDataset.getMeanValue (V1, 10 lines) / DefaultBoxAndWhiskerCategoryDataset.getMeanValue (V1, 8 lines) / DefaultBoxAndWhiskerCategoryDataset.getMedianValue (V1, 8 lines) | — |
| 217 | Chart-22__i | 1500 | seeded draw | KeyedObjects2D.getObject (V1, 25 lines) / KeyedObjects2D.setObject (V1, 25 lines) / KeyedObjects2D.getObject (V1, 13 lines) | — |
| 218 | Cli-13__i | largest5 | 638, 517, 456, 308, 286 | WriteableCommandLineImpl.getValues (V1, 21 lines) / WriteableCommandLineImpl.getSwitch (V1, 16 lines) / ArgumentImpl.validate (V1, 22 lines) | — |
| 219 | Cli-14__i | largest5 | 638, 456, 375, 308, 286 | GroupImpl.canProcess (V1, 33 lines) / GroupImpl.validate (V2, 45 lines) / GroupImpl.helpLines (V2, 38 lines) | — |
| 220 | Cli-15__i | largest5 | 638, 514, 456, 375, 308 | WriteableCommandLineImpl.getValues (V1, 28 lines) / WriteableCommandLineImpl.getSwitch (V1, 16 lines) / WriteableCommandLineImpl.toString (V1, 19 lines) | Cli-13__i |
| 221 | Cli-16__i | largest5 | 638, 456, 375, 308, 286 | WriteableCommandLineImpl.getValues (V1, 28 lines) / GroupImpl.canProcess (V1, 33 lines) / WriteableCommandLineImpl.getSwitch (V1, 16 lines) | Cli-13__i |
| 222 | Cli-21__i | largest5 | 638, 546, 456, 375, 308 | WriteableCommandLineImpl.getValues (V1, 28 lines) / WriteableCommandLineImpl.getSwitch (V1, 16 lines) / WriteableCommandLineImpl.toString (V1, 19 lines) | Cli-13__i |
| 223 | Collections-1__i | largest5 | 2084, 1994, 1685, 1644, 1467 | Flat3Map.get (V1, 29 lines) / Flat3Map.containsKey (V1, 27 lines) / Flat3Map.containsValue (V1, 24 lines) | — |
| 224 | Collections-2__i | largest5 | 2084, 1994, 1644, 1467, 1332 | ExtendedProperties.getInclude (V1, 8 lines) | Collections-13__i |
| 225 | Collections-6__i | largest5 | 2085, 1995, 1717, 1645, 1468 | Flat3Map.get (V1, 29 lines) / Flat3Map.containsKey (V1, 27 lines) / Flat3Map.containsValue (V1, 24 lines) | Collections-1__i |
| 226 | Collections-7__i | largest5 | 2085, 1995, 1645, 1468, 1333 | ExtendedProperties.getInclude (V1, 8 lines) | Collections-2__i, Collections-13__i |
| 227 | Collections-8__i | largest5 | 2085, 1995, 1769, 1645, 1468 | UnboundedFifoBuffer.size (V1, 10 lines) | — |
| 228 | Collections-9__i | largest5 | 2085, 1995, 1645, 1468, 1333 | ExtendedProperties.getInclude (V1, 8 lines) | Collections-2__i, Collections-13__i |
| 229 | Collections-12__i | largest5 | 2085, 1995, 1678, 1468, 1333 | ExtendedProperties.getInclude (V1, 8 lines) | Collections-2__i, Collections-13__i |
| 230 | Compress-11__i | largest5 | 1886, 1495, 1048, 969, 919 | ArchiveStreamFactory.createArchiveInputStream (V0, 32 lines) / ArchiveStreamFactory.createArchiveOutputStream (V0, 26 lines) | — |
| 231 | Compress-13__i | largest5 | 1886, 1495, 1048, 969, 926 | ZipArchiveEntry.getExtraFields (V1, 12 lines) / ZipArchiveEntry.setUnixMode (V2, 9 lines) | — |
| 232 | Compress-15__i | largest5 | 1495, 1340, 1056, 1053, 972 | ZipArchiveEntry.getExtraFields (V1, 12 lines) / ZipArchiveEntry.setUnixMode (V2, 9 lines) | Compress-13__i |
| 233 | Compress-16__i | largest5 | 1495, 1340, 1071, 1053, 972 | ArchiveStreamFactory.createArchiveInputStream (V0, 32 lines) / ArchiveStreamFactory.createArchiveOutputStream (V0, 26 lines) | Compress-11__i |
| 234 | Compress-19__i | largest5 | 1503, 1340, 1092, 1064, 1053 | Zip64ExtendedInformationExtraField.getCentralDirectoryLength (V1, 5 lines) | — |
| 235 | Compress-29__i | largest5 | 1613, 1329, 1121, 1082, 1073 | ArchiveStreamFactory.createArchiveOutputStream (V1, 45 lines) | — |
| 236 | Compress-33__i | largest5 | 1613, 1329, 1121, 1120, 1082 | CompressorStreamFactory.createCompressorOutputStream (V0, 35 lines) / CompressorStreamFactory.createCompressorInputStream (V1, 50 lines) | — |
| 237 | Compress-34__i | largest5 | 1623, 1329, 1129, 1124, 1104 | X7875_NewUnix.hashCode (V1, 8 lines) | — |
| 238 | Compress-42__i | largest5 | 1649, 1334, 1259, 1252, 1131 | ZipArchiveEntry.getExtraField (V1, 9 lines) / ZipArchiveEntry.setUnixMode (V2, 9 lines) / ZipArchiveEntry.hashCode (V2, 6 lines) | — |
| 239 | Compress-46__i | largest5 | 1687, 1405, 1334, 1258, 1136 | X5455_ExtendedTimestamp.hashCode (V1, 14 lines) / X5455_ExtendedTimestamp.getLocalFileDataLength (V1, 6 lines) / X5455_ExtendedTimestamp.getLocalFileDataData (V2, 20 lines) | — |
| 240 | Gson-4__i | largest5 | 1617, 981, 928, 864, 630 | JsonWriter.name (V1, 12 lines) / JsonWriter.close (V1, 8 lines) | — |
| 241 | Gson-9__i | largest5 | 1625, 966, 924, 864, 630 | JsonWriter.name (V1, 12 lines) / JsonWriter.close (V1, 8 lines) | Gson-4__i |
| 242 | Gson-15__i | largest5 | 1617, 989, 906, 864, 630 | JsonWriter.name (V1, 12 lines) / JsonWriter.close (V1, 8 lines) | Gson-4__i |
| 243 | JacksonCore-4__i | 1500 | seeded draw | TextBuffer.contentsAsString (V1, 37 lines) / TextBuffer.expandCurrentSegment (V1, 11 lines) / TextBuffer.size (V1, 12 lines) | — |
| 244 | JacksonCore-8__i | 1500 | seeded draw | TextBuffer.contentsAsString (V1, 37 lines) / TextBuffer.expandCurrentSegment (V1, 11 lines) / TextBuffer.size (V1, 12 lines) | JacksonCore-4__i |
| 245 | JacksonCore-23__i | 1500 | seeded draw | DefaultPrettyPrinter.writeEndObject (V1, 11 lines) / DefaultPrettyPrinter.writeEndArray (V1, 11 lines) / DefaultPrettyPrinter.createInstance (V2, 6 lines) | — |
| 246 | JacksonDatabind-11__i | 1500 | seeded draw | TypeFactory.moreSpecificType (V0, 18 lines) / TypeFactory.findTypeParameters (V2, 28 lines) / TypeFactory.constructParametrizedType (V2, 28 lines) | — |
| 247 | JacksonDatabind-17__i | largest5 | 1793, 1622, 1588, 1486, 1156 | ObjectMapper.setMixInAnnotations (V1, 8 lines) / ObjectMapper.treeToValue (V2, 15 lines) / ObjectMapper.valueToTree (V2, 15 lines) | — |
| 248 | JacksonDatabind-19__i | 1500 | seeded draw | TypeFactory.moreSpecificType (V0, 18 lines) / TypeFactory.findTypeParameters (V2, 28 lines) / TypeFactory.constructParametrizedType (V2, 28 lines) | JacksonDatabind-11__i |
| 249 | JacksonDatabind-20__i | 1500 | seeded draw | ObjectNode.serialize (V1, 14 lines) / ObjectNode.findValuesAsText (V1, 14 lines) / ObjectNode.findValues (V1, 13 lines) | — |
| 250 | JacksonDatabind-21__i | 1500 | seeded draw | JacksonAnnotationIntrospector.findEnumValue (V0, 19 lines) | — |
| 251 | JacksonDatabind-33__i | 1500 | seeded draw | JacksonAnnotationIntrospector.findEnumValue (V0, 23 lines) | JacksonDatabind-21__i |
| 252 | JacksonDatabind-41__i | 1500 | seeded draw | TypeFactory.moreSpecificType (V0, 18 lines) | JacksonDatabind-11__i |
| 253 | JacksonDatabind-61__i | 1500 | seeded draw | StdTypeResolverBuilder.typeProperty (V1, 7 lines) / ObjectMapper.treeToValue (V2, 25 lines) / ObjectMapper.enableDefaultTyping (V2, 14 lines) | — |
| 254 | JacksonDatabind-79__i | 1500 | seeded draw | JacksonAnnotationIntrospector.findEnumValue (V0, 23 lines) / JacksonAnnotationIntrospector.findEnumValues (V0, 30 lines) | JacksonDatabind-21__i |
| 255 | JacksonDatabind-81__i | 1500 | seeded draw | JacksonAnnotationIntrospector.findEnumValues (V0, 30 lines) | — |
| 256 | JacksonDatabind-86__i | 1500 | seeded draw | ResolvedRecursiveType.toString (V1, 11 lines) | — |
| 257 | JacksonDatabind-95__i | 1500 | seeded draw | TypeFactory.moreSpecificType (V0, 18 lines) | JacksonDatabind-11__i |
| 258 | JacksonDatabind-97__i | 1500 | seeded draw | POJONode.serialize (V1, 11 lines) / POJONode.toString (V1, 10 lines) | — |
| 259 | JacksonXml-1__i | largest5 | 1143, 815, 529, 515, 395 | FromXmlParser.getCurrentName (V1, 15 lines) / FromXmlParser.getText (V2, 13 lines) | — |
| 260 | JacksonXml-3__i | largest5 | 1151, 817, 529, 515, 395 | FromXmlParser.getCurrentName (V1, 15 lines) / FromXmlParser.getText (V2, 13 lines) | JacksonXml-1__i |
| 261 | Jsoup-22__i | largest5 | 2306, 658, 615, 536, 454 | Element.children (V1, 8 lines) / Element.textNodes (V1, 7 lines) / Element.dataNodes (V1, 7 lines) | — |
| 262 | Jsoup-32__i | largest5 | 687, 636, 540, 463, 454 | Element.children (V1, 8 lines) / Element.textNodes (V1, 7 lines) / Element.dataNodes (V1, 7 lines) | Jsoup-22__i |
| 263 | Jsoup-37__i | largest5 | 706, 701, 667, 561, 464 | Element.children (V1, 8 lines) / Element.textNodes (V1, 7 lines) / Element.dataNodes (V1, 7 lines) | Jsoup-22__i |
| 264 | Jsoup-41__i | largest5 | 912, 706, 692, 635, 503 | Element.children (V1, 8 lines) / Element.textNodes (V1, 7 lines) / Element.dataNodes (V1, 7 lines) | Jsoup-22__i |
| 265 | Jsoup-42__i | largest5 | 1189, 912, 706, 687, 635 | FormElement.formData (V1, 34 lines) | — |
| 266 | Jsoup-43__i | largest5 | 912, 706, 687, 635, 565 | Element.children (V1, 8 lines) / Element.textNodes (V1, 7 lines) / Element.dataNodes (V1, 7 lines) | Jsoup-22__i |
| 267 | Jsoup-48__i | largest5 | 1221, 706, 703, 679, 635 | HttpConnection.data (V1, 11 lines) | — |
| 268 | Jsoup-57__i | largest5 | 1260, 1033, 729, 706, 695 | Attributes.asList (V1, 9 lines) / Attributes.hasKeyIgnoreCase (V1, 8 lines) / Attributes.getIgnoreCase (V1, 10 lines) | — |
| 269 | Jsoup-61__i | largest5 | 1114, 750, 706, 703, 644 | Element.hasClass (V1, 41 lines) / Element.children (V1, 8 lines) / Element.textNodes (V1, 7 lines) | — |
| 270 | Jsoup-66__i | largest5 | 1204, 753, 725, 714, 646 | Element.textNodes (V1, 7 lines) / Element.dataNodes (V1, 7 lines) / Element.hasText (V1, 13 lines) | — |
| 271 | Jsoup-69__i | largest5 | 1430, 1249, 753, 734, 725 | FormElement.formData (V1, 34 lines) | Jsoup-42__i |
| 272 | Jsoup-70__i | largest5 | 1249, 753, 734, 725, 646 | Element.textNodes (V1, 7 lines) / Element.dataNodes (V1, 7 lines) / Element.hasText (V1, 13 lines) | Jsoup-66__i |
| 273 | Jsoup-90__i | largest5 | 1497, 778, 733, 725, 643 | HttpConnection.data (V1, 11 lines) | Jsoup-48__i |
| 274 | Jsoup-93__i | largest5 | 1524, 1205, 778, 741, 725 | FormElement.formData (V1, 36 lines) | Jsoup-42__i |
| 275 | Lang-4__i | 1500 | seeded draw | LookupTranslator.translate (V1, 15 lines) | — |
| 276 | Lang-28__i | 1500 | seeded draw | NumericEntityUnescaper.translate (V0, 38 lines) | — |
| 277 | Lang-47__i | 1500 | seeded draw | StrBuilder.endsWith (V1, 18 lines) / StrBuilder.lastIndexOf (V1, 13 lines) / StrBuilder.lastIndexOf (V1, 11 lines) | — |
| 278 | Lang-55__i | 1500 | seeded draw | StopWatch.getTime (V1, 11 lines) | — |
| 279 | Lang-59__i | 1500 | seeded draw | StrBuilder.endsWith (V1, 18 lines) / StrBuilder.lastIndexOf (V1, 13 lines) / StrBuilder.lastIndexOf (V1, 11 lines) | Lang-47__i |
| 280 | Lang-60__i | 1500 | seeded draw | StrBuilder.endsWith (V1, 18 lines) / StrBuilder.lastIndexOf (V1, 13 lines) / StrBuilder.lastIndexOf (V1, 11 lines) | Lang-47__i |
| 281 | Lang-61__i | 1500 | seeded draw | StrBuilder.endsWith (V1, 18 lines) / StrBuilder.lastIndexOf (V1, 13 lines) / StrBuilder.lastIndexOf (V1, 11 lines) | Lang-47__i |
| 282 | Math-4__i | 1500 | seeded draw | SubLine.getSegments (V1, 13 lines) / SubLine.split (V2, 33 lines) / SubLine.intersection (V2, 24 lines) | — |
| 283 | Math-8__i | 1500 | seeded draw | DiscreteDistribution.sample (V1, 15 lines) / DiscreteDistribution.sample (V2, 14 lines) | — |
| 284 | Math-17__i | 1500 | seeded draw | Dfp.log10 (V1, 11 lines) / Dfp.negativeOrNull (V2, 10 lines) / Dfp.strictlyNegative (V2, 10 lines) | — |
| 285 | Math-22__i | 1500 | seeded draw | FDistribution.cumulativeProbability (V1, 13 lines) / FDistribution.getNumericalMean (V2, 8 lines) | — |
| 286 | Math-26__i | 1500 | seeded draw | Fraction.toString (V1, 10 lines) / Fraction.abs (V2, 8 lines) | — |
| 287 | Math-27__i | 1500 | seeded draw | Fraction.toString (V1, 10 lines) / Fraction.abs (V2, 8 lines) | Math-26__i |
| 288 | Math-34__i | 1500 | seeded draw | ListPopulation.getFittestChromosome (V1, 10 lines) / ListPopulation.setPopulationLimit (V1, 8 lines) | — |
| 289 | Math-43__i | 1500 | seeded draw | SummaryStatistics.addValue (V1, 19 lines) / SummaryStatistics.hashCode (V2, 11 lines) / SummaryStatistics.getStandardDeviation (V2, 10 lines) | — |
| 290 | Math-49__i | 1500 | seeded draw | OpenMapRealVector.hashCode (V1, 14 lines) / OpenMapRealVector.outerProduct (V1, 13 lines) / OpenMapRealVector.mapAddToSelf (V2, 5 lines) | — |
| 291 | Math-52__i | 1500 | seeded draw | Rotation.getMatrix (V1, 34 lines) / Rotation.applyInverseTo (V1, 13 lines) / Rotation.applyTo (V1, 12 lines) | — |
| 292 | Math-54__i | largest5 | 4047, 2326, 1547, 1532, 1300 | Dfp.log10 (V1, 11 lines) | — |
| 293 | Math-56__i | 1500 | seeded draw | MultidimensionalCounter.getCounts (V1, 24 lines) / MultidimensionalCounter.getCount (V1, 14 lines) | — |
| 294 | Math-60__i | 1500 | seeded draw | NormalDistributionImpl.cumulativeProbability (V1, 7 lines) / NormalDistributionImpl.density (V1, 4 lines) | — |
| 295 | Math-61__i | 1500 | seeded draw | PoissonDistributionImpl.cumulativeProbability (V1, 8 lines) | — |
| 296 | Math-69__i | largest5 | 1833, 1687, 1667, 1506, 1239 | PearsonsCorrelation.correlation (V0, 13 lines) / PearsonsCorrelation.getCorrelationPValues (V1, 16 lines) / PearsonsCorrelation.getCorrelationStandardErrors (V1, 10 lines) | — |
| 297 | Math-75__i | 1500 | seeded draw | Frequency.addValue (V1, 18 lines) / Frequency.getCount (V2, 14 lines) / Frequency.addValue (V2, 8 lines) | — |
| 298 | Math-76__i | 1500 | seeded draw | SingularValueDecompositionImpl.getS (V1, 10 lines) / SingularValueDecompositionImpl.getCovariance (V2, 27 lines) / SingularValueDecompositionImpl.getVT (V2, 10 lines) | — |
| 299 | Math-77__i | 1500 | seeded draw | ArrayRealVector.mapAddToSelf (V1, 5 lines) / ArrayRealVector.mapSubtractToSelf (V1, 5 lines) / ArrayRealVector.mapMultiplyToSelf (V1, 5 lines) | — |
| 300 | Math-86__i | 1500 | seeded draw | CholeskyDecompositionImpl.getDeterminant (V1, 7 lines) / CholeskyDecompositionImpl.getLT (V1, 9 lines) | — |
| 301 | Math-89__i | largest5 | 1836, 1638, 1514, 1450, 1411 | Frequency.addValue (V1, 16 lines) / Frequency.getCount (V2, 14 lines) / Frequency.addValue (V2, 6 lines) | Math-75__i |
| 302 | Math-90__i | largest5 | 1836, 1638, 1514, 1450, 1411 | Frequency.addValue (V1, 16 lines) / Frequency.getCount (V2, 14 lines) | Math-75__i |
| 303 | Math-98__i | largest5 | 1059, 1057, 1041, 1020, 877 | BigMatrixImpl.getSubMatrix (V1, 17 lines) / RealMatrixImpl.getSubMatrix (V1, 17 lines) / BigMatrixImpl.getSubMatrix (V1, 21 lines) | — |
| 304 | Math-103__i | largest5 | 1319, 1069, 1036, 1019, 1016 | NormalDistributionImpl.cumulativeProbability (V1, 13 lines) | Math-60__i |
| 305 | Math-105__i | largest5 | 1318, 1053, 1035, 807, 688 | SimpleRegression.getSlope (V1, 8 lines) | — |
| 306 | Time-4__i | 1500 | seeded draw | Partial.isMatch (V1, 11 lines) / Partial.isMatch (V1, 10 lines) | — |

Expected: UNBUILDABLE outcomes of the batch-5/6/7 kinds (no single-trigger omission; no existing test reaches the facade despite the strict
name check, the overload false positive of Lang-38; nothing to split); JacksonXml and the non-harness Chart bugs are first attempts in
those projects, and a staging failure (G13/G14) is recorded as UNBUILDABLE with its reason.

**Key preflight.** Before any batch-8 builder starts, the coordinator asserts for all 97 keys that no `designs/<key>__i.py`,
`specs/MI-<key>.json`, `instances/MI-<key>/`, `audits/MI-<key>.json` or `history/<key>__i/` exists, that every fixture exists with `.git`, and
that none of the keys appears in the batch-1 to batch-7 task files.

## Cost guard

`mr_cost_guard.py --cap 600`, re-run before every block by `mr_run_blocks.sh`; blocks of at most 5 in batch-8 order; plans
`plans/MR_batch8_block<N>_gpt55.json`. Expected run cost about 97 × 5 × $0.42 ≈ $204 if every candidate were built; with the
batch-7 yield (17 of 19) about $182; with the batch-6 yield (38 of 62) about $125.

## Integrity

1. The batch-1/2, 3, 4, 5, 6 manifests as before; the batch-7 manifest (`b7_integrity_manifest.json`) recorded after the batch-7 runs and
   before any batch-8 row.
2. `mr_integrity.py --verify-frozen batch8_frozen_hashes.json`, written before any batch-8 build: every `mr_*`, `mr2_*` and `mr3_*` script,
   the briefs, the checklist, the addenda and this note, this document, `batch8_tasks.json`, `batch8_checkouts.log`, the batch-1–7 task
   files and dispositions, the pool files, the manifests, the other servers' ledgers, and `AMENDMENTS.md` through W56 as a pinned prefix.

## Outputs

`main-run/batch8_tasks.json`, `batch8_checkouts.log`, `batch8_build_audit_results.json`; `analysis/batch8_dispositions.json`,
`batch8_trace_checks.json`, `batch8_trace_robustness.json`, `batch8_prediction.json` (`mr_batch3_eval.py --batch batch8`, reading the C10i
results file), `batch8_frozen_hashes.json`; rows in `INSTANCE_BUILD_LOG_C10I.csv` / `INSTANCE_PROVENANCE_C10I.csv`; the `mr3_report.py`
files; `SUPERVISOR_PROGRESS_UPDATE.md` as update 8.
