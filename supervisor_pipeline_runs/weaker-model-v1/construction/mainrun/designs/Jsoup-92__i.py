"""Main run Jsoup-92__i (cell C10i, batch 9 / sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Jsoup-92; the real bug modified Attributes, HtmlTreeBuilder, ParseSettings, Token and XmlTreeBuilder; the facade's class
Attributes is one of them). No static pair (BUILD_BRIEF_C10I_B8_NOTE section 1: pool v2 found no tested static facade).

Facade: Attributes.asList() (the only allowed candidate of batch9_tasks.json for this task; facade_planned_by = Jsoup-75__i, so this is
a recorded facade reuse of Jsoup-75__i: no other allowed method exists, and nothing of that task was opened).
Original computation of the facade: for each of the `size` used slots of the parallel arrays keys/vals, a slot whose value is null
(a bare, boolean attribute) gives `new BooleanAttribute(keys[i])`; every other slot gives `new Attribute(keys[i], vals[i], this)`; the
attributes are collected in slot order into an ArrayList of capacity size, which is returned wrapped by Collections.unmodifiableList.

facade_variant: V1+V2. V1 (state as parameters): the facade reads the private field size and the package-private fields keys and vals
(inside Attributes, so no visibility change) and passes the three values to hop 1. V2 (receiver as parameter): the facade also passes
`this`, typed as Attributes, because every valued Attribute of the original is bound to its container (the third constructor argument
`Attributes.this`); the hops call no method of the receiver, they only hand it to the Attribute constructor. No field is written (no
write-back). No private method of Attributes is involved (no V4), and every type the chain names (Attribute, BooleanAttribute,
Attributes, List, ArrayList, Collections) is public (no V3/V5). No signature, modifier, override or throws change; no new type; no
reflection; no test edit.
state_passed: the package-private fields keys and vals (String[] references) and the private field size (int), plus the receiver
`this` as the Attributes parent of the listed attributes; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-92-probe of the fixture, the
first statement of asList was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the `if (true)` only keeps the
rest of the body reachable for javac). Full suite (`defects4j test`): 5 failing tests, each with java.lang.IllegalStateException:
PROBE-REACHED: ElementTest::testAddBooleanAttribute, AttributeParseTest::parsesBooleanAttributes,
ParserSettingsTest::attributesCaseNormalization, TokeniserTest::handleSuperLargeAttributeName and SelectorTest::testByAttributeStarting
(the last through the production caller Evaluator.AttributeStarting.matches, the [^prefix] selector). The facade is reached by
existing tests directly and through its one production caller.

Hosts (host_mode = "largest5": the fixed revision has one other public class of >= 1500 lines; the hosts are EXACTLY hosts_hop_order
of the task record, in that order, none substituted; Attributes.java, the facade's file, is excluded):
  hop 1 nodes.Element            1524 lines  attributesView        the read-only view: wraps the listed attributes with
                                                                    Collections.unmodifiableList (the original's last step)
  hop 2 helper.HttpConnection    1205 lines  attributePairs        pass-through
  hop 3 select.Evaluator          778 lines  matchableAttributes   pass-through
  hop 4 parser.HtmlTreeBuilder    741 lines  tokenAttributes       pass-through
  hop 5 nodes.Node                725 lines  listAttributes        GOLD: the walk over the used slots in slot order, the decision
                                                                    between a bare attribute (BooleanAttribute) and a valued
                                                                    attribute bound to its parent, and the new list
Host newline counts 1524, 1205, 778, 741, 725; the smallest host is Node (725 lines), which is also the gold host. All five are
public top-level classes in which a public static method compiles (Evaluator and Node are abstract, which does not affect a static
method). Evaluator declares a nested class named Attribute, so hop 3 names org.jsoup.nodes.Attribute by its qualified name; the recipe's
anchor in Evaluator.java is the constructor of the public static nested class Evaluator.IsNthOfType, so hop 3 is a static method of
that nested class and hop 2 calls it as Evaluator.IsNthOfType.matchableAttributes.
Anchors: chosen by the recipe (stageB_lib.insert_hop -> pick_anchor -> host_search.pick_insertion_anchor) with seed 6283 + 100 + i,
as mr3_spec.py inserts them; recorded in host_notes.
The correct configuration returns, for every Attributes, the same list as the original: the same slots in the same order, a
BooleanAttribute exactly for the slots whose value is null, an Attribute bound to the receiver for the others, in an unmodifiable
ArrayList-backed view.

Fault (one-line omission of a state reset in the gold's iteration): the gold carries the bare/valued decision of a slot in a local
flag that is set when the slot's value is absent and cleared once the bare attribute has been listed; the line that clears it is
dropped, so every slot after the first bare slot is listed as a BooleanAttribute, values and parent binding lost. The gold then still
reads as the ordinary routine "walk the slots; a slot without a value marks a bare attribute; bare attributes are listed as
BooleanAttribute, the others with their value". Keys, order and the number of attributes are unchanged.
Trigger: the EXISTING test AttributeParseTest::parsesBooleanAttributes. For `<a normal="123" boolean empty="">` the list is still of
size 3 and 'normal' and 'boolean' are still right, but the slot 'empty' (value "", after the bare slot 'boolean') is listed as a
BooleanAttribute: assertFalse("'empty' attribute should not be boolean", ...) fails with java.lang.AssertionError: 'empty' attribute
should not be boolean. It is the only test that newly fails: the other four tests that reach the facade list a single slot
(testAddBooleanAttribute: one bare slot, still a BooleanAttribute; handleSuperLargeAttributeName and attributesCaseNormalization: one
valued slot, still an Attribute with its value) or read only the keys (testByAttributeStarting, through Evaluator.AttributeStarting,
which matches on attribute.getKey(): every key is still listed), and the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the attributes of the used slots, in slot order; a bare attribute, one without a
value, is listed as a BooleanAttribute) and is silent on the flag. The convention that each slot is judged by its own value is pinned
outside the gold: Attributes.iterator() and Attributes.html(Appendable, OutputSettings) treat slot i from keys[i] and vals[i] alone
(html collapses only a slot whose own value allows it, through Attribute.shouldCollapseAttribute(key, val, out)); the producer of the
slots, Token.Tag.newAttribute(), gives each attribute its own three-way value (the pending value, "" for an empty value, null for
none) and clears hasEmptyAttributeValue and hasPendingAttributeValue after every attribute, so an empty value after a bare attribute
is stored as "" (not null); passing tests pin it: ElementTest::testAddBooleanAttribute (a bare slot is listed as a BooleanAttribute),
TokeniserTest::handleSuperLargeAttributeName (a valued slot is listed with its value), AttributeTest::booleanAttributesAreEmptyStringValues
(the iterator gives the bare slot its own empty-string value) and SelectorTest::testByAttributeStarting (every key is listed).

Single owner: only the gold walks the slots and decides, per slot, between a BooleanAttribute and a valued Attribute; hops 2-4 hand the
two arrays, the count and the parent on unchanged and hop 1 only wraps the returned list. The leak runs from one slot to the next
inside the gold's own loop, so no one-line change of the arrays, the count or the parent above the gold restores the empty slot: the
values are already right ("" is not null), shortening the count drops 'empty', and copying or bounding the arrays changes nothing.
Declared alternatives (G9): hop 4 bounds the count by the key slots (Math.min(size, keys.length)); hop 2 hands on trimmed copies of
the two arrays (Arrays.copyOf(.., size)); hop 1 copies the list into a new ArrayList before wrapping it. Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's walk, not repairs of the chain):
 B-1 a hop that calls the gold once per slot, crammed onto one line (a for loop over i calling listAttributes on
     Arrays.copyOfRange(keys, i, i + 1), Arrays.copyOfRange(vals, i, i + 1), count 1, and adding each one-element result): a one-slot
     walk never carries the flag to a next slot, so the trigger passes, while the gold still lists every slot after a bare slot as a
     BooleanAttribute for any multi-slot call; it sidesteps the gold's walk instead of repairing a hop (Java 7 source level: no
     lambda or stream form exists). Checked on the variant in a scratch copy (the loop on one line in hop 4): trigger passes,
     full suite 0 failing tests.
 B-0 the facade's original body (or a hop re-implementing the walk) re-implements the whole computation and makes the chain,
     including the gold, dead.

Lie: the facade's javadoc claims each attribute is created lazily, the first time its position in the returned list is read; the
chain creates every attribute eagerly, in one walk, before the list is returned. It names neither booleans, values, the flag, the
omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: keys gives every listed key; vals gives the bare/valued decision and every listed value; count bounds the walk and sizes
     the list; parent is bound into every valued Attribute; the gold has no argument check.
  T2 absent: list is filled and returned; key and val are read by the constructors and the decision; bare starts false, is set by the
     null-value decision and cleared in the bare branch, and decides which attribute is listed; i advances; both decisions lead to
     different effects (bare set or not; BooleanAttribute or Attribute).
  T3 absent: the pair halves key and value are both used for every slot; the two kinds of listed attribute (bare and valued) both have
     a branch; no enum, type code or named format member is left out.
  T4 absent: 'in slot order' is met by the ascending walk; 'a bare attribute, one without a value, is listed as a BooleanAttribute'
     by `if (val == null) bare = true;` and the bare branch; the @param/@return clauses name no rule the body breaks.
 Variant gold (javadoc, signature, new list, `boolean bare = false`, the walk, `if (val == null) bare = true;`, `if (bare)` lists a
 BooleanAttribute, else an Attribute with the value and the parent, return the list):
  T1 absent: keys gives every listed key; vals decides bare and is the value of every valued Attribute; count bounds the walk and sizes
     the list; parent is passed to every valued Attribute; none is only argument-checked.
  T2 absent: list is returned; key and val are read; bare is initialised to false but reassigned to true inside the loop and tested
     by `if (bare)` (not frozen under (i) or (ii): the loop assigns it); i advances; `if (val == null)` changes bare and `if (bare)`
     chooses between two different attributes, so neither decision is dead.
  T3 absent: key and value are both used (the value in the decision and in the valued Attribute); both kinds of listed attribute
     keep a branch; a missing reset of a loop flag is 'No member handled' (the checklist's 'a word loop with no reset'); the gold's text
     names no class it would handle in part.
  T4 absent: 'Lists the attributes of the used slots ... in slot order' is a general description that the walk addresses; 'a bare
     attribute, one without a value, is listed as a BooleanAttribute' is met for the case it names (a null value sets bare and the
     bare branch lists a BooleanAttribute); '@param vals ... a bare attribute has no value' is a description of the input; '@param
     parent the attributes the slots belong to' and '@return a new list of the attributes' name no concrete rule; no inline comment;
     the identifiers list, key, val and bare name what they hold where they are set."""

