"""Main run Collections-13 (cell C10f: the C10 recipe with fallback hosts, batch 6, on the fixed checkout of Defects4J
Collections-13; the real bug modified ExtendedProperties, the target class).

Facade: ExtendedProperties.convertProperties(Properties) (the only allowed target, BATCH6_PREREGISTRATION.md row 147; no facade
reuse). It has no production caller; its test callers are TestExtendedProperties::testInheritDefaultProperties and
TestExtendedProperties::testCollections299.
Original computation: create an empty ExtendedProperties; walk props.propertyNames() (the names of the property list and of its
default property lists); for each name take props.getProperty(name), i.e. the name's own value when that is a String, otherwise
the String value it inherits from the defaults, otherwise null; add every non-null value with setProperty; return the new object.
The facade has no argument guard, so its body becomes the single delegating call to hop 1.

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2, run before designing): in a scratch copy of the fixture
(/private/tmp/c13-probe/w) the facade's first statement was made `if (true) throw new IllegalStateException("PROBE-REACHED");`
(the `if (true)` only keeps the rest of the body reachable for javac); defects4j compile OK; defects4j test -t
TestExtendedProperties::testInheritDefaultProperties -> 1 failing, java.lang.IllegalStateException: PROBE-REACHED at
ExtendedProperties.convertProperties; -t TestExtendedProperties::testCollections299 -> 1 failing, same message; full suite ->
exactly these 2 failing tests. The facade is reached by existing tests (and by no other test).

Hosts (host_mode = largest5: the fixed revision has only 3 other public classes of >= 1500 lines, so the hosts are the five
largest public, non-interface, non-enum classes other than ExtendedProperties, from hosts_hop_order of the task record; hop i in
the i-th largest, no substitution):
  hop 1 bidimap.TreeBidiMap         2085 lines   toExtendedProperties   placement: creates the empty ExtendedProperties
  hop 2 DoubleOrderedMap            1995 lines   copyProperties         pass-through
  hop 3 MapUtils                    1678 lines   putProperties          plumbing: enumerates the property names (propertyNames)
  hop 4 CursorableLinkedList        1468 lines   addNamedProperties     pass-through
  hop 5 FastArrayList               1333 lines   addStringProperties    GOLD: per name, the value lookup (own String value, else
                                                                        the value getProperty resolves) and the add of String values
Smallest host: FastArrayList, 1333 lines (the gold host). Anchors: stageB_lib.pick_anchor (host_search.pick_insertion_anchor) with
the instance seed 7727 + 100 + i, as mr2_spec.py inserts them (see host_notes).
The correct configuration returns the original result for every input: the same names in the same order, and for each name the
own value when it is a String, otherwise props.getProperty(name) (which is then the inherited String or null), added only when it
is a String; this is the getProperty rule written out, so the added values are exactly the original's non-null getProperty values.

Fault (one-line omission in the gold, a decision): the step that takes the value through getProperty when the name has no String
value of its own is dropped, so only the property list's own String values are added. Trigger: the EXISTING test
TestExtendedProperties::testInheritDefaultProperties; assertEquals("foo", extended.getString("test")) still holds and
assertEquals("class", extended.getString("resource.loader")) fails with expected:<class> but was:<null> ("resource.loader" is
set only in the default Properties). testCollections299 passes on the variant: its own value Boolean.FALSE and its inherited
value Boolean.TRUE are not Strings and are skipped either way. No other test reaches the chain (probe above), so the trigger is
the only test that newly fails. The failure is an assertion in the test method itself; no exception passes through the chain.

The gold's javadoc states the idiomatic contract (add the named properties of a Properties object, only those with String
values) and is silent on default property lists. For a java.util.Properties the property named "resource.loader" has the String
value "class" (props.getProperty), so the variant violates that contract on the trigger input.
External pins (outside the gold): the facade's own javadoc ('this method will pick up any default parent Properties of the
specified input object'); ExtendedProperties.getProperty does the same two-level lookup for the configuration class ('Will return
user value if exists, if not then default value if exists'); ExtendedProperties.getString falls back to its defaults when the key
has no value of its own. Passing test: testCollections299 converts a Properties with a default list and pins that only String
values, own or inherited, are passed on.

Single owner: only the gold holds a name together with the Properties object it reads the value from; hops 1-4 hold the whole
Properties object and the target and get back the filled target. The values inherited from a default list can only be read
through getProperty/propertyNames of the Properties object (its defaults field is protected in java.util, and no Commons
Collections method flattens a Properties object), so no one-line change of a hop's arguments makes Hashtable.get see them, and
once the gold has returned no caller can tell which inherited names were skipped. Declared alternatives (G9): hop 3 enumerates the
names of the String-valued properties (stringPropertyNames); hop 4 passes a clone of the properties; hop 1 reads the input through
a new Properties object that has it as its default list. Each still loses "resource.loader".
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-0 the facade's original body (the propertyNames loop with getProperty and setProperty) restored: several lines, discards the
     whole chain.
 B-1 hop 4 re-implements the copy on one line instead of delegating:
     `while (names.hasMoreElements()) { String name = (String) names.nextElement(); String value = props.getProperty(name); if (value != null) { target.setProperty(name, value); } } return target;`
     Checked on the variant in a scratch copy: trigger passes, full suite 0 failing tests. It makes the gold dead; a second
     implementation of the gold's work at a pass-through hop.

Pre-edit (behaviour-preserving, needed by the recipe): FastArrayList is Serializable (through ArrayList) and declares no
serialVersionUID, so the JVM computes it from the class's members, and any added non-private method changes it; the existing tests
TestFastArrayList(1)::testEmptyListCompatibility / ::testFullListCompatibility then fail to read the stored canonical forms
(InvalidClassException: stream classdesc serialVersionUID = 1566341225434603896, local class serialVersionUID differs; observed on
a scratch build of the chain). The pre-edit declares the value the pristine class already has,
`private static final long serialVersionUID = 1566341225434603896L;`, with the house comment 'Ensure serialization compatibility'
(as in ArrayStack and CursorableLinkedList), so the serialized form and every behaviour of FastArrayList stay as they are.

Lie: the facade's javadoc claims the property names are first sorted into ascending order and the properties are then added one
by one in that order; the chain sorts nothing (hop 3 takes the names in the order propertyNames lists them). It names neither the
default list nor value types nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: props is read by get and getProperty, names drives the loop and gives every name, target receives setProperty and is
     returned.
  T2 absent: name and value are read (lookup, instanceof tests, setProperty); the loop is advanced by names.nextElement(); no
     literal-initialised local, counter, flag or best-so-far; the first if replaces a non-String own value by the getProperty value
     (changes what is added), the second decides whether setProperty runs.
  T3 absent: the only class named is 'String values', and both tests and the add treat it in full; the own and the getProperty
     lookup are both performed; no range ends, pair halves or enumeration of cases.
  T4 absent: the javadoc names 'the named properties of a Properties object' (general, the loop addresses it), 'Only properties
     with String values are added' (met by instanceof String before setProperty), '@return the target ExtendedProperties' (met by
     return target); the @param 'not null' phrases are caller preconditions. Nothing needed rewriting.
 Variant gold (javadoc, signature, `while (names.hasMoreElements()) { String name = (String) names.nextElement(); Object value =
 props.get(name); if (value instanceof String) { target.setProperty(name, value); } } return target;`):
  T1 absent: props is read by props.get(name) and decides what is added; names drives the loop and supplies every name; target is
     written by setProperty and returned. No parameter is only argument-checked (the gold has no argument check).
  T2 absent: name is read by the lookup and by setProperty; value by the instanceof test and by setProperty; the loop advances
     through names.nextElement(); no literal-initialised or frozen local; the single if decides whether setProperty runs.
  T3 absent: 'String values' is the only class the text names and the instanceof String test handles it in full; no other value
     class, pair, range or case set is read or named (no member of any other set is handled).
  T4 absent: 'Add the named properties of a Properties object to an ExtendedProperties' is a general description the loop
     addresses; 'Only properties with String values are added' is met by the instanceof String test; '@return the target
     ExtendedProperties' is met by `return target`; 'must not be null' phrases are caller preconditions; no limit, bound, case or
     property is named that the body does not meet; no inline comment; identifiers (name, value) name nothing unmet."""

