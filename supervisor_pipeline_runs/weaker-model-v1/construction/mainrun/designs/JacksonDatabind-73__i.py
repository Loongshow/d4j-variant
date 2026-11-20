"""Main run JacksonDatabind-73__i (cell C10i, batch 9, sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed
checkout of Defects4J JacksonDatabind-73; the real bug modified POJOPropertiesCollector and POJOPropertyBuilder, and the facade's class
is POJOPropertyBuilder). No static pair (BUILD_BRIEF_C10I_B8_NOTE section 1: pool v2 found no tested static facade).

Facade: POJOPropertyBuilder.getMutator() (the only allowed candidate of batch9_tasks.json; facade_planned_by null, no facade reuse).
Original computation of the facade: the member to use for changing value of the property, by precedence: the constructor parameter
(getConstructorParameter(), itself preferring a parameter of a constructor over one of a factory method), else the setter
(getSetter(), which resolves conflicting setters), else the field (getField()); null when the property has none of them.

facade_variant: V2 (receiver as parameter). The computation needs only public methods of the receiver (hasConstructorParameter,
getConstructorParameter, hasSetter, getSetter, getField; has*() is exactly "the linked list is non-null", which is exactly when the
matching get*() is non-null, so the has/get form is equivalent to the original null tests); no private field is read (no V1), no
private method is called (no V4), no package-private type passes the chain (POJOPropertyBuilder and AnnotatedMember are public; no
V3/V5). The facade passes `this`, typed as its declaring class POJOPropertyBuilder, to hop 1 and returns hop 1's result. No
signature, modifier, @Override or throws change; no new type; no reflection; no test edit.
state_passed: the receiver `this` (as POJOPropertyBuilder) to hop 1; no field is read or written by the facade, no write-back.
Facade javadoc: getMutator had none in POJOPropertyBuilder (its javadoc lives on BeanPropertyDefinition.getMutator), so a pre_edit
adds a javadoc in the class's own voice (the declaring abstract method's sentence) above the existing @Override. The recipe's
rewrite_facade only finds a javadoc that directly precedes the method header, and this file's house style (452 occurrences in the
source tree, none the other way round) puts @Override between the javadoc and the header; so the pre_edit carries the lie sentence
too, in exactly the layout rewrite_facade gives it (the sentence on its own line before the closing */), and rewrite_facade then
splices the body and appends nothing. `lie` below is that same sentence.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-73-probe of the
fixture, the first statement of getMutator was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
`defects4j test -t com.fasterxml.jackson.databind.introspect.TestPOJOPropertiesCollector::testSimpleWithType`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at POJOPropertyBuilder.getMutator(POJOPropertyBuilder.java:405) called directly from
TestPOJOPropertiesCollector.testSimpleWithType(TestPOJOPropertiesCollector.java:410). Full suite with the probe: 555 failing tests
(getMutator is also reached from production code: BeanPropertyDefinition.couldDeserialize, getPrimaryMember for deserialization,
BasicBeanDescription.findBackReferenceProperties). The facade is reached by an existing test directly.

Hosts (host_mode = "1500"; `mr_lib.py preview JacksonDatabind-73 com/fasterxml/jackson/databind/introspect/POJOPropertyBuilder.java 5`
with the instance seed 2385, used in draw order, nothing substituted):
  hop 1 deser.BeanDeserializerBase       1665 lines  findValueMutator       pass-through
  hop 2 util.TokenBuffer                 1917 lines  mutatorForProperty     pass-through
  hop 3 ObjectReader                     1913 lines  findPropertyMutator    pass-through
  hop 4 deser.BasicDeserializerFactory   1964 lines  findMutatorForProperty pass-through
  hop 5 DeserializationContext           1578 lines  findMutatingMember     GOLD: the precedence decision (constructor parameter,
                                                                            setter, field)
Host sizes 1665, 1917, 1913, 1964, 1578; the smallest host is DeserializationContext (1578 lines, the gold host).
The correct configuration returns exactly the original member for every property: the same three lookups in the same order.

Fault (one-step omission of a special-case decision in the gold): the decision that answers a property with a constructor parameter
by that parameter is dropped, so the gold returns the setter, else the field, also for a creator property. The gold then reads as
the ordinary routine "the setter if there is one, otherwise the field". Trigger: the EXISTING test
TestPOJOPropertiesCollector::testSimpleWithType. Its serialization half (getAccessor) still holds; for deserialization of
TypeTestBean (a @JsonCreator constructor parameter "value" of type String, a protected Long field, a getter, no setter)
`assertEquals(AnnotatedParameter.class, m.getClass())` at line 411 fails because the field is returned: expected:<class
...introspect.AnnotatedParameter> but was:<class ...introspect.AnnotatedField>. It is the only test that newly fails: the same omission made directly in the pristine getMutator fails exactly
this one test in the full suite (scratch run), because deserialization builds creator properties from getConstructorParameter and
not from getMutator; the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the member to use for changing value of the given property, the wording of
BeanPropertyDefinition.getMutator without its parenthetical list) and is silent on which members qualify and in what order; for a
property set through its creator the member that changes its value is the constructor parameter. The convention is pinned outside
the gold: BeanPropertyDefinition.getMutator (javadoc "Method used to find mutator (constructor parameter, setter, field) to use for
changing value of the property"), SimpleBeanPropertyDefinition.getMutator (the same precedence: constructor parameter, then setter,
then field), and POJOPropertyBuilder.getNonConstructorMutator, the separately named setter-then-field lookup "that may be called
instead" when constructor parameters are not wanted; POJOPropertyBuilder.getConstructorParameter's comment ("constructor parameter
has the precedence"). Passing tests that pin it: TestCreators::testConstructorCreator (a creator property is set through the
constructor parameter: "ctor:xyz", 13) and TestAnnotationMerging::testSharedTypeInfoWithCtor (the constructor parameter carries the
property's @JsonTypeInfo for deserialization).

Single owner: only the gold decides which member changes the property's value; hops 1-4 hand the property along unchanged. Declared
alternatives (G9), each leaving the trigger failing: hop 2 answers a property with a setter itself; hop 3 uses the property's own
non-constructor lookup getNonConstructorMutator(); hop 4 answers a property with a field itself.
Recorded bypasses (edits that re-implement the gold's decision above it, not repairs of the chain):
 B-1 a hop answers a property with a constructor parameter by that parameter before calling on, e.g. hop 1
     `return prop.hasConstructorParameter() ? prop.getConstructorParameter() : TokenBuffer.mutatorForProperty(prop);` (the facade
     or any hop 2-4 likewise): it re-implements the gold's first precedence step above the gold, which still returns the setter or
     the field for a creator property against its own contract. Checked on the variant in a scratch copy: trigger passes, full
     suite 0 failing tests.
 B-0 the facade's original body (or a hop calling getConstructorParameter/getSetter/getField itself in full) re-implements the whole
     computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims the candidate members are compared by how many explicit annotations each carries, the most
annotated one being used and ties going to the one declared first; the chain counts no annotations (a fixed precedence of three
lookups). It names neither constructor parameters, the precedence, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; `if (prop.hasConstructorParameter()) return prop.getConstructorParameter(); if (prop.hasSetter()) return
 prop.getSetter(); return prop.getField();`):
  T1 absent: prop is the receiver of every test and every returned lookup; there is no argument check.
  T2 absent: no local variable; each of the two decisions returns a different member from the fall-through.
  T3 absent: the members the gold reads (constructor parameter, setter, field) are each returned; the javadoc names no class; the
     has-test precedes the two optional members and the last one is returned as it is (no member read but left untreated).
  T4 absent: 'the member to use for changing value of the given property' is a general description that the returns address; the
     @param/@return clauses name no rule, bound or value class; no inline comment; identifiers name what they hold.
 Variant gold (javadoc, signature, `if (prop.hasSetter()) { return prop.getSetter(); } return prop.getField();`):
  T1 absent: prop is read by the decision and by both returned lookups; no argument check.
  T2 absent: no local variable, no literal-initialised value, no loop, cursor, counter, flag or best-so-far; the one decision returns
     the setter where the fall-through returns the field (different effects).
  T3 absent: the gold reads two members (setter, field) and returns each; nothing in its text (parameters, flags it tests, parts it
     reads, javadoc, names) adds a third member, and no enum, type code or named format is used; no pair or range-end; no class named
     in the text ("Not T3: no member handled" for any member the gold does not read).
  T4 absent: 'Method for finding the member to use for changing value of given property' and '@return Member to use for changing
     the value' are general descriptions the two returns address; '@param prop Property to find the member for' is a caller-side
     description; no inline comment; the identifier findMutatingMember names what the method returns."""