ATTRS = "src/main/java/org/jsoup/nodes/Attributes.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
NODE = "src/main/java/org/jsoup/nodes/Node.java"

GOLD_TEXT = '''/**
 * Lists the attributes of the used slots of parallel key and value arrays, in slot order. A bare attribute, one
 * without a value, is listed as a {@link BooleanAttribute}.
 * @param keys the attribute keys, by slot
 * @param vals the attribute values, by slot; a bare attribute has no value
 * @param count the number of used slots
 * @param parent the attributes the slots belong to
 * @return a new list of the attributes
 */
public static List<Attribute> listAttributes(String[] keys, String[] vals, int count, Attributes parent) {
    List<Attribute> list = new ArrayList<>(count);
    boolean bare = false;
    for (int i = 0; i < count; i++) {
        String key = keys[i];
        String val = vals[i];
        if (val == null)
            bare = true;
        if (bare) {
            list.add(new BooleanAttribute(key));
            bare = false;
        } else {
            list.add(new Attribute(key, val, parent));
        }
    }
    return list;
}'''

HOP1 = '''/**
 * Get a read-only list of the attributes held in parallel key and value slots, in slot order.
 * @param keys the attribute keys, by slot
 * @param vals the attribute values, by slot
 * @param size the number of used slots
 * @param parent the attributes the slots belong to
 * @return an unmodifiable list of the attributes
 */
public static List<Attribute> attributesView(String[] keys, String[] vals, int size, Attributes parent) {
    return Collections.unmodifiableList(HttpConnection.attributePairs(keys, vals, size, parent));
}'''

