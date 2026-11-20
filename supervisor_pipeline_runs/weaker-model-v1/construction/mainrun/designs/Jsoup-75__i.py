"""Main run Jsoup-75__i (cell C10i, batch 9 (9b): the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Jsoup-75; the real bug modified org.jsoup.nodes.Attributes, the facade's class). No static pair (B8 note section 1: pool v2 found no
strictly tested public static method in Attributes); facade_planned_by = null, facade_reuse_of = null.

Facade: Attributes.asList() (the only allowed candidate of batch9_tasks.json, BATCH9_PREREGISTRATION.md rank 358; planned by no
earlier task). Original computation: one pass over the used slots 0..size-1 of the parallel arrays keys/vals; a slot whose value is
null (jsoup's representation of a boolean attribute: "we track boolean attributes as null in values") becomes a BooleanAttribute of
its key, every other slot an Attribute of its key and value bound to this Attributes (Attribute(key, val, Attributes.this)); the list
(in slot order) is returned wrapped by Collections.unmodifiableList.

facade_variant: V1+V2 (state as parameters, with the receiver as a parameter). state_passed: the fields keys (String[]), vals
(String[]) and size (int) are read in the facade and handed to hop 1 together with `this` (typed Attributes), which the chain uses only
as the owner the valued attributes are bound to (no method of it is called); no field is written, no write-back. The facade body is
one call to hop 1 (the original had no guard). No visibility is widened (the package-private keys/vals and the private size are read
inside the class), no type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit. asList
calls no private method of its class, so V4 does not apply; Attribute, Attributes and BooleanAttribute are public types with public
constructors, so V3/V5 do not apply.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-75-probe of the fixture, the first statement of
asList() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; the FULL suite was run
(`defects4j test`): exactly 5 failing tests, each with java.lang.IllegalStateException: PROBE-REACHED -
ElementTest::testAddBooleanAttribute, AttributeParseTest::parsesBooleanAttributes, ParserSettingsTest::attributesCaseNormalization,
TokeniserTest::handleSuperLargeAttributeName, SelectorTest::testByAttributeStarting (the last through the production caller
Evaluator.AttributeStarting.matches). The facade is reached directly by the trigger (AttributeParseTest.java:83).

What each reaching test observes of asList: testAddBooleanAttribute - one slot, a boolean attribute (size 1, instanceof
BooleanAttribute); parsesBooleanAttributes - three slots "normal"="123", "boolean" (null), "empty"="" (size 3; get(0) and get(2) not
BooleanAttribute, get(1) a BooleanAttribute); attributesCaseNormalization and handleSuperLargeAttributeName - one valued slot (key,
value); testByAttributeStarting - keys only (lists of 3, 2 and 1 slots; the boolean attribute "attribute" is matched by its key).

Redistribution of the computation: hop 1 wraps the list (unmodifiable view); hop 2 is the placement/shortcut step: no slots give an
empty list and a single slot a singleton list holding that slot's attribute (the single-slot shortcut decides the kind of its one
attribute itself, by the same null-value rule), any other count goes down the chain; hop 3 creates the list sized to the slots; hop 4
passes through; hop 5, the gold, is the per-slot core: one pass over the slots, adding each slot's attribute (BooleanAttribute for a
null value, otherwise an Attribute bound to the owner) in slot order. The correct configuration returns, for every Attributes, a list
equal element by element (class, key, value, owner) to the original's, unmodifiable as before.

Hosts (host_mode = "largest5"; batch9_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 nodes.Element          1464 lines  attributesView       aggregation: unmodifiable view of the list
  hop 2 helper.HttpConnection  1254 lines  attributesInSlots    placement: empty / single-slot shortcuts, else down the chain
  hop 3 select.Evaluator        778 lines  attributeListOf      aggregation: creates the list sized to the slots and returns it
        (the seeded anchor is after IsOnlyOfType.toString, so the method sits in the public static nested class
        Evaluator.IsOnlyOfType; it compiles there and is called as Evaluator.IsOnlyOfType.attributeListOf)
  hop 4 parser.HtmlTreeBuilder  739 lines  fillAttributeList    pass-through
  hop 5 nodes.Node              725 lines  addSlotAttributes    GOLD: one pass over the slots, adding each slot's attribute
Host newline counts 1464, 1254, 778, 739, 725; the smallest host (and the gold host) has 725 lines (C10F addendum section 1: hosts
under 1500 lines are expected in this regime).

Fault (one-line omission of a special-case step in the gold): the null-value rule is dropped from the gold's per-slot step
(`list.add(value == null ? new BooleanAttribute(keys[i]) : new Attribute(keys[i], value, owner));` becomes
`list.add(new Attribute(keys[i], value, owner));`), so a valueless slot of a list of two or more slots is added as a plain Attribute
with a null value. The gold then reads as the ordinary routine "add an attribute of each slot's key and value". Trigger: the EXISTING
test AttributeParseTest::parsesBooleanAttributes; its assertion assertTrue("'boolean' attribute should be boolean", attributes.get(1)
instanceof BooleanAttribute) fails (the parsed <a normal="123" boolean empty=""> has three slots, so its list is built by the gold).
It is the only test that observes the kind of an attribute in a list of two or more slots: testAddBooleanAttribute's one boolean slot
goes through hop 2's single-slot shortcut (unchanged), the other single-slot tests hold valued slots, and testByAttributeStarting reads
keys only (a plain Attribute keeps the key "attribute"); gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it adds "the attribute held in each" slot, in slot order) and is silent on boolean
attributes and on null values. In jsoup's attribute model the attribute held in a valueless slot is a boolean attribute (Attributes:
"we track boolean attributes as null in values"; BooleanAttribute: "A boolean attribute that is written out without any value"), so
the variant violates the contract on the trigger input (the "boolean" slot is listed as a plain valued Attribute). The convention is
pinned outside the gold: Attribute.isBooleanAttribute() (`... || val == null`), Attribute.shouldCollapseAttribute (a null value always
collapses) and Attributes.html (a null-valued slot is written as its key alone) treat a null value as a boolean attribute in
production; hop 2's single-slot shortcut makes the same decision for a single slot; passing tests: ElementTest::testAddBooleanAttribute
(through the chain: a single null-valued slot is listed as a BooleanAttribute), ElementTest::booleanAttributeOutput (a null-valued
attribute is written without a value), SelectorTest::testByAttributeStarting (through the gold: keys of a three-slot list including a
boolean attribute), TokeniserTest::handleSuperLargeAttributeName (through the chain: key and value of a valued slot).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: keys and values supply each attribute's key and value; count bounds the loop; owner is bound to every valued attribute;
     list receives every attribute.
  T2 absent: i is the loop cursor and advances; value is read by the ternary and the constructor; the ternary's two arms create
     different kinds of attribute; no local is frozen or dead.
  T3 absent: both members of the two-member set {null value, non-null value} are handled; key and value (a pair) are both used.
  T4 absent: "the attribute held in each of the first count slots", "in slot order" and the @param clauses are met by lines of the body;
     no inline comment; the name addSlotAttributes names nothing the body does not do.
 Variant gold (javadoc, signature, the loop, `String value = values[i];`, `list.add(new Attribute(keys[i], value, owner));`):
  T1 absent: keys, values, count, owner and list each change the result (key, value, bound, owner of every attribute, the list
     filled); none is only argument-checked.
  T2 absent: i advances; value reaches a constructor argument; there is no branch, case or ternary; nothing is frozen or dead.
  T3 absent: the gold has no special-value or kind treatment at all ('No member handled'); key and value (pair halves) are both
     passed; the gold's text names no class (no "boolean", no "valued") that it handles only in part.
  T4 absent: "the attribute held in each of the first count slots ... in slot order" is a general description that lines of the body
     address (one attribute per slot, in order, of the slot's key and value); the @param clauses are met; no inline comment;
     identifiers (keys, values, count, owner, list, value) name nothing the body does not meet.

Single owner: only the gold decides the kind of each attribute of a list of two or more slots; hops 1, 3 and 4 only wrap, create and
pass the list, and hop 2's shortcuts apply to no slot and to a single slot only. Once the gold has added a plain Attribute for the
"boolean" slot, a BooleanAttribute can appear at index 1 only if a caller rewrites the gold's output or replaces the gold. Declared
alternatives (G9): hop 3 sizes the list by the arrays' length; hop 4 bounds the count by the value array's length; hop 1 returns a
modifiable copy instead of a view. None makes the trigger pass.
Recorded bypasses (none is a one-line edit; Java 7 source level, no streams): B-0 hop 2 drops the count test of its single-slot
shortcut and builds every list with its own loop of the single-slot decision (a second implementation of the gold's per-slot step,
discarding hops 3-5); B-1 hop 1, 2 or 3 walks the gold's output and replaces each attribute whose value is null by a BooleanAttribute
of its key (rewrites the attributes the gold added).

Lie: the facade's javadoc claims the list is built on the first call and kept, and is built again only after an attribute is added or
removed; no step of the chain keeps a list between calls (every call creates a new one). It names neither boolean attributes nor null
values nor any hop."""

