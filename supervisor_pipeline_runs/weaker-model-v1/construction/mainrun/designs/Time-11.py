"""Main run Time-11 (C10 recipe on the fixed checkout of Defects4J Time-11; the real bug modified ZoneInfoCompiler, the target class).

Facade: ZoneInfoCompiler.main(String[]) (the only allowed target, BATCH5_PREREGISTRATION.md row Time-11). Its only test caller is
TestCompiler::testCompile (through compileAndLoad: -src <tmp dir A> -dst <tmp dir B> tzdata).
Constraint that shapes the design: the Defects4J build runs this same main method. Time.build.xml's `compile` target (which
`defects4j compile` and `defects4j test` both run) calls ZoneInfoCompiler with
  -src src/main/java/org/joda/time/tz/src -dst target/classes/org/joda/time/tz/data africa antarctica asia australasia europe
  northamerica southamerica pacificnew etcetera backward systemv
(failonerror=yes), and every zone test of the suite reads the data it writes. So a fault on the chain must leave that invocation's
output unchanged and still fail testCompile deterministically. The two invocations have the same option structure; they differ in
the number of source names (eleven against one) and in relative versus absolute directories. A failure whose message names the
test's directories is not byte-identical across runs (they contain a random joda-test-<n> component, gate G3b), so the effect has
to separate the two invocations by the number of names: the build's source path holds ten separators, the test's holds none.
Original computation of main: no argument -> usage; read the leading options (-src <dir>, -dst <dir>, -verbose; -? or a value
option without its value -> usage; the first other argument ends the options); no source name left -> usage; each source name
resolved against the -src directory (new File(name) without it); set the verbose flag; new ZoneInfoCompiler().compile(dst, sources).

The facade keeps its argument guard (no argument -> usage) and delegates to a five-hop chain drawn with the instance seed 4347
(mr_lib preview, draw order, no substitution):
  hop 1 LocalDate.compileZoneInfo                 placement: the options map, the usage when the arguments cannot be read, the
                                                  verbose flag, the destination and the compile call
  hop 2 format.DateTimeFormatterBuilder.readCompilerArguments
                                                  decision: the option scan (-src/-dst values, -verbose, -?, missing value, no
                                                  source name -> null)
  hop 3 format.PeriodFormatterBuilder.sourcePathFiles
                                                  fold: joins the source names into a source path (path separator between names)
  hop 4 Period.sourceFilesOn                      placement: the -src path as a File (null without it)
  hop 5 format.ISODateTimeFormat.filesOnPath      GOLD: cuts the path into its names and resolves each name against the
                                                  directory (the per-element core: one File per source name). A path without a
                                                  separator is one name and is returned at once; otherwise the gold takes the name
                                                  before the first separator, the names between separators and the name after the
                                                  last separator.
The correct configuration computes the original result for every command line whose source names do not contain the path separator
character (same usage cases in the same order, last -src/-dst wins, the same File for each name: new File(null, n) is new File(n),
new File(new File(s), n) is new File(s, n); verbose set before compile). Names containing the path separator (':' on Unix) would be
split; no tz source name contains one.

Fault (omission in the gold): the single-name step `if (first < 0) { return new File[] {new File(dir, path)}; }` is dropped. A
path that holds one name has no separator, so `first` is -1 and the name before the first separator is cut with
path.substring(0, -1). Trigger: the EXISTING test TestCompiler::testCompile; its one source name gives the path "tzdata" and the
gold throws java.lang.StringIndexOutOfBoundsException (begin 0, end -1, length 6) inside the gold, below main and hops 1-4 (no
path in the message, deterministic). No other test calls main. The build's own run of main passes a path with ten separators and
returns the same eleven files as before, so the compiled data and every other test are unchanged.
Quiet gold: its javadoc states the idiomatic contract (the files named on a path, each resolved against a directory) and is
silent on how many names a path holds; the path "tzdata" names one file and the variant throws instead of returning it. Hop 3's
javadoc (each name after the first preceded by the separator) and hop 4's (names separated by the separator) admit a path of one
name, which then has no separator.

External pins (the convention outside the gold: a delimited text without its delimiter is one whole item, handled by its own
step, and every item counts): the facade's javadoc (Usage ... <source files>; the original main took one or more names);
ZoneInfoCompiler.parseDataFile cuts a line at its '#' only when it has one (`if (index >= 0)`), so a line without a comment is
read whole (every zone of the compiled data, e.g. TestDateTimeZone::testForID_String_old and testGetID); ZoneInfoCompiler.Rule.
formatName splits a "GMT/BST" format only when it holds the '/' (TestDateTimeZone::testGetNameKey: BST for Europe/London in
summer, GMT in winter) and returns a format without the "%s" marker as it is, by an early return of the same shape as the gold's
single-name step (`if (index < 0) { return nameFormat; }`).

Single owner: only the gold cuts the source path into names; hops 1 and 2 hold the arguments and the options, hop 3 joins the
names, hop 4 passes the joined path on, and the gold's own name step throws. Hop 3's javadoc fixes the path's form (each name after
the first preceded by the separator), so a one-name path has no separator; changing that form does not help: a separator added
after the last name, or before the first, adds an empty name, which the gold resolves to the source directory itself, and compile
then fails reading a directory (on the correct gold too; checked: with `path.append(File.pathSeparatorChar)` in hop 3 the
build's own run of main already fails, since its last name becomes empty). Declared alternatives (G9): hop 4 passes the absolute
source directory; hop 1 writes to the absolute destination directory; hop 2 reads from the current directory when no -src is
given; none changes the one-name path the gold cuts.
Recorded one-line edits above the gold that pass the trigger (checked on the variant in a scratch copy):
 B-0 bypass: the facade's original body (its own option loop, source array and compile call) discards all five hops.
 B-1 bypass: hop 4 (or hop 3) answers a path without a separator itself, e.g. hop 4 returns new File[] {new File(dir,
     sourcePath)} when sourcePath holds no separator and calls the gold otherwise: a second implementation of the gold's per-name
     step for exactly the input the gold is meant to cut.
 B-2 bypass: hop 2 (or hop 1) builds the File array from the arguments itself (a loop), making hops 3-5 dead.
 B-3 test-fitted: hop 3 writes a lone name twice ("tzdata" + separator + "tzdata"), so the source file is compiled twice and the
     trigger passes; it contradicts hop 3's javadoc (the arguments' names joined into the path, each once) and returns one source
     file twice.

Lie: the facade's javadoc claims the option names are matched without regard to case (-SRC and -Dst read as -src and -dst); the
code compares them with equals. It names neither source names nor paths nor any step that is omitted nor any hop.

Pre-edits (behaviour-preserving, needed by the chain): the hops lie outside org.joda.time.tz, so hop 1 cannot reach the original
main's usage printer (private static printUsage) or its verbose flag (package-private ThreadLocal cVerbose). printUsage is made
public, and a public static setVerbose(boolean) (cVerbose.set) is added below verbose(). Nothing else calls either.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: dir is the parent of every File created; path supplies every name and every separator position.
  T2 absent: first is tested and read by substring and the start of the cursor; last bounds the loop and starts the last name;
     index is reassigned in the loop; separator is assigned in the loop and read by substring; files is returned; the single-name
     test returns its own array, so it is a live decision.
  T3 absent: no flag, enum, type code or value class is tested; the first and last separators are both used; the names before the
     first separator, between separators and after the last separator are all taken; the gold names no class.
  T4 absent: the javadoc says 'the files named on a path', 'the path to read the file names from' and 'null for the current
     directory' (met: new File((File) null, name) is new File(name)); no limit, bound, case or property beyond that.
 Variant gold (javadoc, signature, first/last, the list, the name before the first separator, the loop over the names between
 separators, the name after the last separator, the return):
  T1 absent: dir is the parent of each File added; path is searched by indexOf/lastIndexOf and cut by substring; both change the
     result.
  T2 absent: first is read by substring and by the cursor's start; last is read by the loop condition and by the last substring;
     index is reassigned in the loop (index = separator + 1); separator is assigned by indexOf in the loop and read by substring;
     files is written and returned; there is no if/else, switch or ternary, so no dead decision.
  T3 absent: no closed set is treated in part: the first and the last separator (the two ends) are both used, and all three kinds
     of name (before the first, between, after the last separator) are added; the gold tests no indexOf result at all (no member
     of found/not found is handled), and its text names no class, format or standard.
  T4 absent: '@return the files named on the path' and 'Returns the files named on a path, each one resolved against a directory'
     are general descriptions that the body addresses; '@param dir ... null for the current directory' is met by File(File,
     String); '@param path the path to read the file names from' is a caller precondition; no inline comment; identifiers (files,
     first, last, index, separator) name nothing the body does not meet."""

