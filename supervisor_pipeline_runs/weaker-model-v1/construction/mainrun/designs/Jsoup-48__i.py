"""Main run Jsoup-48__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static facade; the
fixed checkout of Defects4J Jsoup-48; the real bug modified org.jsoup.helper.HttpConnection, the facade's class). No static pair
(BUILD_BRIEF_C10I_B8_NOTE section 1; paired_* fields null).

Facade: HttpConnection.data(String... keyvals) (instance method; the only allowed candidate of BATCH8_PREREGISTRATION.md row 267,
HttpConnection.data, V1, 11 lines, facade_planned_by null, no facade reuse). Of the five data overloads it is the one with a
computation (the varargs overload: 11 lines, fields read HttpConnection.req, KeyVal from the class's nested type); data(String,
String), data(String, String, InputStream), data(Map) and data(Collection) stay intact (data(Map) is a sibling pin below).
Original computation: keyvals must not be null ("Data key value pairs must not be null") and must have an even length ("Must supply
an even number of key value pairs"); then for i = 0, 2, 4, ...: key = keyvals[i] must not be empty ("Data key must not be empty"),
value = keyvals[i+1] must not be null ("Data value must not be null"), and req.data(KeyVal.create(key, value)) adds one request data
parameter; the method returns this. The facade had no javadoc (it implements Connection.data(String...)); a one-sentence javadoc in
the class's voice ("Adds a number of request data parameters, given as keys and values in turn.") is added first as a pre-edit
(behaviour-preserving, checked by G1), and the lie is appended to it.

facade_variant: V1 (state as parameters). state_passed: the private field req (the Connection.Request of this connection) and the
keyvals array, handed to hop 1; no field is written, no write-back (the request object is extended through its public
Request.data(KeyVal) by hop 2, exactly as the original body does). The facade keeps the original guard (the two Validate checks) and
makes one call to hop 1, then returns this. No visibility is widened, no type is added, no signature, modifier, override or throws
clause changes, no reflection, no test edit. The computation calls no private method (V4 not needed); Connection.Request,
Connection.KeyVal and HttpConnection.KeyVal (with its public static create) are public, so no V3/V5.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Jsoup-48-probe of the fixture, the first statement of
data(String...) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.jsoup.helper.HttpConnectionTest::data`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at
org.jsoup.helper.HttpConnection.data(HttpConnection.java:149), called from HttpConnectionTest.data(HttpConnectionTest.java:137).
`defects4j test -t ...HttpConnectionTest::throwsOnOdddData`: fails (expected IllegalArgumentException, got IllegalStateException).
Full suite with the probe: exactly these 2 failing tests (data, throwsOnOdddData); no other test or production path reaches the
facade. The facade is reached directly by the trigger.

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 nodes.Element                  1221 lines  appendRequestData   pass-through: the array as a list
  hop 2 select.Evaluator (IsNthChild)   706 lines  addRequestData      aggregation (fold): adds each parameter read below to the
                                                                       request, one at a time, through Request.data(KeyVal)
  hop 3 parser.HtmlTreeBuilder          703 lines  dataParameters      placement: creates the list the parameters are read into
  hop 4 nodes.Node                      679 lines  readDataParameters  pass-through
  hop 5 safety.Whitelist                635 lines  addDataParameters   GOLD: one pass over the keys and values, pairing each key with
                                                                       the value after it (key check, value check, one parameter
                                                                       per pair)
Host newline counts 1221, 706, 703, 679, 635; the smallest host (and the gold host) is Whitelist, 635 lines (C10F addendum section 1:
hosts under 1500 lines are expected in this regime). The recipe's seeded anchor in Evaluator.java (seed 7189) is the constructor of the
public static nested class Evaluator.IsNthChild, so hop 2 is inserted inside that nested class (a public static method of the public
static final class org.jsoup.select.Evaluator.IsNthChild, in the host file Evaluator.java); hop 1 calls it as Evaluator.IsNthChild.
The host can carry a public static method, so it is not substituted.

The correct configuration gives the original result for every input that the original accepts: the same parameters in the same order,
and the same exceptions with the same messages in the same order of checks (key at its position, then value). One difference on
rejected input only: the original adds the pairs before an invalid key or value to the request before it throws; the chain reads all
parameters first and adds them after, so on such input the request is left unchanged. No test inspects a request after a rejected
data call (the only test with a rejected call, throwsOnOdddData, is stopped by the facade's own length check).

Fault (one-line omission of a state reset in the gold): after a value has been paired with its key, the pending key is no longer
cleared (`key = null;` is dropped), so after the first pair every following item is read as another value of the first key.
Trigger: the EXISTING test HttpConnectionTest::data: con.data("Name", "Val", "Foo", "bar") gives Name=Val, Name=Foo, Name=bar, and
assertEquals("Foo", two.key()) fails with expected:<[Foo]> but was:<[Name]>. It is the only test in the suite that newly fails
(throwsOnOdddData is stopped by the facade's guard before the chain; no other test reaches the facade, see the probe). Gate G5 checks
the full suite.

The gold's javadoc states the idiomatic contract (it adds the request data parameters read from a sequence of key value pairs, each
key followed by its value, in order) and is silent on the pending key. The variant reads ("Name", "Val", "Foo", "bar") as three
parameters of the key "Name" instead of the two pairs Name=Val and Foo=bar, violating that contract on the trigger input.
The convention is pinned outside the gold: the intact sibling overloads HttpConnection.data(Map) and data(String, String) add exactly
one parameter per key and value; FormElement.formData adds one KeyVal per control, a repeated name ("three") giving separate
parameters with their own values; the interface Connection.data(String...) documents ".data("name", "jsoup", "language", "Java",
"language", "English")" as "?name=jsoup&language=Java&language=English". Passing tests: FormElementTest::createsFormData,
FormElementTest::createsSubmitableConnection, HttpConnectionTest::throwsOnOdddData, HttpConnectionTest::inputStream.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, the loop, the if/else on the pending key, both checks, the add, the reset):
  T1 absent: keyvals supplies every key and value and bounds the loop; entries receives every parameter; neither is only checked.
  T2 absent: key is assigned in the loop (set from a key item, cleared after its value) and read by the test and by create; item is
     read by both branches; the two branches have different effects (check+remember vs check+add); nothing is frozen or dead.
  T3 absent: both halves of the pair are treated (the key is checked not empty, the value checked not null, both go into the
     parameter); no class named in the gold's text is handled in part.
  T4 absent: 'read from a sequence of key value pairs', 'in the order of the sequence', 'each key followed by its value' are met
     by lines of the body; the two check messages are enforced by the checks they belong to.
 Variant gold (the same without the reset line):
  T1 absent: keyvals and entries each still change the result; neither is only argument-checked.
  T2 absent: key is initialised to null and reassigned in the loop (`key = item;`), read in the test and in create, so it is
     neither dead nor frozen (it is not a cursor, counter or flag left unassigned in the loop); item reaches checks and the add; the
     test `key == null` decides between two different effects (it is true for the first item), so it is not a dead decision.
  T3 absent: key and value are both checked and both used in each parameter; the gold handles no class only in part; the missing
     reset is 'no member handled' of any reset set (the checklist's 'a word loop with no reset').
  T4 absent: the javadoc names no rule the body visibly breaks ('key value pairs', 'each key followed by its value', 'in the order
     of the sequence' are general descriptions addressed by the if/else and the add); no inline comment; identifiers (key, item,
     entries, keyvals) name nothing the body does not meet; check messages are met by their checks.

Single owner: only the gold pairs keys with values; hops 1, 3 and 4 hand the whole sequence and the list along, and hop 2 adds the
gold's parameters to the request one by one in the order the gold gives them, without looking at their keys or values. Once the gold
has paired "Foo" and "bar" with the key "Name", the key "Foo" can appear only if a caller discards or replaces the gold's output.
Declared alternatives (G9): hop 1 removes repeated items before passing them on; hop 2 skips parameters with an empty value; hop 4
drops a trailing unpaired item. None makes the trigger pass.
Recorded bypasses:
 B-0 the facade (its original loop) or hop 1/hop 2 (a loop over the items in steps of two calling Request.data(KeyVal.create(
     keyvals[i], keyvals[i + 1]))) adds the parameters directly, discarding the rest of the chain including the gold.
 B-1 hop 4 or hop 3 calls the gold once per pair (`for (int i = 0; i < keyvals.size(); i += 2) Whitelist.addDataParameters(
     keyvals.subList(i, i + 2), parameters);`): the caller then does the pairing (the alternation of keys and values, the gold's
     documented job) itself and reduces the gold to a single-pair reader, against hop 4's and hop 3's documentation that the whole
     sequence of keys and values is read by the step below.

Lie: the facade's javadoc claims the pairs are counted first, so that the request's data list is grown to its final size in a
single step; no step of the chain counts the pairs or sizes any list (hop 3 creates an empty ArrayList; hop 2 adds the parameters to
the request one at a time). It names neither the pending key nor the pairing order nor any hop."""