ATTRS = "src/main/java/org/jsoup/nodes/Attributes.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
NODE = "src/main/java/org/jsoup/nodes/Node.java"

GOLD_TEXT = '''/**
 * Adds the attribute held in each of the first {@code count} slots of a key and value array pair to a list, in slot
 * order.
 *
 * @param keys the attribute keys, by slot
 * @param values the attribute values, by slot
 * @param count the number of slots in use
 * @param owner the attributes that hold the slots
 * @param list the list to add the attributes to
 */
public static void addSlotAttributes(String[] keys, String[] values, int count, Attributes owner, List<Attribute> list) {
    for (int i = 0; i < count; i++) {
        String value = values[i];
        list.add(value == null ? new BooleanAttribute(keys[i]) : new Attribute(keys[i], value, owner));
    }
}'''

HOP1 = '''/**
 * Get the attributes held in the first {@code count} slots of a key and value array pair, as an unmodifiable list.
 *
 * @param keys the attribute keys, by slot
 * @param values the attribute values, by slot
 * @param count the number of slots in use
 * @param owner the attributes that hold the slots
 * @return an unmodifiable list of the attributes, in slot order
 */
public static List<Attribute> attributesView(String[] keys, String[] values, int count, Attributes owner) {
    return Collections.unmodifiableList(HttpConnection.attributesInSlots(keys, values, count, owner));
}'''

