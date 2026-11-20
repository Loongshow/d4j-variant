"""Main run Jsoup-42__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug without a static facade; the
fixed checkout of Defects4J Jsoup-42, whose real bug modified org.jsoup.nodes.FormElement, the facade's class). No static pair (B8
note section 1).

Facade: FormElement.formData() (the only allowed candidate of batch8_tasks.json / BATCH8_PREREGISTRATION.md row 265;
facade_planned_by null, no facade reuse). Original computation: for each control of the private field `elements` (the form's
associated controls, in the order they were added), skip a control whose tag is not form-submittable, a control with a `disabled`
attribute and a control with an empty `name`; a select submits one pair per `option[selected]` (option.val()), or its first option when
none is selected (nothing when it has no option); a checkbox or radio (type compared case-insensitively) submits only when it has the
`checked` attribute, with its val() or "on" when that is empty; any other control submits el.val(). Element.val() is the text of a
textarea and the `value` attribute of any other element. The pairs are HttpConnection.KeyVal objects in a new ArrayList.

facade_variant: V1 (state as parameters). state_passed: the private field `elements` (the Elements list of associated controls) is
read inside FormElement and handed to hop 1; no field is written, no write-back. The facade body is one delegating call (the original
has no argument guard). The chain needs only public methods of the controls (Element.tag/tagName/attr/hasAttr/select/text,
Tag.isFormSubmittable, HttpConnection.KeyVal.create), so V2 is not needed; formData calls no private method (no V4) and no
package-private type is involved (no V3/V5). No visibility widened, no type added, no signature/modifier/override/throws change, no
reflection, no test edit.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-42-probe/w of the fixture, the first statement
of formData() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; full suite
(`defects4j test`): 5 failing tests, each with java.lang.IllegalStateException: PROBE-REACHED at FormElement.formData(FormElement.java:75):
FormElementTest::createsFormData (direct call, FormElementTest.java:36), ::controlsAddedAfterParseAreLinkedWithForms (direct, :114),
::usesOnForCheckboxValueIfNoValueSet (direct, :121), ::createsSubmitableConnection and ::actionWithNoValue (both through
FormElement.submit, FormElement.java:63). The facade is reached by the trigger directly.

Hosts (host_mode = "largest5"; hosts_hop_order of the task record, used in that order, none substituted):
  hop 1 nodes.Element                 1189 lines  formDataOf          aggregation: a new list, filled by hop 2, returned
  hop 2 helper.HttpConnection          912 lines  appendFormData      the fold: every control, in order, to hop 3
  hop 3 select.Evaluator (IsOnlyChild) 706 lines  addIfSubmittable    decision: only submittable, enabled controls go on
  hop 4 nodes.Node                     687 lines  addNamedFormData    decision: the name attribute; an unnamed control adds nothing
  hop 5 safety.Whitelist               635 lines  addControlValues    GOLD: the per-control core - the control's value (the text of a
                                                                      textarea, else the value attribute) and the pairs it submits by
                                                                      kind (select options, checked checkbox/radio with the "on"
                                                                      default, any other control)
Host newline counts 1189, 912, 706, 687, 635; the smallest host is Whitelist (635 lines, the gold's host). Anchors are the recipe's
(stageB_lib.pick_insertion_anchor through insert_hop, seed 8055 + 100 + i): see host_notes. The recipe's anchor in Evaluator.java
(after `toString`, seed 8157) is the toString of the public static nested class Evaluator.IsOnlyChild (its members are indented with
four spaces and a tab, which the picker reads as an outer-class indent), so hop 3 is a public static method of the existing class
Evaluator.IsOnlyChild and hop 2 calls it by that qualified name. The host file is not substituted: it carries a public static method.

The correct configuration returns exactly the original list for every form: hops 2-4 apply the original's three skips in the
original's order (the submittable and disabled skips at hop 3, the empty-name skip at hop 4) and the gold reproduces the per-control
branches, with option.val() and el.val() written as Element.val() computes them (option is never a textarea; the textarea rule is the
gold's value line).

Fault (one-line omission of a special-case step in the gold): the line that takes a textarea's text as its value
(`if ("textarea".equals(control.tagName())) value = control.text();`) is dropped, so a textarea submits its (absent) value attribute,
the empty String. The gold then reads as the ordinary routine "read the control's value; a select submits its options, a checked
checkbox or radio its value or "on", any other control its value". Trigger: the EXISTING test FormElementTest::createsFormData. Its
size check (6 pairs) and the first three pairs still hold, and assertEquals("six=seven", data.get(3).toString()) for
<textarea name=six>seven</textarea> fails with expected:<six=[seven]> but was:<six=[]>. It is the only test that newly fails: of the
five tests that reach formData (the probe), only createsFormData has a textarea; the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the pairs a control submits; "any other control submits its value") and is silent on
textareas. The convention that a textarea's value is its text is pinned outside the gold by production code doing the same step:
Element.val() ("Get the value of a form element (input, textarea, etc)": the text of a textarea, else the value attribute) and
Element.val(String) (sets a textarea's text), and Elements.val() (the first element's val()), with the passing tests
HtmlParserTest::handlesTextArea (doc.select("textarea").val() is "Hello") and HtmlParserTest::preservesSpaceInTextArea (a textarea's
val() is its text). The facade's own javadoc ("the data that this form submits") is kept unchanged except for the lie.

Single owner: only the gold reads a control's value; hops 1-4 hand the whole control along and never see a value, and the pairs leave
the gold as KeyVal(name, value) without the control, so no caller can recover the textarea's text from them, and no filtering of the
controls above the gold can add the missing text. Declared alternatives (G9): hop 3 lets every form-listed control through
(isFormListed); hop 4 falls back to the id when the name is absent; hop 2 re-selects the controls by tag (input, select, textarea).
Each leaves the trigger failing.
Recorded bypasses (not repairs of the chain):
 B-1 a second implementation of the gold's textarea case at hop 4 (or hop 3):
     `if ("textarea".equals(control.tagName())) { data.add(org.jsoup.helper.HttpConnection.KeyVal.create(name, control.text())); return; }`
     before the call to the gold: the textarea's pair is produced without the gold, whose output for that control is never computed.
 B-2 a DOM write at hop 4 (or hop 3) before the call: `if ("textarea".equals(control.tagName())) control.attr("value", control.text());`
     rewrites the document (every textarea it sees gains a value attribute and is serialised with it), a side effect of reading a
     form's data that contradicts the documentation of every hop it could sit in (hops 1-4 each state that the controls are not
     modified); it feeds the gold a second implementation of the textarea's value through the DOM, and the gold still reads the
     textarea's value attribute against Element.val(). Both B-1 and B-2 were checked on the variant in scratch copies: trigger passes,
     full suite 0 failing tests.
 B-0 the facade's original body (re-implementing the whole computation) makes the chain, including the gold, dead.

Lie: the facade's javadoc claims the data is gathered by a depth-first traversal of the form's descendant nodes, visiting each control
in document order; the chain traverses nothing - it iterates the form's associated-controls list (which may hold controls that are not
descendants of the form). It names neither values, textareas, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: control is read for its type, value, tag name, options and checked attribute; name keys every pair; data receives every
     pair; no argument check.
  T2 absent: type decides the checkbox/radio branch; value is reassigned by the textarea decision and submitted in two branches;
     options is iterated; first is read by the decision and added; no literal-initialised local, no cursor/counter/flag/best-so-far
     (for-each loop only); every decision changes what is added.
  T3 absent: the textarea rule is a value rule for one tag and select is a branch for another tag of an unnamed, larger set of tags (not
     T3); checkbox and radio (the pair) are both handled; selected options and the first-option fallback are both handled.
  T4 absent: each javadoc clause (select options or first option, checkbox/radio value or "on" and only when checked, any other control
     its value, the control not modified) is met by the body; @param clauses name no rule.
 Variant gold (javadoc; type and value read from the attributes; select branch: selected options, else the first option, one pair per
 option value; checkbox/radio branch: only when checked, value or "on"; else branch: the value):
  T1 absent: control, name and data each change the pairs added (control: type, value, tag name, options, checked; name: the key of
     every pair; data: the list written); no argument check.
  T2 absent: type is read by the checkbox/radio decision; value is read by the checkbox/radio pair (value or "on") and by the else
     pair (it is not literal-initialised); options is iterated and may receive first; first is tested and added; the for-each loop has
     no cursor, counter, flag or best-so-far to freeze; the three branches and the inner decisions add different pairs.
  T3 absent: the gold names three kinds (a select; a checkbox or radio button; any other control) and handles all three; both halves of
     the checkbox/radio pair get the same treatment; both selection cases (selected options, none selected) are handled; select is the
     only tag given its own treatment, one member of an unnamed set of tags ('One member of a larger unnamed set'); the gold's text
     names no tag class it would handle in part.
  T4 absent: 'A select submits its selected options, or its first option when none is selected' is met by the select branch;
     'a checkbox or radio button submits its value, or "on" when the value is empty, and only when it is checked' by the
     checkbox/radio branch; 'any other control submits its value' by the else branch (the general description, met by the submitted
     value); 'The control is not modified' is met (the gold only reads the control; the one list it adds to besides data is the
     fresh result of control.select); the @param clauses ('form control', 'name the control's values are submitted under', 'list to
     add the key vals to') name
     no rule; no inline comment; identifiers type, value, options, first name what they hold."""

