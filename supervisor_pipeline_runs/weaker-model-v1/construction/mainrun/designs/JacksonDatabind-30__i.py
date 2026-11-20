"""Main run JacksonDatabind-30__i (cell C10i, batch 9 / sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed
checkout of Defects4J JacksonDatabind-30; the real bug modified ObjectMapper and util.TokenBuffer). No static pair (BUILD_BRIEF_C10I_B8_NOTE
section 1: pool v2 found no strictly tested public static method in the modified classes).

Facade: TokenBuffer.deserialize(JsonParser, DeserializationContext) (allowed instance target of BATCH9_PREREGISTRATION.md, rank 347).
facade_planned_by = JacksonDatabind-7__i: this method is also the planned facade of that earlier task (facade reuse, recorded; it
changes nothing in how this instance is built). The two allowed candidates with facade_planned_by = null or another planner were not
used because neither can carry the recipe validly:
 - ObjectMapper.enableDefaultTyping(DefaultTyping, JsonTypeInfo.As) (planned_by null, preferred if usable): after its guard (the
   EXTERNAL_PROPERTY rejection, which stays in the facade) the computation is a straight configuration chain
   (new DefaultTypeResolverBuilder(applicability).init(Id.CLASS, null).inclusion(includeAs), then setDefaultTyping) with no iteration
   or decision. The only one-line omissions available (dropping init or inclusion) leave a parameter unused (T1) and break default
   typing for every caller (StdTypeResolverBuilder._includeAs stays null; 19 test files use enableDefaultTyping), so no single
   trigger exists; the guard itself is the facade's and an argument check any caller could pre-filter.
 - TokenBuffer.writeBinary(Base64Variant, byte[], int, int) (planned by JacksonDatabind-2__i): a slice copy plus writeObject; every
   one-line omission leaves offset or len unused or a frozen write position (T1/T2), and no existing test writes a non-zero offset
   into a TokenBuffer, so no quiet single-trigger omission exists.
Original computation of the facade: if the parser's current token is not FIELD_NAME, copy the current structure (a scalar, an Array
or an Object from its START_OBJECT) into the buffer; otherwise (#592: a parser at a FIELD_NAME is reading an Object whose START_OBJECT
has already been read) write START_OBJECT, copy each field (do { copyCurrentStructure } while nextToken == FIELD_NAME), require that
the token that ended the loop is END_OBJECT (else ctxt.mappingException("Expected END_OBJECT after copying contents of a JsonParser
into TokenBuffer, got " + t)), write END_OBJECT, and return this buffer.

facade_variant: V2 (receiver as parameter). The computation needs only public methods of the receiver (copyCurrentStructure,
writeStartObject, writeEndObject), so the facade passes `this` (typed TokenBuffer, the declaring class) with its two parameters to hop
1 and returns what hop 1 returns (the same buffer). No field of TokenBuffer is read or written by the computation (no V1), no private
method is called (no V4), no package-private type is involved (no V3/V5). No signature, modifier, override or throws change; no new
type; no reflection; no test edit. state_passed: the receiver `this` (TokenBuffer) plus the parameters p and ctxt to hop 1; no
write-back (hop 1 returns the receiver it was given and the facade returns it).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-30-probe of the
fixture, the first statement of TokenBuffer.deserialize was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
Full suite (defects4j test): 4 failing tests, each with java.lang.IllegalStateException: PROBE-REACHED at
TokenBuffer.deserialize(TokenBuffer.java:435): TestCreatorsDelegating::testDelegateWithTokenBuffer (from TestCreatorsDelegating.java:129,
through the delegating creator of Value592), TestJacksonTypes::testTokenBufferWithSample, TestJacksonTypes::testTokenBufferWithSequence,
and TestDefaultForObject::testTokenBuffer (wrapped in a JsonMappingException through ObjectHolder["value"]). The facade is reached by
existing tests (through TokenBufferDeserializer and the delegating-creator path of BeanDeserializerBase).

Hosts (host_mode = "largest5"; EXACTLY hosts_hop_order of the task record, in that order; none substituted; all are public top-level
classes in which a public static method compiles; BasicDeserializerFactory and BeanDeserializerBase are abstract, TypeFactory is final,
none of which affects a static method):
  hop 1 deser.BasicDeserializerFactory 1918 lines  bufferContents         decision: a parser that is not at a field name is copied
                                                                          whole (the original's first branch); a parser at a field
                                                                          name goes down the chain
  hop 2 ObjectReader                   1820 lines  readIntoBuffer         pass-through
  hop 3 deser.BeanDeserializerBase     1532 lines  deserializeIntoBuffer  pass-through
  hop 4 ObjectWriter                   1390 lines  writeObjectContents    aggregation: requires END_OBJECT as the token that ended
                                                                          the copy (the original's mapping exception), returns the
                                                                          buffer
  hop 5 type.TypeFactory               1311 lines  copyObjectFields       GOLD: writes START_OBJECT, copies the field at which the
                                                                          parser stands and every following field, writes END_OBJECT,
                                                                          returns the token that ended the loop
Host newline counts 1918, 1820, 1532, 1390, 1311; the smallest host is TypeFactory (1311 lines, the gold host). The task record's
pool list had util.TokenBuffer (1841) second; it is a facade file (facade_files_excluded), and hosts_hop_order (confirmed on the
checkout) is used as given.
The correct configuration returns the original token stream for every input: a non-FIELD_NAME start is copied by
copyCurrentStructure exactly as before; a FIELD_NAME start gives START_OBJECT, the current field, every following field while
nextToken() is FIELD_NAME, and END_OBJECT, which is the original do/while; a loop ended by anything but END_OBJECT throws the same
mapping exception (the END_OBJECT the gold has already appended is never seen, the buffer is not returned).

Fault (one-line omission in the gold's iteration): the copy of the field at which the parser stands (the first field, before the loop)
is dropped. The gold then reads as the ordinary Jackson routine "write START_OBJECT; while nextToken() is FIELD_NAME copy the field;
write END_OBJECT", which is correct for a parser at START_OBJECT; but hop 1 sends only parsers that already stand at the first field
name, so the first nextToken() moves past that field's name to its value, the loop never runs, and hop 4 sees VALUE_NUMBER_INT.
Trigger: the EXISTING test TestCreatorsDelegating::testDelegateWithTokenBuffer (readValue("{\"a\":1,\"b\":2}", Value592.class); the
bean deserializer has consumed START_OBJECT and hands the delegating TokenBuffer creator a parser at FIELD_NAME "a"); it fails with
JsonMappingException "Expected END_OBJECT after copying contents of a JsonParser into TokenBuffer, got VALUE_NUMBER_INT", thrown by hop
4 (the gold has already returned and is not on the stack). It is the only test that newly fails: the other three probe-reached tests
start at START_OBJECT, START_ARRAY or a scalar and are handled by hop 1's first branch, which does not reach the gold.

The gold's javadoc states the idiomatic contract (copies the fields of the JSON Object the parser is reading into the buffer, as one
complete Object) and is silent on where the parser stands; the omission violates it on the trigger input (field "a" is not copied and
the Object is not copied). The convention is pinned outside the gold: production deserializers that read an Object treat a parser at
FIELD_NAME as already inside the Object and take the CURRENT field name as the first key (UntypedObjectDeserializer.mapObject:
`else if (t == JsonToken.FIELD_NAME) { key1 = p.getCurrentName(); }`; MapDeserializer._readAndBindStringMap and _readAndBind:
`keyStr = p.getCurrentName()` when not at START_OBJECT; JsonNodeDeserializer.deserializeObject likewise), with the passing tests
TestCreators2::testIssue465 ({"A":12} into a Map delegate keeps the entry) and TestCreators2::testAbstractFactory ({"a":3} into a Map
delegate keeps the entry); hop 1's javadoc states the same convention for this chain.

Single owner: only the gold reads the fields and decides where the copy starts; hops 2-3 pass the buffer, the parser and the context
along, hop 1 only answers non-field-name starts and hop 4 only checks the token the gold returns. The gold writes START_OBJECT itself,
so a caller can neither put the first field inside the Object nor rewind the parser: copying the current field above the gold puts it
before START_OBJECT; writing START_OBJECT above the gold gives two; dropping hop 4's check returns an empty Object; every one-line
change above the gold leaves the trigger failing.
Declared alternatives (G9): hop 4 copies the current field before calling the gold; hop 1 writes START_OBJECT before passing the parser
on; hop 4 accepts any token that ended the copy (drops the check). Each leaves the trigger failing.
Recorded bypass (not a repair of the chain): B-0 any hop (or the facade) replacing the call below it by the facade's original
FIELD_NAME branch (writeStartObject, do { copyCurrentStructure } while (nextToken() == FIELD_NAME), the check, writeEndObject)
re-implements the whole computation and makes the gold dead; it is a multi-line edit.

Lie: the facade's javadoc claims the tokens are first read ahead into a lookahead queue and replayed into this buffer once the token
that closes the value has been seen; the chain reads nothing ahead and queues nothing (each token is appended as it is read). It names
neither field names, START_OBJECT, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (writeStartObject; copyCurrentStructure(p); while ((t = p.nextToken()) == FIELD_NAME) copyCurrentStructure(p);
 writeEndObject; return t):
  T1 absent: buffer receives every write; p is copied from and advanced, and its tokens decide the loop and the return value.
  T2 absent: the only local t is assigned in the loop condition on every iteration and returned; no literal-initialised local; no
     branch (the one loop condition both continues and ends the copy).
  T3 absent: both ends of the Object are written (START_OBJECT and END_OBJECT); the only token tested is FIELD_NAME (one member of
     JsonToken, no sibling treated); no enum, type code or named format member is left out.
  T4 absent: 'copying the fields of a JSON Object ... as one complete Object' is a general description met by the copy, the loop and
     the two Object ends; '@return Token that ended the copy' is met by return t; the @param clauses name no rule; no inline comment.
 Variant gold (writeStartObject; while ((t = p.nextToken()) == FIELD_NAME) copyCurrentStructure(p); writeEndObject; return t):
  T1 absent: buffer receives START_OBJECT, each copied field and END_OBJECT; p is advanced and copied from, and its tokens decide the
     loop and the returned token.
  T2 absent: t is assigned by every evaluation of the loop condition and returned; there is no cursor, counter, flag or best-so-far
     besides it; no literal-initialised local; no if/else, case or ternary.
  T3 absent: both Object ends are written; FIELD_NAME is the only token the gold tests (no sibling token gets a treatment another
     lacks); the gold's text names no class it would handle in part (no "first", "current", "every", "all").
  T4 absent: the javadoc ('Method for copying the fields of a JSON Object, which given parser is reading, into given TokenBuffer, as
     one complete Object') is the canonical description of the loop that the body implements; '@param buffer Buffer to copy the Object
     into', '@param p Parser to copy the fields from' and '@return Token that ended the copy' name no concrete rule, limit or case the
     body visibly does not meet; no inline comment; the identifiers copyObjectFields, buffer, p and t name what they hold."""

TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
ORD = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OWR = "src/main/java/com/fasterxml/jackson/databind/ObjectWriter.java"
TF = "src/main/java/com/fasterxml/jackson/databind/type/TypeFactory.java"

GOLD_TEXT = '''/**
 * Method for copying the fields of a JSON Object, which given parser
 * is reading, into given {@link TokenBuffer}, as one complete Object.
 *
 * @param buffer Buffer to copy the Object into
 * @param p Parser to copy the fields from
 *
 * @return Token that ended the copy
 *
 * @since 2.6
 */
public static JsonToken copyObjectFields(TokenBuffer buffer, JsonParser p) throws IOException
{
    buffer.writeStartObject();
    buffer.copyCurrentStructure(p);
    JsonToken t;
    while ((t = p.nextToken()) == JsonToken.FIELD_NAME) {
        buffer.copyCurrentStructure(p);
    }
    buffer.writeEndObject();
    return t;
}'''

HOP1 = '''/**
 * Helper method for copying contents that given parser points to
 * into given {@link TokenBuffer}. A parser that points to a field name
 * is reading an Object whose START_OBJECT has already been read: such
 * contents are copied as a complete Object.
 *
 * @param buffer Buffer to copy contents into
 * @param p Parser to copy contents from
 * @param ctxt Context for reporting problems
 *
 * @return Buffer given
 *
 * @since 2.6
 */
public static TokenBuffer bufferContents(TokenBuffer buffer, JsonParser p, DeserializationContext ctxt)
    throws IOException
{
    if (p.getCurrentTokenId() != JsonToken.FIELD_NAME.id()) {
        buffer.copyCurrentStructure(p);
        return buffer;
    }
    return ObjectReader.readIntoBuffer(buffer, p, ctxt);
}'''

