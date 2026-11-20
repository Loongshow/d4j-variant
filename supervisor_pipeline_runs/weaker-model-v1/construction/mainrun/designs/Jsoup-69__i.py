"""Main run Jsoup-69__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug with no static facade; the
fixed checkout of Defects4J Jsoup-69, whose real bug modified org.jsoup.nodes.FormElement, the facade's class). No static pair
(BUILD_BRIEF_C10I_B8_NOTE section 1).

Facade: FormElement.formData() (the only allowed instance target of BATCH8_PREREGISTRATION.md row 271; facade_planned_by
Jsoup-42__i, so this is a recorded facade reuse: no allowed candidate with facade_planned_by = null exists for this task).
Original computation: a new ArrayList of Connection.KeyVal; for each element of the private field `elements` (the form's associated
controls, in the order they were added): a control whose tag is not form-submittable, or that has the 'disabled' attribute, or whose
'name' attribute is empty, is skipped; a select box adds one pair (name, option.val()) for each 'option[selected]' descendant, or, if
there is none, for its first 'option' (if any); a checkbox or radio (type compared ignoring case) adds a pair only if it has the
'checked' attribute, with its val(), or "on" if that is empty; any other control adds (name, el.val()), where Element.val() is the
element's text for a textarea and its 'value' attribute otherwise. The list is returned.

facade_variant: V1 (state as parameters). state_passed: the private field `elements` (org.jsoup.select.Elements, a public type) is
read inside FormElement and handed to hop 1; no field is written, no write-back. The facade body is one call to hop 1 (the original has
no argument guard). The computation calls no private method of FormElement (V4 not needed), needs no method of the receiver (V2 not
needed) and no package-private type (V3/V5 not needed): every member the chain uses (Element.tag(), Tag.isFormSubmittable(),
Element.attr/hasAttr/tagName/text/select/selectFirst, HttpConnection.KeyVal.create) is public. No visibility is widened, no type is
added, no signature, modifier, override or throws clause changes, no reflection, no test edit.

reachability_probe (C10I addendum section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-69-probe of the fixture, the first
statement of formData() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.jsoup.nodes.FormElementTest::createsFormData`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED
at org.jsoup.nodes.FormElement.formData(FormElement.java:79), called from FormElementTest.createsFormData(FormElementTest.java:36).
Full suite with the probe: 7 failing tests, all in FormElementTest (createsFormData, actionWithNoValue, removeFormElement,
createsSubmitableConnection, controlsAddedAfterParseAreLinkedWithForms, adoptedFormsRetainInputs, usesOnForCheckboxValueIfNoValueSet;
the last four through submit() or formData()). The facade is reached directly by the trigger.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 nodes.Element          1430 lines  formControlData     aggregation: creates the new list, returns it
  hop 2 helper.HttpConnection  1249 lines  addFormData         fold: each control of the list, in order
  hop 3 select.Evaluator        753 lines  addControlData      (in Evaluator.IsRoot, see below) filter: skips a control whose tag is not form-submittable, a disabled
                                                               control and a control without a name; reads the name
  hop 4 parser.HtmlTreeBuilder  734 lines  appendControlValues pass-through
  hop 5 nodes.Node              725 lines  addSubmittedValues  GOLD: the per-control core, the pairs one named control submits
                                                               (select options, checkable controls, the value of any other control)
Host newline counts 1430, 1249, 753, 734, 725; the smallest host (and the gold host) is Node with 725 lines (C10F addendum section 1:
hosts under 1500 lines are expected in this regime). All five are public top-level classes (Evaluator and Node are abstract) in which a
public static method compiles; the facade's class FormElement is excluded. Evaluator's own top level has no method with a body
besides its constructor (its methods all belong to its public static nested evaluators, indented with tabs, which the anchor picker's
four-space test counts as outer members), so the seeded anchor (seed 2563: after matches at line 581) lies inside the public static
nested class Evaluator.IsRoot; the hop is kept there, at the recipe's anchor in the listed host file, and hop 2 calls it as
Evaluator.IsRoot.addControlData. No host was substituted.
The correct configuration returns the original list for every form: the filter and its order are the original's; the select branch
uses option.attr("value"), which is option.val() for an option; the value of any other control is its text for a textarea and its
'value' attribute otherwise, which is Element.val().

Fault (one-line omission of a special-case step in the gold): the textarea case of the value is dropped from the gold
(`String value = "textarea".equals(control.tagName()) ? control.text() : control.attr("value");` becomes
`String value = control.attr("value");`), so a textarea submits its (absent) 'value' attribute, the empty string, instead of its
text. The gold then reads as the ordinary routine "each control submits its value attribute; select boxes submit their options'
values; checkable controls only when checked". Trigger: the EXISTING test FormElementTest::createsFormData. Its first four assertions
hold (6 pairs; one=two; three=four; three=five) and assertEquals("six=seven", data.get(3).toString()) fails with
expected:<six=[seven]> but was:<six=[]>. It is the only test that submits a textarea through a form: no other formData() / submit()
test has a textarea (the probe's full-suite run lists every test that reaches the facade), and the new hops have no other caller.

The gold's javadoc states the idiomatic contract (any control other than a select box or a checkable control "submits one with its
value") and is silent on textareas. The value of a textarea is its text: the convention is pinned outside the gold by
Element.val() ("Get the value of a form element (input, textarea, etc)": the text for a textarea, the 'value' attribute otherwise),
by its setter Element.val(String) (writes a textarea's text) and by Elements.val(); passing tests: ElementsTest::val
("two" for <textarea>two</textarea>, and val("three") writes <textarea>three</textarea>), and through the chain
FormElementTest::usesOnForCheckboxValueIfNoValueSet, ::adoptedFormsRetainInputs, ::controlsAddedAfterParseAreLinkedWithForms and
::removeFormElement.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: control supplies the tag name, options, value, type and checked state; name is the key of every pair; data receives
     every pair.
  T2 absent: options is read by the loop; first is added when present; value is read by both add calls; type decides the checkable
     branch; every branch and the "on" ternary have different effects; no frozen local (no cursor, counter or flag).
  T3 absent: checkbox and radio get the same treatment; the selected options and the first-option fallback are both handled; the
     select box and the textarea are the two tag names treated, in an unnamed open set (the gold names no list of control kinds and
     handles "any other control"); no class named in the gold's text is handled in part.
  T4 absent: 'one for each of its selected options, or for its first option if none is selected', 'only if it is checked, with the
     value "on" if it has no value of its own' and 'Any other control submits one with its value' are each met by lines of the body.
 Variant gold (javadoc, signature, the select branch, `String value = control.attr("value");`, the checkable/other branches):
  T1 absent: control, name and data each change the result; none is only argument-checked.
  T2 absent: options, first, value and type all reach add calls or decisions; the select/other, checkable/other and checked decisions
     and the ternary have different effects; no local is frozen or dead.
  T3 absent: checkbox and radio are both treated; selected options and the first-option fallback are both treated; the only tag name
     tested is "select" (one member of an unnamed set of tag names; the gold names no class of control kinds that it handles only in
     part, and every control gets a treatment); the gold has no textarea treatment at all.
  T4 absent: 'Any other control submits one with its value' is a general description met by the add of (name, value); the select and
     checkable sentences are met; no inline comment; identifiers (options, first, option, value, type) name nothing the body does not
     meet; the @param clauses are caller descriptions.

Single owner: only the gold reads a control's value; hops 1, 2 and 4 pass the controls and the list along, and hop 3 only decides
whether a control takes part and reads its name. Once the gold has added (six, "") for the textarea, "six=seven" can appear only if a
caller rewrites the gold's output, mutates the control, or replaces the gold. Declared alternatives (G9): hop 3 lets every
non-disabled control through (no submittable test); hop 4 submits under the trimmed name; hop 2 also visits each control's
descendants. None makes the trigger pass.
Recorded bypasses (edits that replace or rewrite the gold's result, not repairs of the chain):
 B-0 the facade's original body (or any hop calling control.val() and adding the pairs itself) re-implements the per-control
     computation and makes the chain, including the gold, dead.
 B-1 hop 3 or hop 4 adds the textarea's pair itself and returns before the gold
     (`if ("textarea".equals(control.tagName())) { data.add(HttpConnection.KeyVal.create(name, control.text())); return; }`): a second
     implementation of the gold's per-control decision for one tag, against hop 3's / hop 4's documented hand-off of every named
     submittable control to the next step.
 B-2 hop 3 or hop 4 copies the textarea's text into a 'value' attribute of the element before the gold reads it
     (`if ("textarea".equals(control.tagName())) control.attr("value", control.text());`): it mutates the DOM, which the facade's
     javadoc says the form data does not affect.
 B-1 and B-2 were checked at hop 4 on the variant in scratch copies (/private/tmp/d4j-mi-Jsoup-69-B1, -B2): trigger passes, full
 suite 0 failing tests. Both are recorded bypasses, not repairs of the chain.

Lie: the facade's javadoc claims the form's descendant elements are walked in document order and each form control found is added in
turn; no step of the chain walks the form's subtree (the chain iterates the form's list of associated controls, which may lie
outside the form element, as FormElementTest::adoptedFormsRetainInputs shows). It names neither textareas nor values nor any hop."""

