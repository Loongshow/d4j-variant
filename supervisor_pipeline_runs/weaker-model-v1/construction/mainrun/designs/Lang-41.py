"""Main run Lang-41 (C10 recipe on the fixed checkout of Defects4J Lang-41; the real bug modified ClassUtils, the target class).

Facade: ClassUtils.getPackageName(String) (allowed batch-3 target ClassUtils.getPackageName). The other allowed targets were set
aside: isAssignable is a decision cascade over two classes with no per-element iteration, every omission in it can be patched by
a one-line special case at any hop that holds both classes, and the array overload's only direct test passes reference classes
only (the autoboxing array overload is exercised by MethodUtilsTest and ConstructorUtilsTest, so no omission there fails exactly
one test); getPublicMethod has a single test whose first candidate type (Set) already declares the method publicly, so no
omission in a per-candidate loop changes its result, and a quiet javadoc cannot name the public-declaration property that the
omission would break (T4). getPackageName(String) holds the whole name decoding; getPackageName(Class) and getPackageName(Object)
delegate to it, and getPackageCanonicalName(String) calls it with a canonical name, so the chain is reached by several production
callers. Original computation: null or empty -> ""; strip the leading '[' characters; strip an 'L' when the name then starts with
'L' and ends with ';'; no package separator -> ""; else the text before the last separator. The facade keeps its argument guard
and delegates to a five-hop chain drawn with the instance seed 2515 (mr_lib preview, draw order, no substitution):
  hop 1 text.StrBuilder.packagePrefix          decision: a name with no package separator gives the empty String
  hop 2 builder.ToStringStyle.classPackage     placement: the package name ends at the last package separator of the name
  hop 3 StringUtils.packageBefore              pass-through
  hop 4 time.DateUtils.packageSegment          pass-through
  hop 5 time.FastDateFormat.packageUpTo        GOLD: the per-character scan over the leading '[' characters of the name, the
                                               skip of the 'L' that opens an object element name ending in ';', and the
                                               substring up to the separator
The chain computes the original result for every class name (the encoding prefix holds no separator, so "no separator" and the
last separator are the same on the raw and on the stripped name, and the package is name.substring(begin, end)); the only
difference is a name made of '[' characters alone, where the original threw StringIndexOutOfBoundsException and the chain
returns "" (no caller produces such a name). getPackageName(Class), getPackageName(Object), getShortClassName and the canonical-
name methods are untouched.

Fault (omission in the gold, a delimiter rule): the step that skips the 'L' of an object element name ending in ';' is dropped,
so the package of an array of objects keeps that letter. Trigger: the EXISTING test ClassUtilsTest::test_getPackageName_Class;
its first array assertion, getPackageName(String[].class) = "java.lang" (ClassUtilsTest.java:146), gets "Ljava.lang". It is the
only test that sends an array name through the facade: test_getPackageName_String and test_getPackageName_Object use plain class
names, and the getPackageCanonicalName tests pass canonical names ("...ClassUtils[]"), which never start with '['. The gold's
javadoc states the idiomatic contract (the package name of a class name, given the last separator) and is silent on how array
names are written; "Ljava.lang" is not the package name of any class.

External pins (convention outside the gold): ClassUtils.getShortClassName(String) strips the leading '[' characters and then the
'L' ... ';' wrapper of the same name format ("Strip Object type encoding"), and test_getShortClassName_Class expects "String[]"
for String[].class; getPackageCanonicalName / getCanonicalName turn "[Lorg.apache.commons.lang.ClassUtils;" into
"org.apache.commons.lang.ClassUtils[]" and give the element type's package, pinned by test_getPackageCanonicalName_String,
_Class and _Object (arrays of ClassUtils -> "org.apache.commons.lang") and test_getShortCanonicalName_String.

Single owner: only the gold reads the characters of the encoding prefix; hops 1-2 decide and place the separator from the raw name
(correct on the trigger input: "[Ljava.lang.String;" has its last separator at 11), hops 3-4 pass the name and the index on. A
doc-consistent repair above the gold must decode the array name itself (every '[' plus the 'L' ... ';' wrapper), which one simple
edit at a hop does not do. Declared one-line alternatives (G9): hop 1 drops a leading "[L" from the name (one dimension only),
hop 1 treats an array name as unpackaged, hop 4 drops a leading letter of the result for a name that starts with "[L"; each still
fails the trigger (String[][].class at ClassUtilsTest.java:159, or String[].class -> "").
Recorded bypasses (absorb the trigger, not declared; B-1 as `p.startsWith("L")` at hop 4, B-2 at hop 1 and B-4 at hop 4 were
checked on the variant in a scratch copy: trigger passes, full suite 0 failing tests):
 B-1 a hop drops a leading 'L' from the result (`p.startsWith("L") ? p.substring(1) : p`), or drops the first character of the
     result for every name ending in ';': both presuppose that the gold returns one character too many, so they contradict the
     gold's documented result (with the gold as documented, the first edit cuts the 'L' of any package such as "Lx", the second
     the first letter of every object-array package); test-fitted, not a repair.
 B-2 the facade or a hop rewrites the name with a regular expression before delegating
     (`className.replaceFirst("^\\\\[+L(.*);$", "$1")`): a second implementation of the whole array-name decoding outside the
     gold, after which the gold's own scan never sees an object-array name.
 B-3 a hop routes a name that starts with '[' through ClassUtils.getPackageCanonicalName (another implementation of the
     decoding, getCanonicalName, which then re-enters the chain with a canonical name).
 B-4 hop 3 or hop 4 passes `className.replace("[L", "[[")`, so that the gold's scan also passes the marker: the gold is then
     handed a string that is not a class name, contrary to its documented parameter; test-fitted, not a repair.

Lie: the facade's javadoc claims the name is split at every package separator and all parts but the last are joined again; the
code splits nothing and joins nothing. It names neither arrays nor the 'L' marker nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 correct gold: T1 absent (className is scanned and cut, end bounds the substring); T2 absent (begin advances in the loop and in
   the marker step and bounds the result; no literal is frozen; both decisions change the result); T3 absent (the gold's text
   names no format or set: it handles the '[' run and the 'L' marker, different treatments, and the element codes it leaves
   alone are an unnamed set of which it handles exactly one member); T4 absent (the javadoc names no rule, bound, value class or
   case; "not null" and "the index of the last package separator" are caller preconditions). Nothing to rewrite.
 variant gold: T1 absent (className is read by the scan and by substring; end is the substring's end); T2 absent (begin is
   assigned inside its loop and is the substring's start; no dead local, no frozen literal, no dead branch); T3 absent (a single
   treatment, the '[' scan, of a set the gold's text does not name; begin and end, the two ends of the range, are both used);
   T4 absent (the javadoc only says the package name is taken from a class name given its last separator; the body produces a
   prefix ending at that separator, and nothing in the text names array names, markers or encodings)."""