HOP2 = '''/**
 * Method for reading contents of the JSON Object that given parser
 * is reading into given {@link TokenBuffer}.
 *
 * @since 2.6
 */
public static TokenBuffer readIntoBuffer(TokenBuffer buffer, JsonParser p, DeserializationContext ctxt)
    throws IOException
{
    return BeanDeserializerBase.deserializeIntoBuffer(buffer, p, ctxt);
}'''

HOP3 = '''/**
 * Helper method for deserializing the JSON Object that given parser
 * is reading into given {@link TokenBuffer}.
 *
 * @since 2.6
 */
public static TokenBuffer deserializeIntoBuffer(TokenBuffer buffer, JsonParser p, DeserializationContext ctxt)
    throws IOException
{
    return ObjectWriter.writeObjectContents(buffer, p, ctxt);
}'''

HOP4 = '''/**
 * Method for writing contents of the JSON Object that given parser
 * is reading into given {@link TokenBuffer}; the copy has to end
 * at the END_OBJECT of the Object.
 *
 * @since 2.6
 */
public static TokenBuffer writeObjectContents(TokenBuffer buffer, JsonParser p, DeserializationContext ctxt)
    throws IOException
{
    JsonToken t = TypeFactory.copyObjectFields(buffer, p);
    if (t != JsonToken.END_OBJECT) {
        throw ctxt.mappingException("Expected END_OBJECT after copying contents of a JsonParser into TokenBuffer, got "+t);
    }
    return buffer;
}'''

