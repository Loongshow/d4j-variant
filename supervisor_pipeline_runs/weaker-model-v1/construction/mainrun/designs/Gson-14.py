"""Main run Gson-14 (C10f recipe, batch 6, on the fixed checkout of Defects4J Gson-14; the real bug modified
com.google.gson.internal.$Gson$Types, the facade's class).

Facade: $Gson$Types.subtypeOf(Type) (allowed target, BATCH6_PREREGISTRATION.md row 171: subtypeOf / supertypeOf). Both allowed
targets are reached by existing tests (probe below); subtypeOf is used and the intact supertypeOf stays beside it as the sibling
pin. subtypeOf is also reached through production code ($Gson$Types.resolve rebuilds a wildcard with a resolved upper bound
through it; seven ParameterizedTypesTest tests and three recursion tests go that way), not only by direct test calls.
Original computation of the facade: when the bound is itself a wildcard type its upper bounds are taken, otherwise the bound
alone; the result is a WildcardTypeImpl with those upper bounds and no lower bound.

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2): in a scratch copy of the fixture the first statement of each allowed
facade was made `if (true) throw new IllegalStateException("PROBE-REACHED");` and the FULL suite was run (defects4j test).
  subtypeOf:   13 failing tests, all 13 with java.lang.IllegalStateException: PROBE-REACHED: RecursiveTypesResolveTest
               testDoubleSubtype, testSubSupertype, testSuperSubtype, testRecursiveResolveSimple, testIssue603PrintStream,
               testIssue440WeakReference; ParameterizedTypesTest testVariableTypeDeserialization,
               testVariableTypeArrayDeserialization, testVariableTypeFieldsAndGenericArraysSerialization,
               testVariableTypeFieldsAndGenericArraysDeserialization, testParameterizedTypeGenericArraysSerialization,
               testParameterizedTypeGenericArraysDeserialization, testParameterizedTypeWithVariableTypeDeserialization.
  supertypeOf: 6 failing tests, all PROBE-REACHED (RecursiveTypesResolveTest testDoubleSupertype, testSubSupertype,
               testSuperSubtype, testRecursiveResolveSimple, testIssue603PrintStream, testIssue440WeakReference).
  A logging probe (scratch) recorded every argument subtypeOf receives in the full suite: classes Integer (the seven
  ParameterizedTypesTest tests), Number and Object; the unbounded wildcard ? (the three recursion tests); wildcards with a lower
  bound, ? super T, ? super CharsetDecoder (testIssue440WeakReference, testIssue603PrintStream) and ? super Number
  (testSubSupertype); and ONE wildcard with an upper bound other than Object, ? extends Number, in testDoubleSubtype only.

Hosts (C10f, host_mode = largest5; n1500_other = 1). Listed hosts_hop_order (newline counts): stream.JsonReader 1617, Gson 989,
internal.bind.TypeAdapters 906, internal.LinkedHashTreeMap 864, stream.JsonWriter 659. Anchors with stageB_lib.pick_anchor /
host_search.pick_insertion_anchor and the instance seed 7828 (+100+i, as mr2_spec inserts them): Gson's 2-space style leaves no
4-space-indented outer-class method, so the picker either finds none (the hop is appended before the class's closing brace) or
lands in a nested class. Two listed hosts cannot carry the hop and were replaced by the next-largest public class:
  hop 3 TypeAdapters (seed 7930: after `read`, line 532) lands inside the anonymous TypeAdapter<InetAddress> INET_ADDRESS, where a
        static method is illegal ("Illegal static declaration in inner class"). Next-largest public class internal.LinkedTreeMap
        (630; seed 7930: after `first`, line 510) lands inside its package-private static nested class Node (line 439), which
        hop 2 in com.google.gson can neither see nor call. internal.$Gson$Types (599) is the facade's own class. Next:
        GsonBuilder (590; no interior anchor, appended) -> hop 3.
  hop 4 LinkedHashTreeMap (seed 7931: after `last`, line 554) lands inside its package-private static nested class Node (line
        467), not visible from hop 3's package. LinkedTreeMap (seed 7931: after `last`, line 523, again in Node) fails the same
        way; GsonBuilder already holds hop 3. Next unused public class: JsonArray (380; no interior anchor, appended) -> hop 4.
  Hops 1, 2 and 5 (JsonReader seed 7928, Gson 7929, JsonWriter 7932) have no interior anchor and are appended.
Hosts used (hop order, newline counts): stream.JsonReader 1617, Gson 989, GsonBuilder 590, JsonArray 380, stream.JsonWriter 659
(gold). Smallest host: JsonArray, 380 lines; gold host 659 lines.

Chain:
  facade $Gson$Types.subtypeOf      keeps only the construction of the private WildcardTypeImpl (no class outside $Gson$Types
                                    can create it) with the empty lower bounds, around ONE delegating call
  hop 1 JsonReader.upperBoundsOf    decision: a wildcard bound with a lower bound (? super X) is bounded above only by Object,
                                    which is then the only upper bound; any other bound is passed on unchanged
  hop 2 Gson.upperBoundsFor         placement: the bound becomes the only element of an array of bounds
  hop 3 GsonBuilder.upperBoundsIn   pass-through
  hop 4 JsonArray.upperBoundsArray  aggregation: the gold's list of upper bounds is copied into an array, in order
  hop 5 JsonWriter.listUpperBounds  GOLD: the per-bound core; a bound that is a wildcard type contributes its own upper bounds,
                                    any other bound is its own upper bound
The correct configuration returns the original result for every wildcard the Java language can express: for a wildcard with a
lower bound, getUpperBounds() is {Object} (reflection and WildcardTypeImpl alike), which hop 1 returns directly; every other
bound reaches the gold and gets exactly the facade's original upper bounds; the same WildcardTypeImpl constructor checks run.

Fault (omission of a special-case step in the gold): the step for a bound that is itself a wildcard type (contribute its own
upper bounds) is dropped, so every bound is taken as its own upper bound. The gold then reads as a complete, ordinary routine
(each bound is an upper bound of a wildcard type that extends it). Trigger: the EXISTING test
RecursiveTypesResolveTest::testDoubleSubtype: assertEquals(subtypeOf(Number.class), subtypeOf(subtypeOf(Number.class))) fails
with "expected:<? extends java.lang.Number> but was:<? extends ? extends java.lang.Number>". It is the only test that gives
subtypeOf a wildcard without a lower bound whose upper bound is not Object: wildcards with a lower bound are answered by hop 1
(testSubSupertype, testIssue440WeakReference, testIssue603PrintStream still get ?), the unbounded ? yields ? extends ?, which
the three recursion tests (adapter creation only) do not observe, and class bounds are unchanged; full suite on the variant in
scratch: 1 failing test, the trigger. The gold's javadoc states the idiomatic contract (the upper bounds of a wildcard type that
extends each of the bounds; the facade's own sense of 'an unknown type that extends bound') and is silent on wildcard bounds; a
wildcard type that extends ? extends Number is an unknown subtype of Number and is bounded above by Number, and an upper bound of
a wildcard type is never itself a wildcard, so {? extends Number} violates that contract on the trigger input.

External pins: the sibling facade $Gson$Types.supertypeOf (intact) takes a wildcard bound's own lower bounds for the new wildcard
(testDoubleSupertype: supertypeOf of ? super Number is ? super Number; testSuperSubtype: supertypeOf of ? extends Number is ?);
$Gson$Types.getCollectionElementType reads a wildcard through its upper bound, and $Gson$Types.getRawType takes a wildcard's raw
type from its upper bound (CollectionTest::testWildcardPrimitiveCollectionDeserilaization reads Collection<? extends Integer>
elements as Integer; MapTest::testMapDeserializationWithWildcardValues reads Map<String, ? extends Long> values as Long);
$Gson$Types.resolve rebuilds a wildcard from its own resolved bound (subtypeOf(upperBound), supertypeOf(lowerBound));
testSubSupertype pins hop 1's case (subtypeOf of ? super Number is ?).

Single owner: only the gold maps a bound to the upper bounds it contributes. Hop 1 answers only wildcard bounds that have a lower
bound and documents that every other bound is passed on unchanged; hop 2 places the bound in an array, hop 3 passes the array
on, hop 4 copies the gold's list into an array in order, the facade wraps that array. Declared alternatives (G9): hop 1 also
answers an unbounded wildcard directly, hop 2 passes on the canonical form of the bound ($Gson$Types.canonicalize keeps a
wildcard a wildcard), hop 4 gives Object for an empty list; none changes the trigger. Recorded one-line edits outside the gold
that pass the trigger and the full suite (each checked on the variant in a scratch copy, defects4j test: 0 failing tests):
 B-0 bypass: the facade's original body (or any hop computing the upper bounds itself), discarding the chain.
 B-1 bypass (a second implementation of the gold's per-bound step placed above it): hop 1's last line passes on a wildcard's
     upper bound instead of the bound, `return Gson.upperBoundsFor(bound instanceof WildcardType ? ((WildcardType) bound).getUpperBounds()[0] : bound);`
     (breaks hop 1's 'any other bound is passed on unchanged'; a two-line hop 1 version that answers every wildcard bound by
     its own upper bounds passes too and breaks the same sentence); likewise hop 2 places a wildcard's upper bounds instead of
     the bound (breaks the documented placement), hop 3 replaces bounds[0] (breaks the pass-through and treats only the first
     of the bounds). The gold still returns the wildcard as its own upper bound and so still contradicts its own javadoc.
 B-2 bypass (after the gold): hop 4 replaces a wildcard first element of the gold's list by that wildcard's upper bounds
     (breaks 'the elements of the list ... in order'; treats only the first element; the gold's result is discarded for it).
 B-3 bypass (in the private WildcardTypeImpl): its constructor takes the upper bound of a wildcard argument,
     `this.upperBound = canonicalize(upperBounds[0] instanceof WildcardType ? ((WildcardType) upperBounds[0]).getUpperBounds()[0] : upperBounds[0]);`,
     re-doing the gold's per-bound step for the first element below the chain, for every caller of the constructor; the gold
     still returns {? extends Number} against its own javadoc.
 B-4 bypass (in the private WildcardTypeImpl): getUpperBounds() answers a wildcard upper bound by that wildcard's upper bounds,
     `return upperBound instanceof WildcardType ? ((WildcardType) upperBound).getUpperBounds() : new Type[] { upperBound };`;
     the trigger's assertEquals then passes through $Gson$Types.equals, but the stored bound is unchanged: toString still gives
     ? extends ? extends java.lang.Number and hashCode (computed from the stored bound) no longer agrees with equals.

Lie: the facade's javadoc claims the new wildcard type is interned, an equal wildcard type created earlier being returned in its
place; nothing is interned anywhere on the path. It names neither wildcard bounds nor upper bounds nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc 'Returns the upper bounds of a wildcard type that extends each of {@code bounds}.'; body: list sized by
 bounds.length; for each bound, a wildcard bound adds all of its upper bounds and continues, any other bound is added; return):
  T1 absent: bounds gives the capacity and every element; each element decides the branch and is added or read for its bounds.
  T2 absent: result (new ArrayList, not a literal) is added to on both paths and returned; bound is the loop variable; the
     wildcard path and the plain path add different things (its upper bounds vs the bound); no cursor, counter, flag or
     best-so-far.
  T3 absent: one binary test over the open interface Type (no closed set); of a wildcard bound only its upper bounds are read,
     which are what the method returns; its lower bounds play no role in an upper bound (getUpperBounds() already reports Object
     for ? super X), so there is no pair of the same role of which one half is treated; no class is named in the gold's text.
  T4 absent: the javadoc names only the upper bounds of a wildcard type that extends each of the bounds, which the loop
     produces; no limit, value class, case or property; no inline comment; identifiers name nothing unmet. Wildcard and
     Collections are written fully qualified inside the omitted step, so the variant leaves no unused import in the gold's
     file. Nothing needed rewriting.
 Variant gold (javadoc and signature unchanged; `List<Type> result = new ArrayList<Type>(bounds.length); for (Type bound :
 bounds) { result.add(bound); } return result;`):
  T1 absent: bounds is read for the capacity and the loop, and every element is added to the returned list.
  T2 absent: result is constructed (not a literal), added to in the loop and returned; bound is the loop variable and is added;
     there is no branch, case or ternary at all, so no dead decision; no frozen cursor, counter or flag.
  T3 absent: no case split, no set and no pair is handled at all ('no member handled'); no class is named.
  T4 absent: 'the upper bounds of a wildcard type that extends each of {@code bounds}' is a general description that the loop
     addresses (each bound becomes an upper bound); no limit, value class, case or property is named; no inline comment;
     identifiers (listUpperBounds, result, bound, bounds) name nothing the body visibly fails."""

