"""Main run Jsoup-93__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Jsoup-93; the real bug modified FormElement, the facade's class). No static pair (BUILD_BRIEF_C10I_B8_NOTE section 1: pool v2 found
no tested static facade in FormElement).

Facade: FormElement.formData() (instance method; the only allowed candidate of batch8_tasks.json, BATCH8_PREREGISTRATION.md row 274;
facade_planned_by = Jsoup-42__i, so this is a recorded facade reuse: no candidate with facade_planned_by = null exists for this task).
Original computation: for each control of the private field elements (the form's associated controls, an Elements list), in order:
a control whose tag is not form-submittable or that has a disabled attribute is skipped; a control with an empty name is skipped; a
control whose type is "button" (any case) is skipped; a select adds one pair (name, option.val()) for each of its option[selected]
descendants, or, if there is none, for its first option (if any); a checkbox or radio button (type, any case) adds a pair only if it
has a checked attribute, with its val() or "on" if that is empty; any other control adds (name, val()). Element.val() is a
textarea's text and otherwise the value attribute. The pairs are returned in a new ArrayList.

facade_variant: V1 (state as parameters). state_passed: the private field elements (Elements) handed to hop 1; no field is written,
no write-back. The facade body is one call to hop 1 (the original has no argument guard; formData takes no argument). The chain needs
only public methods of the controls (Element.tag/attr/hasAttr/normalName/tagName/select/selectFirst/text, Tag.isFormSubmittable)
and public types (Elements, Connection.KeyVal, HttpConnection.KeyVal), so neither V2 (receiver), V3, V4 (no private method of
FormElement is called) nor V5 is needed. No visibility is widened, no type is added, no signature, modifier, override or throws
clause changes, no reflection, no test edit. The gold reads a control's value the way the public Element.val() does (a textarea's
text, otherwise the value attribute; an option is never a textarea, so its value attribute) instead of calling it, so that the value
of a control is part of the gold's per-control computation; Element.val() itself is unchanged and is the sibling pin below.

reachability_probe (C10I addendum section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-93-probe of the fixture, the first
statement of formData() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.jsoup.nodes.FormElementTest::createsFormData`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED
at org.jsoup.nodes.FormElement.formData(FormElement.java:79); FormElementTest::createsSubmitableConnection (through submit()) and
FormElementTest::usesOnForCheckboxValueIfNoValueSet also failed with PROBE-REACHED. The facade is reached directly by the trigger.

Hosts (host_mode = "largest5"; hosts_hop_order of batch8_tasks.json, used exactly in that order, none substituted):
  hop 1 nodes.Element             1524 lines  formPairs           aggregation: creates the new list, returns it
  hop 2 helper.HttpConnection     1205 lines  addFormPairs        pass-through
  hop 3 select.Evaluator           778 lines  gatherPairs         pass-through (the recipe's anchor places it in the public static
                                                                   nested class Evaluator.IsOnlyChild; see host_notes)
  hop 4 parser.HtmlTreeBuilder     741 lines  appendControlPairs  pass-through
  hop 5 nodes.Node                 725 lines  addSubmittedPairs   GOLD: one pass over the controls deciding, per control, whether it
                                                                   submits, and computing its value and the pairs it adds
Host newline counts 1524, 1205, 778, 741, 725; the smallest host (and the gold host) has 725 lines (C10F addendum section 1: hosts
under 1500 lines are expected in this regime). Every host is a public top-level class (Evaluator and Node are abstract) in which a
public static method compiles. The facade's class FormElement is excluded (facade_files_excluded).
The correct configuration computes exactly the original's pairs in the original order for every form (the same skips in the same
order, the select branch tested before the checkbox/radio branch, the same checked rule and "on" default, Element.val()'s value
rule).

Fault (one-line omission of a special-case step in the gold): the line
`if ("textarea".equals(control.tagName())) value = control.text();` is dropped, so a textarea's value is read from its (absent)
value attribute instead of its text. The gold then reads as the ordinary routine "skip the controls that are not submitted, add a
select's selected options, add every other control's value attribute ('on' for an empty checkbox or radio value)". Trigger: the
EXISTING test FormElementTest::createsFormData; the size and the first three pairs still hold, and
assertEquals("six=seven", data.get(3).toString()) fails with expected:<six=[seven]> but was:<six=[]>. It is the only test in which
formData (directly or through submit()) meets a textarea; gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it appends "the name/value pairs that form controls submit") and is silent on how
a control's value is read. A textarea submits its text as its value; the variant appends six= with an empty value, so the contract
is violated on the trigger input. The convention is pinned outside the gold by production code doing the same step: Element.val()
("if (tagName().equals("textarea")) return text(); else return attr("value");"), Element.val(String) (a textarea's value is set as
its text) and Elements.val() (the first matched element's val()), with the passing tests HtmlParserTest::handlesTextArea
(Elements.val() of a textarea is its text), HtmlParserTest::preservesSpaceInTextArea (Element.val() of a textarea is its text) and
ElementsTest::val (val() and val(String) of a textarea and an input), and through the chain by FormElementTest::adoptedFormsRetainInputs
and FormElementTest::usesOnForCheckboxValueIfNoValueSet (input values and the "on" default).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: controls supplies every control the loop reads; data receives every pair.
  T2 absent: control is the loop variable; name, type, options, first, defaultOn and value all reach a pair or a skip; no
     literal-initialised local; value is reassigned only by the textarea step and read by the add; every if/continue skips a
     control, changes a value or adds a pair (no dead branch); options grows only through add.
  T3 absent: checkbox and radio are both tested; a select's selected options and its first-option fallback are both handled; the
     skip conditions (tag not submittable, disabled, empty name, button) and the specially treated tags (select, textarea) are not a
     closed set fixed by the gold's text (no format is named); no class named in the gold's text is handled in part.
  T4 absent: 'the name/value pairs that form controls submit, in the order of the controls' is a general description that the body
     addresses; the @param clauses name nothing the body does not meet; no inline comment; identifiers (defaultOn, options, first,
     value) name what the body does.
 Variant gold (javadoc, signature, the loop without the textarea line):
  T1 absent: controls and data each change the output; neither is only argument-checked.
  T2 absent: value is initialised from control.attr("value") (not a literal) and read by the add; defaultOn decides both the
     checked skip and the "on" default; name, type, options, first reach pairs or skips; no frozen local (no cursor, counter, flag
     or best-so-far); the select/else branches, the checked skip and the ternary each have their own effect; no empty branch.
  T3 absent: the gold has no textarea or element-text treatment at all ('No member handled'); exactly one tag (select) gets its own
     branch and the gold names no closed set of tags or input types; checkbox and radio are both handled (checked skip and "on"
     default); selected options and the first-option fallback are both handled; options and controls both take the value
     attribute.
  T4 absent: 'name/value pairs that form controls submit' is a general description the body addresses (skips, select options,
     values); 'in the order of the controls' is met by the for-each loop; @param controls / @param data are met; identifiers
     (defaultOn: the "on" default is produced for checkbox and radio; value: the value attribute) name nothing the body does not
     meet; no inline comment.

Single owner: only the gold decides, for each control, whether it submits and computes the value of the pairs it adds; hop 1 creates
the list and returns it, hops 2-4 pass the controls on unchanged (their javadoc says so) and the list along. A caller cannot supply
a textarea's value: the gold reads it from the control itself, so a caller could change it only by writing an attribute into the
document (a side effect on the DOM, against "passed on unchanged" and the facade's "changes ... will not be reflected in the DOM"),
and once the gold has appended six= the text can come back only by rewriting the gold's pair from the control's text (a second
implementation of the gold's value rule). Leaving textareas out or filtering controls cannot make the trigger pass.
Declared alternatives (G9): hop 4 leaves out textareas; hop 3 keeps only the controls that have a name attribute; hop 2 leaves out
disabled controls. Each leaves the trigger failing.
Recorded bypasses (checked on the variant in scratch copies):
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.
 B-1 a hop (2, 3 or 4) first copies each textarea's text into a value attribute (`for (Element t : controls.select("textarea"))
     t.attr("value", t.text());`): it mutates the document, breaks that hop's documented rule that the controls are passed on
     unchanged, and re-implements the gold's value rule for textareas.

Lie: the facade's javadoc claims the form's controls are looked up afresh on each call, by a selector query over the form's
descendants; no step of the chain queries the form's descendants for its controls (the facade passes the stored elements list, which
also holds controls that are not descendants, as adoptedFormsRetainInputs exercises). It names neither a textarea nor a value rule
nor any hop."""