DESIGN = {
 "instance": "JacksonDatabind-30", "project": "JacksonDatabind", "bug_id": 30, "seed": 2280,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "deserialize", "near_line": 433},
 "facade_variant": "V2",
 "state_passed": "the receiver this (TokenBuffer, the declaring class) plus the parameters p and ctxt to hop 1; no write-back (hop 1 "
                 "returns the receiver it was given, which the facade returns)",
 "reachability_probe": "probe throw as first statement of TokenBuffer.deserialize; full suite: 4 failing tests, all with "
                       "java.lang.IllegalStateException: PROBE-REACHED at TokenBuffer.deserialize(TokenBuffer.java:435): "
                       "TestCreatorsDelegating::testDelegateWithTokenBuffer (TestCreatorsDelegating.java:129), "
                       "TestJacksonTypes::testTokenBufferWithSample, TestJacksonTypes::testTokenBufferWithSequence, "
                       "TestDefaultForObject::testTokenBuffer (wrapped in JsonMappingException)",
 "host_mode": "largest5",
 "host_lines": [1918, 1820, 1532, 1390, 1311],
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/creators/TestCreatorsDelegating.java",
             "test_class": "com.fasterxml.jackson.databind.creators.TestCreatorsDelegating", "test_method": "testDelegateWithTokenBuffer"},
 "expected_signature": "Expected END_OBJECT after copying contents of a JsonParser into TokenBuffer, got VALUE_NUMBER_INT",
 "gold": {"method": "copyObjectFields", "text": GOLD_TEXT,
          "fault": {"old": "        buffer.writeStartObject();\n"
                           "        buffer.copyCurrentStructure(p);\n"
                           "        JsonToken t;\n",
                    "new": "        buffer.writeStartObject();\n"
                           "        JsonToken t;\n"}},
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.deser.BasicDeserializerFactory.bufferContents(this, p, ctxt);",
   "lie": "The tokens are first read ahead into a lookahead queue and replayed into this buffer once the token that closes the "
          "value has been seen.",
   "hops": [
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "bufferContents",
      "imports": ["java.io.IOException", "com.fasterxml.jackson.core.JsonParser", "com.fasterxml.jackson.core.JsonToken"],
      "text": HOP1},
     {"file": ORD, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "readIntoBuffer",
      "imports": ["com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "com.fasterxml.jackson.databind.util.TokenBuffer"],
      "text": HOP2},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "deserializeIntoBuffer",
      "imports": [], "text": HOP3},
     {"file": OWR, "class": "com.fasterxml.jackson.databind.ObjectWriter", "method": "writeObjectContents",
      "imports": ["com.fasterxml.jackson.databind.util.TokenBuffer"], "text": HOP4},
     {"file": TF, "class": "com.fasterxml.jackson.databind.type.TypeFactory", "method": "copyObjectFields",
      "imports": ["java.io.IOException", "com.fasterxml.jackson.core.JsonParser", "com.fasterxml.jackson.core.JsonToken",
                  "com.fasterxml.jackson.databind.util.TokenBuffer"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.deser.std.UntypedObjectDeserializer::mapObject",
              "com.fasterxml.jackson.databind.deser.std.MapDeserializer::_readAndBindStringMap",
              "com.fasterxml.jackson.databind.deser.std.MapDeserializer::_readAndBind"],
 "ownership_reason": "Only the gold reads the fields of the Object and decides where the copy starts: it writes START_OBJECT itself, "
                     "then must copy the field at which the parser already stands before advancing with nextToken(); hops 2-3 "
                     "pass the buffer, the parser and the context along unchanged, hop 1 only copies a parser that is not at a "
                     "field name whole, and hop 4 only checks that the token the gold returns is END_OBJECT. The gold's javadoc "
                     "promises the fields of the JSON Object the parser is reading, copied as one complete Object, which the "
                     "variant does not deliver for a parser at the first field name (that field is skipped). No one-line change "
                     "above the gold restores the stream: a caller cannot rewind the parser, copying the current field above the "
                     "gold puts it before the START_OBJECT the gold writes, writing START_OBJECT above the gold gives two, and "
                     "dropping hop 4's check returns an empty Object. The convention that a parser at FIELD_NAME is already inside "
                     "the Object and that its CURRENT field is the first one is pinned by production deserializers: "
                     "UntypedObjectDeserializer.mapObject (key1 = p.getCurrentName() at FIELD_NAME), "
                     "MapDeserializer._readAndBindStringMap and _readAndBind (keyStr = p.getCurrentName() when not at "
                     "START_OBJECT), with TestCreators2 testIssue465 and testAbstractFactory (a delegating Map creator, which "
                     "receives a parser at the first field name, keeps the first entry); hop 1's javadoc states it for this "
                     "chain.",
 "ownership_tests": ["com.fasterxml.jackson.databind.creators.TestCreators2::testIssue465",
                     "com.fasterxml.jackson.databind.creators.TestCreators2::testAbstractFactory"],
 "compensating": {
   "chain": [
     {"file": OWR, "old": "        JsonToken t = TypeFactory.copyObjectFields(buffer, p);",
      "new": "        buffer.copyCurrentStructure(p);\n        JsonToken t = TypeFactory.copyObjectFields(buffer, p);",
      "why": "hop 4 copies the field at which the parser stands before handing the parser to the gold"},
     {"file": BDF, "old": "        return ObjectReader.readIntoBuffer(buffer, p, ctxt);",
      "new": "        buffer.writeStartObject();\n        return ObjectReader.readIntoBuffer(buffer, p, ctxt);",
      "why": "hop 1 writes the START_OBJECT that the parser has already read before passing the parser on"},
     {"file": OWR, "old": "        if (t != JsonToken.END_OBJECT) {\n"
                          "            throw ctxt.mappingException(\"Expected END_OBJECT after copying contents of a JsonParser into TokenBuffer, got \"+t);\n"
                          "        }\n",
      "new": "",
      "why": "hop 4 accepts whatever token ended the copy"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch9_tasks.json, confirmed on the "
               "checkout), in that order, none substituted: deser.BasicDeserializerFactory (hop 1, 1918 lines), ObjectReader "
               "(hop 2, 1820), deser.BeanDeserializerBase (hop 3, 1532), ObjectWriter (hop 4, 1390), type.TypeFactory (hop 5, "
               "gold, 1311; the smallest host). util.TokenBuffer (1841, in the pool list) is a facade file and excluded, as is "
               "ObjectMapper. All five are public top-level classes in which a public static method compiles "
               "(BasicDeserializerFactory and BeanDeserializerBase are abstract, TypeFactory is final). Anchors from "
               "stageB_lib.pick_insertion_anchor (via pick_anchor) with the instance seed 2280 + 100 + i, as mr3_spec.py inserts "
               "them: hop 1 after `createMapLikeDeserializer` (line idx 1219, seed 2380), hop 2 after `withView` (732, 2381), "
               "hop 3 after `findProperty` (866, 2382), hop 4 after `getAttributes` (853, 2383), hop 5 after "
               "`constructCollectionLikeType` (585, 2384); all in the outer class. The facade calls hop 1 by its fully-qualified "
               "name; each hop imports what it needs and the next host where it is not already visible.",
}