SU = "src/java/org/apache/commons/lang/StringUtils.java"
CU = "src/java/org/apache/commons/lang/ClassUtils.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
DU = "src/java/org/apache/commons/lang/time/DateUtils.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"

END_DOC = '''/**
 * <p>Gets the package name from a class name, given the index of the
 * last package separator in the name.</p>
 *
 * @param className  the class name to get the package name for, not null
 * @param end  the index of the last package separator in the name
 * @return the package name
 */'''

GOLD_TEXT = END_DOC + '''
public static String packageUpTo(String className, int end) {
    int begin = 0;
    while (className.charAt(begin) == '[') {
        begin++;
    }
    if (className.charAt(begin) == 'L' && className.endsWith(";")) {
        begin++;
    }
    return className.substring(begin, end);
}'''

HOP1 = '''/**
 * <p>Gets the package name from a class name.</p>
 *
 * <p>A name that contains no package separator gives the empty String.</p>
 *
 * @param className  the class name to get the package name for, not null
 * @return the package name or an empty string
 */
public static String packagePrefix(String className) {
    if (className.indexOf(ClassUtils.PACKAGE_SEPARATOR_CHAR) == -1) {
        return "";
    }
    return ToStringStyle.classPackage(className);
}'''

HOP2 = '''/**
 * <p>Gets the package name from a class name that contains a package
 * separator.</p>
 *
 * <p>The package name ends at the last package separator of the name.</p>
 *
 * @param className  the class name to get the package name for, not null
 * @return the package name
 */
public static String classPackage(String className) {
    return StringUtils.packageBefore(className, className.lastIndexOf(ClassUtils.PACKAGE_SEPARATOR_CHAR));
}'''

HOP3 = END_DOC + '''
public static String packageBefore(String className, int end) {
    return DateUtils.packageSegment(className, end);
}'''

HOP4 = END_DOC + '''
public static String packageSegment(String className, int end) {
    return FastDateFormat.packageUpTo(className, end);
}'''