TYPES = "gson/src/main/java/com/google/gson/internal/$Gson$Types.java"
JR = "gson/src/main/java/com/google/gson/stream/JsonReader.java"
GS = "gson/src/main/java/com/google/gson/Gson.java"
GB = "gson/src/main/java/com/google/gson/GsonBuilder.java"
JA = "gson/src/main/java/com/google/gson/JsonArray.java"
JW = "gson/src/main/java/com/google/gson/stream/JsonWriter.java"

EACH_DOC = '''/**
 * Returns the upper bounds of a wildcard type that extends each of
 * {@code bounds}.
 */'''

GOLD_TEXT = EACH_DOC + '''
public static List<Type> listUpperBounds(Type[] bounds) {
  List<Type> result = new ArrayList<Type>(bounds.length);
  for (Type bound : bounds) {
    if (bound instanceof java.lang.reflect.WildcardType) {
      java.util.Collections.addAll(result, ((java.lang.reflect.WildcardType) bound).getUpperBounds());
      continue;
    }
    result.add(bound);
  }
  return result;
}'''

HOP1 = '''/**
 * Returns the upper bounds of a wildcard type that extends {@code bound}.
 * A wildcard bound with a lower bound, such as {@code ? super String}, is
 * bounded above only by {@code Object}, which is then the only upper bound.
 * Any other bound is passed on unchanged.
 */
public static Type[] upperBoundsOf(Type bound) {
  if (bound instanceof WildcardType && ((WildcardType) bound).getLowerBounds().length > 0) {
    return new Type[] { Object.class };
  }
  return Gson.upperBoundsFor(bound);
}'''

