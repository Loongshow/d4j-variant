"""Main run JacksonDatabind-20__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J JacksonDatabind-20; the real bug modified ObjectNode, the target class). No static pair (pool v2: no_tested_static).

Facade: ObjectNode.findValuesAsText(String, List<String>) (allowed instance target of BATCH8_PREREGISTRATION.md row 249;
facade_planned_by null, no facade reuse). The other two allowed targets were not used: ObjectNode.serialize writes every Object node
of every tree serialization (hundreds of tests reach it), and its loop (start marker, name + value per field, end marker) has no
special-case step whose omission only one existing test would catch; ObjectNode.findValues is reached by two tests
(TestFindMethods testNonMatching and testMatchingMultiple) and carries the same computation without the text conversion, so
findValuesAsText is the candidate with the larger per-element core and a single reaching test.
Original computation of the facade: for each field of the node (in insertion order of the LinkedHashMap _children), a field whose
name equals fieldName has its value's asText() added to foundSoFar (the list is created on the first such value when foundSoFar is
null); any other field's value is searched in turn through the virtual JsonNode.findValuesAsText(fieldName, foundSoFar) (ArrayNode
walks its elements, ObjectNode recurses, ValueNode returns the list as is), so the sub-tree below a matching field is not searched;
the (possibly null) list is returned. JsonNode.findValuesAsText(String) turns null into an empty list.

facade_variant: V1 (state as parameters). The method reads one protected field and writes none: the facade gathers the state
`_children.entrySet().iterator()` (the same iterator ObjectNode.fields() returns; inside ObjectNode, so no visibility change) and
passes it with the two parameters to hop 1, then returns hop 1's result. The chain needs no method of the receiver (the descent goes
through the children's own public JsonNode.findValuesAsText), so V2 is not needed; no private method is called (no V4); no
package-private type is involved (no V3/V5). The facade had no javadoc of its own (only @Override); a pre-edit adds one in the class's
voice directly above @Override, and the lie sentence is written at its end there (the recipe's rewrite_facade appends only to a
javadoc that directly precedes the method header, which @Override prevents; the chain's `lie` key holds the same sentence). No
signature, modifier, annotation, override or throws change; no new type; no reflection; no test edit.
state_passed: the iterator over the protected field _children (_children.entrySet().iterator()), plus fieldName and foundSoFar, to
hop 1; no write-back (the method writes no field).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-JacksonDatabind-20-probe of the
fixture, the first statement of ObjectNode.findValuesAsText was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
`defects4j test -t com.fasterxml.jackson.databind.node.TestFindMethods::testMatchingMultiple`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at ObjectNode.findValuesAsText(ObjectNode.java:198) from
JsonNode.findValuesAsText(JsonNode.java:814) from TestFindMethods.testMatchingMultiple(TestFindMethods.java:59). Full suite with the
probe: 1 failing test (testMatchingMultiple only). The facade is reached by exactly one existing test.

Hosts (host_mode = "1500"; `mr_lib.py preview JacksonDatabind-20 com/fasterxml/jackson/databind/node/ObjectNode.java 5`, instance seed
5638; exactly five other public classes of >= 1,500 lines exist, and the seeded draw orders them; nothing substituted):
  hop 1 util.TokenBuffer                 1785 lines  collectFieldText           decision: no fields gives the list back as is
  hop 2 deser.BasicDeserializerFactory   1819 lines  findPropertyValuesAsText   pass-through
  hop 3 ObjectMapper                     3688 lines  treeValuesAsText           pass-through
  hop 4 deser.BeanDeserializerBase       1504 lines  propertyValuesAsText       pass-through (the smallest host)
  hop 5 ObjectReader                     1739 lines  fieldValuesAsText          GOLD: the walk over the fields, the name match, the
                                                                                lazily created list, the text conversion and the
                                                                                descent into the values of the other fields
The correct configuration returns exactly the original list for every node: hop 1's shortcut is the original's empty loop; the gold
is the original loop body over the same iterator, in the same order, with the same virtual descent.

Fault (one-line omission in the gold's iteration): the descent into the value of a field whose name does not match
(`foundSoFar = entry.getValue().findValuesAsText(fieldName, foundSoFar);` with its else) is dropped, so only fields of the node itself
are found. The gold then reads as the ordinary routine "walk the fields, add the text of every value whose name matches". Trigger: the
EXISTING test TestFindMethods::testMatchingMultiple. Its findValues and findParents assertions still hold; for the tree
{"a":{"value":3},"array":[{"b":3},{"value":42},{"other":true}]} the root has no field "value" of its own, so
root.findValuesAsText("value") gives an empty list and assertEquals(2, values.size()) at line 60 fails with expected:<2> but
was:<0>. It is the only test that newly fails: the probe's full-suite run shows that no other test reaches the facade, and the new hops
have no other caller.

The gold's javadoc states the idiomatic contract in Jackson's own words for the find methods ("Method for finding JSON Object fields
with specified name", JsonNode.findValues) and is silent on the descent. The convention is pinned outside the gold: the facade's own
(new, class-voice) javadoc ("in this node or its descendants"); JsonNode.findValues ("If no matching fields are found in this node or
its descendants ... sub-tree search ends if a field is found") and JsonNode.findValuesAsText ("Similar to findValues"); the sibling
ObjectNode.findValues and ObjectNode.findParents, which descend into the other fields' values in the same loop shape;
ArrayNode.findValuesAsText, which walks its elements; with TestFindMethods testMatchingSingle (findValue and findParent find "b" inside
an array element) and testNonMatching passing.

Single owner: only the gold walks the fields and decides, per field, between adding the value and descending into it; hops 2-4 pass
the iterator along and hop 1 only answers an exhausted iterator. Because the fields reach the chain as one iterator, a hop can only
look at a field by consuming it, so a hop that descends into the fields' values itself leaves the gold nothing to match (and loses the
direct matches), and a hop that consumes one field loses it for the gold. Declared alternatives (G9): hop 4 creates the list up
front; hop 2 descends into every remaining field's value before passing the iterator on; hop 3 descends into the first field's value
and passes the rest on. Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-0 the facade's original body (or any hop re-implementing the walk: materialising the fields into a list, matching, descending and
     passing nothing or an empty iterator to the rest of the chain) re-implements the whole computation and makes the gold dead. No
     one-line edit above the gold reproduces the per-field interleaving of matches and descents.

Lie: the facade's javadoc claims field names are matched by comparing their interned forms, one reference comparison per field; the
chain compares names with String.equals. It names neither the descent, the omitted step nor any hop.

Covariates: host_mode 1500; host sizes 1785, 1819, 3688, 1504, 1739 (hop 1 -> 5); the smallest host is BeanDeserializerBase (1504
lines, hop 4); the gold host ObjectReader has 1739 lines.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: fields drives the loop and supplies every name and value; fieldName is compared and passed into the descent;
     foundSoFar is returned, added to and passed into the descent; no argument check exists.
  T2 absent: entry is read for its name, its value's text and the descent; foundSoFar is reassigned by the creation and by the
     descent and returned; the loop cursor is the iterator, advanced by fields.next() in every iteration; no literal-initialised
     local; the match/other decision and the null decision lead to different effects. (The original's comment "only add children if
     parent not added" is not carried over.)
  T3 absent: no enum, type code or named format; the two outcomes per field (added or descended into) are both present.
  T4 absent: "finding JSON Object fields with specified name, and adding their values, as text ... to the given List" is a general
     description that the body addresses; "if null, one is created when the first value is found" is met by the null decision;
     "otherwise the given list" by returning foundSoFar; no inline comment; identifiers name what they hold.
 Variant gold (javadoc, signature, while over fields, entry = fields.next(), name match -> create the list if null and add the
 value's asText(), return foundSoFar):
  T1 absent: fields drives the loop and supplies names and values; fieldName decides which values are added; foundSoFar is
     returned, created when null and added to; none is read only in an argument check (there is none).
  T2 absent: entry is read for its name (decision) and its value (added text); foundSoFar is assigned in the null decision and
     returned; the iterator advances with fields.next() in every iteration; no literal-initialised local, no counter, flag or
     best-so-far; the name decision guards a live add, the null decision a live creation.
  T3 absent: the gold reads a field's name and value and gives each its one treatment (name compared, value converted and added);
     no member of a closed set (enum, type code, named format, pair halves or range ends) is handled while a sibling is not; the
     gold's text names no class it would handle in part (no "descendants", "nested", "all", "every").
  T4 absent: "Method for finding JSON Object fields with specified name, and adding their values, as text (see JsonNode#asText), to
     the given List" is a general description that the name match and the add address; "@param foundSoFar ... if null, one is
     created when the first value is found" is met by the null decision; "@return List with the values added, if any; otherwise the
     given list" by `return foundSoFar`; "@param fields Fields (name and value) of the Object node to look in" and "@param fieldName
     Name of field to look for" name no rule the body breaks; no inline comment; identifiers (entry, foundSoFar) name what they
     hold."""

