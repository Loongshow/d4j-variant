# Run R04: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.compress.archivers.sevenz.SevenZFile::isDirectoryByHeader`
- Gold file in the workspace: `src/main/java/org/apache/commons/compress/archivers/sevenz/SevenZFile.java` (lines 154–159)
- Method the failing test calls (facade): `org.apache.commons.compress.archivers.tar.TarArchiveEntry::isDirectory`
- Failing test: `org.apache.commons.compress.archivers.tar.TarArchiveInputStreamTest::survivesPaxHeaderWithNameEndingInSlash`
- Text removed from the gold (the omission): `return !entry.isPaxHeader() && !entry.isGlobalPaxHeader() && entry.getName().endsWith("/");`
- The same place in the variant now reads: `return entry.getName().endsWith("/");`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  154        public static boolean isDirectoryByHeader(final TarArchiveEntry entry, final byte flag) {
  155            if (flag == TarConstants.LF_DIR) {
  156                return true;
  157            }
  158 >>         return entry.getName().endsWith("/");
  159        }
```
