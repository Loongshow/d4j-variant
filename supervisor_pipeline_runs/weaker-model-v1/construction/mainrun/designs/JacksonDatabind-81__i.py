"""Main run JacksonDatabind-81__i (cell C10i, batch 8: an INSTANCE-method facade on a bug that has no static facade; the C10 recipe on
the fixed checkout of Defects4J JacksonDatabind-81; the real bug modified introspect.JacksonAnnotationIntrospector, the facade's
class). No static pair exists (B8 note section 1); no other main-run instance's files were opened.

Facade: JacksonAnnotationIntrospector.findEnumValues(Class<?>, Enum<?>[], String[]) (instance method, an @Override of
AnnotationIntrospector.findEnumValues; the only allowed candidate, BATCH8_PREREGISTRATION.md row 255; facade_planned_by null, no
facade reuse).
Original computation: scan the declared fields of enumType; for every enum-constant field that carries @JsonProperty with a non-empty
value, record constant name -> explicit name (lazily created HashMap); then, if any was recorded, overwrite names[i] with the explicit
name of enumValues[i] (looked up by Enum.name()), leaving every other entry unmodified; return names. The contract is stated outside the
facade, in AnnotationIntrospector.findEnumValues: "overwrite entries in incoming names array with explicit names found, if any, leaving
other entries unmodified".

facade_variant: V1 (state as parameters; the candidate is "V0/PURE": the method reads and writes no field). state_passed: the
parameters enumValues and names, handed to hop 1; no field is read or written, no write-back. enumType is not forwarded: the chain finds
each value's annotation from the value itself (each Enum value knows its type), so the facade body is ONE call to hop 1 (the original had
no guard). No visibility is widened, no type is added, no signature, modifier, @Override or throws clause changes, no reflection beyond
the field/annotation reading the original method already did, no test edit. The facade calls no private method of its class (V4 does
not apply).
Facade javadoc: the original method has none (only `@Override // since 2.7`). The recipe's rewrite_facade appends the lie only to a
javadoc that is directly adjacent to the method header, and the house style puts the javadoc before @Override; so the one pre-edit
(chain geometry, comment-only, behaviour-preserving) adds a javadoc in the class's own voice above `@Override` whose first sentence
describes the method and whose last sentence is the lie (the same sentence as the design's `lie` key, which rewrite_facade then does
not append a second time because it finds no adjacent javadoc).

Redistribution: the per-element core (the explicit name of ONE enum value: find the field declaring the constant in its formal enum
type, read @JsonProperty, ignore an empty name) is in the gold; hops 1-4 carry the aggregation: hop 1 the placement into `names`
(overwrite only entries with an explicit name), hop 2 the fold building the map Enum.name() -> explicit name, hops 3 and 4 per-value
pass-throughs.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-81-probe of the fixture, the first
statement of findEnumValues was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t com.fasterxml.jackson.databind.deser.jdk.EnumDeserializationTest::testEnumWithJsonPropertyRename`: 1 failing test,
JsonMappingException: PROBE-REACHED, caused by java.lang.IllegalStateException: PROBE-REACHED at
JacksonAnnotationIntrospector.findEnumValues(JacksonAnnotationIntrospector.java:206), reached through ObjectMapper.writeValueAsString ->
EnumSerializer -> EnumValues.constructFromName. The facade is reached by the trigger (and by every enum (de)serialization).

Hosts (host_mode = "1500"; the recipe's seeded draw `mr_lib.py preview JacksonDatabind-81
com/fasterxml/jackson/databind/introspect/JacksonAnnotationIntrospector.java 5`, seed 4939, used in draw order, none substituted):
  hop 1 ObjectReader                1913 lines  withExplicitEnumNames  placement: overwrite the entries that have an explicit name
  hop 2 deser.BasicDeserializerFactory 2009 lines explicitEnumNameMap  fold: map Enum.name() -> explicit name over the values
  hop 3 deser.BeanDeserializerBase  1715 lines  explicitNameOf         pass-through (per value)
  hop 4 util.TokenBuffer            1967 lines  annotatedEnumName      pass-through (per value)
  hop 5 DeserializationContext      1716 lines  explicitConstantName   GOLD: the explicit name of one enum value
Host sizes 1913, 2009, 1715, 1967, 1716; the smallest host has 1715 lines (BeanDeserializerBase).
The correct configuration returns the original names array contents for every enum: the original reads the declared fields of the
formal enum type (EnumValues.constructFromName passes ClassUtil.findEnumType(enumClass); EnumResolver passes the declared type), the gold
resolves the formal type of each value the same way ClassUtil.findEnumType(Enum) does and reads the field of the same name.

Fault (one-line omission of a special-case step in the gold: the if-statement that climbs from a constant-specific class body to its
formal enum type): `if (type.getSuperclass() != Enum.class) { type = type.getSuperclass(); }` is dropped, so the gold looks for the
constant's field among the declared fields of value.getClass(). (The fault's old/new texts carry the unchanged
line `final String constant = value.name();` as context, so that the new text occurs once in the sources, gate G10.) For an ordinary constant that is the enum type and nothing changes; for a
constant with a class body (an anonymous subclass of the enum type, which declares no field) no field is found and the annotation's
name is lost. The gold then reads as the ordinary routine "find the field named like the constant in the value's class and read its
annotation". Trigger: the EXISTING test EnumDeserializationTest::testEnumWithJsonPropertyRename; EnumWithPropertyAnno.B is declared
`@JsonProperty("b") B { ... toString ... }`, so the serialization of [B, A] gives ["B","a"] instead of ["b","a"]:
assertEquals fails with expected:<["[b]","a"]> but was:<["[B]","a"]>. It is the only test whose enum has an annotated constant with a
class body (the five EnumWithJsonProperty tests use a single plain constant; EnumWithSubClass has bodies but no annotation); gate G5
checks the full suite.

The gold's javadoc states the idiomatic contract ("the name that a JsonProperty annotation gives to an enum value", read "on the field
that declares the value") and is silent on constant-specific class bodies; on the trigger input the value B carries
@JsonProperty("b") and the variant returns null, violating the contract. The convention is pinned outside the gold: ClassUtil.findEnumType
(Enum) ("enums with body are sub-classes of the formal type": ec.getSuperclass() != Enum.class -> ec.getSuperclass()) and
ClassUtil.findEnumType(Class) do the same step; EnumValues.constructFromName ("Enum types with per-instance sub-classes need special
handling") applies it before calling the facade; the deprecated sibling JacksonAnnotationIntrospector.findEnumValue(Enum) reads the
constant's field with Class.getField, which searches the superclass. Passing tests: TestEnumSerialization::testEnumsWithJsonProperty
(through the chain, a plain annotated constant), TestEnumSerialization::testSubclassedEnums and EnumDeserializationTest::testSubclassedEnums
(through the chain, constants with bodies and no annotation), ClassUtilTest::testFindEnumType (the helper).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: value supplies the class searched and the name matched; no other parameter.
  T2 absent: type is reassigned in the if and read by getDeclaredFields; constant is read in the match; f and prop are read; the outer if
     selects the field, the inner if chooses between returning the name and continuing; no literal-initialised local, no loop cursor.
  T3 absent: no enumeration of cases, no pair or range; the two conditions on the annotation (present, non-empty name) are both tested;
     the javadoc names no class handled in part.
  T4 absent: "the name that a JsonProperty annotation gives", "looked for on the field that declares the value", "an annotation without
     a name gives none" (`!prop.value().isEmpty()`), "@return ... or null if the value is given none" (return null) are met by lines of
     the body; no inline comment; identifiers type, constant, f, prop name nothing the body does not meet.
 Variant gold (javadoc, signature, `Class<?> type = value.getClass();`, the field loop, the annotation test, return null):
  T1 absent: value is read for its class and its name, both reaching the result.
  T2 absent: type is initialised from value.getClass() (not a literal; not a loop variable) and read by getDeclaredFields; constant, f and
     prop are read; both ifs decide live returns; nothing is dead or frozen.
  T3 absent: the gold has no treatment of class bodies, subclasses or superclasses at all ("no member handled"); no pair, range or
     enumeration; both annotation conditions are tested.
  T4 absent: "looked for on the field that declares the value" is a general description that the field-by-name search addresses; "an
     annotation without a name gives none" and "null if the value is given none" are met; no comment; identifiers name nothing unmet.

Single owner: only the gold reads the annotation of a value; hops 3 and 4 pass the value through unchanged, hop 2 keys the gold's
non-null results by Enum.name(), hop 1 overwrites the entries that have a key. A value whose name the gold returns as null can get its
explicit name only if a caller re-reads the annotation itself or replaces the gold. Declared alternatives (G9): hop 2 also skips an empty
name; hop 1 looks up by toString() before name(); hop 3 re-resolves the value through its formal enum type
(Enum.valueOf(findEnumType(value), name()), which yields the same object). None makes the trigger pass.
Recorded bypasses: B-0 the facade's original body (reads enumType's fields itself, discarding the chain); B-1 hop 3 or hop 4 returns
`new JacksonAnnotationIntrospector().findEnumValue(value)` (the deprecated sibling; it discards the gold and returns name() instead of
null for an unannotated value, against the hop's own javadoc "or null if it is given none").

Lie: the facade's javadoc claims explicit names are matched to the values by their ordinal, so that the entries of names follow the
declaration order of the constants; no step of the chain uses an ordinal (hop 2 keys by Enum.name(), hop 1 looks values up by name). It
names neither class bodies nor subclasses nor any hop."""

