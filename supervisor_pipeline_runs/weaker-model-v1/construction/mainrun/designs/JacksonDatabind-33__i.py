"""Main run JacksonDatabind-33__i (cell C10i, batch 8: an INSTANCE-method facade on a bug with no static facade; the C10 recipe on the
fixed checkout of Defects4J JacksonDatabind-33, revision 660ec8f8c081; the real bug modified JacksonAnnotationIntrospector, the facade's
class). No static pair exists (B8 note section 1).

Facade: JacksonAnnotationIntrospector.findEnumValue(Enum<?>) (instance method, @Override of AnnotationIntrospector.findEnumValue; the
only allowed candidate of the task record, BATCH8_PREREGISTRATION.md row 251). Its facade_planned_by is JacksonDatabind-21__i (facade
reuse recorded in facade_reuse_of); no other candidate is allowed, so the planned-elsewhere method is used. Nothing of that task was read.
Original computation: the public static field of the constant's runtime class with the constant's name (Class.getField, which also finds
an inherited field) is looked up; if it carries @JsonProperty with a non-null, non-empty value, that value is returned; a
SecurityException or NoSuchFieldException is swallowed; otherwise value.name() is returned.

facade_variant: V1 (state as parameters; the method reads no field and writes none, profile variant V0, so the state handed down is the
argument alone). state_passed: the enum value (the method's parameter) passed to hop 1; no field is read, no write-back. The facade body
is one call to hop 1 (the original has no guard). No visibility is widened, no type is added, no signature, modifier, override or throws
clause changes, no test edit. No reflection is added beyond the original's own computation (the original reads the constant's field and
its annotation with java.lang.reflect; the gold does the same with Class.getDeclaredFields / Field.getAnnotation). The facade calls no
private method of its class, so V4 does not apply.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-33-probe of the fixture, the first
statement of findEnumValue was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j
test -t com.fasterxml.jackson.databind.deser.TestEnumDeserialization::testEnumWithJsonPropertyRename`: 1 failing test,
JsonMappingException: PROBE-REACHED, caused by java.lang.IllegalStateException: PROBE-REACHED at
JacksonAnnotationIntrospector.findEnumValue(JacksonAnnotationIntrospector.java:68), reached through enum serialization
(EnumValues.constructFromName). The facade is reached by the trigger.

Redistribution of the computation: the per-constant core (locating the constant's field among the fields of the constant's enumeration
type and reading its @JsonProperty value) is in the gold; hop 1 applies the fallback to name(), hop 2 treats a SecurityException as "no
explicit name", hop 3 treats an empty explicit name as none, hop 4 passes the value through. The chain returns the original result for
every enum constant: the constant's field is an enum-constant field declared by its enumeration type (for a constant with a body, the
superclass of its runtime class), which is the field Class.getField finds.

Hosts (host_mode = "1500"; the recipe's seeded draw `mr_lib.py preview JacksonDatabind-33
com/fasterxml/jackson/databind/introspect/JacksonAnnotationIntrospector.java 5`, seed 7903, used in draw order, none substituted):
  hop 1 deser.BeanDeserializerBase      1532 lines  enumPropertyName      fallback: explicit name if any, else name()
  hop 2 ObjectMapper                    3858 lines  findExplicitEnumName  a SecurityException counts as no explicit name
  hop 3 util.TokenBuffer                1881 lines  explicitEnumText      an empty explicit name counts as none
  hop 4 ObjectReader                    1820 lines  enumNameOverride      pass-through
  hop 5 deser.BasicDeserializerFactory  1918 lines  annotatedEnumName     GOLD: finds the constant's field and reads its annotation
Host sizes 1532, 3858, 1881, 1820, 1918; the smallest host is BeanDeserializerBase (1532 lines, hop 1); the gold host has 1918 lines.

Fault (one-line omission of a special-case step in the gold): the step that takes the enumeration type of a constant whose runtime class
is a subclass of it (`if (type.getSuperclass() != Enum.class) { type = type.getSuperclass(); }`) is dropped, so the gold searches the
fields declared by the constant's runtime class. For a constant with a body (an anonymous subclass) that class declares no
enum-constant field, the search finds nothing and the gold returns null, so the constant is written by its name. Trigger: the EXISTING
test TestEnumDeserialization::testEnumWithJsonPropertyRename; its first assertion, assertEquals("[\"b\",\"a\"]", ...), fails with
expected:<["[b]","a"]> but was:<["[B]","a"]> (constant B has @JsonProperty("b") and a body). It is the only test that uses @JsonProperty
on a constant with a body (the only test enum with @JsonProperty on constants is EnumWithPropertyAnno; the other bodied test enum,
BaseMapTest.EnumWithSubClass, has no annotation and keeps its names); gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it finds the name that @JsonProperty on the field of an enumeration constant gives to
that constant) and is silent on constants with bodies; the variant returns null for B although B's field carries @JsonProperty("b").
The convention (a constant with a body is an instance of a subclass of its enumeration type, which declares the constant) is pinned
outside the gold: ClassUtil.findEnumType(Enum) and findEnumType(Class) do the same step (`if (ec.getSuperclass() != Enum.class) ec =
ec.getSuperclass();`, "enums with body are sub-classes of the formal type"), used in production by EnumValues.constructFromName and
constructFromToString ("Enum types with per-instance sub-classes need special handling") and ClassNameIdResolver; passing tests:
TestClassUtil::testFindEnumType, and through the chain TestEnumSerialization::testSubclassedEnums and
TestEnumDeserialization::testSubclassedEnums (bodied constants without annotation keep their names).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: constant supplies the class to search and the name to match; it is not only argument-checked.
  T2 absent: type is reassigned by the superclass step and read by the loop; name is read in the match; f is the for-each cursor; prop
     is read by the return; the if changes type; the ternary's two outcomes differ; no local is frozen or dead.
  T3 absent: the match tests both that the field is an enum constant and that its name is the constant's; no set named in the gold's
     text is handled in part; the annotation-absent and annotation-present cases are both returned.
  T4 absent: the javadoc ('finds the name that a JsonProperty annotation on the field of an enumeration constant gives to that
     constant', '@return the value of the annotation, or null if none is found') is met by lines of the body; no inline comment.
 Variant gold (javadoc, signature, `Class<?> type = constant.getClass();`, the field loop, the annotation read):
  T1 absent: constant decides the class searched and the name matched.
  T2 absent: type (not a literal; computed before the loop, which only reads it as its bound collection) feeds the loop; name is read in
     the match; f advances; prop reaches the return; the ternary's outcomes differ; the final return null is the not-found path.
  T3 absent: the gold has no treatment of constants with bodies or of class hierarchy at all ('No member handled'); the gold's text
     names no such class; the match tests both of its conditions; both annotation outcomes are returned.
  T4 absent: 'finds the name that a JsonProperty annotation on the field of an enumeration constant gives to that constant' is a
     general description addressed by the loop and the annotation read; '@return the value of the annotation, or null if none is found'
     is met (null is returned when no annotation is found); '@param constant the enumeration constant' is a parameter description;
     identifiers (type, name, f, prop) name nothing the body does not meet.

Single owner: only the gold locates the constant's field and reads its annotation; hops 1-4 receive the constant and the gold's result
only, so no caller can hand the gold a different class or pre-filter the constant (the constant B is the same object whichever way it
is obtained). Once the gold has returned null for B, "b" can appear only if a caller repeats the field lookup itself or replaces the
gold. Declared alternatives (G9): hop 1 falls back to toString() instead of name() (B's toString() is "bb"); hop 3 passes an empty
explicit name through; hop 2 catches every RuntimeException. None makes the trigger pass.
Recorded bypasses: B-0 the facade (its original body) or any hop re-doing the lookup on the value's runtime class with Class.getField
(which finds inherited fields), e.g. hop 4 `return BasicDeserializerFactory.annotatedEnumName(value);` ->
`return value.getClass().getField(value.name()).getAnnotation(...).value();` (a second implementation of the gold, which also changes
its exceptions and its null handling); B-1 hop 2 or hop 4 reads the annotation from ClassUtil.findEnumType(value).getField(...)
(the same: a re-implementation that discards the gold's result).

Lie: the facade's javadoc claims the explicit names of all constants of the value's enumeration are read once and kept in a table from
which later calls take the name; no step of the chain keeps a table or reads other constants' names (each call reads the one constant's
field). It names neither bodies nor subclasses nor any hop. The facade's javadoc is separated from its header by @Override, so the
recipe's rewrite_facade (which appends the lie only to a javadoc directly adjacent to the header) does not place it; the pre_edit puts
the same sentence in the same place and form (appended inside the existing javadoc, before its closing */), a comment-only edit."""

