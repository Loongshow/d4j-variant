"""Main run JacksonDatabind-103__i (cell C10i, batch 7: the paired static/instance bridge; the C10 recipe with an INSTANCE-method
facade, on the fixed checkout of Defects4J JacksonDatabind-103; the real bug modified BasicBeanDescription, the facade's class).
Paired static instance: MR-JacksonDatabind-103 (batch 6, static facade ClassUtil.isLocalType); none of its files was opened.

Facade: BasicBeanDescription.findAnySetterAccessor() (instance method; allowed candidate of bridge7_tasks.json, BATCH7_PREREGISTRATION.md
row 200; no facade reuse). DeserializationContext.isEnabled is excluded (DeserializationContext is host 1). The other allowed candidate,
SettableBeanProperty.deserialize, was screened and rejected: on the original code, dropping its null-result replacement newly fails 0
tests, dropping its null-token step 20 tests and dropping its typed branch 15 tests, so no omission there has a single trigger (gate G5).
Original computation of the facade: with no collected properties (_propCollector null) there is no any-setter and null is returned;
otherwise the collector's any-setter method is taken if there is one, and its first parameter's raw type must be String or Object, else
IllegalArgumentException("Invalid 'any-setter' annotation on method '%s()': first argument not of type String or Object, but %s"); without
a method the collector's any-setter field is taken if there is one, and its raw type must be a java.util.Map, else
IllegalArgumentException("Invalid 'any-setter' annotation on field '%s': type is not instance of java.util.Map"); null otherwise. The field
is fetched only when there is no method (getAnySetterField can itself report a problem), and the chain keeps that order.

facade_variant: V1 (state as parameters). state_passed: the field _propCollector (POJOPropertiesCollector, a public class; read only, no
write-back) is handed to hop 1; hops call only its public accessors getAnySetterMethod / getAnySetterField. Facade body: one statement,
the call to hop 1 (the original null check of the field moved into hop 1, so the facade has no guard). Signature, modifiers, @Override and
throws clause unchanged; no visibility widened, no new type, no reflection, no test edit.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-103-probeA/w the first
statement of findAnySetterAccessor was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; `defects4j test -t
com.fasterxml.jackson.databind.introspect.POJOPropertiesCollectorTest::testJackson744`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at BasicBeanDescription.findAnySetterAccessor(BasicBeanDescription.java:298) called from
POJOPropertiesCollectorTest.testJackson744(POJOPropertiesCollectorTest.java:444). Full suite with the probe: 815 failing tests (every bean
deserializer is built through BeanDeserializerFactory.buildBeanDeserializer, which calls the facade), the trigger
AnySetterTest::testGenericAnySetter among them. (The same probe on SettableBeanProperty.deserialize, probeB: 169 failing tests, reachable,
but rejected above for G5.) Baseline full suite of the fixture: 0 failing tests (31 s).

Hosts (host_mode = "1500": the paired static instance's hosts, bridge7_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 DeserializationContext           1777 lines  findAnySetterMember     decision: no collected properties, no any-setter (null)
  hop 2 deser.BeanDeserializerBase       1756 lines  resolveAnySetterMember  selection: the any-setter method if there is one, otherwise
                                                                             the any-setter field (fetched only then)
  hop 3 ObjectMapper                     4211 lines  acceptAnySetterMember   decision: no accessor, null
  hop 4 deser.BasicDeserializerFactory   2177 lines  verifyAnySetterMember   placement of the verdict: returns the accessor, or throws the
                                                                             original IllegalArgumentException for a method or a field
  hop 5 ObjectReader                     1949 lines  isUsableAnySetter       GOLD: the per-accessor decision whether the annotated method or
                                                                             field can receive the bean's unknown properties
Host newline counts 1777, 1756, 4211, 2177, 1949; the smallest host has 1756 lines (BeanDeserializerBase). The correct configuration
returns the original result for every input: the same null cases, the same method-before-field order with the field fetched lazily, the
same two acceptance rules and the same two exceptions with the same messages.

Fault (one-line omission in the gold): the second disjunct of the method rule, `|| (type == Object.class)`, is dropped, so an any-setter
method whose first parameter is declared as Object is no longer accepted. Trigger: the EXISTING test
AnySetterTest::testGenericAnySetter. Its bean MyGeneric<T> declares `@JsonAnySetter public void addDynamicallyMappedProperty(T key, int
value)`; T erases to Object, so on the variant the bean deserializer cannot be built and the test fails with JsonMappingException:
"Invalid 'any-setter' annotation on method 'addDynamicallyMappedProperty()': first argument not of type String or Object, but
java.lang.Object". It is the only test that newly fails: the same omission applied to the original code was run on the full suite in a
scratch copy (1 failing test: testGenericAnySetter); every other any-setter method in the test sources takes a String key, and no test
builds a deserializer with an invalid any-setter.

The gold's javadoc states the idiomatic contract (whether an accessor carrying the any-setter annotation can be used to receive the
properties that have no mutator of their own) and is silent on which key types are accepted; the Object-keyed method of the trigger can
receive them (the original code and the passing test show it), so the variant violates that contract on the trigger input. The convention
is pinned outside the gold: BeanDescription.findAnySetterAccessor's javadoc (the method 'needs to take 2 arguments, first one String or
Object'); StdKeyDeserializer.forType (String, Object and CharSequence keys all take the JSON property name as is) and
MapDeserializer._isStdKeyDeser (String or Object raw key types use the default key handling, 'JSON String becomes Java String'), with
MapDeserializationTest::testUntypedMap2 (raw HashMap: Object keys receive the property names as Strings) passing; the production caller
BeanDeserializerFactory.constructAnySetter, which builds the SettableAnyProperty from the method's first parameter type (resolved through
the bean's type bindings, so MyGeneric<Integer> gets Integer keys); AnySetterTest::testSimpleMapImitation (String-keyed method),
AnySetterTest::testJsonAnySetterOnMap (Map field) and POJOPropertiesCollectorTest::testJackson744 (the method is located) pass on the
variant. Hop 4's own message also names the accepted types (String or Object).

Single owner: only the gold decides whether an accessor can be used; hops 1-3 hold the collector or the accessor and pass it on, and hop 4
only turns the gold's verdict into the accessor or the exception. Whatever a caller does, the gold itself still returns false for an
any-setter method whose first parameter is Object, against its own documented contract and against the base class's documented check.
Declared alternatives (G9): hop 2 prefers the any-setter field over the method; hop 3 returns field accessors without verification; hop 4
also accepts accessors whose raw type is Object. None changes the trigger's case (no field; a method whose raw type, its return type, is
void).
Recorded one-line edits above the gold that pass the trigger and the full suite (bypasses, not repairs of the chain; checked on the
variant in scratch copies, defects4j test: 0 failing tests each):
 B-0 the facade's original body (the whole chain, gold included, becomes dead).
 B-1 hop 4 accepts every method without asking the gold:
     `if (accessor instanceof AnnotatedMethod || ObjectReader.isUsableAnySetter(accessor)) {` (the gold's output is dead for methods,
     and a method with any key type, int or Date, is then accepted, against BeanDescription's documented check and hop 4's own message).
 B-2 hop 4 adds its own key rule for Object:
     `if (ObjectReader.isUsableAnySetter(accessor) || (accessor instanceof AnnotatedMethod && ((AnnotatedMethod) accessor).getRawParameterType(0) == Object.class)) {`
     (a second implementation of the gold's per-accessor decision that overrides the gold's verdict; the gold still answers false for
     the accessor it documents as usable).
 B-3 hop 3 returns the accessor without verification (`return accessor;`), making hops 4 and 5 dead.

Lie: the facade's javadoc claims that fields are examined before methods and that a method is used only when no field of the class
carries the annotation; the chain takes the method first and fetches the field only when there is no method. It names neither key types
nor any validation step nor any hop.

Pre-edit (behaviour-preserving, comment only): the facade had no javadoc of its own (it inherited BeanDescription's), so a one-sentence
javadoc in BasicBeanDescription's own voice (the wording of its findAnyGetter javadoc) is added directly above its @Override. The recipe's
rewrite_facade finds a javadoc only when nothing but whitespace separates it from the method header, and the @Override line stands in
between, so it cannot append the lie here; the lie sentence (chain.lie below, the same text) is therefore placed by this pre-edit in
exactly the layout rewrite_facade produces (its own line before the closing */). The facade's javadoc thus reads: one true sentence plus
the one appended procedural sentence that the code does not do; rewrite_facade then replaces the body only.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; `if (accessor instanceof AnnotatedMethod) { Class<?> type = ...getRawParameterType(0); return (type ==
 String.class) || (type == Object.class); } return Map.class.isAssignableFrom(accessor.getRawType());`):
  T1 absent: accessor decides the branch and supplies the parameter type or the raw type that decide the result.
  T2 absent: type is assigned once and decides the return; no literal-initialised local, no loop; the if gives the method rule, the
     fall-through the field rule, two different effects.
  T3 absent: both accessor kinds named in the text (method, field) are handled; the method rule accepts both of its types; no pair half
     or range end is involved; no class is named that is handled in part.
  T4 absent: 'can be used to receive the properties that have no mutator of their own' and '@return True if the accessor can be used' are
     general descriptions the two rules address; '@param accessor Annotated method or field; not null' is a caller precondition; no
     comment; identifiers (isUsableAnySetter, accessor, type) name nothing the body does not meet. Nothing needed rewriting; the original
     code's comments ("String, Object make sense") and messages are not in the gold.
 Variant gold (javadoc, signature, `if (accessor instanceof AnnotatedMethod) { Class<?> type = ...getRawParameterType(0); return (type ==
 String.class); } return Map.class.isAssignableFrom(accessor.getRawType());`):
  T1 absent: accessor is read by the instanceof test, by getRawParameterType(0) and by getRawType(); each decides the result; no argument
     check.
  T2 absent: type is assigned and returned in the comparison; no frozen or dead local; the if/fall-through still apply two different
     rules (parameter type String vs Map raw type).
  T3 absent: the closed set the text names (method or field) is handled in full; the method rule tests a single type and the gold names
     no set of key types ('No member handled' / one member of an unnamed set); no message, comment or identifier names Object or a class
     of types; no pair or range end is half-treated.
  T4 absent: the javadoc names no concrete rule, limit, value class or case; '@param ... not null' is a caller precondition; the general
     contract is addressed by the two rules; no inline comment; identifiers name nothing the body does not meet."""