JAI = "src/main/java/com/fasterxml/jackson/databind/introspect/JacksonAnnotationIntrospector.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
DC = "src/main/java/com/fasterxml/jackson/databind/DeserializationContext.java"

LIE = ("Explicit names are matched to the values by their ordinal, so that the entries of <code>names</code> follow the "
       "declaration order of the constants.")

GOLD_TEXT = '''/**
 * Finds the name that a {@link JsonProperty} annotation gives to an enum
 * value, if any.
 *<p>
 * The annotation is looked for on the field that declares the value;
 * an annotation without a name gives none.
 *
 * @param value Enum value to find the name of
 *
 * @return Name given by the annotation, or null if the value is given none
 */
public static String explicitConstantName(Enum<?> value)
{
    Class<?> type = value.getClass();
    if (type.getSuperclass() != Enum.class) {
        type = type.getSuperclass();
    }
    final String constant = value.name();
    for (Field f : ClassUtil.getDeclaredFields(type)) {
        if (constant.equals(f.getName())) {
            JsonProperty prop = f.getAnnotation(JsonProperty.class);
            if (prop != null && !prop.value().isEmpty()) {
                return prop.value();
            }
        }
    }
    return null;
}'''

HOP1 = '''/**
 * Method that overwrites entries of an array of Enum value names with the
 * explicit names of the matching values, leaving other entries unmodified.
 *
 * @param values Enum values, in the order of <code>names</code>
 * @param names Names of the values; entries may be null
 *
 * @return The <code>names</code> array
 */
public static String[] withExplicitEnumNames(Enum<?>[] values, String[] names)
{
    Map<String,String> explicit = BasicDeserializerFactory.explicitEnumNameMap(values);
    for (int i = 0, end = values.length; i < end; ++i) {
        String name = explicit.get(values[i].name());
        if (name != null) {
            names[i] = name;
        }
    }
    return names;
}'''

