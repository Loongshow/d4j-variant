"""Main run JacksonDatabind-17__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static
facade; fixed checkout of Defects4J JacksonDatabind-17, revision a143c05db7a9; the real bug modified ObjectMapper, the facade's class).
No static pair exists (B8 note section 1).

Facade: ObjectMapper.valueToTree(Object) (instance method; allowed targets ObjectMapper.setMixInAnnotations / .treeToValue /
.valueToTree, BATCH8_PREREGISTRATION.md row 247; facade_planned_by null for all three, no facade reuse).
setMixInAnnotations(Map) was not used: its computation is a clear followed by one ClassKey put per entry; the only two tests that call
it (TestMixinSerForFields::testMultipleFieldMixIns, TestMixinSerWithViews::testDataBindingUsage) both need every entry registered, so
any one-line omission in the per-entry step fails both of them, and an omitted clear fails neither (each test uses a fresh mapper).
treeToValue was not used: apart from the exception translation, its only decision depends on nothing but its two arguments (the
node's class against the requested type), so a caller can always decide that case before calling the chain; the binding itself has
no single-trigger one-line omission.
Original computation of valueToTree: a null value gives null (argument guard); otherwise the value is serialized by the mapper into
a TokenBuffer that carries the mapper as its codec (`new TokenBuffer(this, false)`), the buffer's tokens are read back with
readTree, the parser is closed, and any IOException becomes an IllegalArgumentException with the same message and cause.

facade_variant: V2 (receiver as parameter). state_passed: `this` (typed as the declaring class ObjectMapper) and the value, handed
to hop 1; the hops call only the public ObjectMapper methods writeValue(JsonGenerator, Object) and readTree(JsonParser); no field is
read or written, no write-back. The facade body is the original argument guard plus one call to hop 1 (with the original unchecked
cast to T). No visibility is widened, no type is added, no signature, modifier, annotation or throws clause changes, no reflection,
no test edit. The facade calls no private method of its class (V4 does not apply) and passes no package-private type (V3/V5 do not
apply).

Redistribution of the computation: hop 1 translates exceptions (any I/O exception becomes an IllegalArgumentException, as the
facade declares); hops 2 to 4 pass the mapper and the value along; the gold (hop 5) does the conversion itself: it sets up a token
buffer that uses the mapper as its codec, lets the mapper write the value into it, and reads the buffered tokens back as a tree.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-17-probe of the fixture, the first
statement of valueToTree was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t com.fasterxml.jackson.databind.node.TestConversions::testConversionOfPojos`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at ObjectMapper.valueToTree(ObjectMapper.java:2030), called from
TestConversions.java:262; `-t com.fasterxml.jackson.databind.jsontype.TestDefaultForTreeNodes::testValueToTreeWithDefaultTyping`:
1 failing test, PROBE-REACHED at ObjectMapper.valueToTree(ObjectMapper.java:2030), called from TestDefaultForTreeNodes.java:38.
The facade is reached directly by the trigger.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 util.TokenBuffer                1793 lines  valueAsTree      exception translation
  hop 2 deser.BasicDeserializerFactory  1622 lines  treeForValue     pass-through
  hop 3 ObjectReader                    1588 lines  convertToTree    pass-through
  hop 4 deser.BeanDeserializerBase      1486 lines  valueTree        pass-through
  hop 5 SerializerProvider              1156 lines  serializeAsTree  GOLD: buffer with the mapper as codec, write, read back
Host newline counts 1793, 1622, 1588, 1486, 1156; the smallest host (and the gold host) has 1156 lines (C10F addendum section 1: hosts
under 1500 lines are expected in this regime). Anchors: stageB_lib.pick_anchor with seed 6287 + 100 + i, as mr3_spec.py inserts
them (recorded per hop in the spec's stage_b block).
The correct configuration is behaviour-identical to the original for every input: `new TokenBuffer(null, false)` followed by
`setCodec(mapper)` leaves the buffer in the same state as `new TokenBuffer(mapper, false)` (the constructor and setCodec only assign
the codec field), and the write, read, close and exception translation are the original's.

Fault (one-line omission inside the gold): the line `buffer.setCodec(mapper);` is dropped, so the token buffer has no codec. A
serializer that writes a nested value with JsonGenerator.writeObject then no longer has that value serialized by the mapper: the
buffer keeps the raw object as an embedded value, and the tree gets a POJONode where the value's JSON has an object. Which nested
values are affected is decided inside the serialization, by whatever the value's serializers write, so no caller of the gold can
decide the case before the call, and the result cannot be repaired afterwards except by converting the value again. The variant
reads as an ordinary routine: `new TokenBuffer(null, false)` is the construction used by the type deserializers of this code base
(AsPropertyTypeDeserializer, AsWrapperTypeDeserializer, AsArrayTypeDeserializer).
Trigger: the EXISTING test TestConversions::testConversionOfPojos (Issue467Bean, whose serializer writes `jgen.writeObject(new
Issue467TmpBean(i))`; the test checks `writeValueAsString` gives {"x":13}, then that valueToTree gives an object node) fails with
"Expected Object, got POJO". With the same change applied to the original valueToTree (`new TokenBuffer(null, false)`), the full
suite has exactly one failing test, testConversionOfPojos (checked in the probe scratch copy, 18 s): the other valueToTree callers
either write no nested value through writeObject (beans, maps, default typing) or write a tree through writeTree, which an embedded
JsonNode still reads back as the same node (testConversionOfTrees, testBeanToTree). Gate G5 checks it on the variant.

The gold's javadoc states the idiomatic contract (it converts a value into the equivalent JSON tree, by having the mapper write the
value into a token buffer and reading the tokens back) and is silent on the codec. The variant violates that contract on the trigger
input: the JSON the mapper writes for Issue467Bean is {"x":13}, the variant's tree is a POJONode. The facade's javadoc states the same
contract ("construct equivalent JSON Tree representation", "functionally similar to serializing value into JSON and parsing JSON as
tree"). The convention is pinned outside the gold: the intact ObjectMapper._convert (used by every convertValue overload) serializes
into `new TokenBuffer(this, false)`, a buffer that carries the mapper as codec; MappingJsonFactory's constructor gives its generators a
mapper as codec (`setCodec(new ObjectMapper(this))`); passing tests TestGeneratorUsingMapper::testPojoWriting (a generator whose
factory has the mapper as codec writes a POJO as {"x":4}) and testPojoWritingFailing (without a codec, writeObject of a POJO is not
serialized), and TestConversions::testConversionOfTrees and testBeanToTree through the chain.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: mapper is the buffer's codec, writes the value and reads the tree; value is written; neither is only argument-checked.
  T2 absent: buffer, p and tree are each read (call arguments, receiver, return); no literal-initialised local; no loop; no branch.
  T3 absent: no closed set is enumerated (no cases, branches, decodes, key terms); nothing named is handled in part.
  T4 absent: 'Converts a value into the equivalent JSON tree' and 'written by the given mapper into a token buffer ... read back as
     a tree' describe the computation in general and the body's lines address them; @param/@return/@throws are met; no inline
     comment; identifiers (mapper, value, buffer, p, tree, serializeAsTree) name nothing the body does not meet.
 Variant gold (javadoc, signature, `TokenBuffer buffer = new TokenBuffer(null, false); mapper.writeValue(buffer, value);
 JsonParser p = buffer.asParser(); JsonNode tree = mapper.readTree(p); p.close(); return tree;`):
  T1 absent: mapper writes the value and reads the tree, value is written; both change the result.
  T2 absent: buffer is the write target and the parser's source, p is read from and closed, tree is returned; no local is
     initialised to a literal; no loop, cursor, counter or flag; no branch, case or ternary.
  T3 absent: no set is enumerated and no member of one is handled; the constructor arguments are not a set the gold treats in part.
  T4 absent: the javadoc names no rule, limit, bound, value class or case; 'equivalent JSON tree' is a general description that the
     write-then-read lines address; @param mapper 'Mapper that writes the value and reads the tree' is met (writeValue, readTree);
     @throws IOException is the propagated exception of those calls; no inline comment.

Single owner: only the gold builds the tree, and only the gold sees the token buffer: the buffer is created, filled and read inside
it, so its codec cannot be supplied or changed by any caller. Hop 1 only translates exceptions (its javadoc says the value is
converted as it is and I/O exceptions are reported as IllegalArgumentException); hops 2 to 4 pass the mapper and the value along
unchanged, as their javadoc states. Declared alternatives (G9): hop 3 passes a copy of the mapper; hop 2 passes the value converted to
its own class (convertValue returns that very instance); hop 1 reports I/O exceptions as IllegalStateException. None makes the trigger
pass.
Recorded bypasses:
 B-0 the facade (its original body) builds its own buffer and tree, or reads the tree from writeValueAsString, discarding the chain:
     a second implementation of the gold above the gold.
 B-1 a hop (or the facade) replaces the value by mapper.convertValue(value, Object.class) before passing it on: convertValue runs a
     complete second serialization round trip with its own codec-carrying buffer, and the gold then only re-serializes the resulting
     maps and lists. It is a second implementation of the gold's work above the gold, it contradicts hops 2-4 ('passed along
     unchanged') and hop 1 ('the value as it is'), and although the existing suite passes with it, it is lossy against the
     facade's 'equivalent JSON Tree representation': the intermediate Object binding turns every BigDecimal into a Double (unless
     USE_BIG_DECIMAL_FOR_FLOATS is on), so a value holding new BigDecimal("3.00000000") gives a DoubleNode 3.0 where the mapper's
     JSON and the original tree have the decimal 3.00000000 (a DecimalNode).
 B-2 a hop (or the facade) replaces the value by mapper.convertValue(value, JsonNode.class): that call already is the complete
     value-to-tree conversion (convertValue's own buffer, with the mapper as codec), and the gold is left to re-serialize a finished
     tree into a copy of itself; the gold's work is thrown away, and the edit contradicts hops 2-4 and hop 1 as B-1 does.

Lie placement: the facade's annotation (@SuppressWarnings) stands between its javadoc and its header, so the recipe's rewrite_facade
finds no adjacent javadoc and appends nothing; the lie sentence (the design's chain.lie) is therefore appended to the facade's existing
javadoc by the one comment-only pre_edit, as a new paragraph in the javadoc's own format.
Lie: the facade's javadoc claims the conversion is done in a single pass in which the serializer writes directly into the nodes of the
tree, with no intermediate token sequence; the chain in fact writes the value into a token buffer and reads the buffered tokens back.
It names neither the codec nor nested values nor any hop."""

OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
SP = "src/main/java/com/fasterxml/jackson/databind/SerializerProvider.java"

GOLD_TEXT = '''/**
 * Converts a value into the equivalent JSON tree: the value is written
 * by the given mapper into a token buffer, and the buffered tokens are
 * then read back as a tree.
 *
 * @param mapper Mapper that writes the value and reads the tree
 * @param value Value to convert
 *
 * @return Root node of the resulting tree
 *
 * @throws IOException if writing or reading the tokens fails
 */
public static JsonNode serializeAsTree(ObjectMapper mapper, Object value)
    throws IOException
{
    TokenBuffer buffer = new TokenBuffer(null, false);
    buffer.setCodec(mapper);
    mapper.writeValue(buffer, value);
    JsonParser p = buffer.asParser();
    JsonNode tree = mapper.readTree(p);
    p.close();
    return tree;
}'''

HOP1 = '''/**
 * Helper method that converts a value into the equivalent JSON tree
 * using the given mapper; the value is converted as it is. Since no
 * real I/O is done, any I/O exception is reported as an
 * {@link IllegalArgumentException} with the same message and cause.
 *
 * @param mapper Mapper used for the conversion
 * @param value Value to convert
 *
 * @return Root node of the resulting tree
 */
public static JsonNode valueAsTree(ObjectMapper mapper, Object value)
{
    try {
        return BasicDeserializerFactory.treeForValue(mapper, value);
    } catch (IOException e) {
        throw new IllegalArgumentException(e.getMessage(), e);
    }
}'''

