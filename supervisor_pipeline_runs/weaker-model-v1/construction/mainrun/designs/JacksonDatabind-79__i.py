"""Main run JacksonDatabind-79__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J JacksonDatabind-79, a bug with no static facade; the real bug modified JacksonAnnotationIntrospector, the facade's class,
ObjectIdInfo and BeanSerializerBase). No static pair (B8 note section 1).

Facade: JacksonAnnotationIntrospector.findEnumValues(Class<?>, Enum<?>[], String[]) (instance method, @Override of
AnnotationIntrospector.findEnumValues; allowed targets JacksonAnnotationIntrospector.findEnumValue / .findEnumValues,
BATCH8_PREREGISTRATION.md row 254). findEnumValues has facade_planned_by = null and was chosen over findEnumValue (planned by
JacksonDatabind-21__i), so the facade is distinct (no effective reuse). findEnumValue stays intact; it is one of the external pins.
Original computation: every declared field of enumType that is an enum constant and carries a JsonProperty annotation with a
non-empty value gives an explicit name (field name -> annotation value); then, for each enum value i, an explicit name found for
enumValues[i].name() is written into names[i], other entries are left as they are; names is returned.

facade_variant: V1 (state as parameters; the pool profile's V0: the method reads no field of its object). state_passed: the
parameters enumValues and names, handed to hop 1; no field is read or written, no write-back. enumType is not passed: the chain
resolves each value's explicit name from the value itself, as the base implementation AnnotationIntrospector.findEnumValues and the
sibling JacksonAnnotationIntrospector.findEnumValue do (neither consults enumType); for every caller (EnumValues.constructFromName,
EnumResolver.constructFor, AnnotationIntrospectorPair.findEnumValues) enumType is the formal enum type of the values, so the result
is unchanged. The facade body is one call to hop 1 (the original has no guard). No visibility is widened, no type is added, no
signature, modifier, override or throws clause changes, no reflection beyond the original's own field/annotation lookup (moved
into the gold), no test edit. The facade calls no private method of its class, so V4 does not apply.
Facade javadoc: the method had none (only `@Override // since 2.7`). The pre-edit adds a javadoc in the class's own voice (one
sentence, "Since 2.7, ...", like findEnumValue's "Since 2.6, ...") above the annotation, where the class puts its javadocs. Because the
annotation stands between that javadoc and the method header, the recipe's rewrite_facade (which appends the lie only to a javadoc
directly adjacent to the header) cannot place the lie; the pre-edit javadoc therefore ends with the lie sentence, at the position
rewrite_facade would have used (the end of the javadoc), and rewrite_facade adds nothing (checked: the sentence occurs once).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-79-probe of the fixture, the first
statement of findEnumValues was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t com.fasterxml.jackson.databind.ser.TestEnumSerialization::testEnumsWithJsonProperty`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at JacksonAnnotationIntrospector.findEnumValues(JacksonAnnotationIntrospector.java:205),
called from EnumValues.constructFromName(EnumValues.java:51) / EnumSerializer.construct; and
`-t com.fasterxml.jackson.databind.deser.TestEnumDeserialization::testEnumWithJsonPropertyRename` (the trigger): 1 failing test,
JsonMappingException: PROBE-REACHED. The facade is reached by existing tests, including the trigger.

Hosts (host_mode = "1500"; seeded draw `mr_lib.py preview JacksonDatabind-79
com/fasterxml/jackson/databind/introspect/JacksonAnnotationIntrospector.java 5`, seed 3737, used in draw order, none substituted):
  hop 1 util.TokenBuffer                  1893 lines  copyExplicitNames  placement: writes each explicit name found into the entry
                                                                         of names at the same index, leaves the others
  hop 2 deser.BeanDeserializerBase        1572 lines  explicitNamesOf    aggregation: creates the array of explicit names
  hop 3 ObjectMapper                      3929 lines  fillExplicitNames  fold: one pass over the values, one entry per value
  hop 4 deser.BasicDeserializerFactory    1945 lines  explicitNameOf     pass-through
  hop 5 ObjectReader                      1889 lines  findAnnotatedName  GOLD: the explicit name of one enum constant (its formal
                                                                         enum type, the constant's field there, the annotation)
Host sizes 1893, 1572, 3929, 1945, 1889; the smallest host is BeanDeserializerBase (1572 lines); the gold host has 1889 lines.

Fault (one-line omission of a special-case step in the gold): the step that takes an enum constant with a class body to its formal
enum type is dropped (`if (cls.getSuperclass() != Enum.class) { cls = cls.getSuperclass(); }` removed after
`Class<?> cls = en.getClass();`). The gold then reads as the ordinary routine "look up the constant's field in its class and read the
annotation". For a constant with a body, en.getClass() is the anonymous subclass, which declares no field of that name, so the lookup
fails and the constant is treated as having no explicit name. Trigger: the EXISTING test
TestEnumDeserialization::testEnumWithJsonPropertyRename; EnumWithPropertyAnno.B is annotated @JsonProperty("b") and has a class body
("force use of anonymous sub-class, to ensure things still work"); its first assertion fails with expected:<["[b]","a"]> but
was:<["[B]","a"]>. It is the only test whose enum has a constant that both has a body and carries @JsonProperty: constants with a
body and no annotation give null either way (testSubclassedEnums), annotated constants without a body are unchanged
(testEnumsWithJsonProperty*), and gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (the name that a JsonProperty annotation on the field of the given enum constant
defines for it) and is silent on class bodies; on the trigger input the variant returns null for B although its field carries
@JsonProperty("b"), so the contract is violated. The convention is pinned outside the gold: ClassUtil.findEnumType(Enum) ("enums with
'body' are sub-classes of the formal type": `if (ec.getSuperclass() != Enum.class) ec = ec.getSuperclass();`), used by
EnumValues.constructFromName ("Enum types with per-instance sub-classes need special handling") and EnumSerializer; the sibling
JacksonAnnotationIntrospector.findEnumValue (finds the constant's public field through value.getClass().getField, which also searches
the formal enum type). Passing tests: TestEnumSerialization::testSubclassedEnums and TestEnumDeserialization::testSubclassedEnums
(constants with a body through the chain), TestEnumSerialization::testEnumsWithJsonProperty and ::testEnumsWithJsonPropertyAsKey
(annotated constants through the chain).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: en supplies the class and the field name; it decides the result.
  T2 absent: cls is reassigned for a constant with a body and read by the field lookup; f is read by the annotation lookup; prop and n
     are read by the result; `if (prop == null)` and the empty-name ternary each choose between null and the annotation's value.
  T3 absent: no closed set is handled in part: the annotation's two outcomes (absent, empty name) both give null; no enum, type code
     or named format is enumerated.
  T4 absent: 'the name that a JsonProperty annotation on the field of given enum constant defines for it' and '@return Explicit name
     of the constant, if any; null if none' are met by lines of the body.
 Variant gold (javadoc, signature, `Class<?> cls = en.getClass();`, the field lookup with its NoSuchFieldException -> null, the
 annotation lookup, the empty-name ternary):
  T1 absent: en supplies the class and the field name; it decides the result.
  T2 absent: cls is initialised from en.getClass() (not a literal) and read by the lookup; f, prop and n reach the result; the catch
     returns null where no field is found; `if (prop == null)` and the ternary have two different outcomes each; no local is frozen
     or dead, no branch is dead.
  T3 absent: the gold has no treatment of class bodies at all ('No member handled'); its text names no kind of constant; the
     annotation's absent / empty-name outcomes are both handled.
  T4 absent: the javadoc is a general description of what the method computes ('the name that a JsonProperty annotation on the field
     of given enum constant defines for it'), addressed by the field and annotation lookups; '@return ... if any; null if none'
     names no case the body does not meet; no inline comment; identifiers (en, cls, f, prop, n, findAnnotatedName) name nothing the
     body does not meet.

Single owner: only the gold maps an enum value to its formal enum type and reads the annotation of the constant's field; hops 1-4
pass the values along and place the gold's results (hop 3 one entry per value, hop 1 writing non-null entries into names). An enum
value cannot be replaced by a caller (the constant B is the instance of the anonymous subclass, whichever way it is obtained), so once
the gold has missed B's field, "b" can appear only if a caller re-implements the lookup or replaces the gold. Declared alternatives
(G9): hop 4 passes the constant obtained from its declaring class's getEnumConstants() (the same object); hop 1 writes an explicit name
only into an entry that is still null; hop 3 fills the entries from the last value to the first. None makes the trigger pass.
Recorded bypasses (each discards or re-implements the gold): B-0 the facade's original body (scan of enumType's declared fields);
B-1 hop 4 returns `new JacksonAnnotationIntrospector().findEnumValue(value)` (the intact sibling; it returns name() for a value
without annotation, against hop 4's and hop 2's documented null for such values); B-2 hop 4 or hop 3 re-implements the field lookup
on ClassUtil.findEnumType(value).

Lie: the facade's javadoc claims the names found for an enum type are cached, so that the fields of each enum type are scanned only
once; no step of the chain caches anything or scans the fields of the enum type. It names neither class bodies nor the formal enum
type nor any hop."""