HOP2 = '''/**
 * Lists the attributes held in the first {@code count} slots of a key and value array pair, in slot order.
 * <p>
 * No slots give an empty list, and a single slot gives a singleton list of its attribute: a boolean attribute of its key if
 * the slot has no value, otherwise an attribute of its key and value bound to the owner. For more slots, a new list sized to
 * the slots is filled.
 * </p>
 *
 * @param keys the attribute keys, by slot
 * @param values the attribute values, by slot
 * @param count the number of slots in use
 * @param owner the attributes that hold the slots
 * @return the attributes, in slot order
 */
public static List<Attribute> attributesInSlots(String[] keys, String[] values, int count, Attributes owner) {
    if (count == 0)
        return Collections.emptyList();
    if (count == 1) {
        String only = values[0];
        return Collections.singletonList(only == null ? new BooleanAttribute(keys[0]) : new Attribute(keys[0], only, owner));
    }
    return Evaluator.IsOnlyOfType.attributeListOf(keys, values, count, owner);
}'''

HOP3 = '''/**
 * Creates a new list, sized to the slots, holding the attributes of the first {@code count} slots of a key and value
 * array pair, in slot order.
 *
 * @param keys the attribute keys, by slot
 * @param values the attribute values, by slot
 * @param count the number of slots in use
 * @param owner the attributes that hold the slots
 * @return the new list
 */
public static List<org.jsoup.nodes.Attribute> attributeListOf(String[] keys, String[] values, int count, Attributes owner) {
    List<org.jsoup.nodes.Attribute> list = new ArrayList<>(count);
    HtmlTreeBuilder.fillAttributeList(keys, values, count, owner, list);
    return list;
}'''