HOP2 = '''/**
 * Lists the attributes held in parallel key and value slots, in slot order.
 * @param keys the attribute keys, by slot
 * @param vals the attribute values, by slot
 * @param size the number of used slots
 * @param parent the attributes the slots belong to
 * @return the attributes, in slot order
 */
public static List<Attribute> attributePairs(String[] keys, String[] vals, int size, Attributes parent) {
    return Evaluator.IsNthOfType.matchableAttributes(keys, vals, size, parent);
}'''

HOP3 = '''/**
 * Lists the attributes held in parallel key and value slots, in slot order.
 * @param keys the attribute keys, by slot
 * @param vals the attribute values, by slot
 * @param size the number of used slots
 * @param parent the attributes the slots belong to
 * @return the attributes, in slot order
 */
public static List<org.jsoup.nodes.Attribute> matchableAttributes(String[] keys, String[] vals, int size, Attributes parent) {
    return HtmlTreeBuilder.tokenAttributes(keys, vals, size, parent);
}'''

HOP4 = '''/**
 * Lists the attributes held in parallel key and value slots, in slot order.
 * @param keys the attribute keys, by slot
 * @param vals the attribute values, by slot
 * @param size the number of used slots
 * @param parent the attributes the slots belong to
 * @return the attributes, in slot order
 */
public static List<Attribute> tokenAttributes(String[] keys, String[] vals, int size, Attributes parent) {
    return Node.listAttributes(keys, vals, size, parent);
}'''