FE = "src/main/java/org/jsoup/nodes/FormElement.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
ND = "src/main/java/org/jsoup/nodes/Node.java"

GOLD_TEXT = '''/**
 * Add the key vals that a named form control submits to a list. A select box submits one for each of its selected
 * options, or for its first option if none is selected. A checkbox or radio button submits one only if it is checked,
 * with the value "on" if it has no value of its own. Any other control submits one with its value.
 * @param control the form control
 * @param name the name to submit the control's values under
 * @param data the list to add to
 */
public static void addSubmittedValues(Element control, String name, List<Connection.KeyVal> data) {
    if ("select".equals(control.tagName())) {
        Elements options = control.select("option[selected]");
        if (options.isEmpty()) {
            Element first = control.selectFirst("option");
            if (first != null)
                options.add(first);
        }
        for (Element option : options)
            data.add(HttpConnection.KeyVal.create(name, option.attr("value")));
        return;
    }
    String value = "textarea".equals(control.tagName()) ? control.text() : control.attr("value");
    String type = control.attr("type");
    if ("checkbox".equalsIgnoreCase(type) || "radio".equalsIgnoreCase(type)) {
        if (control.hasAttr("checked"))
            data.add(HttpConnection.KeyVal.create(name, value.length() > 0 ? value : "on"));
    } else {
        data.add(HttpConnection.KeyVal.create(name, value));
    }
}'''