ZIC = "src/main/java/org/joda/time/tz/ZoneInfoCompiler.java"
LD = "src/main/java/org/joda/time/LocalDate.java"
DTFB = "src/main/java/org/joda/time/format/DateTimeFormatterBuilder.java"
PFB = "src/main/java/org/joda/time/format/PeriodFormatterBuilder.java"
PER = "src/main/java/org/joda/time/Period.java"
ISO = "src/main/java/org/joda/time/format/ISODateTimeFormat.java"

GOLD_TEXT = '''/**
 * Returns the files named on a path, each one resolved against a
 * directory.
 *
 * @param dir  the directory to resolve the names against, null for the
 *  current directory
 * @param path  the path to read the file names from
 * @return the files named on the path
 */
public static File[] filesOnPath(File dir, String path) {
    int first = path.indexOf(File.pathSeparatorChar);
    if (first < 0) {
        return new File[] {new File(dir, path)};
    }
    int last = path.lastIndexOf(File.pathSeparatorChar);
    List<File> files = new ArrayList<File>();
    files.add(new File(dir, path.substring(0, first)));
    int index = first + 1;
    while (index <= last) {
        int separator = path.indexOf(File.pathSeparatorChar, index);
        files.add(new File(dir, path.substring(index, separator)));
        index = separator + 1;
    }
    files.add(new File(dir, path.substring(last + 1)));
    return files.toArray(new File[files.size()]);
}'''

