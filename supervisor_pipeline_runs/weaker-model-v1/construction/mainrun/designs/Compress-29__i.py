"""Main run Compress-29__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Compress-29, a bug with no static facade; the real bug modified ArchiveStreamFactory, the facade's class, among others). No static pair
(B8 note section 1).

Facade: ArchiveStreamFactory.createArchiveOutputStream(String, OutputStream) (instance method; the only allowed candidate,
BATCH8_PREREGISTRATION.md row 235; facade_planned_by null, no facade reuse). Original computation: a null archiver name or a null
stream is an IllegalArgumentException with its message; otherwise the name is compared, ignoring case, with ar, zip, tar, jar and cpio:
ar gives an ArArchiveOutputStream; zip a ZipArchiveOutputStream on which setEncoding(entryEncoding) is called when the factory's entry
encoding is not null; tar, jar and cpio the stream class's (out, entryEncoding) constructor when the entry encoding is not null and its
(out) constructor otherwise, so that a factory without an entry encoding gets each archiver's own default; 7z is a
StreamingNotSupportedException("7z"); any other name an ArchiveException "Archiver: <name> not found.".

facade_variant: V1 (state as parameters). state_passed: the private volatile field entryEncoding (read once in the facade) is handed to
hop 1 together with the archiver name and the stream; no field is written, no write-back. The facade body is the original two argument
guards plus one call to hop 1. No visibility is widened, no type is added, no signature, modifier, override or throws clause changes, no
reflection, no test edit. The facade calls no private method, so V4 does not apply; every type the chain names is public (V2/V3/V5 not
needed). The original imports of ArchiveStreamFactory are left as they are.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Compress-29-probe/w of the fixture, the first statement
of createArchiveOutputStream was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.apache.commons.compress.archivers.ArchiveStreamFactoryTest::testEncodingOutputStream`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at ArchiveStreamFactory.createArchiveOutputStream(ArchiveStreamFactory.java:272), called
from ArchiveStreamFactoryTest.getOutputStreamFor (line 402) from testEncodingOutputStream (line 329). The facade is reached by the
trigger.

Redistribution of the computation (a chain of responsibility over the archiver names; each format's stream is created by exactly one
step, and that step applies the factory's entry encoding to it):
  hop 1 archivers.zip.ZipArchiveOutputStream             1613 lines  createArchiveStream  zip and jar: the ZIP-family stream, with
                                                                                          setEncoding when the factory has an entry
                                                                                          encoding; other names passed on
  hop 2 compressors.bzip2.BZip2CompressorOutputStream    1329 lines  openArchiveStream    ar (no entry encoding); other names passed on
  hop 3 archivers.zip.ZipFile                            1121 lines  newArchiveStream     7z rejected (StreamingNotSupportedException);
                                                                                          other names passed on
  hop 4 archivers.zip.ZipArchiveInputStream              1082 lines  archiveStreamFor     tar or cpio selected, any other name is the
                                                                                          "not found" ArchiveException
  hop 5 archivers.tar.TarArchiveEntry                    1073 lines  blockArchiveStream   GOLD: creates the tar or cpio stream with the
                                                                                          factory's entry encoding (a factory without
                                                                                          one gets the archiver's own default stream)
host_mode = "largest5" (batch8_tasks.json hosts_hop_order, used in that order, none substituted). Host newline counts 1613, 1329, 1121,
1082, 1073; the smallest host (and the gold host) has 1073 lines (C10F addendum section 1: hosts under 1500 lines are expected here).
The correct configuration returns, for every input, a stream of the same class built with the same arguments as the original (jar:
new JarArchiveOutputStream(out) followed by setEncoding(encoding) is exactly what JarArchiveOutputStream(out, encoding) does), the same
exceptions with the same messages, and checks the names in a different order (the names are distinct, so the order cannot matter).

Fault (omission of a special-case decision in the gold): the branch that gives a factory without an entry encoding the archiver's own
default stream is dropped (`if (encoding == null) { return tar ? new TarArchiveOutputStream(out) : new CpioArchiveOutputStream(out); }`),
so the encoding constructor is always used and a null entry encoding is handed to it. For tar this changes nothing
(TarArchiveOutputStream(out) is TarArchiveOutputStream(out, null)); for cpio, CpioArchiveOutputStream(out) uses US-ASCII for file names
while CpioArchiveOutputStream(out, null) uses the platform's default. The gold then reads as the ordinary routine "create the stream
with the given entry encoding". Trigger: the EXISTING test ArchiveStreamFactoryTest::testEncodingOutputStream; for its row 6 (cpio,
FACTORY = new ArchiveStreamFactory()) the stream's encoding is null instead of CPIO_DEFAULT (US-ASCII), and the test fails with
"Tests failed: 1" (stdout: "Failed test 6. expected: US-ASCII actual: null type: cpio"). It is the only test that inspects the encoding
of a created output stream; every other output test writes ASCII names, which the platform default writes identically. The behaviour was
checked before designing on a scratch copy with the original cpio null branch removed: full suite, 1 failing test
(testEncodingOutputStream); gate G5 checks the full suite on the variant.

The gold's javadoc states the idiomatic contract (it creates the stream "with the entry encoding of an archive stream factory", the
encoding "as ArchiveStreamFactory#getEntryEncoding() returns it") and is silent on the absent encoding. For a factory the absent
encoding means the archiver default (getEntryEncoding: "or null for the archiver default"; setEntryEncoding: "Use null for the archiver
default"), and the cpio archiver default is ASCII (CpioArchiveOutputStream(out): "using ASCII encoding for file names"), so the variant's
cpio stream with the platform default violates the contract on the trigger input. The convention is pinned outside the gold: the intact
siblings ArchiveStreamFactory.createArchiveInputStream(String, InputStream) and createArchiveInputStream(InputStream) do the same step
for cpio (`if (entryEncoding != null) new CpioArchiveInputStream(in, entryEncoding) else new CpioArchiveInputStream(in)`, the ASCII
default) and for zip, jar, arj and dump; passing tests: ArchiveStreamFactoryTest::testEncodingInputStream and
::testEncodingInputStreamAutodetect (cpio with FACTORY expects US-ASCII on both input paths), ::cantWrite7zToStream (through the chain),
ExceptionMessageTest::testMessageWhenOutputStreamIsNull (the facade guard).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: tar selects the class in both returns; out is handed to every constructor; encoding decides the branch and is handed to
     the encoding constructors.
  T2 absent: no locals; the null branch and the final return build different streams for cpio (ASCII default versus the given
     encoding), so the decision is live; both ternaries have two different effects.
  T3 absent: tar and cpio (the pair named by @param tar) both get the absent-encoding branch and both get the encoding constructor; no
     class named in the gold's text is handled in part.
  T4 absent: 'a tar or a cpio archive' (both created), 'with the entry encoding of an archive stream factory' (the factory convention is
     met: the archiver's own default when it has none, its encoding otherwise), the @param/@return clauses are met.
 Variant gold (javadoc, signature, `return tar ? new TarArchiveOutputStream(out, encoding) : new CpioArchiveOutputStream(out,
 encoding);`):
  T1 absent: tar selects the class; out and encoding are handed to the constructor on both paths; none is only argument-checked.
  T2 absent: no locals at all; the ternary builds a tar or a cpio stream, two different effects; nothing is frozen or dead.
  T3 absent: tar and cpio get the same treatment (the encoding constructor with out and encoding); the gold has no null, default or
     special-encoding treatment for any member ('No member handled'); no format constant or enumeration is used, so no wider set is in
     the gold's text.
  T4 absent: 'a tar or a cpio archive' is met; 'with the entry encoding of an archive stream factory' and '@param encoding the entry
     encoding of the factory, as ... getEntryEncoding() returns it' are general descriptions that the body addresses (the value is
     handed to the constructor) and name no concrete rule, value class or case; no inline comment; the identifiers (tar, out, encoding,
     blockArchiveStream) name nothing the body does not meet.

Single owner: each archiver's stream is created by exactly one step of the chain, and only the gold creates tar and cpio streams; hops
2, 3 and 4 pass the entry encoding on unchanged (as their javadoc says) and hop 1 applies it only to the zip and jar streams it creates.
A cpio stream's file-name encoding is fixed by its constructor (the field is final), so once the gold has built it with a null encoding
no caller can recover the ASCII default; a caller can avoid it only by handing the gold an encoding the factory does not hold (contrary
to the gold's and the hops' @param) or by creating the cpio stream itself. Declared alternatives (G9): hop 4 hands the gold US-ASCII for
an absent encoding (the tar default row then fails); hop 1 hands the rest of the chain UTF8 for an absent encoding; hop 2 passes the
archiver name in lower case. None makes the trigger pass.
Recorded bypasses (edits that replace the gold's choice with another implementation, not repairs of the chain; both checked at hop 4
on the variant in the scratch copy /private/tmp/d4j-mi-Compress-29-byp: trigger passes, full suite 0 failing tests):
 B-0 the facade (its original body) or hop 4 creates the cpio stream itself (`if (encoding == null && !tar) { return new
     CpioArchiveOutputStream(out); }`), discarding the gold's result for that input.
 B-1 hop 4 hands the gold US-ASCII for cpio only (`encoding != null || tar ? encoding : CharsetNames.US_ASCII`): a second
     implementation of the gold's per-archiver default, and the gold then receives an encoding the factory does not hold, contrary to
     the gold's @param ("the entry encoding of the factory, as getEntryEncoding() returns it") and hop 4's own javadoc.

Lie: the facade's javadoc claims the archiver name is converted to lower case and looked up in a table that maps each supported name to
its stream constructor; no step of the chain converts the name or uses a table (each step compares the name, ignoring case, with the
names it handles). It names neither the encoding nor any default nor any hop.

Anchors (stageB_lib.pick_anchor / host_search.pick_insertion_anchor with seed 7635 + 100 + i, as mr3_spec.py inserts them): see
host_notes."""