FE = "src/main/java/org/jsoup/nodes/FormElement.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
ND = "src/main/java/org/jsoup/nodes/Node.java"

GOLD_TEXT = '''/**
 * Appends to a list the name/value pairs that form controls submit, in the
 * order of the controls.
 *
 * @param controls the form controls
 * @param data the list to append the pairs to
 */
public static void addSubmittedPairs(Elements controls, List<Connection.KeyVal> data) {
    for (Element control : controls) {
        if (!control.tag().isFormSubmittable() || control.hasAttr("disabled")) continue;
        String name = control.attr("name");
        String type = control.attr("type");
        if (name.length() == 0 || type.equalsIgnoreCase("button")) continue;
        if ("select".equals(control.normalName())) {
            Elements options = control.select("option[selected]");
            if (options.isEmpty()) {
                Element first = control.selectFirst("option");
                if (first != null) options.add(first);
            }
            for (Element option : options)
                data.add(HttpConnection.KeyVal.create(name, option.attr("value")));
        } else {
            boolean defaultOn = "checkbox".equalsIgnoreCase(type) || "radio".equalsIgnoreCase(type);
            if (defaultOn && !control.hasAttr("checked")) continue;
            String value = control.attr("value");
            if ("textarea".equals(control.tagName())) value = control.text();
            data.add(HttpConnection.KeyVal.create(name, defaultOn && value.length() == 0 ? "on" : value));
        }
    }
}'''