FE = "src/main/java/org/jsoup/nodes/FormElement.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
ND = "src/main/java/org/jsoup/nodes/Node.java"
WL = "src/main/java/org/jsoup/safety/Whitelist.java"

GOLD_TEXT = '''/**
 * Adds the key/value pairs that a form control submits under the given name to the data list. A select submits its
 * selected options, or its first option when none is selected; a checkbox or radio button submits its value, or "on"
 * when the value is empty, and only when it is checked; any other control submits its value. The control is not
 * modified.
 *
 * @param control form control
 * @param name name the control's values are submitted under
 * @param data list to add the key vals to
 */
public static void addControlValues(Element control, String name, List<Connection.KeyVal> data) {
    String type = control.attr("type");
    String value = control.attr("value");
    if ("textarea".equals(control.tagName())) value = control.text();
    if ("select".equals(control.tagName())) {
        List<Element> options = control.select("option[selected]");
        Element first = control.select("option").first();
        if (options.isEmpty() && first != null)
            options.add(first);
        for (Element option : options)
            data.add(HttpConnection.KeyVal.create(name, option.attr("value")));
    } else if ("checkbox".equalsIgnoreCase(type) || "radio".equalsIgnoreCase(type)) {
        if (control.hasAttr("checked"))
            data.add(HttpConnection.KeyVal.create(name, value.length() > 0 ? value : "on"));
    } else {
        data.add(HttpConnection.KeyVal.create(name, value));
    }
}'''

