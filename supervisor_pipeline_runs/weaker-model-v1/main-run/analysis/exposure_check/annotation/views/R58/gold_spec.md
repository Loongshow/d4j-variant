# Run R58: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.compress.archivers.zip.ZipFile::encodeOctal`
- Gold file in the workspace: `src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java` (lines 167–181)
- Method the failing test calls (facade): `org.apache.commons.compress.archivers.tar.TarUtils::formatOctalBytes`
- Failing test: `org.apache.commons.compress.archivers.tar.TarUtilsTest::testTrailers`
- Text removed from the gold (the omission): `int pos = offset;         for (int k = length - digits; k > 0; k--) {             buf[pos++] = (byte) '0';         }         for (int bit = 3 * (digits - 1); bit >= 0; bit -= 3) {`
- The same place in the variant now reads: `int pos = offset;         for (int bit = 3 * (digits - 1); bit >= 0; bit -= 3) {`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  167        public static int encodeOctal(final long value, final byte[] buf, final int offset, final int length) {
  168            int digits = 1;
  169            for (long rest = value >>> 3; rest != 0; rest >>>= 3) {
  170                digits++;
  171            }
  172            if (digits > length) {
  173                throw new IllegalArgumentException(value + "=" + Long.toOctalString(value)
  174                        + " will not fit in octal number buffer of length " + length);
  175            }
  176 >>         int pos = offset;
  177 >>         for (int bit = 3 * (digits - 1); bit >= 0; bit -= 3) {
  178                buf[pos++] = (byte) ('0' + (int) ((value >>> bit) & 7));
  179            }
  180            return offset + length;
  181        }
```