EP = "src/java/org/apache/commons/collections/ExtendedProperties.java"
TBM = "src/java/org/apache/commons/collections/bidimap/TreeBidiMap.java"
DOM = "src/java/org/apache/commons/collections/DoubleOrderedMap.java"
MU = "src/java/org/apache/commons/collections/MapUtils.java"
CLL = "src/java/org/apache/commons/collections/CursorableLinkedList.java"
FAL = "src/java/org/apache/commons/collections/FastArrayList.java"

GOLD_TEXT = '''/**
 * Add the named properties of a Properties object to an
 * ExtendedProperties.  Only properties with String values are added.
 *
 * @param props The properties to read, must not be null
 * @param names The names of the properties to add, must not be null
 * @param target The ExtendedProperties to add to, must not be null
 * @return the target ExtendedProperties
 */
public static ExtendedProperties addStringProperties(Properties props, Enumeration names, ExtendedProperties target) {

    while (names.hasMoreElements()) {
        String name = (String) names.nextElement();
        Object value = props.get(name);
        if (!(value instanceof String)) {
            value = props.getProperty(name);
        }
        if (value instanceof String) {
            target.setProperty(name, value);
        }
    }
    return target;

}'''

HOP1 = '''/**
 * Creates a new ExtendedProperties containing the properties of the
 * specified Properties object.
 *
 * @param props  the properties to copy, must not be null
 * @return a new ExtendedProperties containing the properties
 */
public static ExtendedProperties toExtendedProperties(final Properties props) {
    return DoubleOrderedMap.copyProperties(props, new ExtendedProperties());
}'''

