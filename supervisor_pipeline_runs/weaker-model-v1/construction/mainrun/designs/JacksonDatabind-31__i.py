"""Main run JacksonDatabind-31__i (cell C10i, batch 9 (9b): the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J JacksonDatabind-31 (fixed revision fe25f7e14d92f5d4746549e7df22e9af35fdf54b); the real bug modified TokenBuffer, the
facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE section 1: pool v2 found no tested static facade).

Facade: TokenBuffer.deserialize(JsonParser, DeserializationContext) (allowed instance target of BATCH9_PREREGISTRATION.md, row of
JacksonDatabind-31__i). Facade reuse: the same method is the planned facade of JacksonDatabind-7__i (facade_planned_by, recorded in
the task record's facade_reuse_of); the only other allowed target, TokenBuffer.writeBinary(Base64Variant, byte[], int, int), has
facade_planned_by JacksonDatabind-2__i, so no planned-distinct candidate exists, and writeBinary cannot carry the recipe validly
anyway: its computation is one range copy (new byte[len], arraycopy from offset) handed to writeObject, with no decision or
iteration in which a quiet one-line omission could live without leaving offset or len unused, a frozen write position or a dead
copy, and its Base64Variant parameter is unused by the original.
Original computation of the facade: if the parser does not point to a FIELD_NAME, copyCurrentStructure(p) and return this;
otherwise (the [databind#592] case: a field name means the START_OBJECT was already read) writeStartObject(), copy each field
with copyCurrentStructure(p) while the next token is FIELD_NAME, throw ctxt.mappingException("Expected END_OBJECT after copying
contents of a JsonParser into TokenBuffer, got "+t) unless that token is END_OBJECT, writeEndObject(), return this.

facade_variant: V2 (receiver as parameter). The computation needs only public methods of the object (copyCurrentStructure,
copyCurrentEvent, writeStartObject, writeEndObject; TokenBuffer is a public class), so the facade passes `this` (typed as
TokenBuffer) with its two parameters to hop 1 and returns hop 1's result, which is the receiver. It reads no field and writes
none (no V1 write-back); it calls no private method (no V4); no package-private type is involved (no V3/V5). No signature,
modifier, override or throws change; no new type; no reflection; no visibility change; no test edit. The facade has a javadoc
('Helper method used by standard deserializer.', '@since 2.3'); the lie is appended to it by the recipe.
state_passed: the receiver `this` (as TokenBuffer) plus the facade's parameters p and ctxt, to hop 1; no write-back (the facade
returns hop 1's result, the same buffer).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-31-probeD of the
fixture, the first statement of TokenBuffer.deserialize was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`
(the `if (true)` only keeps the rest of the body reachable for javac). Full suite (`defects4j test`): 4 failing tests, all with
PROBE-REACHED at TokenBuffer.deserialize(TokenBuffer.java:435) via TokenBufferDeserializer.deserialize:
TestCreatorsDelegating::testDelegateWithTokenBuffer, TestJacksonTypes::testTokenBufferWithSample,
TestJacksonTypes::testTokenBufferWithSequence, TestDefaultForObject::testTokenBuffer (wrapped in a JsonMappingException). A second
probe that throws only on the FIELD_NAME path (before writeStartObject) made exactly 1 test fail:
TestCreatorsDelegating::testDelegateWithTokenBuffer. (The writeBinary probe, /private/tmp/d4j-mi-JacksonDatabind-31-probeW, made 4
tests fail: TestStringConversions::testBytestoCharArray, ::testBytesToBase64AndBack, TestConversions::testIssue709,
TestTokenBuffer::testSimpleArray.) The facade is reached by existing tests through its production caller TokenBufferDeserializer.

Hosts (host_mode = "largest5"; EXACTLY hosts_hop_order of batch9_tasks.json, in that order, none substituted; TokenBuffer.java,
the facade file, is excluded):
  hop 1 ObjectMapper              3858 lines  copyToBuffer          decision: a parser not at a field name is copied as one
                                                                    structure (the original's first case); otherwise passes on
  hop 2 BasicDeserializerFactory  1918 lines  bufferContent         pass-through
  hop 3 ObjectReader              1820 lines  readIntoBuffer        pass-through
  hop 4 BeanDeserializerBase      1532 lines  bufferObjectContents  placement: START_OBJECT before the fields, the END_OBJECT check
                                                                    on the token the gold returns, END_OBJECT after them
  hop 5 ObjectWriter              1390 lines  writeFields           GOLD: the per-field copy loop (each field name, the advance
                                                                    to its value, the value's structure; stop at the first token
                                                                    that is not a field name, which is returned)
Host newline counts 3858, 1918, 1820, 1532, 1390; the smallest host is ObjectWriter (1390 lines), which is the gold host.
The correct configuration is behaviour-identical to the original: for a FIELD_NAME, TokenBuffer.copyCurrentStructure does
(_checkNativeIds when ids may exist) writeFieldName(name), nextToken(), (_checkNativeIds) and copies the value; the gold's
copyCurrentEvent(p) at the FIELD_NAME does (_checkNativeIds) writeFieldName(p.getCurrentName()), then p.nextToken(), then
copyCurrentStructure(p) at the value token (never a FIELD_NAME) does (_checkNativeIds) and copies the value: the same calls in the
same order.

Fault (one-line omission of a step in the per-field iteration of the gold): the advance from a field name to its value
(`p.nextToken();` between the copy of the field name and the copy of the value) is dropped. copyCurrentStructure(p) then starts
at the field name again and copies the name and its value, so every field name is written twice: the buffer holds START_OBJECT,
"a", "a", 1, "b", "b", 2, END_OBJECT. The gold still reads as the ordinary loop "copy the current event, copy the structure, move
to the next token while it is a field name". Trigger: the EXISTING test TestCreatorsDelegating::testDelegateWithTokenBuffer
([databind#592], @JsonCreator delegating to a TokenBuffer for {"a":1,"b":2}, the only path that reaches a parser at a field name):
assertToken(VALUE_NUMBER_INT, jp.nextToken()) after the first FIELD_NAME fails with "Expected token VALUE_NUMBER_INT, current
token FIELD_NAME". It is the only test that newly fails (the FIELD_NAME probe above: no other test reaches that path; the new hops
have no other caller).

The gold's javadoc states the idiomatic contract (copying the fields of a JSON Object, starting with the field name the parser
points to, into the buffer; the parser is left at the token after the last field) and is silent on the advance; a buffer in which
every field name appears twice is not a copy of the fields. The convention (a field is written as its name once and then the
value, copied from the value token) is pinned outside the gold: TokenBuffer.copyCurrentStructure (for a FIELD_NAME:
writeFieldName, nextToken, then the value), BeanDeserializer.deserializeWithUnwrapped (the loop moves the parser to the value with
p.nextToken(), then writes tokens.writeFieldName(propName) and tokens.copyCurrentStructure(p) at the value) and
BuilderBasedDeserializer.deserializeWithUnwrapped (the same); passing tests TestJacksonTypes::testTokenBufferWithSample (the JSON
spec sample read into a TokenBuffer through deserialize and verified token by token), TestTokenBuffer::testWithJSONSampleDoc
(copyCurrentEvent per token reproduces the sample's field names once each) and TestUnwrapped::testSimpleUnwrappedDeserialize (the
unwrapped buffer of name + value is read back into the bean).

Single owner: only the gold iterates over the fields and moves the parser from a name to its value; hop 1 only routes a parser
that is not at a field name to copyCurrentStructure, hops 2-3 pass the three values along unchanged, hop 4 places START_OBJECT and
END_OBJECT around the gold's fields and checks the token the gold returns. Every one-line edit above the gold leaves the doubled
names: the gold copies the current event and then the structure at the same token for every field, whatever token the caller
starts it at (a caller that advances first gets a doubled value instead). Declared alternatives (G9): hop 1 copies a parser at a
field name as a plain structure as well; hop 3 moves the parser past the first field name before passing it on; hop 4 writes the
first field name itself and moves to its value before calling the gold. Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-1 hop 4 replaces the call `JsonToken t = ObjectWriter.writeFields(buffer, p);` by its own loop
     `JsonToken t; do { buffer.copyCurrentStructure(p); } while ((t = p.nextToken()) == JsonToken.FIELD_NAME);` (one line), which
     re-implements the gold's iteration and makes the gold dead; the gold still writes every name twice against its javadoc.
     Checked on the variant in a scratch copy (/private/tmp/d4j-mi-JacksonDatabind-31-probeD): full suite 0 failing tests.
 B-0 the facade's original body (or hop 1 doing the whole FIELD_NAME case itself) re-implements the whole computation and makes the
     chain, including the gold, dead.

Lie: the facade's javadoc claims the content is first read into a tree of nodes that is then traversed depth-first to write its
tokens into this buffer; the chain builds no tree (tokens go from the parser straight into the buffer through copyCurrentStructure
and copyCurrentEvent). It names neither field names, the advance, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature writeFields(TokenBuffer buffer, JsonParser p), `JsonToken t; do { buffer.copyCurrentEvent(p);
 p.nextToken(); buffer.copyCurrentStructure(p); } while ((t = p.nextToken()) == JsonToken.FIELD_NAME); return t;`):
  T1 absent: buffer receives every copy; p is copied from, advanced and tested by the loop; there is no argument check.
  T2 absent: the only local t is assigned in the loop condition on every iteration, tested by it and returned; no literal-initialised
     local; the do-while condition decides whether another field is copied.
  T3 absent: the gold tests one member of JsonToken (FIELD_NAME) and gives no member a treatment that a sibling lacks; there is no
     pair or range end (no start/end marker is written in the gold); the text names no class it handles in part.
  T4 absent: 'copying the fields of a JSON Object, starting with the field name that the given parser points to' is a general
     description that the loop addresses; 'Parser is left pointing to the token that follows the last field' and '@return Token
     that follows the last field copied' are met by the loop condition and `return t`; '@param p Parser that points to the first
     field name to copy' is a caller precondition; no inline comment; identifiers buffer, p, t name what they hold.
 Variant gold (the same with `p.nextToken();` inside the loop body removed: `do { buffer.copyCurrentEvent(p);
 buffer.copyCurrentStructure(p); } while ((t = p.nextToken()) == JsonToken.FIELD_NAME); return t;`):
  T1 absent: buffer receives both copies of every iteration; p is read by both copies and advanced and tested in the condition;
     both decide the effect and the return value; no argument check.
  T2 absent: t is assigned by the loop condition in every iteration, tested there and returned (not frozen, not dead); the parser
     cursor still advances once per iteration in the condition; no literal-initialised local; no if/else, case or ternary; the
     loop condition decides whether another iteration copies.
  T3 absent: only FIELD_NAME of JsonToken is tested, and no other member gets any treatment (no parallel siblings); no two-member
     set (no start/end marker, no key/value pair named in the text; 'field' is not split into handled and unhandled halves in the
     text); the gold's text names no class ('finite', 'all', 'nested', ...) that it handles in part.
  T4 absent: the javadoc's 'copying the fields of a JSON Object ... into given buffer' is a general description that the copy lines
     address (like 'joins the elements'); 'starting with the field name that the given parser points to' is met by the first
     copyCurrentEvent(p); 'Parser is left pointing to the token that follows the last field' and '@return Token that follows the
     last field copied' are met by the loop condition and `return t`; '@param buffer Buffer to copy fields into' and '@param p
     Parser that points to the first field name to copy' name no rule the gold checks; no inline comment."""

TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OW = "src/main/java/com/fasterxml/jackson/databind/ObjectWriter.java"

GOLD_TEXT = '''/**
 * Method for copying the fields of a JSON Object, starting with the
 * field name that the given parser points to, into given buffer.
 * Parser is left pointing to the token that follows the last field.
 *
 * @param buffer Buffer to copy fields into
 * @param p Parser that points to the first field name to copy
 *
 * @return Token that follows the last field copied
 */
public static JsonToken writeFields(TokenBuffer buffer, JsonParser p) throws IOException
{
    JsonToken t;
    do {
        buffer.copyCurrentEvent(p);
        p.nextToken();
        buffer.copyCurrentStructure(p);
    } while ((t = p.nextToken()) == JsonToken.FIELD_NAME);
    return t;
}'''

HOP1 = '''/**
 * Method that copies contents that the given parser points to into
 * the given buffer. A parser that points to a field name is taken to be
 * within a JSON Object whose START_OBJECT has already been read.
 *
 * @param buffer Buffer to copy contents into
 * @param p Parser that points to contents to copy
 * @param ctxt Context to use for reporting problems
 *
 * @return Buffer given
 */
public static TokenBuffer copyToBuffer(TokenBuffer buffer, JsonParser p, DeserializationContext ctxt)
    throws IOException
{
    if (p.getCurrentTokenId() != JsonToken.FIELD_NAME.id()) {
        buffer.copyCurrentStructure(p);
        return buffer;
    }
    return BasicDeserializerFactory.bufferContent(buffer, p, ctxt);
}'''

