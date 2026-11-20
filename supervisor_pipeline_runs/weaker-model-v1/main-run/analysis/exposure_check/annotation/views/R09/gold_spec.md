# Run R09: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.compress.archivers.tar.TarArchiveEntry::appendEntryName`
- Gold file in the workspace: `src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java` (lines 390–395)
- Method the failing test calls (facade): `org.apache.commons.compress.archivers.tar.TarUtils::parseName`
- Failing test: `org.apache.commons.compress.archivers.tar.TarUtilsTest::testName`
- Text removed from the gold (the omission): `for (int i = offset; entryName.length() < entryName.capacity() && header[i] != 0; ++i) {`
- The same place in the variant now reads: `for (int i = offset; header[i] != 0; ++i) {`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  390        public static void appendEntryName(final StringBuffer entryName, final byte[] header,
  391                                           final int offset) {
  392 >>         for (int i = offset; header[i] != 0; ++i) {
  393                entryName.append((char) (header[i] & 0xFF));
  394            }
  395        }
```