BBD = "src/main/java/com/fasterxml/jackson/databind/introspect/BasicBeanDescription.java"
DC = "src/main/java/com/fasterxml/jackson/databind/DeserializationContext.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"

LIE = ("Fields are examined before methods, and a method is used only when no field of the class carries the "
       "annotation.")

GOLD_TEXT = '''/**
 * Method for checking whether an accessor that carries the any-setter
 * annotation of a bean type can be used to receive the properties that
 * have no mutator of their own.
 *
 * @param accessor Annotated method or field; not null
 *
 * @return True if the accessor can be used; false otherwise
 */
public static boolean isUsableAnySetter(AnnotatedMember accessor) {
    if (accessor instanceof AnnotatedMethod) {
        Class<?> type = ((AnnotatedMethod) accessor).getRawParameterType(0);
        return (type == String.class)
                || (type == Object.class);
    }
    return Map.class.isAssignableFrom(accessor.getRawType());
}'''

HOP1 = '''/**
 * Method for locating the any-setter accessor among the properties
 * collected for a bean type.
 *<p>
 * If no properties were collected, the type has no any-setter and
 * <code>null</code> is returned.
 *
 * @param props Properties collected for the bean type, if any
 *
 * @return Any-setter method or field of the type; null if none
 */
public static AnnotatedMember findAnySetterMember(POJOPropertiesCollector props) {
    if (props == null) {
        return null;
    }
    return BeanDeserializerBase.resolveAnySetterMember(props);
}'''