HOP1 = '''/**
 * Get the data that a list of form controls submits.
 * @param controls the form controls, in the order their data is listed
 * @return a new list of the key vals of the controls
 */
public static List<Connection.KeyVal> formControlData(Elements controls) {
    List<Connection.KeyVal> data = new ArrayList<>();
    HttpConnection.addFormData(controls, data);
    return data;
}'''

HOP2 = '''/**
 * Add the data of each form control in a list to a list of key vals, in the order of the controls.
 * @param controls the form controls
 * @param data the list to add to
 */
public static void addFormData(Elements controls, List<Connection.KeyVal> data) {
    for (Element control : controls) {
        Evaluator.IsRoot.addControlData(control, data);
    }
}'''

HOP3 = '''/**
 * Add the data that a form control submits to a list of key vals. A control is skipped if its tag is not submittable
 * with a form, if it is disabled, or if it has no name; any other control is passed on with its name.
 * @param control the form control
 * @param data the list to add to
 */
public static void addControlData(Element control, List<Connection.KeyVal> data) {
    if (!control.tag().isFormSubmittable() || control.hasAttr("disabled")) return;
    String name = control.attr("name");
    if (name.length() == 0) return;
    HtmlTreeBuilder.appendControlValues(control, name, data);
}'''

HOP4 = '''/**
 * Append the values that a named form control submits to a list of key vals.
 * @param control the form control
 * @param name the name to submit the values under
 * @param data the list to append to
 */
public static void appendControlValues(Element control, String name, List<Connection.KeyVal> data) {
    Node.addSubmittedValues(control, name, data);
}'''

