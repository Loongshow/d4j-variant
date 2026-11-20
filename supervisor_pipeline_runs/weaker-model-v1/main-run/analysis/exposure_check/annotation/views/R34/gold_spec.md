# Run R34: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream::endPositions`
- Gold file in the workspace: `src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorInputStream.java` (lines 389–398)
- Method the failing test calls (facade): `org.apache.commons.compress.archivers.zip.Zip64ExtendedInformationExtraField::getCentralDirectoryLength`
- Failing test: `org.apache.commons.compress.archivers.zip.Zip64ExtendedInformationExtraFieldTest::testWriteCDSizeAndDisk`
- Text removed from the gold (the omission): `end += present ? (i < 3 ? 8 : 4) : 0;`
- The same place in the variant now reads: `end += i < 3 ? 8 : 4;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  389        public static int[] endPositions(final Object[] fields) {
  390            final int[] ends = new int[fields.length];
  391            int end = 0;
  392            for (int i = 0; i < fields.length; i++) {
  393                final boolean present = fields[i] != null;
  394 >>             end += i < 3 ? 8 : 4;
  395                ends[i] = present ? end : -1;
  396            }
  397            return ends;
  398        }
```