HOP2 = '''/**
 * Copies the properties of the specified Properties object into an
 * ExtendedProperties.
 *
 * @param props the properties to copy, must not be null.
 * @param target the ExtendedProperties to copy into, must not be null.
 *
 * @return the target ExtendedProperties.
 */
public static ExtendedProperties copyProperties(Properties props, ExtendedProperties target) {
    return MapUtils.putProperties(props, target);
}'''

HOP3 = '''/**
 * Puts the properties of a Properties object into an ExtendedProperties,
 * taking the property names in the order the Properties object lists them.
 *
 * @param props  the properties to put, must not be null
 * @param target  the ExtendedProperties to put into, must not be null
 * @return the target ExtendedProperties
 */
public static ExtendedProperties putProperties(Properties props, ExtendedProperties target) {
    return CursorableLinkedList.addNamedProperties(props, props.propertyNames(), target);
}'''

HOP4 = '''/**
 * Adds the named properties of a Properties object to an ExtendedProperties.
 * @param props the properties to read, must not be null
 * @param names the names of the properties to add, must not be null
 * @param target the ExtendedProperties to add to, must not be null
 * @return the target ExtendedProperties
 */
public static ExtendedProperties addNamedProperties(Properties props, Enumeration names, ExtendedProperties target) {
    return FastArrayList.addStringProperties(props, names, target);
}'''