HOP1 = '''/**
 * Compiles the zone info source files named on a command line.
 * <p>
 * The compiled files are written to the directory given by the
 * <code>-dst</code> option, and <code>-verbose</code> turns on verbose
 * logging. When the command line cannot be read, the usage is printed
 * instead.
 *
 * @param args  the command line arguments, not empty
 * @throws IOException if a source file cannot be read or a compiled file
 *  cannot be written
 */
public static void compileZoneInfo(String[] args) throws IOException {
    Map<String, String> options = new HashMap<String, String>();
    File[] sources = DateTimeFormatterBuilder.readCompilerArguments(args, options);
    if (sources == null) {
        ZoneInfoCompiler.printUsage();
        return;
    }
    ZoneInfoCompiler.setVerbose(options.containsKey("-verbose"));
    String dst = options.get("-dst");
    new ZoneInfoCompiler().compile(dst == null ? null : new File(dst), sources);
}'''

HOP2 = '''/**
 * Reads the options at the start of a zone info compiler command line, and
 * returns the source files named after them.
 * <p>
 * The values of the <code>-src</code> and <code>-dst</code> options are
 * stored in the map under the option names, and <code>-verbose</code> is
 * stored with the value <code>"true"</code>. The options end at the first
 * other argument.
 *
 * @param args  the command line arguments
 * @param options  the map to store the options in
 * @return the source files, or null if the command line asks for the
 *  usage, lacks the value of an option or names no source file
 */
public static File[] readCompilerArguments(String[] args, Map<String, String> options) {
    int i = 0;
    for (; i < args.length; i++) {
        String arg = args[i];
        if ("-src".equals(arg) || "-dst".equals(arg)) {
            if (i + 1 == args.length) {
                return null;
            }
            options.put(arg, args[++i]);
        } else if ("-verbose".equals(arg)) {
            options.put(arg, "true");
        } else if ("-?".equals(arg)) {
            return null;
        } else {
            break;
        }
    }
    if (i == args.length) {
        return null;
    }
    return PeriodFormatterBuilder.sourcePathFiles(args, i, options.get("-src"));
}'''

