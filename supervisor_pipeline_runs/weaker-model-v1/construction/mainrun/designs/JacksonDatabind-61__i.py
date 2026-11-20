"""Main run JacksonDatabind-61__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static
facade; fixed checkout of Defects4J JacksonDatabind-61, whose real bug modified ObjectMapper and StdTypeResolverBuilder). No static
pair (B8 note section 1).

Facade: ObjectMapper.treeToValue(TreeNode, Class) (allowed instance target of BATCH8_PREREGISTRATION.md row 253; facade_planned_by
null, no facade reuse). The other two allowed targets were not used: StdTypeResolverBuilder.typeProperty is one defaulting step (a null
or empty name becomes the id type's default property name) that every @JsonTypeInfo-annotated type of the suite passes through (the
introspector calls it with the annotation's property, "" by default), so any one-line omission there makes many tests fail and no
single trigger exists; ObjectMapper.enableDefaultTyping(DefaultTyping, As) builds and installs one resolver that 22 test files depend
on in the same way, with no decision or iteration a single test alone observes.
Original computation of the facade: a tree that already is of the requested type (valueType != Object.class and
valueType.isAssignableFrom(n.getClass())) is returned as it is (the simple cast, [databind#11]); a VALUE_EMBEDDED_OBJECT POJONode whose
wrapped value is null or of the requested type gives that value ([databind#1208]); any other tree is bound with
readValue(treeAsTokens(n), valueType); a JsonProcessingException passes through and any other IOException becomes an
IllegalArgumentException with the same message and cause.

facade_variant: V2 (receiver as parameter). The computation needs the mapper's public methods readValue(JsonParser, Class) and
treeAsTokens(TreeNode), so the facade passes `this` (typed ObjectMapper) and its two parameters to hop 1; the hops call only those public
methods of the receiver. The method reads and writes no field (no V1 state), calls no private method (no V4), and no package-private type
is involved (no V3/V5). The facade body is one call to hop 1 (the original has no argument guard). No visibility is widened, no type is
added, no signature, modifier, override or throws clause changes (the method keeps @Override and `throws JsonProcessingException`), no
reflection, no test edit.
state_passed: the receiver `this` (ObjectMapper) with the parameters n and valueType, handed to hop 1; no field is read or written, no
write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-61-probe of the
fixture, the first statement of treeToValue was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile
OK; `defects4j test -t com.fasterxml.jackson.databind.node.TestConversions::testTreeToValueWithPOJO`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at ObjectMapper.treeToValue(ObjectMapper.java:2580). Full suite with the probe: 7 failing
tests, all with PROBE-REACHED (TestBeanConversions::testNodeConvert, TestUpdateValue::testIssue744, TestConversions::testTreeToValue,
::testIssue709, ::testTreeToValueWithPOJO, TestTreeTraversingParser::testDataBind, ObjectReaderTest::testNoPointerLoading). The facade
is reached directly by existing tests, the trigger among them.

Hosts (host_mode = "1500"; `mr_lib.py preview JacksonDatabind-61 com/fasterxml/jackson/databind/ObjectMapper.java 5` with the instance
seed 5839, used in draw order, none substituted; the draw excludes the facade's file, and the other allowed candidate's file,
StdTypeResolverBuilder, is not in the >= 1500-line pool):
  hop 1 util.TokenBuffer                 1917 lines  valueFromTree         plumbing: a processing exception passes through, any other
                                                                           I/O exception becomes an IllegalArgumentException
  hop 2 deser.BasicDeserializerFactory   1954 lines  deserializeTreeValue  pass-through
  hop 3 DeserializationContext           1578 lines  readTreeValue         pass-through
  hop 4 deser.BeanDeserializerBase       1649 lines  deserializeFromTree   pass-through
  hop 5 ObjectReader                     1910 lines  bindTreeValue         GOLD: the decision between the tree as it is, the value a POJO
                                                                           node wraps, and binding the tree by reading it
Host newline counts 1917, 1954, 1578, 1649, 1910; the smallest host is DeserializationContext (1578 lines); the gold host has 1910 lines.
The correct configuration returns the original result for every input: the gold's two shortcuts are the original's tests verbatim, except
that the POJO test drops the redundant `n.asToken() == JsonToken.VALUE_EMBEDDED_OBJECT` conjunct (POJONode.asToken() always returns
VALUE_EMBEDDED_OBJECT and no class of the checkout extends POJONode); hop 1 wraps exceptions exactly as the original try/catch did.

Fault (one-line omission of a special-case step in the gold): the simple-cast step, `if (type != Object.class &&
type.isAssignableFrom(tree.getClass())) return (T) tree;`, is dropped from the gold, so a tree that already is of the requested type is
bound again by reading it and an equal copy is returned. The variant gold then reads as the ordinary routine "a POJO node gives the value
it wraps if that value fits, any other tree is bound by reading it". Trigger: the EXISTING test TestBeanConversions::testNodeConvert
(MAPPER.treeToValue(node, ObjectNode.class) with assertSame(src, result), "[Issue-11]: simple cast, for Tree") fails with
junit.framework.AssertionFailedError: expected same:<{}> was not:<{}>. On the fixture, removing the original's simple-cast test makes
exactly this one test of the full suite fail (checked in the probe copy); gate G5 checks the variant.

The gold's javadoc states the idiomatic contract (it converts the tree into a value of the given type, using the mapper for binding) and
is silent on trees that already are of that type. The Jackson convention for a conversion is pinned outside the gold: the facade's own
javadoc says treeToValue is functionally equivalent to convertValue(n, valueClass), and ObjectMapper.convertValue's javadoc says the
conversion happens "if (but only if!) conversion is needed. If given value is already of requested type, value is returned as is";
ObjectMapper._convert does the same step in production (targetType != Object.class && !hasGenericTypes() &&
targetType.isAssignableFrom(fromValue.getClass()) -> return fromValue), as does FromStringDeserializer.deserialize for an embedded value
("instance of type itself returned as is"). Passing tests: TestBeanConversions::testConvertUsingCast (convertValue returns the same
String), TestConversions::testTreeToValueWithPOJO (through the chain: the wrapped Calendar is returned as it is),
TestConversions::testTreeToValue and TestTreeTraversingParser::testDataBind (through the chain: ordinary trees are bound).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: mapper binds the read path; tree is returned, unwrapped or read; type decides both shortcuts and is the read target.
  T2 absent: pojo is returned or tested; no local is frozen; each if has its own effect (return the tree / return the wrapped value).
  T3 absent: the gold's text names no class or set (its javadoc is a general description); both the tree and the wrapped value get an
     as-is test (the Object.class exclusion applies to the tree only, because a tree must be converted to natural values for Object,
     while a wrapped value already is one; no closed set by the checklist's closure rule); null is accepted for the wrapped value only,
     since a tree is never null there.
  T4 absent: 'converts given tree into a value of given type, using given mapper for binding' and the @param/@return clauses are met.
 Variant gold (javadoc, signature, the POJONode block, the read):
  T1 absent: mapper (readValue, treeAsTokens), tree (instanceof, getPojo, read) and type (isInstance, read target) all reach the result.
  T2 absent: pojo is tested and returned; no literal-initialised or loop local; the if/else paths return different values; no dead
     branch.
  T3 absent: one kind of node (POJONode) has its own treatment and every other tree is read: one member of an unnamed larger set of node
     kinds, which the gold's text does not name; null and in-type wrapped values are both returned; no pair, range or named class.
  T4 absent: the javadoc names no rule, value class or case beyond the general conversion; @return 'Value converted from the tree' is
     met; no inline comment; identifiers (bindTreeValue, tree, pojo, type) name nothing the body does not meet.

Single owner: only the gold decides whether a tree is returned as it is, unwrapped, or bound; hops 1-4 pass the receiver, the tree and the
type along unchanged and return the gold's result (hop 1 only maps exceptions). Once the gold binds a tree that already is of the type,
the result is a new, equal node, and no caller can recover the original instance from it. Declared alternatives (G9): hop 2 binds through
the mapper's ObjectReader for the type; hop 3 re-reads the tree into a new tree before passing it on; hop 4 binds with a copy of the
mapper. None makes the trigger pass.
Recorded bypasses:
 B-0 hop 1 (or any hop) calls mapper.convertValue(tree, type) instead of the next hop, discarding the rest of the chain including the
     gold (convertValue has its own simple-cast step).
 B-1 a hop before the gold returns the tree first when it already is of the type (`if (type != Object.class &&
     type.isAssignableFrom(tree.getClass())) return (T) tree;`), a second implementation of the gold's decision that skips the gold for
     those trees and breaks the hop's documented role of passing the conversion on.

Lie placement: the facade's javadoc is followed by @SuppressWarnings("unchecked") and @Override, so the recipe's rewrite_facade
(find_javadoc_start accepts only whitespace between the javadoc and the header) does not reach it and appends nothing; the one
pre_edit (chain) appends the lie to that javadoc in exactly the recipe's form (two spaces and the sentence on its own line before
the closing '*/'), and rewrite_facade then only replaces the body. The pre_edit changes a comment only.
Lie: the facade's javadoc claims the tree is traversed once before binding to verify that it does not contain itself, so that a cyclic
tree is rejected; no step of the chain traverses the tree for cycles. It names neither the type test, nor POJO nodes, nor any hop."""

OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
DC = "src/main/java/com/fasterxml/jackson/databind/DeserializationContext.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"

LIE = ("Before binding, the tree is traversed once to verify that it does not contain itself, so that a cyclic tree is "
       "rejected instead of being bound without end.")

GOLD_TEXT = '''/**
 * Helper method for converting given tree into a value of given type,
 * using given mapper for binding.
 *
 * @param mapper Mapper to use for binding
 * @param tree Tree to convert
 * @param type Type of value to produce
 *
 * @return Value converted from the tree
 */
@SuppressWarnings("unchecked")
public static <T> T bindTreeValue(ObjectMapper mapper, TreeNode tree, Class<T> type)
    throws IOException
{
    if (type != Object.class && type.isAssignableFrom(tree.getClass())) return (T) tree;
    if (tree instanceof POJONode) {
        Object pojo = ((POJONode) tree).getPojo();
        if ((pojo == null) || type.isInstance(pojo)) {
            return (T) pojo;
        }
    }
    return mapper.readValue(mapper.treeAsTokens(tree), type);
}'''

HOP1 = '''/**
 * Helper method for converting given tree into a value of given type,
 * using given mapper.
 *
 * @param mapper Mapper to use for binding
 * @param tree Tree to convert
 * @param type Type of value to produce
 *
 * @return Value converted from the tree
 *
 * @throws IllegalArgumentException If reading the tree fails due to an
 *   I/O problem other than a processing problem; if so, root cause is
 *   that problem
 */
public static <T> T valueFromTree(ObjectMapper mapper, TreeNode tree, Class<T> type)
    throws JsonProcessingException
{
    try {
        return BasicDeserializerFactory.deserializeTreeValue(mapper, tree, type);
    } catch (JsonProcessingException e) {
        throw e;
    } catch (IOException e) {
        throw new IllegalArgumentException(e.getMessage(), e);
    }
}'''

