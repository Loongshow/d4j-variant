"""Main run JacksonDatabind-21__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J JacksonDatabind-21; the real bug modified JacksonAnnotationIntrospector, the target class). Batch 8: the bug has no
static-facade instance (pool v2: no_tested_static), so there is no static pair.

Facade: JacksonAnnotationIntrospector.findEnumValue(Enum<?>) (the single allowed candidate of batch8_tasks.json /
BATCH8_PREREGISTRATION.md row 250; facade_planned_by = null, no facade reuse). Original computation: the enumeration value's
public static field of the same name is looked up by reflection (value.getClass().getField(value.name())); if the field carries
@JsonProperty with a non-empty value, that value is returned; otherwise (no field, no annotation -- the original reaches this case
through a caught NullPointerException --, or an empty value) value.name() is returned.

facade_variant: V1 (state as parameters). The candidate profile labels it V0 (PURE): the method reads and writes no field of the
introspector; the only state is its parameter, which the facade passes unchanged to hop 1, and it returns hop 1's String. No method
of the receiver is needed (no V2), no private method is called (no V4), no package-private type is involved (no V3/V5). No
signature, modifier, @Override, throws change; no new type; no test edit. The chain adds no reflection of its own: the gold carries
the original's own reflective field lookup (Class field lookup and getAnnotation), which is the method's computation (the
original's comment explains that AnnotatedClass cannot be used for enum values).
state_passed: the parameter value (Enum<?>) only; no field is read or written back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-21-probe of the
fixture, the first statement of findEnumValue was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
`defects4j test -t com.fasterxml.jackson.databind.deser.TestEnumDeserialization::testEnumWithJsonPropertyRename`: 1 failing test,
JsonMappingException: PROBE-REACHED, caused by java.lang.IllegalStateException: PROBE-REACHED at
JacksonAnnotationIntrospector.findEnumValue(JacksonAnnotationIntrospector.java:68), reached from ObjectMapper.writeValueAsString at
TestEnumDeserialization.java:472. Full suite with the probe: 57 failing tests (findEnumValue has production callers: EnumValues
.constructFromName for serialization and EnumResolver.constructFor for deserialization, so every enum serialised or read by name
reaches it). The facade is reached by existing tests.

Hosts (host_mode = "1500"; `mr_lib.py preview JacksonDatabind-21 com/fasterxml/jackson/databind/introspect/
JacksonAnnotationIntrospector.java 5`, instance seed 2613; the draw excludes the facade's file; used in draw order, none
substituted):
  hop 1 deser.BeanDeserializerBase      1533 lines  enumValueName         decision: the explicit name if there is one, else name()
  hop 2 ObjectMapper                    3831 lines  explicitNameFor       pass-through
  hop 3 ObjectReader                    1760 lines  resolveEnumName       pass-through
  hop 4 util.TokenBuffer                1802 lines  enumPropertyName      pass-through
  hop 5 deser.BasicDeserializerFactory  1895 lines  findExplicitEnumName  GOLD: the formal enum type of the value, the field of
                                                                          that type named like the value, its @JsonProperty, and
                                                                          the non-empty-value decision
Host sizes 1533, 3831, 1760, 1802, 1895 (hop order); the smallest host is BeanDeserializerBase (1533 lines); the gold host has 1895.
The correct configuration returns the original String for every enumeration value: an enum constant with a body is an instance of
an anonymous subclass of the formal enum type (getSuperclass() != Enum.class), and the gold then looks the field up on the formal
type, where every constant is a declared public static field; getField (public, inherited) in the original finds the same field.
No field / no annotation / an empty value give null at the gold and value.name() at hop 1, as the original.

Fault (one-line omission of a special-case step in the gold): the step that replaces the runtime class of a constant with a body by
its superclass, the formal enum type, is dropped, so the field lookup is made on the anonymous subclass, which declares no field of
that name; the gold returns null and hop 1 falls back to name(). The gold then reads as the ordinary routine "look up the field
named like the value on its class, read its @JsonProperty, return a non-empty value". Trigger: the EXISTING test
TestEnumDeserialization::testEnumWithJsonPropertyRename (also the Defects4J trigger of the bug): EnumWithPropertyAnno.A
(@JsonProperty("a"), no body) still gives "a", B (@JsonProperty("b"), with a body: an anonymous subclass "to ensure things still
work") gives "B", so assertEquals("[\"b\",\"a\"]", json) fails with expected:<["[b]","a"]> but was:<["[B]","a"]>. It is the only
test that newly fails: it is the only test whose enum constants carry @JsonProperty, and constants with a body but no annotation
(EnumWithSubClass in TestEnumSerialization / TestEnumDeserialization) give name() either way.

The gold's javadoc states the idiomatic contract (the explicit name a @JsonProperty annotation gives to an enumeration value, null
if none) and is silent on constants with a body; B has the explicit name "b". The convention is pinned outside the gold:
ClassUtil.findEnumType(Enum<?>) ("This is either class of enum instance (for 'simple' enumerations), or its superclass (for enums
with instance fields or methods)"; "enums with 'body' are sub-classes of the formal type"; the same getSuperclass() != Enum.class
step) and ClassUtil.findEnumType(Class<?>), used by EnumValues.constructFromName ("Enum types with per-instance sub-classes need
special handling") before it asks the introspector for each constant's value, with TestClassUtil::testFindEnumType and the
subclassed-enum tests TestEnumSerialization::testSubclassedEnums and TestEnumDeserialization::testSubclassedEnums passing.

Single owner: only the gold looks at the class of the value, its fields and annotations; hops 2-4 pass the value along and hop 1 only
chooses between the gold's result and name(). Every value a caller can hand on for B (the constant itself, the same constant found
through getDeclaringClass().getEnumConstants() or ClassUtil.findEnumType(..).getEnumConstants(), Enum.valueOf) is the same object of
the anonymous subclass, so no change of the argument above the gold changes what the gold looks up; a different fallback at hop 1
(toString()) gives "bb" for B and changes toString-overriding enums. Declared alternatives (G9): hop 1 falls back to toString(); hop 2
passes the constant found through the declaring class's constants; hop 3 passes the constant found through
ClassUtil.findEnumType. Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-1 any hop (or the facade) re-deriving the name itself, e.g. hop 1 doing its own
     value.getDeclaringClass().getField(value.name()).getAnnotation(JsonProperty.class) lookup instead of using the gold's result,
     makes the gold dead.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Pre-edit (comment only): the lie is placed in the facade's javadoc by a pre-edit, as two javadoc lines after the existing text
("Since 2.6, we have supported use of {@link JsonProperty} for specifying explicit serialized name"), because the facade's javadoc
is separated from its header by @Override, so the recipe's rewrite_facade finds no javadoc adjacent to the header and appends
nothing (it is called with the same sentence and leaves the javadoc unchanged). The resulting text is the recipe's: the one lie
sentence appended at the end of the facade's own javadoc; the @Override annotation stays where it is.

Lie: the facade's javadoc claims the explicit name is located by matching the ordinal of the value against the declaration order of
the annotated constants; the chain looks the field up by the value's name and never uses the ordinal or any declaration order. It
names neither constants with a body, the formal type, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: value gives the class whose field is looked up and the field's name (value.name()); no argument check.
  T2 absent: enumType is initialised from value.getClass() (not a literal), reassigned by the body decision and read by the field
     lookup; prop is read by the null decision and gives name; name is read by the empty decision and returned; no loop; the three
     decisions (superclass, prop == null, empty) each change the result or avoid a throw.
  T3 absent: the null and empty decisions concern different values (the annotation, its String); no enum, type code, pair, range
     end or named format member is left out.
  T4 absent: 'the explicit name that a JsonProperty annotation gives to an enumeration value' is met by the lookup and the return of
     prop.value(); '@return ... if one is given; null if not' is met by the three null returns (no field, no annotation, empty name).
 Variant gold (javadoc, signature, enumType = value.getClass(), the declared field named value.name() and its @JsonProperty,
 null when the field or the annotation is missing, the value of the annotation unless it is empty):
  T1 absent: value is read for its class and for its name, both of which decide the field looked up and so the result.
  T2 absent: enumType is initialised from value.getClass() (not a literal) and read by the lookup; prop is read by a decision and
     gives name; name is read by a decision and returned; no loop, cursor, counter, flag or best-so-far; both decisions and the
     catch lead to different outcomes from the fall-through (prop == null avoids a NullPointerException, the ternary returns null
     or the name).
  T3 absent: no class of enumeration values (simple / with a body) is handled at all ('No member handled'); the null and empty
     tests are on different values (the annotation and its String), not siblings of one set; no enum, type code, pair or range
     end; the gold's text names no class of values (no "simple", "body", "subclass", "constant with methods").
  T4 absent: 'locating the explicit name that a JsonProperty annotation gives to an enumeration value' is a general description
     that the lookup and the return of prop.value() address; '@param value Enumeration value to find the name for' is a caller
     description; '@return Explicit name of the value, if one is given; null if not' is met by the returns; no inline comment; the
     identifiers enumType, prop and name name what they hold."""