JAI = "src/main/java/com/fasterxml/jackson/databind/introspect/JacksonAnnotationIntrospector.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"

LIE = ("The explicit names of all constants of the value's enumeration are read once and kept in a table, from which "
       "later calls take the name.")

GOLD_TEXT = '''/**
 * Helper method that finds the name that a {@link JsonProperty} annotation
 * on the field of an enumeration constant gives to that constant.
 *
 * @param constant the enumeration constant
 * @return the value of the annotation, or null if none is found
 */
public static String annotatedEnumName(Enum<?> constant)
{
    Class<?> type = constant.getClass();
    if (type.getSuperclass() != Enum.class) {
        type = type.getSuperclass();
    }
    final String name = constant.name();
    for (Field f : type.getDeclaredFields()) {
        if (f.isEnumConstant() && f.getName().equals(name)) {
            JsonProperty prop = f.getAnnotation(JsonProperty.class);
            return (prop == null) ? null : prop.value();
        }
    }
    return null;
}'''

HOP1 = '''/**
 * Helper method for finding the name to use for given enum value: the
 * explicit name given to it with an annotation, if there is one;
 * otherwise its declared name.
 *
 * @param value Enum value to find the name for
 * @return Name to use for the value; never null
 */
public static String enumPropertyName(Enum<?> value)
{
    String explicit = ObjectMapper.findExplicitEnumName(value);
    return (explicit == null) ? value.name() : explicit;
}'''