HOP1 = '''/**
 * Get the name/value pairs that a set of form controls submit, as a new list. The controls are passed on unchanged, and
 * the pairs are listed in the order of the controls.
 * @param controls the form controls
 * @return a new list of the pairs the controls submit
 */
public static List<Connection.KeyVal> formPairs(Elements controls) {
    List<Connection.KeyVal> data = new ArrayList<>();
    HttpConnection.addFormPairs(controls, data);
    return data;
}'''

HOP2 = '''/**
 * Add the name/value pairs that a set of form controls submit to a list of request data. The controls are passed on
 * unchanged, in order.
 * @param controls the form controls
 * @param data the request data to add the pairs to
 */
public static void addFormPairs(Elements controls, List<Connection.KeyVal> data) {
    Evaluator.IsOnlyChild.gatherPairs(controls, data);
}'''

HOP3 = '''/**
 * Gathers the name/value pairs that a set of form controls submit into a list. The controls are passed on unchanged, in
 * order.
 * @param controls the form controls
 * @param data the list to gather the pairs into
 */
public static void gatherPairs(Elements controls, List<Connection.KeyVal> data) {
    HtmlTreeBuilder.appendControlPairs(controls, data);
}'''

HOP4 = '''/**
 * Appends the name/value pairs that a set of form controls submit to a list. The controls are passed on unchanged, in
 * order.
 * @param controls the form controls
 * @param data the list to append the pairs to
 */
public static void appendControlPairs(Elements controls, List<Connection.KeyVal> data) {
    Node.addSubmittedPairs(controls, data);
}'''