JAI = "src/main/java/com/fasterxml/jackson/databind/introspect/JacksonAnnotationIntrospector.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"

GOLD_TEXT = '''/**
 * Helper method for locating the explicit name that a {@link JsonProperty}
 * annotation gives to an enumeration value.
 *
 * @param value Enumeration value to find the name for
 *
 * @return Explicit name of the value, if one is given; null if not
 */
public static String findExplicitEnumName(Enum<?> value)
{
    Class<?> enumType = value.getClass();
    if (enumType.getSuperclass() != Enum.class) {
        enumType = enumType.getSuperclass();
    }
    JsonProperty prop;
    try {
        prop = enumType.getDeclaredField(value.name()).getAnnotation(JsonProperty.class);
    } catch (NoSuchFieldException e) {
        return null;
    }
    if (prop == null) {
        return null;
    }
    String name = prop.value();
    return name.isEmpty() ? null : name;
}'''

HOP1 = '''/**
 * Helper method for determining the String value to use for given
 * enumeration value: the explicit name given to it, if any;
 * otherwise its {@link Enum#name()}.
 */
public static String enumValueName(Enum<?> value)
{
    String explicit = ObjectMapper.explicitNameFor(value);
    return (explicit == null) ? value.name() : explicit;
}'''

HOP2 = '''/**
 * Method for finding the explicit name given to specified
 * enumeration value, if any.
 *
 * @return Explicit name of the value; null if it has none
 */
public static String explicitNameFor(Enum<?> value) {
    return ObjectReader.resolveEnumName(value);
}'''