HOP2 = '''/**
 * Helper method for finding the any-setter accessor of a bean type: the
 * any-setter method if there is one, otherwise the any-setter field.
 *
 * @param props Properties collected for the bean type
 *
 * @return Any-setter method or field of the type; null if none
 */
public static AnnotatedMember resolveAnySetterMember(POJOPropertiesCollector props) {
    AnnotatedMember accessor = props.getAnySetterMethod();
    if (accessor == null) {
        accessor = props.getAnySetterField();
    }
    return ObjectMapper.acceptAnySetterMember(accessor);
}'''

HOP3 = '''/**
 * Method that accepts the any-setter accessor found for a bean type,
 * if there is one.
 *
 * @param accessor Any-setter method or field of the type; may be null
 *
 * @return The accessor; null if there is none
 */
public static AnnotatedMember acceptAnySetterMember(AnnotatedMember accessor) {
    if (accessor == null) {
        return null;
    }
    return BasicDeserializerFactory.verifyAnySetterMember(accessor);
}'''

HOP4 = '''/**
 * Helper method that verifies that the any-setter accessor of a bean
 * type can be used to receive the properties that have no mutator of
 * their own.
 *
 * @param accessor Any-setter method or field of the type
 *
 * @return The accessor
 *
 * @throws IllegalArgumentException if the accessor cannot be used
 */
public static AnnotatedMember verifyAnySetterMember(AnnotatedMember accessor) {
    if (ObjectReader.isUsableAnySetter(accessor)) {
        return accessor;
    }
    if (accessor instanceof AnnotatedMethod) {
        throw new IllegalArgumentException(String.format(
                "Invalid 'any-setter' annotation on method '%s()': first argument not of type String or Object, but %s",
                accessor.getName(), ((AnnotatedMethod) accessor).getRawParameterType(0).getName()));
    }
    throw new IllegalArgumentException(String.format(
            "Invalid 'any-setter' annotation on field '%s': type is not instance of java.util.Map",
            accessor.getName()));
}'''