ASF = "src/main/java/org/apache/commons/compress/archivers/ArchiveStreamFactory.java"
ZAOS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveOutputStream.java"
BZOS = "src/main/java/org/apache/commons/compress/compressors/bzip2/BZip2CompressorOutputStream.java"
ZF = "src/main/java/org/apache/commons/compress/archivers/zip/ZipFile.java"
ZAIS = "src/main/java/org/apache/commons/compress/archivers/zip/ZipArchiveInputStream.java"
TAE = "src/main/java/org/apache/commons/compress/archivers/tar/TarArchiveEntry.java"

GOLD_TEXT = '''/**
 * Creates an archive output stream that writes a tar or a cpio
 * archive with the entry encoding of an archive stream factory.
 *
 * @param tar true for a tar archive, false for a cpio archive
 * @param out the output stream to write the archive to
 * @param encoding the entry encoding of the factory, as
 * {@link org.apache.commons.compress.archivers.ArchiveStreamFactory#getEntryEncoding()}
 * returns it
 * @return the archive output stream
 */
public static ArchiveOutputStream blockArchiveStream(final boolean tar, final OutputStream out,
                                                     final String encoding) {
    if (encoding == null) {
        return tar ? new TarArchiveOutputStream(out) : new CpioArchiveOutputStream(out);
    }
    return tar ? new TarArchiveOutputStream(out, encoding) : new CpioArchiveOutputStream(out, encoding);
}'''