HOP1 = '''/**
 * Get the key/value pairs that the given form controls submit, in the order of the controls. The controls are not
 * modified.
 * @param controls form controls
 * @return a new list of key vals
 */
public static List<Connection.KeyVal> formDataOf(List<Element> controls) {
    List<Connection.KeyVal> data = new ArrayList<Connection.KeyVal>();
    HttpConnection.appendFormData(controls, data);
    return data;
}'''

HOP2 = '''/**
 * Adds the key/value pairs of each of the given form controls to the data list, in the order of the controls. The
 * controls are not modified.
 * @param controls form controls
 * @param data list to add the key vals to
 */
public static void appendFormData(List<Element> controls, List<Connection.KeyVal> data) {
    for (Element control : controls)
        Evaluator.IsOnlyChild.addIfSubmittable(control, data);
}'''

HOP3 = '''/**
 * Adds the key/value pairs of a form control to the data list, if the control is submittable and not disabled. The
 * control is not modified.
 * @param control form control
 * @param data list to add the key vals to
 */
public static void addIfSubmittable(Element control, List<Connection.KeyVal> data) {
    if (!control.tag().isFormSubmittable() || control.hasAttr("disabled"))
        return;
    Node.addNamedFormData(control, data);
}'''

HOP4 = '''/**
 * Adds the key/value pairs of a form control to the data list, under the control's name attribute. A control without
 * a name adds nothing. The control is not modified.
 * @param control form control
 * @param data list to add the key vals to
 */
public static void addNamedFormData(Element control, List<Connection.KeyVal> data) {
    String name = control.attr("name");
    if (name.length() == 0)
        return;
    Whitelist.addControlValues(control, name, data);
}'''