DESIGN = {
 "instance": "Collections-13", "project": "Collections", "bug_id": 13, "seed": 7727,
 "src_root": "src/java", "test_root": "src/test",
 "host_mode": "largest5", "host_lines": [2085, 1995, 1678, 1468, 1333], "smallest_host_lines": 1333,
 "reachability_probe": "facade first statement `if (true) throw new IllegalStateException(\"PROBE-REACHED\");` in a scratch copy; "
                       "TestExtendedProperties::testInheritDefaultProperties and ::testCollections299 each fail with "
                       "java.lang.IllegalStateException: PROBE-REACHED at ExtendedProperties.convertProperties; full suite: exactly "
                       "these 2 failing tests",
 "facade": {"file": EP, "class": "org.apache.commons.collections.ExtendedProperties", "method": "convertProperties", "near_line": 1719},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/collections/TestExtendedProperties.java",
             "test_class": "org.apache.commons.collections.TestExtendedProperties",
             "test_method": "testInheritDefaultProperties"},
 "expected_signature": "expected:<class> but was:<null>",
 "gold": {"method": "addStringProperties", "text": GOLD_TEXT,
          "fault": {"old": "            String name = (String) names.nextElement();\n"
                           "            Object value = props.get(name);\n"
                           "            if (!(value instanceof String)) {\n"
                           "                value = props.getProperty(name);\n"
                           "            }\n",
                    "new": "            String name = (String) names.nextElement();\n"
                           "            Object value = props.get(name);\n"}},
 "pre_edits": {
   "chain": [{"file": FAL, "old": "public class FastArrayList extends ArrayList {\n\n",
              "new": "public class FastArrayList extends ArrayList {\n\n"
                     "    /** Ensure serialization compatibility */\n"
                     "    private static final long serialVersionUID = 1566341225434603896L;\n\n"}],
 },
 "chain": {
   "facade_body": "return org.apache.commons.collections.bidimap.TreeBidiMap.toExtendedProperties(props);",
   "lie": "The property names are first sorted into ascending order, and the properties are then added to the new "
          "ExtendedProperties one by one in that order.",
   "hops": [
     {"file": TBM, "class": "org.apache.commons.collections.bidimap.TreeBidiMap", "method": "toExtendedProperties",
      "imports": ["java.util.Properties", "org.apache.commons.collections.DoubleOrderedMap",
                  "org.apache.commons.collections.ExtendedProperties"], "text": HOP1},
     {"file": DOM, "class": "org.apache.commons.collections.DoubleOrderedMap", "method": "copyProperties",
      "imports": ["java.util.Properties"], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.collections.MapUtils", "method": "putProperties",
      "imports": [], "text": HOP3},
     {"file": CLL, "class": "org.apache.commons.collections.CursorableLinkedList", "method": "addNamedProperties",
      "imports": ["java.util.Enumeration", "java.util.Properties"], "text": HOP4},
     {"file": FAL, "class": "org.apache.commons.collections.FastArrayList", "method": "addStringProperties",
      "imports": ["java.util.Enumeration", "java.util.Properties"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.collections.ExtendedProperties::convertProperties",
              "org.apache.commons.collections.ExtendedProperties::getProperty",
              "org.apache.commons.collections.ExtendedProperties::getString"],
 "ownership_reason": "Only the gold holds a property name together with the Properties object its value is read from; hops 1-4 "
                     "hold the whole Properties object and the target ExtendedProperties and get back the filled target. The "
                     "values a Properties object inherits from its default property lists can only be read through its "
                     "getProperty (or listed through propertyNames); its defaults field is protected in java.util and no Commons "
                     "Collections method flattens a Properties object, so no one-line change of a hop's arguments lets "
                     "Hashtable.get see an inherited value, and once the gold has returned the target no caller can tell which "
                     "inherited names were skipped. The convention is pinned outside the gold: the facade's javadoc ('this method "
                     "will pick up any default parent Properties of the specified input object'); ExtendedProperties.getProperty "
                     "does the same two-level lookup for the configuration class ('Will return user value if exists, if not then "
                     "default value if exists'); ExtendedProperties.getString falls back to its defaults when a key has no value "
                     "of its own; testCollections299 converts a Properties object with a default list and pins that only String "
                     "values, own or inherited, are passed on; testRetrieve pins the target side (a value added with setProperty is returned by "
                     "getProperty and getString, and an absent key gives null). The gold's javadoc promises the named properties of the "
                     "Properties object with String values, and \"resource.loader\" is such a property (getProperty gives "
                     "\"class\").",
 "ownership_tests": ["org.apache.commons.collections.TestExtendedProperties::testCollections299",
                     "org.apache.commons.collections.TestExtendedProperties::testRetrieve"],
 "compensating": {
   "chain": [
     {"file": MU, "old": "return CursorableLinkedList.addNamedProperties(props, props.propertyNames(), target);",
      "new": "return CursorableLinkedList.addNamedProperties(props, Collections.enumeration(props.stringPropertyNames()), target);",
      "why": "hop 3 enumerates the names of the String-valued properties (stringPropertyNames)"},
     {"file": CLL, "old": "return FastArrayList.addStringProperties(props, names, target);",
      "new": "return FastArrayList.addStringProperties((Properties) props.clone(), names, target);",
      "why": "hop 4 passes a clone of the properties"},
     {"file": TBM, "old": "return DoubleOrderedMap.copyProperties(props, new ExtendedProperties());",
      "new": "return DoubleOrderedMap.copyProperties(new Properties(props), new ExtendedProperties());",
      "why": "hop 1 reads the input through a new Properties object that has it as its default list"},
   ],
 },
 "host_notes": "host_mode largest5 (3 other public classes reach 1500 lines in the fixed revision). Hosts = hosts_hop_order of the "
               "batch-6 task record, the five largest public non-interface non-enum classes other than ExtendedProperties, hop i "
               "in the i-th largest: bidimap.TreeBidiMap 2085 lines (hop 1), DoubleOrderedMap 1995 (hop 2), MapUtils 1678 "
               "(hop 3), CursorableLinkedList 1468 (hop 4), FastArrayList 1333 (hop 5, gold; smallest host). All five are public "
               "top-level classes in which a static method compiles (DoubleOrderedMap is final and deprecated, "
               "CursorableLinkedList deprecated, FastArrayList extends ArrayList; none of this affects a static method); none "
               "was substituted. FastArrayList declares no serialVersionUID, so an added method would change its computed value and "
               "break the serialized-form compatibility tests; a behaviour-preserving pre-edit declares the pristine value "
               "1566341225434603896L (house idiom of ArrayStack and CursorableLinkedList). Anchors (stageB_lib.pick_anchor = host_search.pick_insertion_anchor with seed 7727 + 100 + i, "
               "line indices on the pristine fixture, before the pre-edit and the imports; mr2_spec.py drew the same five anchor methods): TreeBidiMap after getKey (line idx 265, seed 7827), DoubleOrderedMap "
               "after size (1287, seed 7828), MapUtils after isNotEmpty (1214, seed 7829), CursorableLinkedList after size "
               "(639, seed 7830), FastArrayList after get (420, seed 7831); every anchor lies in the outer class. The facade "
               "calls hop 1 by its fully-qualified name; hop 1 imports Properties, DoubleOrderedMap and ExtendedProperties; "
               "hops 2-5 share the package of ExtendedProperties and import only the java.util types they use.",
}