HOP2 = '''/**
 * Returns the upper bounds of a wildcard type that extends {@code bound}.
 * The bound is passed on as the only element of an array of bounds.
 */
public static Type[] upperBoundsFor(Type bound) {
  return GsonBuilder.upperBoundsIn(new Type[] { bound });
}'''

HOP3 = EACH_DOC + '''
public static Type[] upperBoundsIn(Type[] bounds) {
  return JsonArray.upperBoundsArray(bounds);
}'''

HOP4 = '''/**
 * Returns the upper bounds of a wildcard type that extends each of
 * {@code bounds}, as an array that holds the elements of the list of
 * upper bounds in order.
 */
public static Type[] upperBoundsArray(Type[] bounds) {
  List<Type> upperBounds = JsonWriter.listUpperBounds(bounds);
  return upperBounds.toArray(new Type[upperBounds.size()]);
}'''

DESIGN = {
 "instance": "Gson-14", "project": "Gson", "bug_id": 14, "seed": 7828,
 "src_root": "gson/src/main/java", "test_root": "gson/src/test/java",
 "facade": {"file": TYPES, "class": "com.google.gson.internal.$Gson$Types", "method": "subtypeOf", "near_line": 77},
 "trigger": {"existing": True, "test_file": "gson/src/test/java/com/google/gson/internal/bind/RecursiveTypesResolveTest.java",
             "test_class": "com.google.gson.internal.bind.RecursiveTypesResolveTest", "test_method": "testDoubleSubtype"},
 "expected_signature": "expected:<? extends java.lang.Number> but was:<? extends ? extends java.lang.Number>",
 "gold": {"method": "listUpperBounds", "text": GOLD_TEXT,
          "fault": {"old": "      for (Type bound : bounds) {\n"
                           "        if (bound instanceof java.lang.reflect.WildcardType) {\n"
                           "          java.util.Collections.addAll(result, ((java.lang.reflect.WildcardType) bound).getUpperBounds());\n"
                           "          continue;\n"
                           "        }\n"
                           "        result.add(bound);",
                    "new": "      for (Type bound : bounds) {\n"
                           "        result.add(bound);"}},
 "chain": {
   "facade_body": "return new WildcardTypeImpl(com.google.gson.stream.JsonReader.upperBoundsOf(bound), EMPTY_TYPE_ARRAY);",
   "lie": "The new wildcard type is interned: when a wildcard type equal to it was created before, that earlier instance is "
          "returned in its place.",
   "hops": [
     {"file": JR, "class": "com.google.gson.stream.JsonReader", "method": "upperBoundsOf",
      "imports": ["java.lang.reflect.Type", "java.lang.reflect.WildcardType", "com.google.gson.Gson"], "text": HOP1},
     {"file": GS, "class": "com.google.gson.Gson", "method": "upperBoundsFor",
      "imports": [], "text": HOP2},
     {"file": GB, "class": "com.google.gson.GsonBuilder", "method": "upperBoundsIn",
      "imports": [], "text": HOP3},
     {"file": JA, "class": "com.google.gson.JsonArray", "method": "upperBoundsArray",
      "imports": ["java.lang.reflect.Type", "com.google.gson.stream.JsonWriter"], "text": HOP4},
     {"file": JW, "class": "com.google.gson.stream.JsonWriter", "method": "listUpperBounds",
      "imports": ["java.lang.reflect.Type", "java.util.ArrayList", "java.util.List"],
      "gold": True},
   ],
 },
 "evidence": ["com.google.gson.internal.$Gson$Types::supertypeOf",
              "com.google.gson.internal.$Gson$Types::getCollectionElementType",
              "com.google.gson.internal.$Gson$Types::getRawType",
              "com.google.gson.internal.$Gson$Types::resolve"],
 "ownership_reason": "Only the gold maps a bound to the upper bounds it contributes to the new wildcard type. Hop 1 answers "
                     "only a wildcard bound that has a lower bound (bounded above only by Object) and documents that any other "
                     "bound is passed on unchanged; hop 2 places the bound as the only element of an array; hop 3 passes the "
                     "array on; hop 4 copies the gold's list into an array in order; the facade wraps that array in the "
                     "wildcard type with no lower bound. The gold's javadoc promises the upper bounds of a wildcard type that "
                     "extends each of the bounds; a wildcard type that extends ? extends Number is an unknown subtype of Number "
                     "and is bounded above by Number (an upper bound of a wildcard type is never itself a wildcard), so "
                     "{? extends Number} violates it on the trigger input, as the trigger's ? extends ? extends Number shows. "
                     "The convention is pinned outside the gold: the sibling facade $Gson$Types.supertypeOf (intact) gives the "
                     "new wildcard a wildcard bound's own lower bounds (testDoubleSupertype: supertypeOf of ? super Number is "
                     "? super Number; testSuperSubtype: supertypeOf of ? extends Number is ?); "
                     "$Gson$Types.getCollectionElementType and $Gson$Types.getRawType read a wildcard through its own upper "
                     "bound (CollectionTest testWildcardPrimitiveCollectionDeserilaization reads Collection<? extends Integer> "
                     "elements as Integer; MapTest testMapDeserializationWithWildcardValues reads Map<String, ? extends Long> "
                     "values as Long); $Gson$Types.resolve rebuilds a wildcard from its own resolved bound; testSubSupertype "
                     "pins hop 1's case (subtypeOf of ? super Number is ?). One-line edits outside the gold that pass the "
                     "suite either compute the upper bounds themselves and discard the chain (the facade's original body), or "
                     "replace a wildcard bound by its own upper bound before the gold (a second implementation of the gold's "
                     "per-bound step: it breaks hop 1's 'passed on unchanged', hop 2's placement or hop 3's pass-through, and "
                     "treats only the first of the bounds at hops 2-3), or replace the first element of the gold's list after "
                     "it (hop 4, against its 'elements of the list in order'), or make the private WildcardTypeImpl constructor "
                     "unwrap a wildcard argument for every caller, or make WildcardTypeImpl.getUpperBounds() mask the stored "
                     "wildcard (toString still shows ? extends ? extends Number and hashCode no longer agrees with equals); in "
                     "every case the gold still returns the wildcard as its own upper bound against its own javadoc.",
 "ownership_tests": ["com.google.gson.internal.bind.RecursiveTypesResolveTest::testDoubleSupertype",
                     "com.google.gson.internal.bind.RecursiveTypesResolveTest::testSuperSubtype",
                     "com.google.gson.internal.bind.RecursiveTypesResolveTest::testSubSupertype",
                     "com.google.gson.functional.CollectionTest::testWildcardPrimitiveCollectionDeserilaization",
                     "com.google.gson.functional.MapTest::testMapDeserializationWithWildcardValues"],
 "compensating": {
   "chain": [
     {"file": JR, "old": "if (bound instanceof WildcardType && ((WildcardType) bound).getLowerBounds().length > 0) {",
      "new": "if (bound instanceof WildcardType && (((WildcardType) bound).getLowerBounds().length > 0 || ((WildcardType) bound).getUpperBounds()[0] == Object.class)) {",
      "why": "hop 1 also answers an unbounded wildcard directly"},
     {"file": GS, "old": "return GsonBuilder.upperBoundsIn(new Type[] { bound });",
      "new": "return GsonBuilder.upperBoundsIn(new Type[] { com.google.gson.internal.$Gson$Types.canonicalize(bound) });",
      "why": "hop 2 places the canonical form of the bound"},
     {"file": JA, "old": "return upperBounds.toArray(new Type[upperBounds.size()]);",
      "new": "return upperBounds.isEmpty() ? new Type[] { Object.class } : upperBounds.toArray(new Type[upperBounds.size()]);",
      "why": "hop 4 gives Object when no upper bound is left"},
   ],
 },
 "host_notes": "C10f host_mode largest5 (n1500_other = 1). Listed hosts_hop_order: stream.JsonReader 1617, Gson 989, "
               "internal.bind.TypeAdapters 906, internal.LinkedHashTreeMap 864, stream.JsonWriter 659. Anchors with the "
               "recipe's picker and seed 7828+100+i (Gson's 2-space style leaves no 4-space outer-class method, so the "
               "picker finds no interior anchor or lands in a nested class). Hop 3: TypeAdapters' anchor (seed 7930, after "
               "`read`, line 532) is inside the anonymous TypeAdapter<InetAddress> INET_ADDRESS, where a static method is "
               "illegal; the next-largest public class internal.LinkedTreeMap (630; seed 7930, after `first`, line 510) puts "
               "the hop in its package-private static nested class Node (line 439), which hop 2 in com.google.gson cannot "
               "access; internal.$Gson$Types (599) is the facade's class; next GsonBuilder (590) has no interior anchor -> "
               "hop 3, appended to the outer class. Hop 4: LinkedHashTreeMap's anchor (seed 7931, after `last`, line 554) is "
               "inside its package-private static nested class Node (line 467), not visible from hop 3's package; "
               "LinkedTreeMap (seed 7931, after `last`, line 523, again in Node) fails the same way; GsonBuilder holds hop 3; "
               "next unused public class JsonArray (380) has no interior anchor -> hop 4, appended. Hops 1, 2 and 5 "
               "(JsonReader seed 7928, Gson 7929, JsonWriter 7932) have no interior anchor and are appended before the "
               "class's closing brace. Hosts used: JsonReader 1617, Gson 989, GsonBuilder 590, JsonArray 380, JsonWriter 659 "
               "(gold); smallest host 380 lines. All five are public top-level classes. The facade calls hop 1 by its "
               "fully-qualified name; JsonReader imports Type, WildcardType and Gson; Gson and GsonBuilder share the package "
               "with the next host; JsonArray imports Type and JsonWriter; JsonWriter imports Type, ArrayList and List. The "
               "facade keeps the construction of $Gson$Types' private WildcardTypeImpl, which no class outside $Gson$Types "
               "can create.",
}