JAI = "src/main/java/com/fasterxml/jackson/databind/introspect/JacksonAnnotationIntrospector.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"

LIE = ("The names found for an enum type are cached, so that the fields of each enum type are scanned only once.")

GOLD_TEXT = '''/**
 * Method for finding the name that a {@link JsonProperty} annotation on the
 * field of given enum constant defines for it.
 *
 * @param en Enum constant to check
 *
 * @return Explicit name of the constant, if any; null if none
 */
public static String findAnnotatedName(Enum<?> en)
{
    Class<?> cls = en.getClass();
    if (cls.getSuperclass() != Enum.class) {
        cls = cls.getSuperclass();
    }
    Field f;
    try {
        f = cls.getDeclaredField(en.name());
    } catch (NoSuchFieldException e) {
        return null;
    }
    JsonProperty prop = f.getAnnotation(JsonProperty.class);
    if (prop == null) {
        return null;
    }
    String n = prop.value();
    return n.isEmpty() ? null : n;
}'''

HOP1 = '''/**
 * Helper method that copies explicit names of given enum values into the
 * entries of given array at the same index, leaving entries of values
 * without explicit name as they are.
 *
 * @param values Enum values to find explicit names for
 * @param names Array of names, one entry per enum value
 *
 * @return Array of names passed in
 */
public static String[] copyExplicitNames(Enum<?>[] values, String[] names)
{
    String[] explicit = BeanDeserializerBase.explicitNamesOf(values);
    for (int i = 0, end = values.length; i < end; ++i) {
        if (explicit[i] != null) {
            names[i] = explicit[i];
        }
    }
    return names;
}'''