HOP3 = '''/**
 * Method for resolving the explicit name of given enumeration value.
 *
 * @return Explicit name of the value, if any; null if none
 */
public static String resolveEnumName(Enum<?> value) {
    return TokenBuffer.enumPropertyName(value);
}'''

HOP4 = '''/**
 * Helper method for accessing the explicit property name given
 * to an enumeration value.
 *
 * @return Explicit name, if any; null otherwise
 */
public static String enumPropertyName(Enum<?> value) {
    return BasicDeserializerFactory.findExplicitEnumName(value);
}'''

DESIGN = {
 "instance": "JacksonDatabind-21", "project": "JacksonDatabind", "bug_id": 21, "seed": 2613,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the parameter value (Enum<?>) only, passed unchanged to hop 1; no field read, no write-back (profile: V0, PURE)",
 "host_mode": "1500", "host_lines": [1533, 3831, 1760, 1802, 1895],
 "reachability_probe": "findEnumValue first statement made to throw IllegalStateException(\"PROBE-REACHED\"): "
                       "TestEnumDeserialization::testEnumWithJsonPropertyRename fails with JsonMappingException: PROBE-REACHED, "
                       "caused by IllegalStateException: PROBE-REACHED at JacksonAnnotationIntrospector.findEnumValue"
                       "(JacksonAnnotationIntrospector.java:68), from TestEnumDeserialization.java:472; full suite with the probe: "
                       "57 failing tests (production callers EnumValues.constructFromName, EnumResolver.constructFor)",
 "facade": {"file": JAI, "class": "com.fasterxml.jackson.databind.introspect.JacksonAnnotationIntrospector",
            "method": "findEnumValue", "near_line": 66},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/deser/TestEnumDeserialization.java",
             "test_class": "com.fasterxml.jackson.databind.deser.TestEnumDeserialization",
             "test_method": "testEnumWithJsonPropertyRename"},
 "expected_signature": "expected:<[\"[b]\",\"a\"]> but was:<[\"[B]\",\"a\"]>",
 "gold": {"method": "findExplicitEnumName", "text": GOLD_TEXT,
          "fault": {"old": "        Class<?> enumType = value.getClass();\n"
                           "        if (enumType.getSuperclass() != Enum.class) {\n"
                           "            enumType = enumType.getSuperclass();\n"
                           "        }\n",
                    "new": "        Class<?> enumType = value.getClass();\n"}},
 "pre_edits": {
   "chain": [{"file": JAI,
              "old": "     * Since 2.6, we have supported use of {@link JsonProperty} for specifying\n"
                     "     * explicit serialized name\n"
                     "     */\n",
              "new": "     * Since 2.6, we have supported use of {@link JsonProperty} for specifying\n"
                     "     * explicit serialized name\n"
                     "     * The explicit name is located by matching the ordinal of the value against\n"
                     "     * the declaration order of the annotated constants.\n"
                     "     */\n"}],
 },
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.deser.BeanDeserializerBase.enumValueName(value);",
   "lie": "The explicit name is located by matching the ordinal of the value against the declaration order of the annotated "
          "constants.",
   "hops": [
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "enumValueName",
      "imports": [], "text": HOP1},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "explicitNameFor",
      "imports": [], "text": HOP2},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "resolveEnumName",
      "imports": ["com.fasterxml.jackson.databind.util.TokenBuffer"], "text": HOP3},
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "enumPropertyName",
      "imports": ["com.fasterxml.jackson.databind.deser.BasicDeserializerFactory"], "text": HOP4},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "findExplicitEnumName",
      "imports": ["com.fasterxml.jackson.annotation.JsonProperty"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.util.ClassUtil::findEnumType",
              "com.fasterxml.jackson.databind.util.EnumValues::constructFromName"],
 "ownership_reason": "Only the gold looks at the class of the enumeration value, its fields and the @JsonProperty annotation; "
                     "hops 2-4 pass the value along unchanged and hop 1 only chooses between the gold's result and name(). "
                     "The gold's javadoc promises the explicit name a JsonProperty annotation gives to an enumeration value, "
                     "which for EnumWithPropertyAnno.B is \"b\", not null. No change of the argument above the gold helps: "
                     "every Enum a caller can hand on for B (the value, the constant found through getDeclaringClass()"
                     ".getEnumConstants() or ClassUtil.findEnumType(..).getEnumConstants(), Enum.valueOf) is the same object of "
                     "the anonymous subclass; a different fallback at hop 1 (toString()) gives \"bb\". The convention is pinned "
                     "outside the gold: ClassUtil.findEnumType(Enum<?>) (the formal enumeration type is the class of the "
                     "instance for simple enumerations and its superclass for enums with instance fields or methods; 'enums "
                     "with body are sub-classes of the formal type', the same getSuperclass() != Enum.class step) and "
                     "EnumValues.constructFromName ('Enum types with per-instance sub-classes need special handling', via "
                     "ClassUtil.findEnumType) with TestClassUtil testFindEnumType and the subclassed-enum serialization and "
                     "deserialization tests passing.",
 "ownership_tests": ["com.fasterxml.jackson.databind.util.TestClassUtil::testFindEnumType",
                     "com.fasterxml.jackson.databind.ser.TestEnumSerialization::testSubclassedEnums",
                     "com.fasterxml.jackson.databind.deser.TestEnumDeserialization::testSubclassedEnums"],
 "compensating": {
   "chain": [
     {"file": BDB, "old": "return (explicit == null) ? value.name() : explicit;",
      "new": "return (explicit == null) ? value.toString() : explicit;",
      "why": "hop 1 falls back to the toString() of the value instead of its name()"},
     {"file": OM, "old": "return ObjectReader.resolveEnumName(value);",
      "new": "return ObjectReader.resolveEnumName(value.getDeclaringClass().getEnumConstants()[value.ordinal()]);",
      "why": "hop 2 passes the constant found through the constants of the value's declaring class"},
     {"file": OR, "old": "return TokenBuffer.enumPropertyName(value);",
      "new": "return TokenBuffer.enumPropertyName(com.fasterxml.jackson.databind.util.ClassUtil.findEnumType(value).getEnumConstants()[value.ordinal()]);",
      "why": "hop 3 passes the constant found through the formal enumeration type"},
   ],
 },
 "host_notes": "host_mode 1500 (batch8_tasks.json; n1500_other_checkout = 5, so the pool is exactly the five public classes of "
               ">= 1500 lines other than the facade's file). mr_lib.py preview JacksonDatabind-21 com/fasterxml/jackson/databind/"
               "introspect/JacksonAnnotationIntrospector.java 5 with the instance seed 2613 draws, in order: "
               "deser.BeanDeserializerBase (hop 1, 1533 lines; the smallest host; abstract, which does not affect a static "
               "method), ObjectMapper (hop 2, 3831), ObjectReader (hop 3, 1760), util.TokenBuffer (hop 4, 1802), "
               "deser.BasicDeserializerFactory (hop 5, gold, 1895; abstract). None substituted; all five are public top-level "
               "classes in which a static method compiles. Anchors from the recipe (seed 2613 + 100 + i): hop 1 after "
               "`findProperty` (line 867, seed 2713), hop 2 after `canSerialize` (2541, 2714), hop 3 after `readValues` (990, "
               "2715), hop 4 after `canWriteTypeId` (874, 2716), hop 5 after `findPropertyContentTypeDeserializer` (1490, "
               "2717). The facade calls hop 1 by its fully-qualified name; ObjectMapper is visible in BeanDeserializerBase "
               "through its databind.* import and ObjectReader is in ObjectMapper's package; ObjectReader, TokenBuffer and "
               "BasicDeserializerFactory get one import each (TokenBuffer, BasicDeserializerFactory, JsonProperty).",
}