ON = "src/main/java/com/fasterxml/jackson/databind/node/ObjectNode.java"
TB = "src/main/java/com/fasterxml/jackson/databind/util/TokenBuffer.java"
BDF = "src/main/java/com/fasterxml/jackson/databind/deser/BasicDeserializerFactory.java"
OM = "src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java"
BDB = "src/main/java/com/fasterxml/jackson/databind/deser/BeanDeserializerBase.java"
OR = "src/main/java/com/fasterxml/jackson/databind/ObjectReader.java"

LIE = "Field names are matched by comparing their interned forms, one reference comparison per field."

GOLD_TEXT = '''/**
 * Method for finding JSON Object fields with specified name, and
 * adding their values, as text (see {@link JsonNode#asText}), to the
 * given List.
 *
 * @param fields Fields (name and value) of the Object node to look in
 * @param fieldName Name of field to look for
 * @param foundSoFar List to add values to; if null, one is created
 *    when the first value is found
 *
 * @return List with the values added, if any; otherwise the given list
 */
public static List<String> fieldValuesAsText(Iterator<Map.Entry<String, JsonNode>> fields,
        String fieldName, List<String> foundSoFar)
{
    while (fields.hasNext()) {
        Map.Entry<String, JsonNode> entry = fields.next();
        if (fieldName.equals(entry.getKey())) {
            if (foundSoFar == null) {
                foundSoFar = new ArrayList<String>();
            }
            foundSoFar.add(entry.getValue().asText());
        } else {
            foundSoFar = entry.getValue().findValuesAsText(fieldName, foundSoFar);
        }
    }
    return foundSoFar;
}'''

