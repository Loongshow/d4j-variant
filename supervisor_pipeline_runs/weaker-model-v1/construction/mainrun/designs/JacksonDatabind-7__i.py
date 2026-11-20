"""Main run JacksonDatabind-7__i (cell C10i, batch 9: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J JacksonDatabind-7; the real bug modified com.fasterxml.jackson.databind.util.TokenBuffer, the facade's class). No static
pair (pool v2: no_tested_static), so addendum section 2 has nothing to refer to.

Facade: TokenBuffer.deserialize(JsonParser, DeserializationContext) (allowed candidate of batch9_tasks.json, facade_planned_by
null; no facade reuse). The other allowed candidate, TokenBuffer.writeBinary(Base64Variant, byte[], int, int), was not used: it was
planned by JacksonDatabind-2__i (distinctness preferred), and its computation is one array copy of a range followed by writeObject,
which has no decision or iteration a quiet one-line omission could live in without leaving offset or len unused (T1) or one range
end untreated (T3b).
Original computation of the facade: when the parser does not point to a FIELD_NAME, the current structure is copied into this
buffer (copyCurrentStructure) and the buffer is returned; when it points to a FIELD_NAME (the START_OBJECT was already consumed by
the caller, databind#592), a START_OBJECT is written, every field (name and value) is copied while the next token is a FIELD_NAME,
the token after the last field must be END_OBJECT (otherwise ctxt.mappingException), and END_OBJECT is written.

facade_variant: V2 (receiver as parameter). The computation needs public methods of the receiver (copyCurrentStructure,
writeStartObject, writeFieldName, writeEndObject) and reads or writes no field directly: the facade passes `this` (typed as
TokenBuffer, its declaring class) with its two parameters to hop 1 and returns hop 1's result (the same buffer). The method has no
argument guard. The hops call only public methods of TokenBuffer, JsonParser and DeserializationContext. No private method is
called (no V4), no package-private type is involved (no V3/V5). No signature, modifier, override or throws change; no new type; no
reflection; no test edit.
state_passed: the receiver `this` (TokenBuffer) plus the facade parameters jp and ctxt to hop 1; no field write-back (the buffer is
filled through its own public write methods and returned).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-7-probe/w of the
fixture, the first statement of TokenBuffer.deserialize was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
Full suite (defects4j test): 4 failing tests, all with PROBE-REACHED at TokenBuffer.deserialize(TokenBuffer.java:405) called from
TokenBufferDeserializer.deserialize(TokenBufferDeserializer.java:31): TestCreatorsDelegating::testDelegateWithTokenBuffer,
TestJacksonTypes::testTokenBufferWithSample, TestJacksonTypes::testTokenBufferWithSequence, TestDefaultForObject::testTokenBuffer
(wrapped in a JsonMappingException). A second probe placed at the start of the FIELD_NAME case only: 1 failing test
(TestCreatorsDelegating::testDelegateWithTokenBuffer). The facade is reached by existing tests through its only production caller
TokenBufferDeserializer.deserialize.

Hosts (host_mode = "largest5"; exactly hosts_hop_order of the task record, in that order, none substituted; every allowed
candidate's file, TokenBuffer.java, excluded):
  hop 1 ObjectMapper              3190 lines  bufferContents        decision: a parser not at a field name has its current
                                                                    structure copied (the original's first case); a field name
                                                                    is passed on
  hop 2 deser.BasicDeserializerFactory 1622 lines  bufferObjectFields  pass-through
  hop 3 ObjectReader              1585 lines  readFieldsInto        pass-through
  hop 4 deser.BeanDeserializerBase 1486 lines copyPropertiesInto    pass-through
  hop 5 SerializerProvider        1125 lines  copyFieldsAsObject    GOLD: writes START_OBJECT, copies every field (its name, then
                                                                    its value after moving the parser to it) while the next
                                                                    token is a field name, requires END_OBJECT and writes it
Host newline counts 3190, 1622, 1585, 1486, 1125; the smallest host is SerializerProvider (1125 lines), the gold host.
The correct configuration gives the original token stream for every JSON parser: for a FIELD_NAME, TokenBuffer.copyCurrentStructure
itself writes the field name, moves to the value and copies it; the gold does the same two steps explicitly and then lets
copyCurrentStructure copy the value. (For a parser with native type/object ids, copyCurrentStructure also looks for native ids at
the field-name token; the gold looks for them at the value, where formats attach them; no test or parser of this checkout has
native ids at a field name.)

Fault (one-line omission of a step in the per-field iteration of the gold): the statement that moves the parser from a field name
to its value (`jp.nextToken();`) is dropped. copyCurrentStructure then starts at the field name and writes the name a second time
before the value, so every field reaches the buffer as FIELD_NAME, FIELD_NAME, value. The gold still reads as the ordinary routine
"open the Object, write each field's name and copy the current structure, close the Object". Trigger: the EXISTING test
TestCreatorsDelegating::testDelegateWithTokenBuffer ({"a":1,"b":2} bound through a @JsonCreator taking a TokenBuffer, whose
delegate deserializer hands the parser over at the first FIELD_NAME): START_OBJECT and FIELD_NAME "a" still hold, and the next
assertToken(VALUE_NUMBER_INT, ...) at line 134 fails with "Expected token VALUE_NUMBER_INT, current token FIELD_NAME". It is the only
test that newly fails: the field-name case is reached by this test only (the second probe), the other three tests that reach the
facade take hop 1's copyCurrentStructure case, and the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the fields of the Object are copied into the buffer as a single Object; copying
ends at the token after the last field, which has to close the Object) and is silent on how the parser is moved within a field;
an Object with every field name written twice is not the Object's fields. The convention is pinned outside the gold by production
code that does the same step: AsPropertyTypeDeserializer.deserializeTypedFromObject (`String name = jp.getCurrentName();
jp.nextToken(); // to point to the value` ... `tb.writeFieldName(name); tb.copyCurrentStructure(jp);`),
BeanDeserializer.deserializeWithUnwrapped (`String propName = jp.getCurrentName(); jp.nextToken();` ...
`tokens.writeFieldName(propName); tokens.copyCurrentStructure(jp);`) and TokenBuffer.copyCurrentStructure (on a FIELD_NAME:
writeFieldName, `t = jp.nextToken(); // fall-through to copy the associated value`); passing tests: TestVisibleTypeId
testVisibleWithProperty (reads {"a":7, "type":"BaseType"}: the field before the type id is buffered by name and value),
TestUnwrapped testSimpleUnwrappedDeserialize (unwrapped fields buffered by name and value), TestJacksonTypes
testTokenBufferWithSample (copyCurrentStructure round trip of Objects with fields).

Single owner: only the gold iterates over the fields and moves the parser within a field; hop 1 only routes a parser that is not at
a field name to copyCurrentStructure, and hops 2-4 pass buffer, parser and context along unchanged. No one-line change above the
gold restores the stream: a hop that moves the parser to the first value before calling the gold fixes the first field only (the
loop's own nextToken lands on the next FIELD_NAME, and the trigger's second field "b" is written twice); a START_OBJECT written by a
hop adds a second START_OBJECT; routing the field-name case to copyCurrentStructure loses the START_OBJECT (the original #592
behaviour) and stops after one field.
Declared alternatives (G9): hop 1 writes the START_OBJECT itself before passing the field name on; hop 4 moves the parser to the
first value before handing it to the gold; hop 3 copies the current structure itself instead of passing the field name on. Each
leaves the trigger failing.
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-1 any hop (or the facade) replacing the call below it with the original loop (writeStartObject; do copyCurrentStructure while
     the next token is a FIELD_NAME; check; writeEndObject) re-implements the whole field-name case and makes the gold dead.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims the content is first read into a tree of nodes, which is then written into this buffer in document
order; the chain builds no tree (tokens are copied from the parser straight into the buffer). It names neither field names, the
parser's position, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: buffer receives every write and is returned; jp supplies the field names, is advanced and copied from, and its next
     token decides the loop and the END_OBJECT check; ctxt builds the exception thrown when the Object is not closed (no argument
     check exists in the gold).
  T2 absent: the only local t is assigned in the loop condition on every iteration and read by the loop condition, the END_OBJECT
     check and the exception message; no literal-initialised local; the one if has a throw on one side and the closing write on
     the other.
  T3 absent: START_OBJECT and END_OBJECT are both written; every field gets its name written and its value copied (key and value
     both treated); the two JsonToken constants tested (FIELD_NAME continues the loop, END_OBJECT is required at its end) have
     different roles, and no enum member gets a treatment a sibling lacks.
  T4 absent: 'copies the fields of a JSON Object ... as a single Object' is met by the start write, the loop and the end write;
     'Copying ends at the token that follows the last field; that token has to close the Object' is met by the loop condition and
     the END_OBJECT check with its throw; the @param clauses are caller preconditions ('points to the first field name to copy').
 Variant gold (javadoc, signature, writeStartObject, do { writeFieldName(jp.getCurrentName()); copyCurrentStructure(jp); } while
 the next token is FIELD_NAME, END_OBJECT check with throw, writeEndObject, return buffer):
  T1 absent: buffer is written and returned; jp gives the names, is copied from and advanced by the loop condition, and decides the
     loop and the check; ctxt builds the thrown exception.
  T2 absent: t is assigned in the loop condition each iteration and read by the condition, the check and the message; there is no
     cursor, counter, flag or best-so-far local (the parser is advanced in the loop condition and by copyCurrentStructure); the if
     has two different effects.
  T3 absent: both Object markers are written; each field has its name written and its structure copied; no member of the JsonToken
     enum receives a treatment that a sibling of the same role lacks; the gold's text names no class (no 'scalar', 'array',
     'native id') that it handles only in part.
  T4 absent: 'the fields of a JSON Object ... as a single Object' is a general description the body addresses (start write, a copy
     per field, end write); 'that token has to close the Object' is met by the END_OBJECT check; no inline comment; the identifiers
     (copyFieldsAsObject, buffer, jp, ctxt, t) name what they hold or do."""

TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
SP = "src/main/java/com/fasterxml/jackson/databind/SerializerProvider.java"

GOLD_TEXT = '''/**
 * Method that copies the fields of a JSON Object into given buffer,
 * starting at the field name given parser points to, and writes them
 * into the buffer as a single Object.
 *<p>
 * Copying ends at the token that follows the last field; that token
 * has to close the Object.
 *
 * @param buffer Buffer to copy the fields into
 * @param jp Parser that points to the first field name to copy
 * @param ctxt Context used for reporting problems
 *
 * @return Buffer given, for convenience
 */
public static TokenBuffer copyFieldsAsObject(TokenBuffer buffer, JsonParser jp, DeserializationContext ctxt)
    throws IOException
{
    buffer.writeStartObject();
    JsonToken t;
    do {
        buffer.writeFieldName(jp.getCurrentName());
        jp.nextToken();
        buffer.copyCurrentStructure(jp);
    } while ((t = jp.nextToken()) == JsonToken.FIELD_NAME);
    if (t != JsonToken.END_OBJECT) {
        throw ctxt.mappingException("Expected END_OBJECT after copying contents of a JsonParser into TokenBuffer, got "+t);
    }
    buffer.writeEndObject();
    return buffer;
}'''

HOP1 = '''/**
 * Method that copies the content given parser points to into given
 * {@link TokenBuffer}. If the parser points to a field name, the content
 * is taken to be the fields of a JSON Object whose START_OBJECT has
 * already been read.
 *
 * @param buffer Buffer to copy the content into
 * @param jp Parser that points to the content to copy
 * @param ctxt Context used for reporting problems
 *
 * @return Buffer given, for convenience
 */
public static TokenBuffer bufferContents(TokenBuffer buffer, JsonParser jp, DeserializationContext ctxt)
    throws IOException
{
    if (jp.getCurrentTokenId() != JsonToken.FIELD_NAME.id()) {
        buffer.copyCurrentStructure(jp);
        return buffer;
    }
    return BasicDeserializerFactory.bufferObjectFields(buffer, jp, ctxt);
}'''