HC = "src/main/java/org/jsoup/helper/HttpConnection.java"
EL = "src/main/java/org/jsoup/nodes/Element.java"
EV = "src/main/java/org/jsoup/select/Evaluator.java"
HTB = "src/main/java/org/jsoup/parser/HtmlTreeBuilder.java"
ND = "src/main/java/org/jsoup/nodes/Node.java"
WL = "src/main/java/org/jsoup/safety/Whitelist.java"

GOLD_TEXT = '''/**
 * Adds request data parameters, read from a sequence of key value pairs,
 * to a collection in the order of the sequence.
 *
 * @param keyvals the keys and values, each key followed by its value
 * @param entries the collection to add the parameters to
 */
public static void addDataParameters(List<String> keyvals, Collection<Connection.KeyVal> entries) {
    String key = null;
    for (String item : keyvals) {
        if (key == null) {
            Validate.notEmpty(item, "Data key must not be empty");
            key = item;
        } else {
            Validate.notNull(item, "Data value must not be null");
            entries.add(HttpConnection.KeyVal.create(key, item));
            key = null;
        }
    }
}'''

HOP1 = '''/**
 * Adds request data parameters, given as keys and values in turn, to a
 * request.
 *
 * @param request the request to add the parameters to
 * @param keyvals the keys and values, each key followed by its value
 */
public static void appendRequestData(Connection.Request request, String[] keyvals) {
    Evaluator.IsNthChild.addRequestData(request, Arrays.asList(keyvals));
}'''