HOP2 = '''/**
 * Converts a value into the equivalent JSON tree; the mapper and the
 * value are passed along unchanged.
 *
 * @param mapper Mapper used for the conversion
 * @param value Value to convert
 *
 * @return Root node of the resulting tree
 */
public static JsonNode treeForValue(ObjectMapper mapper, Object value)
    throws IOException
{
    return ObjectReader.convertToTree(mapper, value);
}'''

HOP3 = '''/**
 * Converts a value into the equivalent JSON tree; the mapper and the
 * value are passed along unchanged.
 *
 * @param mapper Mapper used for the conversion
 * @param value Value to convert
 *
 * @return Root node of the resulting tree
 */
public static JsonNode convertToTree(ObjectMapper mapper, Object value)
    throws IOException
{
    return BeanDeserializerBase.valueTree(mapper, value);
}'''

HOP4 = '''/**
 * Converts a value into the equivalent JSON tree; the mapper and the
 * value are passed along unchanged.
 *
 * @param mapper Mapper used for the conversion
 * @param value Value to convert
 *
 * @return Root node of the resulting tree
 */
public static JsonNode valueTree(ObjectMapper mapper, Object value)
    throws IOException
{
    return SerializerProvider.serializeAsTree(mapper, value);
}'''

DESIGN = {
 "instance": "JacksonDatabind-17", "project": "JacksonDatabind", "bug_id": 17, "seed": 6287,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "this (the receiver, typed as ObjectMapper) and fromValue, passed to hop 1 after the original null guard; the hops "
                 "call only the public ObjectMapper.writeValue(JsonGenerator, Object) and readTree(JsonParser); no field read or "
                 "written, no write-back",
 "host_mode": "largest5", "host_lines": [1793, 1622, 1588, 1486, 1156],
 "reachability_probe": "valueToTree first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-JacksonDatabind-17-probe: TestConversions::testConversionOfPojos fails with "
                       "PROBE-REACHED at ObjectMapper.valueToTree(ObjectMapper.java:2030), called from TestConversions.java:262; "
                       "TestDefaultForTreeNodes::testValueToTreeWithDefaultTyping likewise (TestDefaultForTreeNodes.java:38)",
 "facade": {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "valueToTree", "near_line": 2027},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/node/TestConversions.java",
             "test_class": "com.fasterxml.jackson.databind.node.TestConversions", "test_method": "testConversionOfPojos"},
 "expected_signature": "Expected Object, got POJO",
 "gold": {"method": "serializeAsTree", "text": GOLD_TEXT,
          "fault": {"old": "        TokenBuffer buffer = new TokenBuffer(null, false);\n"
                           "        buffer.setCodec(mapper);\n"
                           "        mapper.writeValue(buffer, value);",
                    "new": "        TokenBuffer buffer = new TokenBuffer(null, false);\n"
                           "        mapper.writeValue(buffer, value);"}},
 "pre_edits": {
   "chain": [{"file": OM,
              "old": "     * support conversions using full serialization, if raw values must be\n"
                     "     * preserved.\n",
              "new": "     * support conversions using full serialization, if raw values must be\n"
                     "     * preserved.\n"
                     "     *<p>\n"
                     "     * Conversion is done in a single pass: the value's serializer writes\n"
                     "     * directly into the nodes of the resulting tree, with no intermediate\n"
                     "     * token sequence in between.\n"}],
 },
 "chain": {
   "facade_body": "if (fromValue == null) return null;\n        return (T) TokenBuffer.valueAsTree(this, fromValue);",
   "lie": "Conversion is done in a single pass: the value's serializer writes directly into the nodes of the resulting tree, "
          "with no intermediate token sequence in between.",
   "hops": [
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "valueAsTree",
      "imports": ["com.fasterxml.jackson.databind.deser.BasicDeserializerFactory"], "text": HOP1},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "treeForValue",
      "imports": ["java.io.IOException"], "text": HOP2},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "convertToTree",
      "imports": ["com.fasterxml.jackson.databind.deser.BeanDeserializerBase"], "text": HOP3},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "valueTree",
      "imports": [], "text": HOP4},
     {"file": SP, "class": "com.fasterxml.jackson.databind.SerializerProvider", "method": "serializeAsTree",
      "imports": ["com.fasterxml.jackson.databind.util.TokenBuffer"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.ObjectMapper::_convert",
              "com.fasterxml.jackson.databind.MappingJsonFactory::MappingJsonFactory"],
 "ownership_reason": "Only the gold builds the tree, and only the gold sees the token buffer that the value is written into: the "
                     "buffer is created, given the mapper as its codec, filled and read inside the gold, so no caller can supply or "
                     "change its codec. Without the codec, a nested value that a serializer writes with writeObject is kept as a raw "
                     "embedded object and becomes a POJONode in the tree, where the mapper's JSON for the value has an object; which "
                     "values are affected is decided during serialization, so no caller can decide the case before the call. Hop 1 "
                     "only translates exceptions (I/O exceptions as IllegalArgumentException, the value converted as it is) and hops 2 "
                     "to 4 pass the mapper and the value along unchanged, as their javadoc states. The gold's javadoc and the facade's "
                     "('construct equivalent JSON Tree representation') state the contract the variant violates on the trigger input. "
                     "The convention is pinned outside the gold: the intact ObjectMapper._convert (used by every convertValue overload) "
                     "serializes into new TokenBuffer(this, false), a buffer carrying the mapper as codec; MappingJsonFactory gives its "
                     "generators a mapper as codec; TestGeneratorUsingMapper::testPojoWriting (a POJO written by a generator with the "
                     "mapper as codec gives {\"x\":4}) and testPojoWritingFailing (no codec, no serialization of the POJO) pass, and "
                     "TestConversions::testConversionOfTrees and testBeanToTree pass through the chain.",
 "ownership_tests": ["com.fasterxml.jackson.databind.TestGeneratorUsingMapper::testPojoWriting",
                     "com.fasterxml.jackson.databind.TestGeneratorUsingMapper::testPojoWritingFailing",
                     "com.fasterxml.jackson.databind.node.TestConversions::testConversionOfTrees",
                     "com.fasterxml.jackson.databind.node.TestConversions::testBeanToTree"],
 "compensating": {
   "chain": [
     {"file": OR, "old": "    return BeanDeserializerBase.valueTree(mapper, value);",
      "new": "    return BeanDeserializerBase.valueTree(mapper.copy(), value);",
      "why": "hop 3 converts with a copy of the mapper"},
     {"file": BDF, "old": "    return ObjectReader.convertToTree(mapper, value);",
      "new": "    return ObjectReader.convertToTree(mapper, mapper.convertValue(value, value.getClass()));",
      "why": "hop 2 passes the value converted to its own class"},
     {"file": TB, "old": "throw new IllegalArgumentException(e.getMessage(), e);",
      "new": "throw new IllegalStateException(e.getMessage(), e);",
      "why": "hop 1 reports I/O exceptions as IllegalStateException"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn or chosen by this "
               "builder): util.TokenBuffer (hop 1, 1793 lines), deser.BasicDeserializerFactory (hop 2, 1622), ObjectReader (hop 3, "
               "1588), deser.BeanDeserializerBase (hop 4, 1486), SerializerProvider (hop 5, gold, 1156; the smallest host). All five "
               "are public top-level classes in which a public static method compiles; the facade's class ObjectMapper (the only "
               "allowed candidates' file) is excluded. Anchors from stageB_lib.pick_anchor with seed 6287 + 100 + i, as mr3_spec.py "
               "inserts them (recorded in the spec's stage_b block). The facade calls hop 1 by its simple name (ObjectMapper already "
               "imports util.TokenBuffer). Imports added: TokenBuffer gets deser.BasicDeserializerFactory, BasicDeserializerFactory "
               "gets java.io.IOException, ObjectReader gets deser.BeanDeserializerBase, SerializerProvider gets util.TokenBuffer; "
               "the hosts already see ObjectMapper, JsonNode, JsonParser and IOException through their imports or package.",
}