HOP2 = '''/**
 * Helper method for copying the fields of a JSON Object, starting at
 * the field name given parser points to, into given buffer.
 *
 * @param buffer Buffer to copy the fields into
 * @param jp Parser that points to the first field name
 * @param ctxt Context used for reporting problems
 *
 * @return Buffer given, for convenience
 */
public static TokenBuffer bufferObjectFields(TokenBuffer buffer, JsonParser jp, DeserializationContext ctxt)
    throws IOException
{
    return ObjectReader.readFieldsInto(buffer, jp, ctxt);
}'''

HOP3 = '''/**
 * Method for reading the fields of a JSON Object, starting at the
 * field name given parser points to, into given buffer.
 *
 * @param buffer Buffer to read the fields into
 * @param jp Parser that points to the first field name
 * @param ctxt Context used for reporting problems
 *
 * @return Buffer given, for convenience
 */
public static TokenBuffer readFieldsInto(TokenBuffer buffer, JsonParser jp, DeserializationContext ctxt)
    throws IOException
{
    return BeanDeserializerBase.copyPropertiesInto(buffer, jp, ctxt);
}'''

HOP4 = '''/**
 * Helper method that copies the properties of a JSON Object, starting
 * at the property name given parser points to, into given buffer.
 *
 * @param buffer Buffer to copy the properties into
 * @param jp Parser that points to the first property name
 * @param ctxt Context used for reporting problems
 *
 * @return Buffer given, for convenience
 */
public static TokenBuffer copyPropertiesInto(TokenBuffer buffer, JsonParser jp, DeserializationContext ctxt)
    throws IOException
{
    return SerializerProvider.copyFieldsAsObject(buffer, jp, ctxt);
}'''