HOP2 = '''/**
 * Helper method for finding the explicit name given to an enum value
 * with {@link JsonProperty}. If access to the fields of the enum type
 * is denied, the value is considered to have no explicit name.
 *
 * @param value Enum value to check
 * @return Explicit name of the value, if any; null if none
 */
public static String findExplicitEnumName(Enum<?> value)
{
    try {
        return TokenBuffer.explicitEnumText(value);
    } catch (SecurityException e) {
        return null;
    }
}'''

HOP3 = '''/**
 * Helper method that returns the explicit name given to an enum value,
 * if that name is not empty.
 *
 * @param value Enum value to check
 * @return Explicit name, or null if no name, or an empty one, is given
 */
public static String explicitEnumText(Enum<?> value)
{
    String text = ObjectReader.enumNameOverride(value);
    return (text == null || text.isEmpty()) ? null : text;
}'''

HOP4 = '''/**
 * Helper method that returns the name given to an enum value with
 * {@link com.fasterxml.jackson.annotation.JsonProperty}, if any.
 *
 * @param value Enum value to check
 * @return Name given with the annotation, or null if none
 */
public static String enumNameOverride(Enum<?> value) {
    return BasicDeserializerFactory.annotatedEnumName(value);
}'''

DESIGN = {
 "instance": "JacksonDatabind-33", "project": "JacksonDatabind", "bug_id": 33, "seed": 7903,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the enum value (the method's parameter) passed to hop 1; no field read (profile variant V0), no write-back",
 "host_mode": "1500", "host_lines": [1532, 3858, 1881, 1820, 1918],
 "reachability_probe": "findEnumValue first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-JacksonDatabind-33-probe: TestEnumDeserialization::testEnumWithJsonPropertyRename fails "
                       "with JsonMappingException: PROBE-REACHED caused by IllegalStateException: PROBE-REACHED at "
                       "JacksonAnnotationIntrospector.findEnumValue(JacksonAnnotationIntrospector.java:68)",
 "facade": {"file": JAI, "class": "com.fasterxml.jackson.databind.introspect.JacksonAnnotationIntrospector",
            "method": "findEnumValue", "near_line": 66},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/deser/TestEnumDeserialization.java",
             "test_class": "com.fasterxml.jackson.databind.deser.TestEnumDeserialization",
             "test_method": "testEnumWithJsonPropertyRename"},
 "expected_signature": "expected:<[\"[b]\",\"a\"]> but was:<[\"[B]\",\"a\"]>",
 "gold": {"method": "annotatedEnumName", "text": GOLD_TEXT,
          "fault": {"old": "        Class<?> type = constant.getClass();\n"
                           "        if (type.getSuperclass() != Enum.class) {\n"
                           "            type = type.getSuperclass();\n"
                           "        }\n",
                    "new": "        Class<?> type = constant.getClass();\n"}},
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.deser.BeanDeserializerBase.enumPropertyName(value);",
   "lie": LIE,
   "hops": [
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "enumPropertyName",
      "imports": [], "text": HOP1},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "findExplicitEnumName",
      "imports": [], "text": HOP2},
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "explicitEnumText",
      "imports": [], "text": HOP3},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "enumNameOverride",
      "imports": ["com.fasterxml.jackson.databind.deser.BasicDeserializerFactory"], "text": HOP4},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "annotatedEnumName",
      "imports": ["java.lang.reflect.Field", "com.fasterxml.jackson.annotation.JsonProperty"], "gold": True},
   ],
 },
 "pre_edits": {"chain": [
   {"file": JAI,
    "old": "     * explicit serialized name\n     */\n    @Override\n    public String findEnumValue(Enum<?> value)",
    "new": "     * explicit serialized name\n       " + LIE + "\n     */\n    @Override\n    public String findEnumValue(Enum<?> value)"},
 ]},
 "evidence": ["com.fasterxml.jackson.databind.util.ClassUtil::findEnumType",
              "com.fasterxml.jackson.databind.util.EnumValues::constructFromName",
              "com.fasterxml.jackson.databind.jsontype.impl.ClassNameIdResolver::_idFrom"],
 "ownership_reason": "Only the gold locates the field of an enumeration constant and reads its @JsonProperty annotation; hops 1-4 "
                     "receive the constant and the gold's result only (hop 1 falls back to name(), hop 2 treats a SecurityException "
                     "as no explicit name, hop 3 treats an empty name as none, hop 4 passes the value through), so no caller can "
                     "hand the gold another class or pre-filter the constant. The gold's javadoc promises the name that "
                     "@JsonProperty on the constant's field gives it; for a constant with a body (an instance of an anonymous "
                     "subclass of its enumeration type) the variant searches the subclass, finds no field and returns null although "
                     "the field carries @JsonProperty(\"b\"). The convention is pinned outside the gold: ClassUtil.findEnumType(Enum) "
                     "and findEnumType(Class) take the superclass of a constant's class when it is not Enum ('enums with body are "
                     "sub-classes of the formal type'), used in production by EnumValues.constructFromName / constructFromToString "
                     "and ClassNameIdResolver; TestClassUtil::testFindEnumType passes, and TestEnumSerialization::testSubclassedEnums "
                     "and TestEnumDeserialization::testSubclassedEnums pass through the chain with bodied constants.",
 "ownership_tests": ["com.fasterxml.jackson.databind.util.TestClassUtil::testFindEnumType",
                     "com.fasterxml.jackson.databind.ser.TestEnumSerialization::testSubclassedEnums",
                     "com.fasterxml.jackson.databind.deser.TestEnumDeserialization::testSubclassedEnums"],
 "compensating": {
   "chain": [
     {"file": BDB, "old": "return (explicit == null) ? value.name() : explicit;",
      "new": "return (explicit == null) ? value.toString() : explicit;",
      "why": "hop 1 falls back to toString() instead of name()"},
     {"file": TB, "old": "return (text == null || text.isEmpty()) ? null : text;",
      "new": "return text;",
      "why": "hop 3 passes an empty explicit name through"},
     {"file": OM, "old": "} catch (SecurityException e) {",
      "new": "} catch (RuntimeException e) {",
      "why": "hop 2 treats every runtime exception as no explicit name"},
   ],
 },
 "host_notes": "host_mode 1500: hosts from the recipe's seeded draw (mr_lib.py preview JacksonDatabind-33 "
               "com/fasterxml/jackson/databind/introspect/JacksonAnnotationIntrospector.java 5, seed 7903), used in draw order, none "
               "substituted: deser.BeanDeserializerBase (hop 1, 1532 lines; abstract public class), ObjectMapper (hop 2, 3858), "
               "util.TokenBuffer (hop 3, 1881), ObjectReader (hop 4, 1820), deser.BasicDeserializerFactory (hop 5, gold, 1918; "
               "abstract public class). The smallest host is BeanDeserializerBase (1532). Preview anchors: hop 1 after hasProperty "
               "(seed 8003), hop 2 after readValue (8004), hop 3 after setFeatureMask (8005), hop 4 after withoutFeatures (8006), "
               "hop 5 after createEnumDeserializer (8007). Imports: BeanDeserializerBase sees ObjectMapper through "
               "com.fasterxml.jackson.databind.*; ObjectMapper imports util.TokenBuffer and com.fasterxml.jackson.annotation.*; "
               "TokenBuffer sees ObjectReader through com.fasterxml.jackson.databind.*; ObjectReader gets an import of "
               "deser.BasicDeserializerFactory; the gold host gets java.lang.reflect.Field and annotation.JsonProperty. The facade "
               "calls hop 1 by its fully-qualified name. Source level 1.6 (no multi-catch).",
}