HOP3 = '''/**
 * Returns the source files named by the arguments of a command line from
 * the given index on, read from a source directory.
 * <p>
 * The names are joined into a source path, each name after the first
 * preceded by the path separator character.
 *
 * @param args  the command line arguments
 * @param first  the index of the first source file name
 * @param sourceDir  the path of the source directory, null for the
 *  current directory
 * @return the source files
 */
public static File[] sourcePathFiles(String[] args, int first, String sourceDir) {
    StringBuffer path = new StringBuffer(args[first]);
    for (int i = first + 1; i < args.length; i++) {
        path.append(File.pathSeparatorChar).append(args[i]);
    }
    return Period.sourceFilesOn(path.toString(), sourceDir);
}'''

HOP4 = '''/**
 * Returns the source files on a source path, read from a source directory.
 *
 * @param sourcePath  the names of the source files, separated by the path
 *  separator character
 * @param sourceDir  the path of the source directory, null for the
 *  current directory
 * @return the source files
 */
public static File[] sourceFilesOn(String sourcePath, String sourceDir) {
    File dir = (sourceDir == null ? null : new File(sourceDir));
    return ISODateTimeFormat.filesOnPath(dir, sourcePath);
}'''

DESIGN = {
 "instance": "Time-11", "project": "Time", "bug_id": 11, "seed": 4347,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": ZIC, "class": "org.joda.time.tz.ZoneInfoCompiler", "method": "main", "near_line": 94},
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/tz/TestCompiler.java",
             "test_class": "org.joda.time.tz.TestCompiler", "test_method": "testCompile"},
 "expected_signature": "java.lang.StringIndexOutOfBoundsException",
 "gold": {"method": "filesOnPath", "text": GOLD_TEXT,
          "fault": {"old": "        int first = path.indexOf(File.pathSeparatorChar);\n"
                           "        if (first < 0) {\n"
                           "            return new File[] {new File(dir, path)};\n"
                           "        }\n"
                           "        int last = path.lastIndexOf(File.pathSeparatorChar);",
                    "new": "        int first = path.indexOf(File.pathSeparatorChar);\n"
                           "        int last = path.lastIndexOf(File.pathSeparatorChar);"}},
 "pre_edits": {
   "chain": [
     {"file": ZIC, "old": "    private static void printUsage() {\n",
      "new": "    public static void printUsage() {\n"},
     {"file": ZIC,
      "old": "    public static boolean verbose() {\n"
             "        return cVerbose.get();\n"
             "    }\n",
      "new": "    public static boolean verbose() {\n"
             "        return cVerbose.get();\n"
             "    }\n"
             "\n"
             "    /**\n"
             "     * Sets a flag indicating that verbose logging is required.\n"
             "     * @param verbose  true to log verbosely\n"
             "     */\n"
             "    public static void setVerbose(boolean verbose) {\n"
             "        cVerbose.set(verbose);\n"
             "    }\n"},
   ],
 },
 "chain": {
   "facade_body": "if (args.length == 0) {\n"
                  "            printUsage();\n"
                  "            return;\n"
                  "        }\n"
                  "        org.joda.time.LocalDate.compileZoneInfo(args);",
   "lie": "The option names are matched without regard to case, so that -SRC and -Dst are read as -src and -dst.",
   "hops": [
     {"file": LD, "class": "org.joda.time.LocalDate", "method": "compileZoneInfo",
      "imports": ["java.io.File", "java.util.HashMap", "java.util.Map",
                  "org.joda.time.format.DateTimeFormatterBuilder", "org.joda.time.tz.ZoneInfoCompiler"], "text": HOP1},
     {"file": DTFB, "class": "org.joda.time.format.DateTimeFormatterBuilder", "method": "readCompilerArguments",
      "imports": ["java.io.File"], "text": HOP2},
     {"file": PFB, "class": "org.joda.time.format.PeriodFormatterBuilder", "method": "sourcePathFiles",
      "imports": ["java.io.File", "org.joda.time.Period"], "text": HOP3},
     {"file": PER, "class": "org.joda.time.Period", "method": "sourceFilesOn",
      "imports": ["java.io.File", "org.joda.time.format.ISODateTimeFormat"], "text": HOP4},
     {"file": ISO, "class": "org.joda.time.format.ISODateTimeFormat", "method": "filesOnPath",
      "imports": ["java.io.File", "java.util.ArrayList", "java.util.List"], "gold": True},
   ],
 },
 "evidence": ["org.joda.time.tz.ZoneInfoCompiler::main",
              "org.joda.time.tz.ZoneInfoCompiler::parseDataFile",
              "org.joda.time.tz.ZoneInfoCompiler$Rule::formatName"],
 "ownership_reason": "Only the gold cuts the source path into names: hops 1 and 2 hold the command line and its options, hop 3 "
                     "joins the source names into the path (each name after the first preceded by the path separator, per its "
                     "javadoc, so a path of one name has no separator), hop 4 passes the path on with the source directory, and "
                     "the gold returns one File per name. On the path 'tzdata' the gold's own name step cuts the name before a "
                     "separator that the path does not hold (substring(0, -1)) and throws, although its javadoc promises the "
                     "files named on the path and that path names one file. No hop can avoid it while keeping the documented "
                     "path form: a separator added after the last name or before the first adds an empty name, which the gold "
                     "resolves to the source directory itself, so compile fails reading a directory; answering the one-name "
                     "path above the gold means resolving the name a second time outside the method that cuts paths into "
                     "names. The convention that a delimited text without its delimiter is one whole item, handled by its own "
                     "step, is pinned outside the gold: the facade's usage (<source files>: one or more names); "
                     "ZoneInfoCompiler.parseDataFile cuts a line at '#' only when it holds one, so a line without a comment is "
                     "read whole (TestDateTimeZone testForID_String_old and testGetID read zones compiled from such lines); "
                     "ZoneInfoCompiler.Rule.formatName splits a 'GMT/BST' format only when it holds the '/' (TestDateTimeZone "
                     "testGetNameKey: BST in summer, GMT in winter for Europe/London) and returns a format without the '%s' "
                     "marker as it is, by its own early return.",
 "ownership_tests": ["org.joda.time.TestDateTimeZone::testForID_String_old",
                     "org.joda.time.TestDateTimeZone::testGetID",
                     "org.joda.time.TestDateTimeZone::testGetNameKey"],
 "compensating": {
   "chain": [
     {"file": PER, "old": "File dir = (sourceDir == null ? null : new File(sourceDir));",
      "new": "File dir = (sourceDir == null ? null : new File(sourceDir).getAbsoluteFile());",
      "why": "hop 4 passes the absolute source directory"},
     {"file": LD, "old": "new ZoneInfoCompiler().compile(dst == null ? null : new File(dst), sources);",
      "new": "new ZoneInfoCompiler().compile(dst == null ? null : new File(dst).getAbsoluteFile(), sources);",
      "why": "hop 1 writes to the absolute destination directory"},
     {"file": DTFB, "old": "return PeriodFormatterBuilder.sourcePathFiles(args, i, options.get(\"-src\"));",
      "new": "return PeriodFormatterBuilder.sourcePathFiles(args, i, options.containsKey(\"-src\") ? options.get(\"-src\") : \".\");",
      "why": "hop 2 reads from the current directory when no -src option is given"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4347 (mr_lib preview, target org/joda/time/tz/ZoneInfoCompiler.java): LocalDate "
               "(hop 1), format.DateTimeFormatterBuilder (hop 2), format.PeriodFormatterBuilder (hop 3), Period (hop 4), "
               "format.ISODateTimeFormat (hop 5, gold). All five are public top-level classes in which a static method compiles "
               "(LocalDate and Period are final, ISODateTimeFormat has a protected constructor; neither affects a static "
               "method); every preview anchor lies in the outer class; none was skipped. None of the hosts is in "
               "org.joda.time.tz, so two behaviour-preserving pre-edits make the original main's usage printer public and add "
               "a public setter for its verbose flag, both reached from hop 1. The facade calls hop 1 by its fully-qualified "
               "name; each hop imports java.io.File and the next host (hop 2 and hop 3 share the format package, hop 3 imports "
               "Period, hop 4 imports ISODateTimeFormat).",
}