DESIGN = {
 "instance": "JacksonDatabind-7", "project": "JacksonDatabind", "bug_id": 7, "seed": 4038,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "deserialize", "near_line": 403},
 "facade_variant": "V2",
 "state_passed": "the receiver this (TokenBuffer) with the facade parameters jp and ctxt to hop 1; no field write-back (the "
                 "buffer is filled through its own public write methods and returned)",
 "reachability_probe": "full suite with the facade's first statement throwing PROBE-REACHED: 4 failing tests, all at "
                       "TokenBuffer.deserialize(TokenBuffer.java:405) from TokenBufferDeserializer.deserialize: "
                       "TestCreatorsDelegating::testDelegateWithTokenBuffer, TestJacksonTypes::testTokenBufferWithSample, "
                       "TestJacksonTypes::testTokenBufferWithSequence, TestDefaultForObject::testTokenBuffer; probe in the "
                       "field-name case only: 1 failing test (testDelegateWithTokenBuffer)",
 "host_mode": "largest5",
 "host_lines": [3190, 1622, 1585, 1486, 1125],
 "trigger": {"existing": True,
             "test_file": "src/test/java/com/fasterxml/jackson/databind/creators/TestCreatorsDelegating.java",
             "test_class": "com.fasterxml.jackson.databind.creators.TestCreatorsDelegating",
             "test_method": "testDelegateWithTokenBuffer"},
 "expected_signature": "Expected token VALUE_NUMBER_INT, current token FIELD_NAME",
 "gold": {"method": "copyFieldsAsObject", "text": GOLD_TEXT,
          "fault": {"old": "            buffer.writeFieldName(jp.getCurrentName());\n"
                           "            jp.nextToken();\n"
                           "            buffer.copyCurrentStructure(jp);\n",
                    "new": "            buffer.writeFieldName(jp.getCurrentName());\n"
                           "            buffer.copyCurrentStructure(jp);\n"}},
 "chain": {
   "facade_body": "return ObjectMapper.bufferContents(this, jp, ctxt);",
   "lie": "The content is first read into a tree of nodes, which is then written into this buffer in document order.",
   "hops": [
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "bufferContents",
      "imports": [], "text": HOP1},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "bufferObjectFields",
      "imports": ["java.io.IOException", "com.fasterxml.jackson.core.JsonParser"], "text": HOP2},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "readFieldsInto",
      "imports": ["com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "com.fasterxml.jackson.databind.util.TokenBuffer"],
      "text": HOP3},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "copyPropertiesInto",
      "imports": [], "text": HOP4},
     {"file": SP, "class": "com.fasterxml.jackson.databind.SerializerProvider", "method": "copyFieldsAsObject",
      "imports": ["com.fasterxml.jackson.databind.util.TokenBuffer"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.jsontype.impl.AsPropertyTypeDeserializer::deserializeTypedFromObject",
              "com.fasterxml.jackson.databind.deser.BeanDeserializer::deserializeWithUnwrapped",
              "com.fasterxml.jackson.databind.util.TokenBuffer::copyCurrentStructure"],
 "ownership_reason": "Only the gold iterates over the fields of the Object and moves the parser within a field; hop 1 only "
                     "routes a parser that is not at a field name to copyCurrentStructure, and hops 2-4 pass buffer, parser "
                     "and context along unchanged. The gold's javadoc promises the fields of the JSON Object copied into the "
                     "buffer as a single Object, which a stream with every field name written twice is not. No one-line change "
                     "above the gold restores the stream: moving the parser to the first value before the gold fixes only the "
                     "first field (the trigger's second field is still written twice), a START_OBJECT written by a hop is a "
                     "second one, and routing the field-name case to copyCurrentStructure loses the START_OBJECT and stops "
                     "after one field. The convention is pinned outside the gold by production code doing the same step: "
                     "AsPropertyTypeDeserializer.deserializeTypedFromObject and BeanDeserializer.deserializeWithUnwrapped read "
                     "the field name, call jp.nextToken() 'to point to the value', then writeFieldName(name) and "
                     "copyCurrentStructure(jp); TokenBuffer.copyCurrentStructure on a FIELD_NAME writes the name and moves to "
                     "the value before copying it. Passing tests: TestVisibleTypeId testVisibleWithProperty ({\"a\":7, "
                     "\"type\":\"BaseType\"}, the field before the type id buffered by name and value), TestUnwrapped "
                     "testSimpleUnwrappedDeserialize, TestJacksonTypes testTokenBufferWithSample.",
 "ownership_tests": ["com.fasterxml.jackson.databind.jsontype.TestVisibleTypeId::testVisibleWithProperty",
                     "com.fasterxml.jackson.databind.struct.TestUnwrapped::testSimpleUnwrappedDeserialize",
                     "com.fasterxml.jackson.databind.deser.TestJacksonTypes::testTokenBufferWithSample"],
 "compensating": {
   "chain": [
     {"file": OM, "old": "return BasicDeserializerFactory.bufferObjectFields(buffer, jp, ctxt);",
      "new": "buffer.writeStartObject(); return BasicDeserializerFactory.bufferObjectFields(buffer, jp, ctxt);",
      "why": "hop 1 writes the START_OBJECT of the Object itself before passing the field name on"},
     {"file": BDB, "old": "return SerializerProvider.copyFieldsAsObject(buffer, jp, ctxt);",
      "new": "jp.nextToken(); return SerializerProvider.copyFieldsAsObject(buffer, jp, ctxt);",
      "why": "hop 4 moves the parser from the first field name to its value before handing it to the gold"},
     {"file": OR, "old": "return BeanDeserializerBase.copyPropertiesInto(buffer, jp, ctxt);",
      "new": "buffer.copyCurrentStructure(jp); return buffer;",
      "why": "hop 3 copies the current structure itself instead of passing the field name on"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are exactly hosts_hop_order of the task record (batch9_tasks.json), in that order, none "
               "substituted; TokenBuffer.java (the file of both allowed candidates) is excluded: ObjectMapper (hop 1, 3190 "
               "lines), deser.BasicDeserializerFactory (hop 2, 1622; abstract, which does not affect a static method), "
               "ObjectReader (hop 3, 1585), deser.BeanDeserializerBase (hop 4, 1486; abstract), SerializerProvider (hop 5, "
               "gold, 1125; abstract; the smallest host). All five are public top-level classes in which a public static "
               "method compiles. Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 4038 + 100 "
               "+ i (as mr3_spec.py inserts them): hop 1 after `writerWithType` (line idx 2436, seed 4138), hop 2 after "
               "`withAdditionalDeserializers` (149, 4139), hop 3 after `with` (379, 4140), hop 4 after `handledType` (760, "
               "4141), hop 5 after `getAnnotationIntrospector` (297, 4142); all in the outer class. The facade calls hop 1 "
               "through TokenBuffer's existing import com.fasterxml.jackson.databind.*; each hop imports what it needs.",
}