DESIGN = {
 "instance": "Jsoup-92", "project": "Jsoup", "bug_id": 92, "seed": 6283,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": ATTRS, "class": "org.jsoup.nodes.Attributes", "method": "asList", "near_line": 288},
 "facade_variant": "V1+V2",
 "state_passed": "package-private fields keys and vals (String[]) and private field size (int), plus the receiver this as the "
                 "Attributes parent of the listed attributes; no write-back",
 "reachability_probe": "full suite with `if (true) throw new IllegalStateException(\"PROBE-REACHED\")` as asList's first statement: "
                       "5 failing tests, all PROBE-REACHED: ElementTest::testAddBooleanAttribute, "
                       "AttributeParseTest::parsesBooleanAttributes, ParserSettingsTest::attributesCaseNormalization, "
                       "TokeniserTest::handleSuperLargeAttributeName, SelectorTest::testByAttributeStarting (via "
                       "Evaluator.AttributeStarting.matches)",
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/parser/AttributeParseTest.java",
             "test_class": "org.jsoup.parser.AttributeParseTest", "test_method": "parsesBooleanAttributes"},
 "expected_signature": "'empty' attribute should not be boolean",
 "gold": {"method": "listAttributes", "text": GOLD_TEXT,
          "fault": {"old": "                list.add(new BooleanAttribute(key));\n"
                           "                bare = false;\n",
                    "new": "                list.add(new BooleanAttribute(key));\n"}},
 "chain": {
   "facade_body": "return Element.attributesView(keys, vals, size, this);",
   "lie": "Each attribute is created lazily, the first time its position in the returned list is read.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "attributesView",
      "imports": ["org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "attributePairs",
      "imports": ["org.jsoup.nodes.Attribute", "org.jsoup.nodes.Attributes", "org.jsoup.select.Evaluator"], "text": HOP2},
     {"file": EV, "class": "org.jsoup.select.Evaluator.IsNthOfType", "method": "matchableAttributes",
      "imports": ["org.jsoup.nodes.Attributes", "org.jsoup.parser.HtmlTreeBuilder"], "text": HOP3},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "tokenAttributes",
      "imports": ["org.jsoup.nodes.Attribute", "org.jsoup.nodes.Attributes"], "text": HOP4},
     {"file": NODE, "class": "org.jsoup.nodes.Node", "method": "listAttributes", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.nodes.Attributes::iterator",
              "org.jsoup.nodes.Attributes::html",
              "org.jsoup.parser.Token.Tag::newAttribute"],
 "ownership_reason": "Only the gold walks the used slots and decides, slot by slot, between a BooleanAttribute (no value) and an "
                     "Attribute with its value bound to the parent; hops 2-4 hand the two arrays, the count and the parent on "
                     "unchanged and hop 1 only wraps the returned list read-only. The gold's javadoc promises the attributes of "
                     "the used slots in slot order with a bare attribute, one without a value, listed as a BooleanAttribute; the "
                     "slot 'empty' of <a normal=\"123\" boolean empty=\"\"> has the value \"\" and is not bare, yet the variant "
                     "lists it as a BooleanAttribute. The decision of one slot leaks into the next inside the gold's own loop, so "
                     "no one-line change of the arrays, the count or the parent above the gold restores it: the values reaching "
                     "the gold are already right, a shorter count drops the slot, and copying or bounding the arrays changes "
                     "nothing. The convention is pinned outside the gold: Attributes.iterator() and Attributes.html(Appendable, "
                     "OutputSettings) treat slot i from keys[i] and vals[i] alone (html collapses a slot only through "
                     "Attribute.shouldCollapseAttribute(key, val, out) on that slot's own value); Token.Tag.newAttribute(), which "
                     "fills the slots, gives each attribute its own value (the pending value, \"\" for an empty value, null for "
                     "none) and clears hasEmptyAttributeValue and hasPendingAttributeValue after every attribute; passing tests: "
                     "ElementTest testAddBooleanAttribute (a bare slot is listed as a BooleanAttribute), TokeniserTest "
                     "handleSuperLargeAttributeName (a valued slot is listed with its value), AttributeTest "
                     "booleanAttributesAreEmptyStringValues (the iterator gives a bare slot its own empty value) and SelectorTest "
                     "testByAttributeStarting (every key is listed).",
 "ownership_tests": ["org.jsoup.nodes.ElementTest::testAddBooleanAttribute",
                     "org.jsoup.parser.TokeniserTest::handleSuperLargeAttributeName",
                     "org.jsoup.nodes.AttributeTest::booleanAttributesAreEmptyStringValues",
                     "org.jsoup.select.SelectorTest::testByAttributeStarting"],
 "compensating": {
   "chain": [
     {"file": HTB, "old": "return Node.listAttributes(keys, vals, size, parent);",
      "new": "return Node.listAttributes(keys, vals, Math.min(size, keys.length), parent);",
      "why": "hop 4 bounds the slot count by the number of key slots"},
     {"file": HC, "old": "return Evaluator.IsNthOfType.matchableAttributes(keys, vals, size, parent);",
      "new": "return Evaluator.IsNthOfType.matchableAttributes(java.util.Arrays.copyOf(keys, size), java.util.Arrays.copyOf(vals, size), size, parent);",
      "why": "hop 2 hands on copies of the used slots only"},
     {"file": EL, "old": "return Collections.unmodifiableList(HttpConnection.attributePairs(keys, vals, size, parent));",
      "new": "return Collections.unmodifiableList(new ArrayList<>(HttpConnection.attributePairs(keys, vals, size, parent)));",
      "why": "hop 1 copies the listed attributes before wrapping them"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are EXACTLY hosts_hop_order of the task record (batch9_tasks.json), in that order, none "
               "substituted: nodes.Element (hop 1, 1524 lines), helper.HttpConnection (hop 2, 1205), select.Evaluator (hop 3, "
               "778), parser.HtmlTreeBuilder (hop 4, 741), nodes.Node (hop 5, gold, 725; the smallest host). Attributes.java, the "
               "facade's file, is excluded. All five are public top-level classes in which a public static method compiles "
               "(Evaluator and Node are abstract). Evaluator declares a nested class Attribute, so hop 3 names "
               "org.jsoup.nodes.Attribute by its qualified name. Anchors from the recipe's anchor picker "
               "(stageB_lib.insert_hop / pick_anchor / host_search.pick_insertion_anchor) with seed 6283 + 100 + i, as "
               "mr3_spec.py inserts them: "
               "hop 1 after `previousElementSiblings` (line idx 733, seed 6383), hop 2 after the outer `url(URL)` (134, 6384), "
               "hop 3 after the constructor `IsNthOfType` (517, 6385), hop 4 after `getFromStack` (328, 6386), hop 5 after "
               "`siblingNodes` (494, 6387). Hops 1, 2, 4 and 5 land in the outer class; the recipe's anchor in Evaluator is the "
               "tab-indented constructor of the public static nested class Evaluator.IsNthOfType, so hop 3 is a public static "
               "method of that nested class (it compiles there and is callable from any package); hop 2 therefore calls it as "
               "Evaluator.IsNthOfType.matchableAttributes, and its decoy class is recorded as org.jsoup.select.Evaluator.IsNthOfType. "
               "The host (Evaluator.java) and the anchor are the recipe's, unchanged. The facade calls hop 1 as Element.attributesView (same "
               "package); each hop imports the next host.",
}