HOP2 = '''/**
 * Helper method used for buffering contents of a JSON Object, starting
 * from the field name that the given parser points to.
 */
public static TokenBuffer bufferContent(TokenBuffer buffer, JsonParser p, DeserializationContext ctxt)
    throws IOException
{
    return ObjectReader.readIntoBuffer(buffer, p, ctxt);
}'''

HOP3 = '''/**
 * Method for reading contents of a JSON Object, starting from the
 * field name that the given parser points to, into given buffer.
 *
 * @param buffer Buffer to read contents into
 * @param p Parser that points to the first field name
 * @param ctxt Context to use for reporting problems
 *
 * @return Buffer given
 */
public static TokenBuffer readIntoBuffer(TokenBuffer buffer, JsonParser p, DeserializationContext ctxt)
    throws IOException
{
    return BeanDeserializerBase.bufferObjectContents(buffer, p, ctxt);
}'''

HOP4 = '''/**
 * Helper method for buffering contents of a JSON Object whose START_OBJECT
 * has already been read, so that the parser points to its first field name.
 * Buffered contents form a complete JSON Object.
 */
public static TokenBuffer bufferObjectContents(TokenBuffer buffer, JsonParser p, DeserializationContext ctxt)
    throws IOException
{
    buffer.writeStartObject();
    JsonToken t = ObjectWriter.writeFields(buffer, p);
    if (t != JsonToken.END_OBJECT) {
        throw ctxt.mappingException("Expected END_OBJECT after copying contents of a JsonParser into TokenBuffer, got "+t);
    }
    buffer.writeEndObject();
    return buffer;
}'''