HOP2 = '''/**
 * Method for converting given tree into a value of given type, using
 * given mapper for binding.
 *
 * @param mapper Mapper to use for binding
 * @param tree Tree to convert
 * @param type Type of value to produce
 *
 * @return Value converted from the tree
 */
public static <T> T deserializeTreeValue(ObjectMapper mapper, TreeNode tree, Class<T> type)
    throws IOException
{
    return DeserializationContext.readTreeValue(mapper, tree, type);
}'''

HOP3 = '''/**
 * Convenience method for converting given tree into a value of given
 * type, using given mapper for binding.
 *
 * @param mapper Mapper to use for binding
 * @param tree Tree to convert
 * @param type Type of value to produce
 *
 * @return Value converted from the tree
 */
public static <T> T readTreeValue(ObjectMapper mapper, TreeNode tree, Class<T> type)
    throws IOException
{
    return BeanDeserializerBase.deserializeFromTree(mapper, tree, type);
}'''

HOP4 = '''/**
 * Helper method for converting given tree into a value of given type,
 * using given mapper for binding.
 *
 * @param mapper Mapper to use for binding
 * @param tree Tree to convert
 * @param type Type of value to produce
 *
 * @return Value converted from the tree
 */
public static <T> T deserializeFromTree(ObjectMapper mapper, TreeNode tree, Class<T> type)
    throws IOException
{
    return ObjectReader.bindTreeValue(mapper, tree, type);
}'''