PB = "src/main/java/com/fasterxml/jackson/databind/introspect/POJOPropertyBuilder.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
DC = "src/main/java/com/fasterxml/jackson/databind/DeserializationContext.java"

LIE = ("Candidate members are compared by the number of explicit annotations each carries, and the most annotated one is used, "
       "ties going to the one declared first.")

GOLD_TEXT = '''/**
 * Method for finding the member to use for changing value of
 * given property.
 *
 * @param prop Property to find the member for
 *
 * @return Member to use for changing the value
 */
public static AnnotatedMember findMutatingMember(POJOPropertyBuilder prop)
{
    if (prop.hasConstructorParameter()) {
        return prop.getConstructorParameter();
    }
    if (prop.hasSetter()) {
        return prop.getSetter();
    }
    return prop.getField();
}'''

HOP1 = '''/**
 * Helper method for finding the member to use for changing value
 * of given property.
 */
public static AnnotatedMember findValueMutator(POJOPropertyBuilder prop)
{
    return TokenBuffer.mutatorForProperty(prop);
}'''

HOP2 = '''/**
 * Helper method for locating the member to use for changing value
 * of given property.
 *
 * @param prop Property to locate the member for
 */
public static AnnotatedMember mutatorForProperty(POJOPropertyBuilder prop)
{
    return ObjectReader.findPropertyMutator(prop);
}'''