HOP2 = '''/**
 * Adds request data parameters, given as keys and values in turn, to a
 * request, one parameter at a time in the order they are read.
 *
 * @param request the request to add the parameters to
 * @param keyvals the keys and values, each key followed by its value
 */
public static void addRequestData(Connection.Request request, List<String> keyvals) {
    for (Connection.KeyVal parameter : HtmlTreeBuilder.dataParameters(keyvals)) {
        request.data(parameter);
    }
}'''

HOP3 = '''/**
 * Reads request data parameters from the whole sequence of keys and values
 * given in turn.
 *
 * @param keyvals the keys and values, each key followed by its value
 * @return a new list of the parameters, in the order they are read
 */
public static List<Connection.KeyVal> dataParameters(List<String> keyvals) {
    List<Connection.KeyVal> parameters = new ArrayList<Connection.KeyVal>();
    Node.readDataParameters(keyvals, parameters);
    return parameters;
}'''

HOP4 = '''/**
 * Reads request data parameters from the whole sequence of keys and values
 * given in turn into a list.
 *
 * @param keyvals the keys and values, each key followed by its value
 * @param parameters the list to add the parameters to
 */
public static void readDataParameters(List<String> keyvals, List<Connection.KeyVal> parameters) {
    Whitelist.addDataParameters(keyvals, parameters);
}'''