DESIGN = {
 "instance": "JacksonDatabind-31", "project": "JacksonDatabind", "bug_id": 31, "seed": 5643,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "deserialize", "near_line": 433},
 "facade_variant": "V2",
 "state_passed": "the receiver `this` (as TokenBuffer) plus the facade's parameters p and ctxt, to hop 1; no write-back (the "
                 "facade returns hop 1's result, the same buffer)",
 "reachability_probe": "full suite with PROBE-REACHED as the first statement of TokenBuffer.deserialize: 4 failing tests, all "
                       "PROBE-REACHED at TokenBuffer.deserialize(TokenBuffer.java:435) via TokenBufferDeserializer "
                       "(TestCreatorsDelegating::testDelegateWithTokenBuffer, TestJacksonTypes::testTokenBufferWithSample, "
                       "TestJacksonTypes::testTokenBufferWithSequence, TestDefaultForObject::testTokenBuffer); a probe on the "
                       "FIELD_NAME path only: 1 failing test (testDelegateWithTokenBuffer)",
 "host_mode": "largest5",
 "trigger": {"existing": True,
             "test_file": "src/test/java/com/fasterxml/jackson/databind/creators/TestCreatorsDelegating.java",
             "test_class": "com.fasterxml.jackson.databind.creators.TestCreatorsDelegating",
             "test_method": "testDelegateWithTokenBuffer"},
 "expected_signature": "Expected token VALUE_NUMBER_INT, current token FIELD_NAME",
 "gold": {"method": "writeFields", "text": GOLD_TEXT,
          "fault": {"old": "            buffer.copyCurrentEvent(p);\n"
                           "            p.nextToken();\n"
                           "            buffer.copyCurrentStructure(p);\n",
                    "new": "            buffer.copyCurrentEvent(p);\n"
                           "            buffer.copyCurrentStructure(p);\n"}},
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.ObjectMapper.copyToBuffer(this, p, ctxt);",
   "lie": "The content is first read into a tree of nodes, which is then traversed depth-first to write its tokens into "
          "this buffer.",
   "hops": [
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "copyToBuffer",
      "imports": [], "text": HOP1},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "bufferContent",
      "imports": ["java.io.IOException", "com.fasterxml.jackson.core.JsonParser"], "text": HOP2},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "readIntoBuffer",
      "imports": ["com.fasterxml.jackson.databind.deser.BeanDeserializerBase",
                  "com.fasterxml.jackson.databind.util.TokenBuffer"], "text": HOP3},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "bufferObjectContents",
      "imports": [], "text": HOP4},
     {"file": OW, "class": "com.fasterxml.jackson.databind.ObjectWriter", "method": "writeFields",
      "imports": ["com.fasterxml.jackson.databind.util.TokenBuffer"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.util.TokenBuffer::copyCurrentStructure",
              "com.fasterxml.jackson.databind.deser.BeanDeserializer::deserializeWithUnwrapped",
              "com.fasterxml.jackson.databind.deser.BuilderBasedDeserializer::deserializeWithUnwrapped"],
 "ownership_reason": "Only the gold iterates over the fields of the object and moves the parser from each field name to its "
                     "value; hop 1 only sends a parser that is not at a field name to copyCurrentStructure, hops 2-3 pass the "
                     "buffer, the parser and the context along unchanged, and hop 4 writes START_OBJECT before and END_OBJECT "
                     "after the gold's fields and checks the token the gold returns. The gold's javadoc promises a copy of the "
                     "fields of the JSON Object starting with the field name the parser points to; a buffer in which every field "
                     "name appears twice is not that copy. No one-line edit above the gold restores it: the gold copies the "
                     "current event and then the structure at the same token for every field, whatever token a caller starts it "
                     "at. The convention (a field written as its name once, then the value copied from the value token) is "
                     "pinned outside the gold: TokenBuffer.copyCurrentStructure (for a FIELD_NAME: writeFieldName, nextToken, "
                     "then the value), BeanDeserializer.deserializeWithUnwrapped and BuilderBasedDeserializer."
                     "deserializeWithUnwrapped (p.nextToken() to the value, then writeFieldName(propName) and "
                     "copyCurrentStructure(p)), with TestJacksonTypes testTokenBufferWithSample, TestTokenBuffer "
                     "testWithJSONSampleDoc and TestUnwrapped testSimpleUnwrappedDeserialize passing.",
 "ownership_tests": ["com.fasterxml.jackson.databind.deser.TestJacksonTypes::testTokenBufferWithSample",
                     "com.fasterxml.jackson.databind.util.TestTokenBuffer::testWithJSONSampleDoc",
                     "com.fasterxml.jackson.databind.struct.TestUnwrapped::testSimpleUnwrappedDeserialize"],
 "compensating": {
   "chain": [
     {"file": OM, "old": "return BasicDeserializerFactory.bufferContent(buffer, p, ctxt);",
      "new": "buffer.copyCurrentStructure(p);\n        return buffer;",
      "why": "hop 1 copies a parser at a field name as a plain structure as well"},
     {"file": OR, "old": "return BeanDeserializerBase.bufferObjectContents(buffer, p, ctxt);",
      "new": "p.nextToken();\n        return BeanDeserializerBase.bufferObjectContents(buffer, p, ctxt);",
      "why": "hop 3 moves the parser past the first field name before passing it on"},
     {"file": BDB, "old": "JsonToken t = ObjectWriter.writeFields(buffer, p);",
      "new": "buffer.writeFieldName(p.getCurrentName()); p.nextToken(); JsonToken t = ObjectWriter.writeFields(buffer, p);",
      "why": "hop 4 writes the first field name itself and moves to its value before calling the field copy"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch9_tasks.json), in that order, none "
               "substituted: ObjectMapper (hop 1, 3858 lines), deser.BasicDeserializerFactory (hop 2, 1918), ObjectReader (hop 3, "
               "1820), deser.BeanDeserializerBase (hop 4, 1532; abstract, which does not affect a static method), ObjectWriter "
               "(hop 5, gold, 1390; the smallest host). The excluded file is util/TokenBuffer.java (both allowed candidates). All "
               "five are public top-level classes in which a static method compiles. Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 5643 + 100 + i (as mr3_spec.py inserts them), checked on the pristine "
               "files: hop 1 after `acceptJsonFormatVisitor` (seed 5743), hop 2 after `_valueInstantiatorInstance` (5744), hop 3 "
               "after `withType` (5745), hop 4 after `getObjectIdReader` (5746), hop 5 after `isEnabled` (5747); all in the outer "
               "class. The facade calls hop 1 by its fully-qualified name; each hop names the next host by its simple name "
               "(imports added where the host lacked them).",
}