HOP1 = '''/**
 * Creates an archive output stream for an archiver name.
 *
 * <p>Zip and jar archives are written by this class; the entry
 * encoding of the factory is set on the stream when the factory has
 * one. Any other archiver name is passed on together with the entry
 * encoding.</p>
 *
 * @param archiverName the archiver name, not null
 * @param out the output stream to write the archive to, not null
 * @param encoding the entry encoding of the factory
 * @return the archive output stream
 * @throws ArchiveException if the archiver name is not known
 */
public static ArchiveOutputStream createArchiveStream(final String archiverName, final OutputStream out,
                                                      final String encoding) throws ArchiveException {
    final boolean jar = ArchiveStreamFactory.JAR.equalsIgnoreCase(archiverName);
    if (!jar && !ArchiveStreamFactory.ZIP.equalsIgnoreCase(archiverName)) {
        return BZip2CompressorOutputStream.openArchiveStream(archiverName, out, encoding);
    }
    final ZipArchiveOutputStream zip = jar ? new JarArchiveOutputStream(out) : new ZipArchiveOutputStream(out);
    if (encoding != null) {
        zip.setEncoding(encoding);
    }
    return zip;
}'''

HOP2 = '''/**
 * Creates an archive output stream for an archiver name.
 *
 * <p>Ar archives, which have no entry encoding, are written directly;
 * any other archiver name is passed on together with the entry
 * encoding of the factory.</p>
 *
 * @param archiverName the archiver name, not null
 * @param out the output stream to write the archive to, not null
 * @param encoding the entry encoding of the factory
 * @return the archive output stream
 * @throws ArchiveException if the archiver name is not known
 */
public static ArchiveOutputStream openArchiveStream(final String archiverName, final OutputStream out,
                                                    final String encoding) throws ArchiveException {
    if (ArchiveStreamFactory.AR.equalsIgnoreCase(archiverName)) {
        return new ArArchiveOutputStream(out);
    }
    return ZipFile.newArchiveStream(archiverName, out, encoding);
}'''