DESIGN = {
 "instance": "JacksonDatabind-61", "project": "JacksonDatabind", "bug_id": 61, "seed": 5839,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "the receiver this (ObjectMapper) with the parameters n and valueType, handed to hop 1; no field read or written, "
                 "no write-back",
 "host_mode": "1500", "host_lines": [1917, 1954, 1578, 1649, 1910],
 "reachability_probe": "treeToValue first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-JacksonDatabind-61-probe: TestConversions::testTreeToValueWithPOJO fails with PROBE-REACHED "
                       "at ObjectMapper.treeToValue(ObjectMapper.java:2580); full suite: 7 tests fail with PROBE-REACHED, "
                       "TestBeanConversions::testNodeConvert (the trigger) among them",
 "facade": {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "treeToValue", "near_line": 2577},
 "trigger": {"existing": True,
             "test_file": "src/test/java/com/fasterxml/jackson/databind/convert/TestBeanConversions.java",
             "test_class": "com.fasterxml.jackson.databind.convert.TestBeanConversions", "test_method": "testNodeConvert"},
 "expected_signature": "expected same:<{}> was not:<{}>",
 "gold": {"method": "bindTreeValue", "text": GOLD_TEXT,
          "fault": {"old": "    {\n"
                           "        if (type != Object.class && type.isAssignableFrom(tree.getClass())) return (T) tree;\n"
                           "        if (tree instanceof POJONode) {",
                    "new": "    {\n"
                           "        if (tree instanceof POJONode) {"}},
 "pre_edits": {"chain": [
   {"file": OM,
    "old": "     *   objectMapper.convertValue(n, valueClass);\n     *</pre>\n     */\n    @SuppressWarnings(\"unchecked\")\n"
           "    @Override\n    public <T> T treeToValue(",
    "new": "     *   objectMapper.convertValue(n, valueClass);\n     *</pre>\n       " + LIE + "\n     */\n"
           "    @SuppressWarnings(\"unchecked\")\n    @Override\n    public <T> T treeToValue("},
 ]},
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.util.TokenBuffer.valueFromTree(this, n, valueType);",
   "lie": LIE,
   "hops": [
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "valueFromTree",
      "imports": ["com.fasterxml.jackson.databind.deser.BasicDeserializerFactory"], "text": HOP1},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "deserializeTreeValue",
      "imports": ["java.io.IOException", "com.fasterxml.jackson.core.TreeNode"], "text": HOP2},
     {"file": DC, "class": "com.fasterxml.jackson.databind.DeserializationContext", "method": "readTreeValue",
      "imports": [], "text": HOP3},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "deserializeFromTree",
      "imports": [], "text": HOP4},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "bindTreeValue",
      "imports": ["com.fasterxml.jackson.databind.node.POJONode"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.ObjectMapper::convertValue",
              "com.fasterxml.jackson.databind.ObjectMapper::_convert",
              "com.fasterxml.jackson.databind.deser.std.FromStringDeserializer::deserialize"],
 "ownership_reason": "Only the gold decides how a tree becomes a value: returned as it is, unwrapped from a POJO node, or bound by "
                     "reading it with the mapper. Hops 1-4 pass the receiver, the tree and the type along unchanged and return the "
                     "gold's result (hop 1 only maps an I/O exception that is not a processing exception to IllegalArgumentException). "
                     "Once the gold binds a tree that already is of the requested type, the result is a new, equal node, and no caller "
                     "can recover the original instance from it. The gold's javadoc promises a conversion of the tree into a value of "
                     "the type; the Jackson convention for a conversion is pinned outside the gold: the facade's javadoc says "
                     "treeToValue is functionally equivalent to convertValue(n, valueClass), whose javadoc says conversion happens "
                     "only if needed and a value already of the requested type is returned as is; ObjectMapper._convert does that "
                     "step in production (Object.class excluded), as does FromStringDeserializer.deserialize for an embedded value. "
                     "TestBeanConversions::testConvertUsingCast pins the same-instance result on the sibling path; "
                     "TestConversions::testTreeToValueWithPOJO (a wrapped value returned as is), TestConversions::testTreeToValue and "
                     "TestTreeTraversingParser::testDataBind (ordinary trees bound) pass through the chain.",
 "ownership_tests": ["com.fasterxml.jackson.databind.convert.TestBeanConversions::testConvertUsingCast",
                     "com.fasterxml.jackson.databind.node.TestConversions::testTreeToValueWithPOJO",
                     "com.fasterxml.jackson.databind.node.TestConversions::testTreeToValue",
                     "com.fasterxml.jackson.databind.node.TestTreeTraversingParser::testDataBind"],
 "compensating": {
   "chain": [
     {"file": BDF, "old": "return DeserializationContext.readTreeValue(mapper, tree, type);",
      "new": "return mapper.readerFor(type).treeToValue(tree, type);",
      "why": "hop 2 binds through the mapper's ObjectReader for the type"},
     {"file": DC, "old": "return BeanDeserializerBase.deserializeFromTree(mapper, tree, type);",
      "new": "return BeanDeserializerBase.deserializeFromTree(mapper, mapper.readTree(mapper.treeAsTokens(tree)), type);",
      "why": "hop 3 re-reads the tree into a new tree before passing it on"},
     {"file": BDB, "old": "return ObjectReader.bindTreeValue(mapper, tree, type);",
      "new": "return ObjectReader.bindTreeValue(mapper.copy(), tree, type);",
      "why": "hop 4 binds with a copy of the mapper"},
   ],
 },
 "host_notes": "host_mode 1500: mr_lib.py preview JacksonDatabind-61 com/fasterxml/jackson/databind/ObjectMapper.java 5 with seed 5839 "
               "drew util.TokenBuffer (hop 1, 1917 lines), deser.BasicDeserializerFactory (hop 2, 1954), DeserializationContext "
               "(hop 3, 1578; the smallest host), deser.BeanDeserializerBase (hop 4, 1649) and ObjectReader (hop 5, gold, 1910), "
               "used in that order, none substituted (the draw relaxed the distinct-package constraint for hosts 3-5: the checkout "
               "has only five other classes of >= 1500 lines). Both allowed-candidate files are excluded: ObjectMapper by the draw, "
               "StdTypeResolverBuilder (under 1500 lines) is not in the pool. All five hosts are public top-level classes "
               "(DeserializationContext and BeanDeserializerBase abstract) in which a public static generic method compiles. Anchors "
               "from the preview (seed 5839 + 100 + i): hop 1 after toString (5939), hop 2 after withDeserializerModifier (5940), "
               "hop 3 after hasValueDeserializerFor (5941), hop 4 after resolve (5942), hop 5 after readValue (5943). The facade "
               "calls hop 1 by its fully-qualified name; TokenBuffer imports deser.BasicDeserializerFactory; BasicDeserializerFactory "
               "imports java.io.IOException and core.TreeNode; DeserializationContext and BeanDeserializerBase see the next host "
               "through their existing imports; ObjectReader imports node.POJONode.",
}