HOP4 = '''/**
 * Adds the attributes of the first {@code count} slots of a key and value array pair to a list, in slot order.
 *
 * @param keys the attribute keys, by slot
 * @param values the attribute values, by slot
 * @param count the number of slots in use
 * @param owner the attributes that hold the slots
 * @param list the list to add the attributes to
 */
public static void fillAttributeList(String[] keys, String[] values, int count, Attributes owner, List<Attribute> list) {
    Node.addSlotAttributes(keys, values, count, owner, list);
}'''

DESIGN = {
 "instance": "Jsoup-75", "project": "Jsoup", "bug_id": 75, "seed": 4794,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "batch": "batch9", "facade_variant": "V1+V2",
 "state_passed": "the fields keys (String[]), vals (String[]) and size (int), and the receiver this (Attributes, used only as the "
                 "owner the valued attributes are bound to; no method of it is called), passed to hop 1; no write-back",
 "host_mode": "largest5", "host_lines": [1464, 1254, 778, 739, 725],
 "reachability_probe": "asList() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Jsoup-75-probe; full suite: 5 failing tests, all with PROBE-REACHED: "
                       "ElementTest::testAddBooleanAttribute, AttributeParseTest::parsesBooleanAttributes, "
                       "ParserSettingsTest::attributesCaseNormalization, TokeniserTest::handleSuperLargeAttributeName, "
                       "SelectorTest::testByAttributeStarting",
 "facade": {"file": ATTRS, "class": "org.jsoup.nodes.Attributes", "method": "asList", "near_line": 275},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/parser/AttributeParseTest.java",
             "test_class": "org.jsoup.parser.AttributeParseTest", "test_method": "parsesBooleanAttributes"},
 "expected_signature": "'boolean' attribute should be boolean",
 "gold": {"method": "addSlotAttributes", "text": GOLD_TEXT,
          "fault": {"old": "            list.add(value == null ? new BooleanAttribute(keys[i]) : new Attribute(keys[i], value, owner));",
                    "new": "            list.add(new Attribute(keys[i], value, owner));"}},
 "chain": {
   "facade_body": "return Element.attributesView(keys, vals, size, this);",
   "lie": "The list is built on the first call and kept, and is built again only after an attribute is added or removed.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "attributesView",
      "imports": ["org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "attributesInSlots",
      "imports": ["org.jsoup.nodes.Attribute", "org.jsoup.nodes.Attributes", "org.jsoup.nodes.BooleanAttribute",
                  "org.jsoup.select.Evaluator"], "text": HOP2},
     {"file": EV, "class": "org.jsoup.select.Evaluator.IsOnlyOfType", "method": "attributeListOf",
      "imports": ["java.util.ArrayList", "org.jsoup.nodes.Attributes", "org.jsoup.parser.HtmlTreeBuilder"], "text": HOP3},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "fillAttributeList",
      "imports": ["org.jsoup.nodes.Attribute", "org.jsoup.nodes.Attributes"], "text": HOP4},
     {"file": NODE, "class": "org.jsoup.nodes.Node", "method": "addSlotAttributes", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.nodes.Attribute::isBooleanAttribute",
              "org.jsoup.nodes.Attribute::shouldCollapseAttribute",
              "org.jsoup.nodes.Attributes::html"],
 "ownership_reason": "Only the gold decides the kind of each attribute of a list of two or more slots: it adds the attribute held "
                     "in each slot, in slot order. Hops 1, 3 and 4 only wrap, create and pass the list; hop 2's shortcuts apply to "
                     "no slot and to a single slot only, so the three-slot list of the trigger is built entirely by the gold. Once "
                     "the gold has added a plain Attribute for the valueless 'boolean' slot, a BooleanAttribute can appear at index "
                     "1 only if a caller rewrites the gold's output or replaces the gold. In jsoup's attribute model the attribute "
                     "held in a valueless slot is a boolean attribute (Attributes tracks boolean attributes as null values; "
                     "BooleanAttribute is the attribute written without any value), so the variant breaks the gold's contract on "
                     "the trigger input. The convention is pinned outside the gold: Attribute.isBooleanAttribute() (a null value "
                     "makes a boolean attribute), Attribute.shouldCollapseAttribute (a null value always collapses) and "
                     "Attributes.html (a null-valued slot is written as its key alone), and hop 2's single-slot shortcut makes the "
                     "same decision; ElementTest::testAddBooleanAttribute (through the chain: a single null-valued slot is listed as "
                     "a BooleanAttribute), ElementTest::booleanAttributeOutput, SelectorTest::testByAttributeStarting (through the "
                     "gold) and TokeniserTest::handleSuperLargeAttributeName pass.",
 "ownership_tests": ["org.jsoup.nodes.ElementTest::testAddBooleanAttribute",
                     "org.jsoup.nodes.ElementTest::booleanAttributeOutput",
                     "org.jsoup.select.SelectorTest::testByAttributeStarting",
                     "org.jsoup.parser.TokeniserTest::handleSuperLargeAttributeName"],
 "compensating": {
   "chain": [
     {"file": EV, "old": "    List<org.jsoup.nodes.Attribute> list = new ArrayList<>(count);",
      "new": "    List<org.jsoup.nodes.Attribute> list = new ArrayList<>(keys.length);",
      "why": "hop 3 sizes the list by the arrays' length"},
     {"file": HTB, "old": "    Node.addSlotAttributes(keys, values, count, owner, list);",
      "new": "    Node.addSlotAttributes(keys, values, Math.min(count, values.length), owner, list);",
      "why": "hop 4 bounds the count by the value array's length"},
     {"file": EL, "old": "    return Collections.unmodifiableList(HttpConnection.attributesInSlots(keys, values, count, owner));",
      "new": "    return new ArrayList<>(HttpConnection.attributesInSlots(keys, values, count, owner));",
      "why": "hop 1 returns a modifiable copy instead of a view"},
   ],
 },
 "host_notes": "host_mode largest5 (batch9_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder; "
               "the facade's file Attributes.java is excluded): nodes.Element (hop 1, 1464 lines), helper.HttpConnection (hop 2, "
               "1254), select.Evaluator (hop 3, 778), parser.HtmlTreeBuilder (hop 4, 739), nodes.Node (hop 5, gold, 725; the "
               "smallest host). Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 4794 + 100 + i, "
               "as mr3_spec.py inserts them: hop 1 after Element.insertChildren (seed 4894), hop 2 after HttpConnection.data(Map) "
               "(4895), hop 3 after IsOnlyOfType.toString (4896; the anchor method belongs to the public static nested class "
               "Evaluator.IsOnlyOfType, whose header indentation mixes spaces and a tab, so the hop is inserted inside that nested "
               "class; it compiles there and hop 2 calls it as Evaluator.IsOnlyOfType.attributeListOf; inside it the simple name "
               "Attribute denotes the evaluator Evaluator.Attribute, so the hop names org.jsoup.nodes.Attribute in full), hop 4 "
               "after HtmlTreeBuilder.setFormElement (4897), hop 5 after Node.outerHtml() (4898). All five are public top-level classes "
               "(Node and Evaluator abstract) in which a public static method compiles.",
}