DESIGN = {
 "instance": "Jsoup-69", "project": "Jsoup", "bug_id": 69, "seed": 2461,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private field elements (org.jsoup.select.Elements) passed to hop 1; no field written, no write-back",
 "host_mode": "largest5", "host_lines": [1430, 1249, 753, 734, 725],
 "reachability_probe": "formData() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Jsoup-69-probe: FormElementTest::createsFormData fails with PROBE-REACHED at "
                       "FormElement.formData(FormElement.java:79); full suite with the probe: 7 failing tests, all FormElementTest",
 "facade": {"file": FE, "class": "org.jsoup.nodes.FormElement", "method": "formData", "near_line": 78},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/nodes/FormElementTest.java",
             "test_class": "org.jsoup.nodes.FormElementTest", "test_method": "createsFormData"},
 "expected_signature": "expected:<six=[seven]> but was:<six=[]>",
 "gold": {"method": "addSubmittedValues", "text": GOLD_TEXT,
          "fault": {"old": "        String value = \"textarea\".equals(control.tagName()) ? control.text() : control.attr(\"value\");",
                    "new": "        String value = control.attr(\"value\");"}},
 "chain": {
   "facade_body": "return Element.formControlData(elements);",
   "lie": "The form's descendant elements are walked in document order, and each form control found is added in turn.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "formControlData",
      "imports": ["org.jsoup.Connection", "org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "addFormData",
      "imports": ["org.jsoup.nodes.Element", "org.jsoup.select.Elements", "org.jsoup.select.Evaluator"], "text": HOP2},
     {"file": EV, "class": "org.jsoup.select.Evaluator.IsRoot", "method": "addControlData",
      "imports": ["org.jsoup.Connection", "org.jsoup.parser.HtmlTreeBuilder"], "text": HOP3},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "appendControlValues",
      "imports": ["org.jsoup.Connection"], "text": HOP4},
     {"file": ND, "class": "org.jsoup.nodes.Node", "method": "addSubmittedValues",
      "imports": ["org.jsoup.Connection", "org.jsoup.helper.HttpConnection", "org.jsoup.select.Elements"], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.nodes.Element::val", "org.jsoup.select.Elements::val"],
 "ownership_reason": "Only the gold reads a control's value and decides the pairs a named control submits: hops 1, 2 and 4 pass the "
                     "controls and the list along, and hop 3 only decides whether a control takes part (form-submittable tag, not "
                     "disabled, a non-empty name) and reads its name. Once the gold has added (six, \"\") for the textarea, "
                     "'six=seven' can appear only if a caller rewrites the gold's output, mutates the control, or replaces the gold. "
                     "The gold's javadoc promises that any control other than a select box or a checkable control submits one pair "
                     "with its value; the value of a textarea is its text, which the variant drops. The convention is pinned "
                     "outside the gold: Element.val() ('Get the value of a form element (input, textarea, etc)': the text for a "
                     "textarea, the 'value' attribute otherwise), its setter Element.val(String) and Elements.val(); "
                     "ElementsTest::val passes (\"two\" for <textarea>two</textarea>), as do the chain's other form tests "
                     "(usesOnForCheckboxValueIfNoValueSet, adoptedFormsRetainInputs, controlsAddedAfterParseAreLinkedWithForms, "
                     "removeFormElement).",
 "ownership_tests": ["org.jsoup.select.ElementsTest::val",
                     "org.jsoup.nodes.FormElementTest::usesOnForCheckboxValueIfNoValueSet",
                     "org.jsoup.nodes.FormElementTest::adoptedFormsRetainInputs",
                     "org.jsoup.nodes.FormElementTest::controlsAddedAfterParseAreLinkedWithForms"],
 "compensating": {
   "chain": [
     {"file": EV, "old": "if (!control.tag().isFormSubmittable() || control.hasAttr(\"disabled\")) return;",
      "new": "if (control.hasAttr(\"disabled\")) return;",
      "why": "hop 3 lets every non-disabled control through"},
     {"file": HTB, "old": "Node.addSubmittedValues(control, name, data);",
      "new": "Node.addSubmittedValues(control, name.trim(), data);",
      "why": "hop 4 submits under the trimmed name"},
     {"file": HC, "old": "    for (Element control : controls) {\n            Evaluator.IsRoot.addControlData(control, data);",
      "new": "    for (Element control : controls.select(\"*\")) {\n            Evaluator.IsRoot.addControlData(control, data);",
      "why": "hop 2 also visits each control's descendants"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this "
               "builder): nodes.Element (hop 1, 1430 lines), helper.HttpConnection (hop 2, 1249), select.Evaluator (hop 3, 753; "
               "abstract), parser.HtmlTreeBuilder (hop 4, 734), nodes.Node (hop 5, gold, 725; abstract; the smallest host). All five "
               "are public top-level classes in which a public static method compiles; the facade's class FormElement is excluded. "
               "Anchors from stageB_lib.pick_insertion_anchor with seed 2461 + 100 + i, as mr3_spec.py inserts them: hop 1 after "
               "Element.textNodes (seed 2561), hop 2 after an HttpConnection.data overload (2562), hop 3 after "
               "Evaluator.IsRoot.matches (2563; inside the public static nested class IsRoot, because Evaluator's top level has "
               "no method with a body besides its constructor, so the hop's class is org.jsoup.select.Evaluator.IsRoot and hop 2 "
               "calls Evaluator.IsRoot.addControlData; the listed host file is kept, not substituted), hop 4 after "
               "HtmlTreeBuilder.maybeSetBaseUri (2564), hop 5 after Node.setBaseUri (2565). The "
               "facade calls hop 1 by its simple name (same package); each hop imports the next host and org.jsoup.Connection as "
               "needed. Hop 2 names Connection.KeyVal explicitly (HttpConnection has its own nested KeyVal); hop 3 names no type "
               "Evaluator nests (it does not name Tag or Attribute).",
}