DESIGN = {
 "instance": "Jsoup-42", "project": "Jsoup", "bug_id": 42, "seed": 8055,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": FE, "class": "org.jsoup.nodes.FormElement", "method": "formData", "near_line": 74},
 "facade_variant": "V1",
 "state_passed": "private field elements (the form's associated controls, an Elements list) to hop 1; no field written, no write-back",
 "reachability_probe": "full suite with `if (true) throw new IllegalStateException(\"PROBE-REACHED\")` as formData's first statement: "
                       "5 failing tests, all PROBE-REACHED at FormElement.formData(FormElement.java:75): FormElementTest::createsFormData, "
                       "::controlsAddedAfterParseAreLinkedWithForms, ::usesOnForCheckboxValueIfNoValueSet (direct calls), "
                       "::createsSubmitableConnection, ::actionWithNoValue (through FormElement.submit)",
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/nodes/FormElementTest.java",
             "test_class": "org.jsoup.nodes.FormElementTest", "test_method": "createsFormData"},
 "expected_signature": "expected:<six=[seven]> but was:<six=[]>",
 "gold": {"method": "addControlValues", "text": GOLD_TEXT,
          "fault": {"old": "        String value = control.attr(\"value\");\n"
                           "        if (\"textarea\".equals(control.tagName())) value = control.text();\n",
                    "new": "        String value = control.attr(\"value\");\n"}},
 "chain": {
   "facade_body": "return Element.formDataOf(elements);",
   "lie": "The data is gathered by a depth-first traversal of this form's descendant nodes, so that each control is visited in "
          "document order.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "formDataOf",
      "imports": ["org.jsoup.Connection", "org.jsoup.helper.HttpConnection"], "text": HOP1},
     {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "appendFormData",
      "imports": ["org.jsoup.nodes.Element", "org.jsoup.select.Evaluator"], "text": HOP2},
     {"file": EV, "class": "org.jsoup.select.Evaluator.IsOnlyChild", "method": "addIfSubmittable",
      "imports": ["org.jsoup.Connection"], "text": HOP3},
     {"file": ND, "class": "org.jsoup.nodes.Node", "method": "addNamedFormData",
      "imports": ["org.jsoup.Connection", "org.jsoup.safety.Whitelist"], "text": HOP4},
     {"file": WL, "class": "org.jsoup.safety.Whitelist", "method": "addControlValues",
      "imports": ["org.jsoup.Connection", "org.jsoup.helper.HttpConnection", "java.util.List"], "gold": True},
   ],
 },
 "evidence": ["org.jsoup.nodes.Element::val",
              "org.jsoup.select.Elements::val",
              "org.jsoup.nodes.FormElement::submit"],
 "ownership_reason": "Only the gold reads a form control's value and decides which pairs the control submits; hop 1 creates and "
                     "returns the list, hop 2 hands every control to hop 3 in order, hop 3 drops controls that are not submittable "
                     "or are disabled, hop 4 reads the name and drops unnamed controls - none of them reads a value. The gold's "
                     "javadoc promises that any control other than a select, checkbox or radio submits its value; the value of a "
                     "textarea is its text, as Element.val() computes it ('Get the value of a form element (input, textarea, etc)'), "
                     "Element.val(String) sets it and Elements.val() returns it (HtmlParserTest handlesTextArea and "
                     "preservesSpaceInTextArea pass), yet the gold submits the textarea's empty value attribute. The pairs leave the "
                     "gold as name/value KeyVals without the control, so no caller can recover the text, and no filtering of the "
                     "controls above the gold can supply it. The facade's javadoc ('the data that this form submits') and its caller "
                     "FormElement.submit, which posts that data, fix the meaning of a submitted value.",
 "ownership_tests": ["org.jsoup.parser.HtmlParserTest::handlesTextArea",
                     "org.jsoup.parser.HtmlParserTest::preservesSpaceInTextArea",
                     "org.jsoup.nodes.FormElementTest::usesOnForCheckboxValueIfNoValueSet"],
 "compensating": {
   "chain": [
     {"file": EV, "old": "if (!control.tag().isFormSubmittable() || control.hasAttr(\"disabled\"))",
      "new": "if (!control.tag().isFormListed() || control.hasAttr(\"disabled\"))",
      "why": "hop 3 lets every form-listed control through, not only the submittable ones"},
     {"file": ND, "old": "String name = control.attr(\"name\");\n        if (name.length() == 0)",
      "new": "String name = control.hasAttr(\"name\") ? control.attr(\"name\") : control.id();\n        if (name.length() == 0)",
      "why": "hop 4 falls back to the control's id when it has no name attribute"},
     {"file": HC, "old": "for (Element control : controls)\n            Evaluator.IsOnlyChild",
      "new": "for (Element control : new org.jsoup.select.Elements(controls).select(\"input, select, textarea\"))\n            Evaluator.IsOnlyChild",
      "why": "hop 2 re-selects the controls by tag (input, select, textarea) before handing them on"},
   ],
 },
 "host_notes": "host_mode largest5. Hosts are hosts_hop_order of the task record (batch8_tasks.json), in that order, none "
               "substituted: nodes.Element (hop 1, 1189 lines), helper.HttpConnection (hop 2, 912), select.Evaluator (hop 3, 706), "
               "nodes.Node (hop 4, 687), safety.Whitelist (hop 5, gold, 635; the smallest host). FormElement.java (the only allowed "
               "candidate's file) is excluded. All five are public top-level classes (Evaluator and Node are abstract, which does not "
               "affect a static method). Anchors from stageB_lib.pick_insertion_anchor with seed 8055 + 100 + i (as mr3_spec.py "
               "inserts them): hop 1 after Element.html(String) (line idx 1161, seed 8155), hop 2 after HttpConnection.get() (196, "
               "8156), hop 3 after `toString` (570, 8157), hop 4 after Node.after(Node) (333, 8158), hop 5 after "
               "Whitelist.removeAttributes (315, 8159). Hop 3's anchor is the toString of the public static nested class "
               "Evaluator.IsOnlyChild (its members are indented with four spaces and a tab, which the picker takes for an outer-class "
               "member), so the recipe places hop 3 inside Evaluator.IsOnlyChild, an existing public static class of the host file; "
               "hop 2 calls it as Evaluator.IsOnlyChild.addIfSubmittable. The facade calls hop 1 as Element.formDataOf (FormElement "
               "extends Element, same package); each hop imports the next host and org.jsoup.Connection as needed; the gold imports "
               "HttpConnection (for KeyVal.create) and java.util.List.",
}