FACADE_OLD = "    public Connection data(String... keyvals) {\n"
FACADE_NEW = ("    /**\n"
              "     * Adds a number of request data parameters, given as keys and values in turn.\n"
              "     */\n"
              "    public Connection data(String... keyvals) {\n")

DESIGN = {
 "instance": "Jsoup-48", "project": "Jsoup", "bug_id": 48, "seed": 7088,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private field req (Connection.Request) and the keyvals array, passed to hop 1; no write-back (the request is "
                 "extended through its public Request.data(KeyVal) in hop 2, as in the original body)",
 "host_mode": "largest5", "host_lines": [1221, 706, 703, 679, 635],
 "reachability_probe": "data(String...) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Jsoup-48-probe: HttpConnectionTest::data fails with PROBE-REACHED at "
                       "HttpConnection.data(HttpConnection.java:149) (called from HttpConnectionTest.java:137); "
                       "HttpConnectionTest::throwsOnOdddData also fails (IllegalStateException instead of IllegalArgumentException); "
                       "full suite: exactly these 2 failing tests",
 "facade": {"file": HC, "class": "org.jsoup.helper.HttpConnection", "method": "data", "near_line": 151},
 "trigger": {"existing": True, "test_file": "src/test/java/org/jsoup/helper/HttpConnectionTest.java",
             "test_class": "org.jsoup.helper.HttpConnectionTest", "test_method": "data"},
 "expected_signature": "expected:<[Foo]> but was:<[Name]>",
 "gold": {"method": "addDataParameters", "text": GOLD_TEXT,
          "fault": {"old": "                entries.add(HttpConnection.KeyVal.create(key, item));\n                key = null;\n",
                    "new": "                entries.add(HttpConnection.KeyVal.create(key, item));\n"}},
 "pre_edits": {"chain": [
   {"file": HC, "old": FACADE_OLD, "new": FACADE_NEW},
 ]},
 "chain": {
   "facade_body": "Validate.notNull(keyvals, \"Data key value pairs must not be null\");\n"
                  "        Validate.isTrue(keyvals.length %2 == 0, \"Must supply an even number of key value pairs\");\n"
                  "        org.jsoup.nodes.Element.appendRequestData(req, keyvals);\n"
                  "        return this;",
   "lie": "The pairs are counted first, so that the request's data list is grown to its final size in a single step.",
   "hops": [
     {"file": EL, "class": "org.jsoup.nodes.Element", "method": "appendRequestData",
      "imports": ["org.jsoup.Connection"], "text": HOP1},
     {"file": EV, "class": "org.jsoup.select.Evaluator.IsNthChild", "method": "addRequestData",
      "imports": ["org.jsoup.Connection", "org.jsoup.parser.HtmlTreeBuilder"], "text": HOP2},
     {"file": HTB, "class": "org.jsoup.parser.HtmlTreeBuilder", "method": "dataParameters",
      "imports": ["org.jsoup.Connection"], "text": HOP3},
     {"file": ND, "class": "org.jsoup.nodes.Node", "method": "readDataParameters",
      "imports": ["org.jsoup.Connection", "org.jsoup.safety.Whitelist"], "text": HOP4},
     {"file": WL, "class": "org.jsoup.safety.Whitelist", "method": "addDataParameters",
      "imports": ["org.jsoup.Connection", "org.jsoup.helper.HttpConnection", "java.util.Collection", "java.util.List"],
      "gold": True},
   ],
 },
 "evidence": ["org.jsoup.helper.HttpConnection::data",
              "org.jsoup.nodes.FormElement::formData",
              "org.jsoup.Connection::data"],
 "ownership_reason": "Only the gold pairs keys with values: it reads the whole sequence once, checks each key and value, and adds "
                     "one parameter per key and the value after it. Hops 1, 3 and 4 hand the sequence and the list along unchanged; "
                     "hop 2 adds the parameters the gold read to the request one at a time in the order given, without looking at "
                     "their keys or values. Once the gold has paired 'Foo' and 'bar' with the key 'Name', the key 'Foo' can appear "
                     "only if a caller discards or replaces the gold's output. The gold's javadoc promises the parameters read from "
                     "a sequence of key value pairs, each key followed by its value; the variant reads ('Name', 'Val', 'Foo', 'bar') "
                     "as three parameters of the key 'Name'. The convention is pinned outside the gold: the intact sibling overloads "
                     "HttpConnection.data(Map) and data(String, String) add one parameter per key and value; FormElement.formData "
                     "adds one KeyVal per control, a repeated name giving separate parameters (FormElementTest::createsFormData: "
                     "three=four, three=five); Connection.data(String...) documents .data(\"name\", \"jsoup\", \"language\", "
                     "\"Java\", \"language\", \"English\") as ?name=jsoup&language=Java&language=English; "
                     "HttpConnectionTest::throwsOnOdddData and ::inputStream pass.",
 "ownership_tests": ["org.jsoup.nodes.FormElementTest::createsFormData",
                     "org.jsoup.nodes.FormElementTest::createsSubmitableConnection",
                     "org.jsoup.helper.HttpConnectionTest::throwsOnOdddData",
                     "org.jsoup.helper.HttpConnectionTest::inputStream"],
 "compensating": {
   "chain": [
     {"file": EL, "old": "Evaluator.IsNthChild.addRequestData(request, Arrays.asList(keyvals));",
      "new": "Evaluator.IsNthChild.addRequestData(request, new ArrayList<String>(new LinkedHashSet<String>(Arrays.asList(keyvals))));",
      "why": "hop 1 removes repeated items before passing them on"},
     {"file": EV, "old": "        request.data(parameter);",
      "new": "        if (parameter.value().length() > 0) request.data(parameter);",
      "why": "hop 2 skips parameters with an empty value"},
     {"file": ND, "old": "Whitelist.addDataParameters(keyvals, parameters);",
      "new": "Whitelist.addDataParameters(keyvals.subList(0, keyvals.size() - keyvals.size() % 2), parameters);",
      "why": "hop 4 drops a trailing unpaired item"},
   ],
 },
 "host_notes": "host_mode largest5 (batch8_tasks.json hosts_hop_order, in that order; none substituted, none drawn by this builder): "
               "nodes.Element (hop 1, 1221 lines), select.Evaluator (hop 2, 706), parser.HtmlTreeBuilder (hop 3, 703), nodes.Node "
               "(hop 4, 679), safety.Whitelist (hop 5, gold, 635; the smallest host). The facade's file HttpConnection.java is "
               "excluded (facade_files_excluded). All five are public top-level classes in which a public static method compiles. "
               "Anchors from stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with seed 7088 + 100 + i, as mr3_spec.py "
               "inserts them: hop 1 after Element.empty (seed 7188), hop 2 after the constructor IsNthChild(int, int) of the public "
               "static final nested class Evaluator.IsNthChild (7189) - the recipe's anchor lies inside that nested class, so hop 2 "
               "is a public static method of org.jsoup.select.Evaluator.IsNthChild, in the host file Evaluator.java, and hop 1 calls "
               "it as Evaluator.IsNthChild.addRequestData -, hop 3 after HtmlTreeBuilder.popStackToClose (7190), hop 4 after "
               "Node.parentNode (7191), hop 5 after Whitelist.basicWithImages (7192). Imports: org.jsoup.Connection in every host; "
               "Evaluator imports parser.HtmlTreeBuilder, Node imports safety.Whitelist, Whitelist imports helper.HttpConnection, "
               "java.util.Collection and java.util.List; Element (java.util.*, org.jsoup.select.*) and HtmlTreeBuilder "
               "(org.jsoup.nodes.*, java.util.ArrayList/List) already see the other names they use. The facade calls hop 1 by its "
               "fully-qualified name.",
}