HOP3 = '''/**
 * Creates an archive output stream for an archiver name.
 *
 * <p>The 7z format can only be written to a file and is rejected; any
 * other archiver name is passed on together with the entry encoding of
 * the factory.</p>
 *
 * @param archiverName the archiver name, not null
 * @param out the output stream to write the archive to, not null
 * @param encoding the entry encoding of the factory
 * @return the archive output stream
 * @throws StreamingNotSupportedException if the format cannot be
 * written to a stream
 * @throws ArchiveException if the archiver name is not known
 */
public static ArchiveOutputStream newArchiveStream(final String archiverName, final OutputStream out,
                                                   final String encoding) throws ArchiveException {
    if (ArchiveStreamFactory.SEVEN_Z.equalsIgnoreCase(archiverName)) {
        throw new StreamingNotSupportedException(ArchiveStreamFactory.SEVEN_Z);
    }
    return ZipArchiveInputStream.archiveStreamFor(archiverName, out, encoding);
}'''

HOP4 = '''/**
 * Creates an archive output stream for the tar or the cpio archiver
 * name.
 *
 * <p>The entry encoding is passed on as the factory holds it.</p>
 *
 * @param archiverName the archiver name, not null
 * @param out the output stream to write the archive to, not null
 * @param encoding the entry encoding of the factory
 * @return the archive output stream
 * @throws ArchiveException if the archiver name is neither tar nor
 * cpio
 */
public static ArchiveOutputStream archiveStreamFor(final String archiverName, final OutputStream out,
                                                   final String encoding) throws ArchiveException {
    final boolean tar = ArchiveStreamFactory.TAR.equalsIgnoreCase(archiverName);
    if (!tar && !ArchiveStreamFactory.CPIO.equalsIgnoreCase(archiverName)) {
        throw new ArchiveException("Archiver: " + archiverName + " not found.");
    }
    return TarArchiveEntry.blockArchiveStream(tar, out, encoding);
}'''