HOP1 = '''/**
 * Method for finding JSON Object fields with specified name, and
 * adding their values, as text, to the given List. If there are no
 * fields, the given List is returned as is.
 *
 * @param fields Fields (name and value) of the Object node to look in
 * @param fieldName Name of field to look for
 * @param foundSoFar List to add values to; may be null
 *
 * @return List with the values added, if any; otherwise the given list
 */
public static List<String> collectFieldText(Iterator<Map.Entry<String, JsonNode>> fields,
        String fieldName, List<String> foundSoFar)
{
    if (!fields.hasNext()) {
        return foundSoFar;
    }
    return BasicDeserializerFactory.findPropertyValuesAsText(fields, fieldName, foundSoFar);
}'''

HOP2 = '''/**
 * Method for finding JSON Object fields with specified name, and
 * adding their values, as text, to the given List.
 *
 * @param fields Fields (name and value) of the Object node to look in
 * @param fieldName Name of field to look for
 * @param foundSoFar List to add values to; may be null
 *
 * @return List with the values added, if any; otherwise the given list
 */
public static List<String> findPropertyValuesAsText(Iterator<Map.Entry<String, JsonNode>> fields,
        String fieldName, List<String> foundSoFar)
{
    return ObjectMapper.treeValuesAsText(fields, fieldName, foundSoFar);
}'''

HOP3 = '''/**
 * Method for finding JSON Object fields with specified name, and
 * adding their values, as text, to the given List.
 *
 * @param fields Fields (name and value) of the Object node to look in
 * @param fieldName Name of field to look for
 * @param foundSoFar List to add values to; may be null
 *
 * @return List with the values added, if any; otherwise the given list
 */
public static List<String> treeValuesAsText(Iterator<Map.Entry<String, JsonNode>> fields,
        String fieldName, List<String> foundSoFar)
{
    return BeanDeserializerBase.propertyValuesAsText(fields, fieldName, foundSoFar);
}'''