HOP2 = '''/**
 * Helper method for finding explicit names of given enum values.
 *
 * @param values Enum values to find explicit names for
 *
 * @return Array that has the explicit name of each enum value at the same
 *    index, or null for a value that has none
 */
public static String[] explicitNamesOf(Enum<?>[] values)
{
    String[] result = new String[values.length];
    ObjectMapper.fillExplicitNames(values, result);
    return result;
}'''

HOP3 = '''/**
 * Helper method that assigns, for each of given enum values, its explicit
 * name (or null if it has none) to the entry of given array at the same
 * index.
 *
 * @param values Enum values to find explicit names for
 * @param result Array to assign names to; as long as <code>values</code>
 */
public static void fillExplicitNames(Enum<?>[] values, String[] result)
{
    for (int i = 0, end = values.length; i < end; ++i) {
        result[i] = BasicDeserializerFactory.explicitNameOf(values[i]);
    }
}'''

HOP4 = '''/**
 * Helper method for finding explicit name of given enum value, if any.
 *
 * @return Explicit name of the value, or null if it has none
 */
public static String explicitNameOf(Enum<?> value)
{
    return ObjectReader.findAnnotatedName(value);
}'''

DESIGN = {
 "instance": "JacksonDatabind-79", "project": "JacksonDatabind", "bug_id": 79, "seed": 3737,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the parameters enumValues and names, passed to hop 1 (enumType not passed; the chain resolves each value's formal "
                 "enum type itself); no field read or written, no write-back",
 "host_mode": "1500", "host_lines": [1893, 1572, 3929, 1945, 1889],
 "reachability_probe": "findEnumValues first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-JacksonDatabind-79-probe: TestEnumSerialization::testEnumsWithJsonProperty fails with "
                       "PROBE-REACHED at JacksonAnnotationIntrospector.findEnumValues(JacksonAnnotationIntrospector.java:205) via "
                       "EnumValues.constructFromName; TestEnumDeserialization::testEnumWithJsonPropertyRename fails with "
                       "JsonMappingException: PROBE-REACHED",
 "facade": {"file": JAI, "class": "com.fasterxml.jackson.databind.introspect.JacksonAnnotationIntrospector",
            "method": "findEnumValues", "near_line": 204},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/deser/TestEnumDeserialization.java",
             "test_class": "com.fasterxml.jackson.databind.deser.TestEnumDeserialization",
             "test_method": "testEnumWithJsonPropertyRename"},
 "expected_signature": "expected:<[\"[b]\",\"a\"]> but was:<[\"[B]\",\"a\"]>",
 "gold": {"method": "findAnnotatedName", "text": GOLD_TEXT,
          "fault": {"old": "        Class<?> cls = en.getClass();\n"
                           "        if (cls.getSuperclass() != Enum.class) {\n"
                           "            cls = cls.getSuperclass();\n"
                           "        }\n",
                    "new": "        Class<?> cls = en.getClass();\n"}},
 "pre_edits": {
   "chain": [{"file": JAI,
              "old": "    @Override // since 2.7\n"
                     "    public String[] findEnumValues(Class<?> enumType, Enum<?>[] enumValues, String[] names) {\n",
              "new": "    /**\n"
                     "     * Since 2.7, explicit names defined using {@link JsonProperty} are\n"
                     "     * found for all values of an enum type at once.\n"
                     "     * The names found for an enum type are cached, so that the fields of\n"
                     "     * each enum type are scanned only once.\n"
                     "     */\n"
                     "    @Override // since 2.7\n"
                     "    public String[] findEnumValues(Class<?> enumType, Enum<?>[] enumValues, String[] names) {\n"}],
 },
 "chain": {
   "facade_body": "return TokenBuffer.copyExplicitNames(enumValues, names);",
   "lie": LIE,
   "hops": [
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "copyExplicitNames",
      "imports": ["com.fasterxml.jackson.databind.deser.BeanDeserializerBase"], "text": HOP1},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "explicitNamesOf",
      "imports": [], "text": HOP2},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "fillExplicitNames",
      "imports": [], "text": HOP3},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "explicitNameOf",
      "imports": [], "text": HOP4},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "findAnnotatedName",
      "imports": ["java.lang.reflect.Field", "com.fasterxml.jackson.annotation.JsonProperty"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.util.ClassUtil::findEnumType",
              "com.fasterxml.jackson.databind.util.EnumValues::constructFromName",
              "com.fasterxml.jackson.databind.introspect.JacksonAnnotationIntrospector::findEnumValue"],
 "ownership_reason": "Only the gold maps an enum value to its formal enum type and reads the JsonProperty annotation of the "
                     "constant's field there; hops 1-4 pass the values along and place the gold's results (hop 3 one entry per "
                     "value, hop 1 writing the non-null entries into names). The enum value itself cannot be replaced by a caller: "
                     "the constant B is the instance of its anonymous subclass however it is obtained, so once the gold has looked "
                     "for B's field in that subclass and found none, the name 'b' can appear only if a caller re-implements the "
                     "lookup or replaces the gold. The gold's javadoc promises the name that a JsonProperty annotation on the field "
                     "of the given enum constant defines; for B, annotated @JsonProperty(\"b\"), the variant returns null. The "
                     "convention is pinned outside the gold: ClassUtil.findEnumType(Enum) ('enums with \"body\" are sub-classes of "
                     "the formal type': the superclass is taken when it is not Enum), used by EnumValues.constructFromName ('Enum "
                     "types with per-instance sub-classes need special handling') and EnumSerializer; the intact sibling "
                     "JacksonAnnotationIntrospector.findEnumValue finds the constant's public field through getField, which also "
                     "searches the formal enum type. testSubclassedEnums (ser and deser: constants with a body through the chain) "
                     "and testEnumsWithJsonProperty / testEnumsWithJsonPropertyAsKey (annotated constants through the chain) pass.",
 "ownership_tests": ["com.fasterxml.jackson.databind.ser.TestEnumSerialization::testSubclassedEnums",
                     "com.fasterxml.jackson.databind.deser.TestEnumDeserialization::testSubclassedEnums",
                     "com.fasterxml.jackson.databind.ser.TestEnumSerialization::testEnumsWithJsonProperty",
                     "com.fasterxml.jackson.databind.ser.TestEnumSerialization::testEnumsWithJsonPropertyAsKey"],
 "compensating": {
   "chain": [
     {"file": BDF, "old": "    return ObjectReader.findAnnotatedName(value);",
      "new": "    return ObjectReader.findAnnotatedName(value.getDeclaringClass().getEnumConstants()[value.ordinal()]);",
      "why": "hop 4 passes the constant obtained from its declaring class"},
     {"file": TB, "old": "        if (explicit[i] != null) {",
      "new": "        if (explicit[i] != null && names[i] == null) {",
      "why": "hop 1 writes an explicit name only into an entry that is still null"},
     {"file": OM, "old": "    for (int i = 0, end = values.length; i < end; ++i) {\n            result[i] = BasicDeserializerFactory",
      "new": "    for (int i = values.length - 1; i >= 0; --i) {\n            result[i] = BasicDeserializerFactory",
      "why": "hop 3 fills the entries from the last value to the first"},
   ],
 },
 "host_notes": "host_mode 1500 (batch8_tasks.json; five other public classes of >= 1500 lines on the checkout). Hosts are the "
               "recipe's seeded draw `mr_lib.py preview JacksonDatabind-79 "
               "com/fasterxml/jackson/databind/introspect/JacksonAnnotationIntrospector.java 5` (seed 3737; the draw excludes the "
               "facade's file, the only allowed-candidate file), used in draw order, none substituted: hop 1 util.TokenBuffer "
               "(1893 lines, anchor after canWriteBinaryNatively, seed 3837), hop 2 deser.BeanDeserializerBase (1572, after "
               "handledType, 3838), hop 3 ObjectMapper (3929, after setPropertyInclusion, 3839), hop 4 "
               "deser.BasicDeserializerFactory (1945, after findPropertyTypeDeserializer, 3840), hop 5 ObjectReader (gold, 1889, "
               "after without, 3841). All five are public top-level classes (BeanDeserializerBase and BasicDeserializerFactory "
               "abstract) in which a public static method compiles. The facade calls hop 1 by its simple name (the facade's class "
               "imports databind.util.*); hop 1 imports deser.BeanDeserializerBase; hops 2-4 see the next host through their "
               "existing wildcard imports (databind.*, databind.deser.*); the gold imports java.lang.reflect.Field and "
               "com.fasterxml.jackson.annotation.JsonProperty. Smallest host: BeanDeserializerBase, 1572 lines.",
}