HOP3 = '''/**
 * Method for finding the member to use for changing value of given
 * property.
 */
public static AnnotatedMember findPropertyMutator(POJOPropertyBuilder prop)
{
    return BasicDeserializerFactory.findMutatorForProperty(prop);
}'''

HOP4 = '''/**
 * Helper method used to find the member to use for changing value
 * of given property.
 */
public static AnnotatedMember findMutatorForProperty(POJOPropertyBuilder prop)
{
    return DeserializationContext.findMutatingMember(prop);
}'''

FACADE_JAVADOC_OLD = ("    @Override\n"
                      "    public AnnotatedMember getMutator()\n")
FACADE_JAVADOC_NEW = ("    /**\n"
                      "     * Method used to find mutator (constructor parameter, setter, field) to use for\n"
                      "     * changing value of the property.\n"
                      "       " + LIE + "\n"
                      "     */\n"
                      "    @Override\n"
                      "    public AnnotatedMember getMutator()\n")

DESIGN = {
 "instance": "JacksonDatabind-73", "project": "JacksonDatabind", "bug_id": 73, "seed": 2385,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": PB, "class": "com.fasterxml.jackson.databind.introspect.POJOPropertyBuilder", "method": "getMutator",
            "near_line": 403},
 "facade_variant": "V2",
 "state_passed": "the receiver this (as POJOPropertyBuilder) to hop 1; no field read or written, no write-back",
 "reachability_probe": "TestPOJOPropertiesCollector::testSimpleWithType fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "POJOPropertyBuilder.getMutator(POJOPropertyBuilder.java:405) from TestPOJOPropertiesCollector.java:410; "
                       "full suite with the probe: 555 failing tests (production callers too)",
 "trigger": {"existing": True,
             "test_file": "src/test/java/com/fasterxml/jackson/databind/introspect/TestPOJOPropertiesCollector.java",
             "test_class": "com.fasterxml.jackson.databind.introspect.TestPOJOPropertiesCollector",
             "test_method": "testSimpleWithType"},
 "expected_signature": "expected:<class com.fasterxml.jackson.databind.introspect.AnnotatedParameter> but was:<class "
                       "com.fasterxml.jackson.databind.introspect.AnnotatedField>",
 "gold": {"method": "findMutatingMember", "text": GOLD_TEXT,
          "fault": {"old": "    public static AnnotatedMember findMutatingMember(POJOPropertyBuilder prop)\n"
                           "    {\n"
                           "        if (prop.hasConstructorParameter()) {\n"
                           "            return prop.getConstructorParameter();\n"
                           "        }\n",
                    "new": "    public static AnnotatedMember findMutatingMember(POJOPropertyBuilder prop)\n"
                           "    {\n"}},
 "pre_edits": {"chain": [
   {"file": PB, "old": FACADE_JAVADOC_OLD, "new": FACADE_JAVADOC_NEW},
 ]},
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.deser.BeanDeserializerBase.findValueMutator(this);",
   "lie": LIE,
   "hops": [
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "findValueMutator",
      "imports": [], "text": HOP1},
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "mutatorForProperty",
      "imports": ["com.fasterxml.jackson.databind.introspect.AnnotatedMember",
                  "com.fasterxml.jackson.databind.introspect.POJOPropertyBuilder"], "text": HOP2},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "findPropertyMutator",
      "imports": ["com.fasterxml.jackson.databind.deser.BasicDeserializerFactory",
                  "com.fasterxml.jackson.databind.introspect.AnnotatedMember",
                  "com.fasterxml.jackson.databind.introspect.POJOPropertyBuilder"], "text": HOP3},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "findMutatorForProperty",
      "imports": [], "text": HOP4},
     {"file": DC, "class": "com.fasterxml.jackson.databind.DeserializationContext", "method": "findMutatingMember",
      "imports": ["com.fasterxml.jackson.databind.introspect.AnnotatedMember",
                  "com.fasterxml.jackson.databind.introspect.POJOPropertyBuilder"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.introspect.BeanPropertyDefinition::getMutator",
              "com.fasterxml.jackson.databind.util.SimpleBeanPropertyDefinition::getMutator",
              "com.fasterxml.jackson.databind.introspect.POJOPropertyBuilder::getNonConstructorMutator",
              "com.fasterxml.jackson.databind.introspect.POJOPropertyBuilder::getConstructorParameter"],
 "ownership_reason": "Only the gold decides which member is used for changing the value of the property (constructor parameter, "
                     "else setter, else field); hops 1-4 hand the property along unchanged and the facade passes its receiver. "
                     "The gold's javadoc promises the member to use for changing value of the given property, which for a "
                     "property set through its @JsonCreator constructor is the constructor parameter, not the field. The "
                     "convention is pinned outside the gold: BeanPropertyDefinition.getMutator documents the mutator as "
                     "'(constructor parameter, setter, field)'; SimpleBeanPropertyDefinition.getMutator implements that "
                     "precedence; POJOPropertyBuilder.getNonConstructorMutator is the separately named setter-then-field "
                     "lookup; POJOPropertyBuilder.getConstructorParameter notes that the constructor parameter 'has the "
                     "precedence'. Passing tests: TestCreators testConstructorCreator (a creator property is set through the "
                     "constructor parameter) and TestAnnotationMerging testSharedTypeInfoWithCtor (the constructor parameter "
                     "carries the property's type information for deserialization). A hop answering creator properties itself "
                     "re-implements the gold's first precedence step above it (recorded bypass) and leaves the gold returning the "
                     "field for a creator property against its own contract.",
 "ownership_tests": ["com.fasterxml.jackson.databind.creators.TestCreators::testConstructorCreator",
                     "com.fasterxml.jackson.databind.introspect.TestAnnotationMerging::testSharedTypeInfoWithCtor"],
 "compensating": {
   "chain": [
     {"file": TB, "old": "return ObjectReader.findPropertyMutator(prop);",
      "new": "return prop.hasSetter() ? prop.getSetter() : ObjectReader.findPropertyMutator(prop);",
      "why": "hop 2 answers a property with a setter itself"},
     {"file": OR, "old": "return BasicDeserializerFactory.findMutatorForProperty(prop);",
      "new": "return prop.getNonConstructorMutator();",
      "why": "hop 3 uses the property's own non-constructor lookup"},
     {"file": BDF, "old": "return DeserializationContext.findMutatingMember(prop);",
      "new": "return prop.hasField() ? prop.getField() : DeserializationContext.findMutatingMember(prop);",
      "why": "hop 4 answers a property with a field itself"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts drawn by mr_lib.py preview JacksonDatabind-73 "
               "com/fasterxml/jackson/databind/introspect/POJOPropertyBuilder.java 5 with the instance seed 2385 (the draw excludes "
               "the facade file), used in draw order, none substituted: deser.BeanDeserializerBase (hop 1, 1665 lines), "
               "util.TokenBuffer (hop 2, 1917), ObjectReader (hop 3, 1913), deser.BasicDeserializerFactory (hop 4, 1964), "
               "DeserializationContext (hop 5, gold, 1578; the smallest host). The draw relaxed package distinctness for hop 5 "
               "(pool of six classes >= 1500 lines). All five are public top-level classes (three abstract), in which a public "
               "static method compiles. Preview anchors (seed 2385 + 100 + i): hop 1 after `BeanDeserializerBase` (line 354), "
               "hop 2 after `writeObjectId` (947), hop 3 after `withView` (785), hop 4 after `createCollectionLikeDeserializer` "
               "(1095), hop 5 after `getNodeFactory` (404). The facade calls hop 1 by its fully-qualified name; TokenBuffer, "
               "ObjectReader and DeserializationContext get imports for AnnotatedMember/POJOPropertyBuilder (and ObjectReader for "
               "BasicDeserializerFactory); BeanDeserializerBase and BasicDeserializerFactory already import introspect.*, "
               "util.* and databind.*.",
}