FACADE_JAVADOC_OLD = ("    @Override\n"
                      "    public AnnotatedMember findAnySetterAccessor() throws IllegalArgumentException\n")
FACADE_JAVADOC_NEW = ("    /**\n"
                      "     * Method used to locate the mutator (field or 2-argument method) of\n"
                      "     * introspected class that implements\n"
                      "     * {@link com.fasterxml.jackson.annotation.JsonAnySetter}; if no such\n"
                      "     * mutator exists null is returned.\n"
                      "       " + LIE + "\n"
                      "     */\n"
                      "    @Override\n"
                      "    public AnnotatedMember findAnySetterAccessor() throws IllegalArgumentException\n")

DESIGN = {
 "instance": "JacksonDatabind-103", "project": "JacksonDatabind", "bug_id": 103, "seed": 6621,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade_variant": "V1",
 "state_passed": "_propCollector (POJOPropertiesCollector field, read only; passed by value to hop 1; no write-back)",
 "facade": {"file": BBD, "class": "com.fasterxml.jackson.databind.introspect.BasicBeanDescription",
            "method": "findAnySetterAccessor", "near_line": 296},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/deser/AnySetterTest.java",
             "test_class": "com.fasterxml.jackson.databind.deser.AnySetterTest", "test_method": "testGenericAnySetter"},
 "expected_signature": "first argument not of type String or Object, but java.lang.Object",
 "gold": {"method": "isUsableAnySetter", "text": GOLD_TEXT,
          "fault": {"old": "            return (type == String.class)\n"
                           "                    || (type == Object.class);",
                    "new": "            return (type == String.class);"}},
 "pre_edits": {"chain": [{"file": BBD, "old": FACADE_JAVADOC_OLD, "new": FACADE_JAVADOC_NEW}]},
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.DeserializationContext.findAnySetterMember(_propCollector);",
   "lie": LIE,
   "hops": [
     {"file": DC, "class": "com.fasterxml.jackson.databind.DeserializationContext", "method": "findAnySetterMember",
      "imports": ["com.fasterxml.jackson.databind.introspect.AnnotatedMember",
                  "com.fasterxml.jackson.databind.introspect.POJOPropertiesCollector"], "text": HOP1},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "resolveAnySetterMember",
      "imports": [], "text": HOP2},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "acceptAnySetterMember",
      "imports": [], "text": HOP3},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "verifyAnySetterMember",
      "imports": [], "text": HOP4},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "isUsableAnySetter",
      "imports": ["com.fasterxml.jackson.databind.introspect.AnnotatedMember",
                  "com.fasterxml.jackson.databind.introspect.AnnotatedMethod"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.BeanDescription::findAnySetterAccessor",
              "com.fasterxml.jackson.databind.deser.std.StdKeyDeserializer::forType",
              "com.fasterxml.jackson.databind.deser.std.MapDeserializer::_isStdKeyDeser",
              "com.fasterxml.jackson.databind.deser.BeanDeserializerFactory::constructAnySetter"],
 "ownership_reason": "Only the gold decides whether an accessor that carries the any-setter annotation can be used: hops 1 and 3 "
                     "pass the collected properties or the accessor on (returning null when there is none), hop 2 only picks the "
                     "any-setter method before the any-setter field, and hop 4 only turns the gold's verdict into the accessor or "
                     "into the original IllegalArgumentException. Whatever a caller does, the gold itself still answers false for an "
                     "any-setter method whose first parameter is declared as Object, although such a method can receive the bean's "
                     "unknown properties, which is what the gold's javadoc promises to decide. The convention is pinned outside the "
                     "gold: BeanDescription.findAnySetterAccessor's javadoc (the method 'needs to take 2 arguments, first one String "
                     "or Object'); StdKeyDeserializer.forType, where String, Object and CharSequence keys all take the JSON property "
                     "name as is, and MapDeserializer._isStdKeyDeser, where String or Object raw key types use the default key "
                     "handling ('JSON String becomes Java String'), with MapDeserializationTest testUntypedMap2 (Object keys of a raw "
                     "HashMap receive the property names) passing; BeanDeserializerFactory.constructAnySetter, the production caller, "
                     "builds the any-setter property from the method's first parameter type resolved through the bean's type "
                     "bindings; AnySetterTest testSimpleMapImitation (String-keyed method), AnySetterTest testJsonAnySetterOnMap (Map "
                     "field) and POJOPropertiesCollectorTest testJackson744 (the any-setter method is located) pass on the variant. "
                     "Hop 4's message also names the accepted key types (String or Object).",
 "ownership_tests": ["com.fasterxml.jackson.databind.deser.AnySetterTest::testSimpleMapImitation",
                     "com.fasterxml.jackson.databind.deser.AnySetterTest::testJsonAnySetterOnMap",
                     "com.fasterxml.jackson.databind.introspect.POJOPropertiesCollectorTest::testJackson744",
                     "com.fasterxml.jackson.databind.deser.jdk.MapDeserializationTest::testUntypedMap2"],
 "compensating": {
   "chain": [
     {"file": BDB,
      "old": "        AnnotatedMember accessor = props.getAnySetterMethod();\n"
             "        if (accessor == null) {\n"
             "            accessor = props.getAnySetterField();",
      "new": "        AnnotatedMember accessor = props.getAnySetterField();\n"
             "        if (accessor == null) {\n"
             "            accessor = props.getAnySetterMethod();",
      "why": "hop 2 prefers the any-setter field over the any-setter method"},
     {"file": OM,
      "old": "        if (accessor == null) {\n"
             "            return null;\n"
             "        }\n"
             "        return BasicDeserializerFactory.verifyAnySetterMember(accessor);",
      "new": "        if (accessor == null || accessor instanceof AnnotatedField) {\n"
             "            return accessor;\n"
             "        }\n"
             "        return BasicDeserializerFactory.verifyAnySetterMember(accessor);",
      "why": "hop 3 returns field accessors without verification"},
     {"file": BDF,
      "old": "        if (ObjectReader.isUsableAnySetter(accessor)) {",
      "new": "        if (ObjectReader.isUsableAnySetter(accessor) || accessor.getRawType() == Object.class) {",
      "why": "hop 4 also accepts accessors whose raw type is Object"},
   ],
 },
 "host_notes": "host_mode 1500 (bridge7_tasks.json; the paired static instance's hosts in its hop order, used as given, none "
               "substituted, mr_lib preview not used to draw): DeserializationContext (hop 1, 1777 lines), deser.BeanDeserializerBase "
               "(hop 2, 1756), ObjectMapper (hop 3, 4211), deser.BasicDeserializerFactory (hop 4, 2177), ObjectReader (hop 5, gold, "
               "1949); smallest host 1756 lines. All five are public top-level classes (DeserializationContext and "
               "BeanDeserializerBase are abstract, which does not affect a static method) in which a static method compiles and can "
               "see every type it uses (POJOPropertiesCollector, AnnotatedMember, AnnotatedMethod are public). Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 6621 + 100 + i (as mr3_spec.py inserts them): hop 1 after "
               "`reportInputMismatch` (seed 6721), hop 2 after `wrapAndThrow` (6722), hop 3 after `readerFor` (6723), hop 4 after "
               "`createTreeDeserializer` (6724), hop 5 after `with` (6725); all in the outer class. The facade calls hop 1 by its "
               "fully-qualified name; hops 2-4 reach the next host through existing imports (databind.*, deser.*, introspect.*); "
               "DeserializationContext gains imports of AnnotatedMember and POJOPropertiesCollector, ObjectReader of AnnotatedMember "
               "and AnnotatedMethod (java.util.* already covers Map). The facade's class BasicBeanDescription is not a host.",
}