HOP4 = '''/**
 * Method for finding JSON Object fields with specified name, and
 * adding their values, as text, to the given List.
 *
 * @param fields Fields (name and value) of the Object node to look in
 * @param fieldName Name of field to look for
 * @param foundSoFar List to add values to; may be null
 *
 * @return List with the values added, if any; otherwise the given list
 */
public static List<String> propertyValuesAsText(Iterator<Map.Entry<String, JsonNode>> fields,
        String fieldName, List<String> foundSoFar)
{
    return ObjectReader.fieldValuesAsText(fields, fieldName, foundSoFar);
}'''

FACADE_DOC_OLD = ("    @Override\n"
                  "    public List<String> findValuesAsText(String fieldName, List<String> foundSoFar)\n")
FACADE_DOC_NEW = ("    /**\n"
                  "     * Method for finding JSON Object fields with specified name in this\n"
                  "     * node or its descendants, and adding their values, as text, to the\n"
                  "     * given List, which is created if null when the first value is found.\n"
                  "     * Field names are matched by comparing their interned forms, one\n"
                  "     * reference comparison per field.\n"
                  "     */\n"
                  "    @Override\n"
                  "    public List<String> findValuesAsText(String fieldName, List<String> foundSoFar)\n")

DESIGN = {
 "instance": "JacksonDatabind-20", "project": "JacksonDatabind", "bug_id": 20, "seed": 5638,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": ON, "class": "com.fasterxml.jackson.databind.node.ObjectNode", "method": "findValuesAsText", "near_line": 196},
 "facade_variant": "V1",
 "state_passed": "the iterator over the protected field _children (_children.entrySet().iterator()) plus fieldName and foundSoFar "
                 "to hop 1; no write-back (the method writes no field)",
 "reachability_probe": "testMatchingMultiple fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "ObjectNode.findValuesAsText(ObjectNode.java:198) from JsonNode.findValuesAsText(JsonNode.java:814) from "
                       "TestFindMethods.java:59; full suite with the probe: 1 failing test (testMatchingMultiple)",
 "host_mode": "1500",
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/databind/node/TestFindMethods.java",
             "test_class": "com.fasterxml.jackson.databind.node.TestFindMethods", "test_method": "testMatchingMultiple"},
 "expected_signature": "expected:<2> but was:<0>",
 "gold": {"method": "fieldValuesAsText", "text": GOLD_TEXT,
          "fault": {"old": "                foundSoFar.add(entry.getValue().asText());\n"
                           "            } else {\n"
                           "                foundSoFar = entry.getValue().findValuesAsText(fieldName, foundSoFar);\n"
                           "            }\n",
                    "new": "                foundSoFar.add(entry.getValue().asText());\n"
                           "            }\n"}},
 "pre_edits": {"chain": [
     {"file": ON, "old": FACADE_DOC_OLD, "new": FACADE_DOC_NEW},
 ]},
 "chain": {
   "facade_body": "return com.fasterxml.jackson.databind.util.TokenBuffer.collectFieldText(_children.entrySet().iterator(),\n"
                  "                fieldName, foundSoFar);",
   "lie": LIE,
   "hops": [
     {"file": TB, "class": "com.fasterxml.jackson.databind.util.TokenBuffer", "method": "collectFieldText",
      "imports": ["java.util.Iterator", "java.util.List", "java.util.Map",
                  "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory"], "text": HOP1},
     {"file": BDF, "class": "com.fasterxml.jackson.databind.deser.BasicDeserializerFactory", "method": "findPropertyValuesAsText",
      "imports": [], "text": HOP2},
     {"file": OM, "class": "com.fasterxml.jackson.databind.ObjectMapper", "method": "treeValuesAsText",
      "imports": [], "text": HOP3},
     {"file": BDB, "class": "com.fasterxml.jackson.databind.deser.BeanDeserializerBase", "method": "propertyValuesAsText",
      "imports": [], "text": HOP4},
     {"file": OR, "class": "com.fasterxml.jackson.databind.ObjectReader", "method": "fieldValuesAsText",
      "imports": ["java.util.ArrayList", "java.util.List"], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.databind.node.ObjectNode::findValues",
              "com.fasterxml.jackson.databind.node.ObjectNode::findParents",
              "com.fasterxml.jackson.databind.node.ArrayNode::findValuesAsText",
              "com.fasterxml.jackson.databind.JsonNode::findValues"],
 "ownership_reason": "Only the gold walks the fields of the Object node and decides, per field, between adding the text of a "
                     "value whose name matches and searching the value of any other field (through the child's own "
                     "JsonNode.findValuesAsText); hops 2-4 pass the iterator over the fields along unchanged and hop 1 only "
                     "answers an exhausted iterator with the given list. Because the fields reach the chain as one iterator, "
                     "no one-line edit above the gold can search the other fields' values without consuming the fields the "
                     "gold must match. The find methods' convention is pinned outside the gold: the facade's javadoc ('in this "
                     "node or its descendants'); JsonNode.findValues ('If no matching fields are found in this node or its "
                     "descendants ... sub-tree search ends if a field is found') and JsonNode.findValuesAsText ('Similar to "
                     "findValues'); the sibling ObjectNode.findValues and ObjectNode.findParents, which search the other "
                     "fields' values in the same loop; ArrayNode.findValuesAsText, which walks its elements; with "
                     "TestFindMethods testMatchingSingle (findValue and findParent find 'b' inside an array element) and "
                     "testNonMatching passing.",
 "ownership_tests": ["com.fasterxml.jackson.databind.node.TestFindMethods::testMatchingSingle",
                     "com.fasterxml.jackson.databind.node.TestFindMethods::testNonMatching"],
 "compensating": {
   "chain": [
     {"file": BDB, "old": "        return ObjectReader.fieldValuesAsText(fields, fieldName, foundSoFar);",
      "new": "        return ObjectReader.fieldValuesAsText(fields, fieldName,\n"
             "                (foundSoFar == null) ? new ArrayList<String>() : foundSoFar);",
      "why": "hop 4 creates the list up front instead of leaving it to the first value"},
     {"file": BDF, "old": "        return ObjectMapper.treeValuesAsText(fields, fieldName, foundSoFar);",
      "new": "        while (fields.hasNext()) {\n"
             "            foundSoFar = fields.next().getValue().findValuesAsText(fieldName, foundSoFar);\n"
             "        }\n"
             "        return ObjectMapper.treeValuesAsText(fields, fieldName, foundSoFar);",
      "why": "hop 2 searches the value of every remaining field before passing the fields on"},
     {"file": OM, "old": "        return BeanDeserializerBase.propertyValuesAsText(fields, fieldName, foundSoFar);",
      "new": "        foundSoFar = fields.next().getValue().findValuesAsText(fieldName, foundSoFar);\n"
             "        return BeanDeserializerBase.propertyValuesAsText(fields, fieldName, foundSoFar);",
      "why": "hop 3 searches the value of the first field and passes the rest on"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts drawn with `mr_lib.py preview JacksonDatabind-20 "
               "com/fasterxml/jackson/databind/node/ObjectNode.java 5` (instance seed 5638; the draw excludes the facade file "
               "ObjectNode.java, the only allowed-candidate file); exactly five other public classes of >= 1,500 lines exist "
               "and the seeded draw orders them: util.TokenBuffer (hop 1, 1785 lines, anchor after `getOutputContext`, line 542, "
               "seed 5738), deser.BasicDeserializerFactory (hop 2, 1819, after `withAdditionalKeyDeserializers`, line 150, seed "
               "5739), ObjectMapper (hop 3, 3688, after `findAndRegisterModules`, line 893, seed 5740), "
               "deser.BeanDeserializerBase (hop 4, 1504, the smallest host, after `properties`, line 819, seed 5741), "
               "ObjectReader (hop 5, gold, 1739, after `withFeatures`, line 400, seed 5742); all anchors in the outer class. "
               "None substituted: all five are public top-level classes in which a static method compiles "
               "(BasicDeserializerFactory and BeanDeserializerBase are abstract, which does not affect a static method). The "
               "facade calls hop 1 by its fully-qualified name; each hop names the next host (imports added only where the "
               "host did not already see the type).",
}