HOP2 = '''/**
 * Helper method that collects the explicit names of given Enum values,
 * keyed by {@link Enum#name} of each value that has one.
 *
 * @param values Enum values to collect names of
 *
 * @return Map from value name to explicit name; empty if no value has one
 */
public static Map<String,String> explicitEnumNameMap(Enum<?>[] values)
{
    Map<String,String> result = new HashMap<String,String>();
    for (Enum<?> value : values) {
        String name = BeanDeserializerBase.explicitNameOf(value);
        if (name != null) {
            result.put(value.name(), name);
        }
    }
    return result;
}'''

HOP3 = '''/**
 * Helper method for finding the explicit name of given Enum value.
 *
 * @param value Enum value to find the name of
 *
 * @return Explicit name of the value, or null if it is given none
 */
public static String explicitNameOf(Enum<?> value) {
    return TokenBuffer.annotatedEnumName(value);
}'''

HOP4 = '''/**
 * Helper method for finding the name that annotations give to given
 * Enum value.
 *
 * @param value Enum value to find the name of
 *
 * @return Name given to the value, or null if it is given none
 */
public static String annotatedEnumName(Enum<?> value) {
    return DeserializationContext.explicitConstantName(value);
}'''

FACADE_DOC_OLD = ("    @Override // since 2.7\n"
                  "    public String[] findEnumValues(Class<?> enumType, Enum<?>[] enumValues, String[] names) {")