DESIGN = {
 "instance": "Jsoup-93", "project": "Jsoup", "bug_id": 93, "seed": 6202,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private field elements (Elements, the form's associated controls), passed to hop 1; no write-back",
 "host_mode": "largest5", "host_lines": [1524, 1205, 778, 741, 725],
 "facade_reuse_of": ["Jsoup-42__i"],
 "reachability_probe": "formData() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Jsoup-93-probe: FormElementTest::createsFormData fails with PROBE-REACHED at "
                       "org.jsoup.nodes.FormElement.formData(FormElement.java:79) (also createsSubmitableConnection and "
                       "usesOnForCheckboxValueIfNoValueSet)",
 "facade": {"file": FE, "class": "org.jsoup.nodes.FormElement", "method": "formData", "near_line": 78},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/nodes/FormElementTest.java",
             "test_class": "org.jsoup.nodes.FormElementTest", "test_method": "createsFormData"},
 "expected_signature": "expected:<six=[seven]> but was:<six=[]>",
 "gold": {"method": "addSubmittedPairs", "text": GOLD_TEXT,
          "fault": {"old": "                String value = control.attr(\"value\");\n"
                           "                if (\"textarea\".equals(control.tagName())) value = control.text();\n"
                           "                data.add(HttpConnection.KeyVal.create(name, defaultOn && value.length() == 0 ? \"on\" : value));",
                    "new": "                String value = control.attr(\"value\");\n"
                           "                data.add(HttpConnection.KeyVal.create(name, defaultOn && value.length() == 0 ? \"on\" : value));"}},
 "chain": {
   "facade_body": "return Element.formPairs(elements);",
   "lie": "The form's controls are looked up afresh on each call, by a selector query over the descendants of this form.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "formPairs",
      "imports": ["org.jsoup.Connection", "org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "addFormPairs",
      "imports": ["org.jsoup.select.Elements", "org.jsoup.select.Evaluator"], "text": HOP2},
     {"file": EV, "class": "org.jsoup.select.Evaluator$IsOnlyChild", "method": "gatherPairs",
      "imports": ["org.jsoup.Connection", "org.jsoup.parser.HtmlTreeBuilder"], "text": HOP3},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "appendControlPairs",
      "imports": ["org.jsoup.Connection"], "text": HOP4},
     {"file": ND, "class": "org.jsoup.nodes.Node", "method": "addSubmittedPairs",
      "imports": ["org.jsoup.Connection", "org.jsoup.helper.HttpConnection", "org.jsoup.select.Elements"], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.nodes.Element::val",
              "org.jsoup.select.Elements::val",
              "org.jsoup.nodes.FormElement::submit"],
 "ownership_reason": "Only the gold decides, for each form control, whether it submits and computes the value of the pairs it adds "
                     "(the value attribute, a textarea's text, 'on' for a checked checkbox or radio button without a value, a "
                     "select's selected options). Hop 1 creates the list and returns it; hops 2-4 pass the controls on unchanged, as "
                     "their javadoc says, and the list along. A caller cannot supply a textarea's value, which the gold reads from "
                     "the control itself, except by writing an attribute into the document (a side effect against the hops' and the "
                     "facade's documentation); once the gold has appended six= with an empty value, the text can come back only if a "
                     "caller rewrites the gold's pair from the control's text, a second implementation of the gold's value rule. The "
                     "gold's javadoc promises the pairs that the controls submit; a textarea submits its text. The convention is "
                     "pinned outside the gold by production code doing the same step: Element.val() (a textarea's value is its "
                     "text, otherwise the value attribute), Element.val(String) and Elements.val(), with the passing tests "
                     "HtmlParserTest::handlesTextArea, HtmlParserTest::preservesSpaceInTextArea and ElementsTest::val, and through "
                     "the chain FormElementTest::adoptedFormsRetainInputs and FormElementTest::usesOnForCheckboxValueIfNoValueSet.",
 "ownership_tests": ["org.jsoup.parser.HtmlParserTest::handlesTextArea",
                     "org.jsoup.parser.HtmlParserTest::preservesSpaceInTextArea",
                     "org.jsoup.select.ElementsTest::val",
                     "org.jsoup.nodes.FormElementTest::adoptedFormsRetainInputs",
                     "org.jsoup.nodes.FormElementTest::usesOnForCheckboxValueIfNoValueSet"],
 "compensating": {
   "chain": [
     {"file": HTB, "old": "Node.addSubmittedPairs(controls, data);",
      "new": "Node.addSubmittedPairs(controls.not(\"textarea\"), data);",
      "why": "hop 4 leaves out the textareas"},
     {"file": EV, "old": "HtmlTreeBuilder.appendControlPairs(controls, data);",
      "new": "HtmlTreeBuilder.appendControlPairs(controls.select(\"[name]\"), data);",
      "why": "hop 3 keeps only the controls that have a name attribute"},
     {"file": HC, "old": "Evaluator.IsOnlyChild.gatherPairs(controls, data);",
      "new": "Evaluator.IsOnlyChild.gatherPairs(controls.not(\"[disabled]\"), data);",
      "why": "hop 2 leaves out the disabled controls"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, used in that order; none substituted, none drawn by this "
               "builder): nodes.Element (hop 1, 1524 lines), helper.HttpConnection (hop 2, 1205), select.Evaluator (hop 3, 778; "
               "public abstract class), parser.HtmlTreeBuilder (hop 4, 741), nodes.Node (hop 5, gold, 725; public abstract class; "
               "the smallest host). All five are public top-level classes in which a public static method compiles; the facade's "
               "class FormElement is excluded. Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed "
               "6202 + 100 + i, as mr3_spec.py inserts them: hop 1 after child (seed 6302), hop 2 after parser (6303), hop 3 after "
               "toString (6304): the drawn anchor is the toString of the public static final nested class Evaluator.IsOnlyChild, "
               "whose members are indented with four spaces and a tab, so the anchor picker's four-space outer-member filter admits "
               "it and the hop lands inside IsOnlyChild (a static method compiles there; the hop is recorded as class "
               "org.jsoup.select.Evaluator$IsOnlyChild, the harness catalog's binary name, and hop 2 calls it as "
               "Evaluator.IsOnlyChild.gatherPairs); Evaluator was kept as the host because it can carry a public static method, "
               "so the substitution rule does not apply; hop 4 after insertMarkerToFormattingElements (6305), hop 5 after hasAttr "
               "(6306). The facade calls hop 1 as "
               "Element.formPairs (FormElement's superclass, same package); each hop imports the next host and org.jsoup.Connection "
               "/ org.jsoup.select.Elements as needed; the gold imports org.jsoup.helper.HttpConnection. Hop 3 names no nested "
               "Evaluator type (Tag, Attribute, Class).",
}