DESIGN = {
 "instance": "Lang-41", "project": "Lang", "bug_id": 41, "seed": 2515,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": CU, "class": "org.apache.commons.lang.ClassUtils", "method": "getPackageName", "near_line": 257},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/ClassUtilsTest.java",
             "test_class": "org.apache.commons.lang.ClassUtilsTest", "test_method": "test_getPackageName_Class"},
 "expected_signature": "expected:<[]java.lang> but was:<[L]java.lang>",
 "gold": {"method": "packageUpTo", "text": GOLD_TEXT,
          "fault": {"old": "            begin++;\n"
                           "        }\n"
                           "        if (className.charAt(begin) == 'L' && className.endsWith(\";\")) {\n"
                           "            begin++;\n"
                           "        }\n"
                           "        return className.substring(begin, end);",
                    "new": "            begin++;\n"
                           "        }\n"
                           "        return className.substring(begin, end);"}},
 "chain": {
   "facade_body": "if (className == null || className.length() == 0) {\n            return StringUtils.EMPTY;\n        }\n"
                  "        return org.apache.commons.lang.text.StrBuilder.packagePrefix(className);",
   "lie": "The name is split into its parts at every package separator, and all of the parts except the last are joined "
          "again, separator by separator, to give the package name.",
   "hops": [
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "packagePrefix",
      "imports": ["org.apache.commons.lang.ClassUtils", "org.apache.commons.lang.builder.ToStringStyle"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "classPackage",
      "imports": ["org.apache.commons.lang.StringUtils"], "text": HOP2},
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "packageBefore",
      "imports": ["org.apache.commons.lang.time.DateUtils"], "text": HOP3},
     {"file": DU, "class": "org.apache.commons.lang.time.DateUtils", "method": "packageSegment",
      "imports": [], "text": HOP4},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "packageUpTo", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.ClassUtils::getShortClassName",
              "org.apache.commons.lang.ClassUtils::getPackageCanonicalName",
              "org.apache.commons.lang.ClassUtils::getCanonicalName"],
 "ownership_reason": "Only the gold reads the characters of the encoding prefix of the name; hop 1 decides on the presence of a "
                     "package separator and hop 2 places the last separator, both correctly on the trigger input, and hops 3 "
                     "and 4 pass the name and the index on. Repairing the result above the gold means decoding the array name "
                     "there (every '[' and the 'L' ... ';' wrapper) or presupposing that the gold returns one character too "
                     "many, which contradicts the gold's documented result. The convention is pinned outside the gold: "
                     "ClassUtils.getShortClassName(String) strips the '[' run and then the 'L' ... ';' wrapper of the same name "
                     "format (test_getShortClassName_Class expects \"String[]\" for String[].class); getPackageCanonicalName "
                     "and getCanonicalName give an array of objects the package of its element type "
                     "(\"[Lorg.apache.commons.lang.ClassUtils;\" -> \"org.apache.commons.lang\"), pinned by the "
                     "getPackageCanonicalName tests, which pass through the facade with canonical names.",
 "ownership_tests": ["org.apache.commons.lang.ClassUtilsTest::test_getShortClassName_Class",
                     "org.apache.commons.lang.ClassUtilsTest::test_getPackageCanonicalName_String",
                     "org.apache.commons.lang.ClassUtilsTest::test_getPackageCanonicalName_Class",
                     "org.apache.commons.lang.ClassUtilsTest::test_getPackageName_String",
                     "org.apache.commons.lang.ClassUtilsTest::test_getShortCanonicalName_String"],
 "compensating": {
   "chain": [
     {"file": SB, "old": "    return ToStringStyle.classPackage(className);",
      "new": "    return ToStringStyle.classPackage(className.startsWith(\"[L\") ? className.substring(2) : className);",
      "why": "hop 1 drops a leading [L from the name"},
     {"file": SB, "old": "    if (className.indexOf(ClassUtils.PACKAGE_SEPARATOR_CHAR) == -1) {",
      "new": "    if (className.indexOf(ClassUtils.PACKAGE_SEPARATOR_CHAR) == -1 || className.startsWith(\"[\")) {",
      "why": "hop 1 treats an array name as unpackaged"},
     {"file": DU, "old": "    return FastDateFormat.packageUpTo(className, end);",
      "new": "    return className.startsWith(\"[L\") ? FastDateFormat.packageUpTo(className, end).substring(1) : FastDateFormat.packageUpTo(className, end);",
      "why": "hop 4 drops the first letter of the result for a name that starts with [L"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 2515 (mr_lib preview, target org/apache/commons/lang/ClassUtils.java): "
               "text.StrBuilder (hop 1), builder.ToStringStyle (hop 2), StringUtils (hop 3), time.DateUtils (hop 4), "
               "time.FastDateFormat (hop 5, gold). All five are public classes in which a static method compiles "
               "(ToStringStyle is abstract, which does not affect a static method); none was skipped. The draw relaxed the "
               "distinct-package constraint for hops 3-5 (recorded by the recipe: fewer than two other-package classes above "
               "1500 lines), so StringUtils shares the target's package. The facade calls hop 1 by its fully-qualified name; "
               "each hop imports the next host (DateUtils and FastDateFormat share a package).",
}