DESIGN = {
 "instance": "Compress-29", "project": "Compress", "bug_id": 29, "seed": 7635,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private volatile field entryEncoding, passed to hop 1 with archiverName and out; no write-back",
 "host_mode": "largest5", "host_lines": [1613, 1329, 1121, 1082, 1073],
 "reachability_probe": "createArchiveOutputStream first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Compress-29-probe/w: ArchiveStreamFactoryTest::testEncodingOutputStream fails with "
                       "PROBE-REACHED at ArchiveStreamFactory.createArchiveOutputStream(ArchiveStreamFactory.java:272)",
 "facade": {"file": ASF, "class": "org.apache.commons.compress.archivers.ArchiveStreamFactory",
            "method": "createArchiveOutputStream", "near_line": 269},
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/compress/archivers/ArchiveStreamFactoryTest.java",
             "test_class": "org.apache.commons.compress.archivers.ArchiveStreamFactoryTest",
             "test_method": "testEncodingOutputStream"},
 "expected_signature": "Tests failed: 1",
 "gold": {"method": "blockArchiveStream", "text": GOLD_TEXT,
          "fault": {"old": "        if (encoding == null) {\n"
                           "            return tar ? new TarArchiveOutputStream(out) : new CpioArchiveOutputStream(out);\n"
                           "        }\n"
                           "        return tar ? new TarArchiveOutputStream(out, encoding) : new CpioArchiveOutputStream(out, encoding);",
                    "new": "        return tar ? new TarArchiveOutputStream(out, encoding) : new CpioArchiveOutputStream(out, encoding);"}},
 "chain": {
   "facade_body": "if (archiverName == null) {\n"
                  "            throw new IllegalArgumentException(\"Archivername must not be null.\");\n"
                  "        }\n"
                  "        if (out == null) {\n"
                  "            throw new IllegalArgumentException(\"OutputStream must not be null.\");\n"
                  "        }\n"
                  "        return ZipArchiveOutputStream.createArchiveStream(archiverName, out, entryEncoding);",
   "lie": "The archiver name is converted to lower case and looked up in a table that maps each supported name to its "
          "stream constructor.",
   "hops": [
     {"file": ZAOS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream", "method": "createArchiveStream",
      "imports": ["org.apache.commons.compress.archivers.ArchiveException",
                  "org.apache.commons.compress.archivers.ArchiveStreamFactory",
                  "org.apache.commons.compress.archivers.jar.JarArchiveOutputStream",
                  "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream"], "text": HOP1},
     {"file": BZOS, "class": "org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream",
      "method": "openArchiveStream",
      "imports": ["org.apache.commons.compress.archivers.ArchiveException",
                  "org.apache.commons.compress.archivers.ArchiveOutputStream",
                  "org.apache.commons.compress.archivers.ArchiveStreamFactory",
                  "org.apache.commons.compress.archivers.ar.ArArchiveOutputStream",
                  "org.apache.commons.compress.archivers.zip.ZipFile"], "text": HOP2},
     {"file": ZF, "class": "org.apache.commons.compress.archivers.zip.ZipFile", "method": "newArchiveStream",
      "imports": ["java.io.OutputStream",
                  "org.apache.commons.compress.archivers.ArchiveException",
                  "org.apache.commons.compress.archivers.ArchiveOutputStream",
                  "org.apache.commons.compress.archivers.ArchiveStreamFactory",
                  "org.apache.commons.compress.archivers.StreamingNotSupportedException"], "text": HOP3},
     {"file": ZAIS, "class": "org.apache.commons.compress.archivers.zip.ZipArchiveInputStream", "method": "archiveStreamFor",
      "imports": ["java.io.OutputStream",
                  "org.apache.commons.compress.archivers.ArchiveException",
                  "org.apache.commons.compress.archivers.ArchiveOutputStream",
                  "org.apache.commons.compress.archivers.ArchiveStreamFactory",
                  "org.apache.commons.compress.archivers.tar.TarArchiveEntry"], "text": HOP4},
     {"file": TAE, "class": "org.apache.commons.compress.archivers.tar.TarArchiveEntry", "method": "blockArchiveStream",
      "imports": ["java.io.OutputStream",
                  "org.apache.commons.compress.archivers.ArchiveOutputStream",
                  "org.apache.commons.compress.archivers.cpio.CpioArchiveOutputStream"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.compress.archivers.ArchiveStreamFactory::createArchiveInputStream",
              "org.apache.commons.compress.archivers.ArchiveStreamFactory::getEntryEncoding",
              "org.apache.commons.compress.archivers.cpio.CpioArchiveOutputStream::CpioArchiveOutputStream"],
 "ownership_reason": "Each archiver's stream is created by exactly one step of the chain, and only the gold creates tar and cpio "
                     "streams; hops 2, 3 and 4 pass the factory's entry encoding on unchanged, as their javadoc says, and hop 1 "
                     "applies it only to the zip and jar streams it creates itself. The gold's javadoc promises a stream 'with the "
                     "entry encoding of an archive stream factory', the encoding 'as ArchiveStreamFactory#getEntryEncoding() "
                     "returns it'; for a factory, an absent entry encoding means the archiver default (getEntryEncoding: 'or null "
                     "for the archiver default'; setEntryEncoding: 'Use null for the archiver default'), and the cpio archiver "
                     "default is ASCII (CpioArchiveOutputStream(OutputStream): 'using ASCII encoding for file names'). The variant "
                     "gold always uses the encoding constructor, so a factory without an entry encoding gets a cpio stream with the "
                     "platform's default instead. A cpio stream's file-name encoding is fixed by its constructor, so no caller can "
                     "recover it after the gold returns. The convention is pinned outside the gold: the intact sibling factory "
                     "methods ArchiveStreamFactory.createArchiveInputStream(String, InputStream) and createArchiveInputStream("
                     "InputStream) create the cpio (and zip, jar, arj, dump) stream with the archiver's own default constructor when "
                     "the entry encoding is null; ArchiveStreamFactoryTest testEncodingInputStream and "
                     "testEncodingInputStreamAutodetect (cpio with a default factory expects US-ASCII) pass, as do "
                     "cantWrite7zToStream through the chain and ExceptionMessageTest testMessageWhenOutputStreamIsNull.",
 "ownership_tests": ["org.apache.commons.compress.archivers.ArchiveStreamFactoryTest::testEncodingInputStream",
                     "org.apache.commons.compress.archivers.ArchiveStreamFactoryTest::testEncodingInputStreamAutodetect",
                     "org.apache.commons.compress.archivers.ArchiveStreamFactoryTest::cantWrite7zToStream",
                     "org.apache.commons.compress.archivers.ExceptionMessageTest::testMessageWhenOutputStreamIsNull"],
 "compensating": {
   "chain": [
     {"file": ZAIS, "old": "return TarArchiveEntry.blockArchiveStream(tar, out, encoding);",
      "new": "return TarArchiveEntry.blockArchiveStream(tar, out, "
             "encoding != null ? encoding : org.apache.commons.compress.utils.CharsetNames.US_ASCII);",
      "why": "hop 4 hands the gold US-ASCII when the factory has no entry encoding"},
     {"file": ZAOS, "old": "return BZip2CompressorOutputStream.openArchiveStream(archiverName, out, encoding);",
      "new": "return BZip2CompressorOutputStream.openArchiveStream(archiverName, out, "
             "encoding != null ? encoding : ZipEncodingHelper.UTF8);",
      "why": "hop 1 hands the rest of the chain UTF8 when the factory has no entry encoding"},
     {"file": BZOS, "old": "return ZipFile.newArchiveStream(archiverName, out, encoding);",
      "new": "return ZipFile.newArchiveStream(archiverName.toLowerCase(java.util.Locale.ENGLISH), out, encoding);",
      "why": "hop 2 passes the archiver name on in lower case"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, used in that order; none substituted, none drawn by this "
               "builder; the excluded facade file is archivers/ArchiveStreamFactory.java): archivers.zip.ZipArchiveOutputStream "
               "(hop 1, 1613 lines), compressors.bzip2.BZip2CompressorOutputStream (hop 2, 1329), archivers.zip.ZipFile (hop 3, "
               "1121), archivers.zip.ZipArchiveInputStream (hop 4, 1082), archivers.tar.TarArchiveEntry (hop 5, gold, 1073; the "
               "smallest host). All five are public concrete top-level classes in which a public static method compiles. Anchors "
               "from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 7635 + 100 + i, as mr3_spec.py inserts "
               "them: hop 1 after canWriteEntryData (seed 7735), hop 2 after flush (7736), hop 3 after getUnixSymlink (7737), "
               "hop 4 after skip (7738), hop 5 after isBlockDevice (7739). The facade calls hop 1 by its simple name "
               "(ArchiveStreamFactory already imports ZipArchiveOutputStream); each hop imports the next host when it is in "
               "another package and the archivers types it names. Static parameters named out and encoding shadow instance "
               "fields of the same names (out in ZipArchiveOutputStream and BZip2CompressorOutputStream; encoding in "
               "ZipArchiveOutputStream, ZipFile and ZipArchiveInputStream), which a static method cannot use anyway.",
}