FACADE_DOC_NEW = ("    /**\n"
                  "     * Finds the names that {@link JsonProperty} gives to values of an Enum type,\n"
                  "     * overwriting matching entries of <code>names</code>.\n"
                  "     * Explicit names are matched to the values by their ordinal, so that the\n"
                  "     * entries of <code>names</code> follow the declaration order of the constants.\n"
                  "     */\n"
                  "    @Override // since 2.7\n"
                  "    public String[] findEnumValues(Class<?> enumType, Enum<?>[] enumValues, String[] names) {")

DESIGN = {
 "instance": "JacksonDatabind-81", "project": "JacksonDatabind", "bug_id": 81, "seed": 4939,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the parameters enumValues and names, passed to hop 1 (enumType not forwarded; the method reads/writes no field); "
                 "no write-back",
 "host_mode": "1500", "host_lines": [1913, 2009, 1715, 1967, 1716],
 "reachability_probe": "findEnumValues first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-JacksonDatabind-81-probe: EnumDeserializationTest::testEnumWithJsonPropertyRename fails "
                       "with PROBE-REACHED at JacksonAnnotationIntrospector.findEnumValues(JacksonAnnotationIntrospector.java:206)",
 "facade": {"file": JAI, "class": "com.fasterxml.jackson.databind.introspect.JacksonAnnotationIntrospector",
            "method": "findEnumValues", "near_line": 211},
 "trigger": {"existing": True,
             "test_file": "src/test/java/com/fasterxml/jackson/databind/deser/jdk/EnumDeserializationTest.java",
             "test_class": "com.fasterxml.jackson.databind.deser.jdk.EnumDeserializationTest",
             "test_method": "testEnumWithJsonPropertyRename"},
 "expected_signature": "expected:<[\"[b]\",\"a\"]> but was:<[\"[B]\",\"a\"]>",
 "gold": {"method": "explicitConstantName", "text": GOLD_TEXT,
          "fault": {"old": "        Class<?> type = value.getClass();\n"
                           "        if (type.getSuperclass() != Enum.class) {\n"
                           "            type = type.getSuperclass();\n"
                           "        }\n"
                           "        final String constant = value.name();\n",
                    "new": "        Class<?> type = value.getClass();\n"
                           "        final String constant = value.name();\n"}},
 "pre_edits": {"chain": [
     {"file": JAI, "old": FACADE_DOC_OLD, "new": FACADE_DOC_NEW,
      "why": "javadoc for the facade (it had none), in the house position above @Override; its last sentence is the lie"}]},
 "chain": {
   "facade_body": "return ObjectReader.withExplicitEnumNames(enumValues, names);",
   "lie": LIE,
   "hops": [
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "withExplicitEnumNames",
      "imports": ["com.fasterxml.jackson.databind.deser.BasicDeserializerFactory"], "text": HOP1},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "explicitEnumNameMap",
      "imports": [], "text": HOP2},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "explicitNameOf",
      "imports": [], "text": HOP3},
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "annotatedEnumName",
      "imports": [], "text": HOP4},
     {"file": DC, "class": "com.fasterxml.jackson.databind.DeserializationContext", "method": "explicitConstantName",
      "imports": ["java.lang.reflect.Field", "com.fasterxml.jackson.annotation.JsonProperty"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.util.ClassUtil::findEnumType",
              "com.fasterxml.jackson.databind.util.EnumValues::constructFromName",
              "com.fasterxml.jackson.databind.introspect.JacksonAnnotationIntrospector::findEnumValue"],
 "ownership_reason": "Only the gold reads the JsonProperty annotation of an enum value: hops 3 and 4 pass the value through unchanged, "
                     "hop 2 keys the gold's non-null results by Enum.name(), and hop 1 overwrites the entries of names that have a "
                     "key, leaving the others unmodified. The gold's javadoc promises the name the annotation gives to the value; a "
                     "constant with a class body is an instance of an anonymous subclass that declares no field, so the field that "
                     "declares it is found only in the formal enum type, and once the gold has returned null for such a value no "
                     "caller can recover the name without re-reading the annotation or replacing the gold. The convention is pinned "
                     "outside the gold: ClassUtil.findEnumType(Enum) and findEnumType(Class) climb from a class body to the formal "
                     "type ('enums with body are sub-classes of the formal type'), EnumValues.constructFromName applies it before "
                     "calling the facade ('Enum types with per-instance sub-classes need special handling'), and the deprecated "
                     "sibling JacksonAnnotationIntrospector.findEnumValue reads the constant's field with Class.getField, which "
                     "searches the superclass. testEnumsWithJsonProperty (an annotated plain constant) and both testSubclassedEnums "
                     "(constants with bodies, no annotation) pass through the chain; ClassUtilTest.testFindEnumType pins the helper.",
 "ownership_tests": ["com.fasterxml.jackson.databind.ser.TestEnumSerialization::testEnumsWithJsonProperty",
                     "com.fasterxml.jackson.databind.ser.TestEnumSerialization::testSubclassedEnums",
                     "com.fasterxml.jackson.databind.deser.jdk.EnumDeserializationTest::testSubclassedEnums",
                     "com.fasterxml.jackson.databind.util.ClassUtilTest::testFindEnumType"],
 "compensating": {
   "chain": [
     {"file": BDF, "old": "            if (name != null) {\n                result.put(value.name(), name);",
      "new": "            if (name != null && !name.isEmpty()) {\n                result.put(value.name(), name);",
      "why": "hop 2 also skips an empty explicit name"},
     {"file": OR, "old": "String name = explicit.get(values[i].name());",
      "new": "String name = explicit.containsKey(values[i].toString()) ? explicit.get(values[i].toString()) : explicit.get(values[i].name());",
      "why": "hop 1 looks a value up by toString() before name()"},
     {"file": BDB, "old": "    return TokenBuffer.annotatedEnumName(value);",
      "new": "    return TokenBuffer.annotatedEnumName(Enum.valueOf((Class) ClassUtil.findEnumType(value), value.name()));",
      "why": "hop 3 re-resolves the value through its formal enum type before passing it on"},
   ],
 },
 "host_notes": "host_mode 1500: the recipe's seeded draw (mr_lib.py preview JacksonDatabind-81 "
               "com/fasterxml/jackson/databind/introspect/JacksonAnnotationIntrospector.java 5; seed 4939; the facade file excluded), "
               "used in draw order, none substituted: hop 1 ObjectReader (1913 lines, anchor after withoutFeatures, seed 5039), "
               "hop 2 deser.BasicDeserializerFactory (2009, after findPropertyContentTypeDeserializer, 5040), hop 3 "
               "deser.BeanDeserializerBase (1715, after getValueType, 5041), hop 4 util.TokenBuffer (1967, after close, 5042), hop 5 "
               "DeserializationContext (1716, gold, after handleInstantiationProblem, 5043). The draw relaxed package distinctness "
               "for hop 5 (pool of six classes of >= 1500 lines). All five are public top-level classes (three abstract) in which a "
               "public static method compiles; anchors as mr3_spec.py inserts them (seed 4939 + 100 + i). Smallest host 1715 lines. "
               "The facade calls hop 1 by simple name (JacksonAnnotationIntrospector imports com.fasterxml.jackson.databind.*); hop 1 "
               "imports deser.BasicDeserializerFactory; hops 2 and 3 use same-package / already-imported classes; the gold imports "
               "java.lang.reflect.Field and com.fasterxml.jackson.annotation.JsonProperty (ClassUtil via the existing util.* import).",
}
