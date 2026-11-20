"""Main run Lang-32 (C10 recipe on the fixed checkout of Defects4J Lang-32; the real bug modified HashCodeBuilder).

Facade: HashCodeBuilder.reflectionHashCode(int, int, T, boolean, Class<? super T>, String[]), the pool's 14-line candidate and the
overload every other reflectionHashCode overload delegates to (reflectionHashCode(Object), (Object, boolean), (Object, String[]),
... are called directly by HashCodeBuilderTest and HashCodeBuilderAndEqualsBuilderTest). Its body keeps the null-object guard and
delegates to hop 1. The original computation (private reflectionAppend + the superclass walk) is redistributed along the chain:

  hop 1 text.StrBuilder.toFieldHash        plumbing: creates the HashCodeBuilder (odd-number checks) and returns toHashCode()
  hop 2 StringUtils.appendLineage          fold over classes: the class of the object, then superclasses up to upTo (inclusive)
  hop 3 time.FastDateFormat.appendOnce     guard: the per-class registry check / register / unregister (cycle protection)
  hop 4 ArrayUtils.addDeclared             placement: the declared fields of the class, made accessible
  hop 5 time.DateUtils.addFieldValues      GOLD: the per-field loop (static and synthetic fields skipped, transient fields
                                           skipped unless requested, excluded names skipped, each remaining value appended)

The correct configuration performs exactly the original computation in the original order (same registry protocol, same
field order, same filters, same append), so every caller and test sees the original behaviour.

Fault (omission in the gold, a special-case skip): the transient skip is dropped, so a transient field is appended even when
testTransients is false; the loop still reads as an ordinary filter-and-append loop. Trigger: the EXISTING test
HashCodeBuilderTest::testReflectionHierarchyHashCode, whose first assertion hashes TestSubObject(0, 0, 0) (fields b, transient t,
inherited a) without transients and expects 17*37*37 = 23273; the variant appends t as well and returns 17*37^3 = 861101. It is
the only test that hashes an object with a transient field and compares the value: HashCodeBuilderAndEqualsBuilderTest hashes
pairs of equal objects (equal either way), the Ex tests stop in the constructor or at the null guard.

The gold's javadoc states the contract (useTransients: whether to use transient fields) and is silent on how the skip is done.
External pins (same rule in other production code, passing tests): the facade's own javadoc ('transient members will be
tested, otherwise they are ignored'); EqualsBuilder.reflectionAppend and CompareToBuilder.reflectionAppend
('(useTransients || !Modifier.isTransient(f.getModifiers()))'); ReflectionToStringBuilder.accept ('Reject transient fields');
EqualsBuilderTest::testReflectionHierarchyEquals, CompareToBuilderTest::testReflectionHierarchyCompareTransients and
ToStringBuilderTest::testReflectionHierarchy assert the rule through those builders.

Single owner: only the gold sees individual fields and their modifiers. Once a transient value has been appended the builder's
running total cannot be taken apart, and no hop above can leave transient fields out with a one-line change (hops 1-3 hold only
the class, hop 4 holds the Field[] but lang3 has no utility that filters a field array by modifier; forcing the flag at a hop
has no effect because the variant ignores it). Declared alternatives (G9): hop 3 passes false for the flag, hop 4 passes the
flag negated, hop 2 visits only the class of the object unless a superclass is given (passes the first assertion, fails the
second). Recorded bypass: a hop holding the class could re-implement the whole field loop inline (multi-statement), discarding
the gold; no one-line bypass exists (calling any reflectionHashCode overload from a hop recurses into the facade).

Pre-edits (chain geometry, behaviour-preserving): the registry helpers isRegistered/register/unregister are widened from
package-private to public, because hop 3 lives outside the builder package (no drawn host is in that package); the private
reflectionAppend, which held the whole per-class computation and is dead once the facade delegates, is removed together with
the four imports only it used (as B4 removed the private getMode).

Lie: the facade's javadoc claims the declared fields are sorted by name and the classes visited from the given superclass down
to the class of the object; the code walks upward from the class of the object in declaration order. It names neither
transient fields nor any skipping nor any hop."""

HCB = "src/main/java/org/apache/commons/lang3/builder/HashCodeBuilder.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"

GOLD_TEXT = '''/**
 * <p>Appends the values that the given fields hold in an object to a hash
 * code builder, in the order of the fields.</p>
 *
 * @param object  the object to read the field values from
 * @param declared  the fields declared by one class of the object, accessible
 * @param builder  the builder to append to
 * @param useTransients  whether to use transient fields
 * @param excludeFields  the names of the fields to exclude, may be null
 */
public static void addFieldValues(final Object object, final Field[] declared, final HashCodeBuilder builder,
        final boolean useTransients, final String[] excludeFields) {
    for (final Field field : declared) {
        final int modifiers = field.getModifiers();
        if (Modifier.isStatic(modifiers) || field.getName().indexOf('$') != -1) {
            continue;
        }
        if (Modifier.isTransient(modifiers) && !useTransients) {
            continue;
        }
        if (ArrayUtils.contains(excludeFields, field.getName())) {
            continue;
        }
        try {
            builder.append(field.get(object));
        } catch (IllegalAccessException e) {
            throw new InternalError("Unexpected IllegalAccessException");
        }
    }
}'''

HOP1 = '''/**
 * <p>Builds a hash code from the values of the fields of an object, using
 * the fields declared by its class and by its superclasses up to the given
 * class.</p>
 *
 * @param initial  a non-zero, odd number used as the initial value
 * @param multiplier  a non-zero, odd number used as the multiplier
 * @param object  the object to build a hash code for, not null
 * @param useTransients  whether to use transient fields
 * @param upTo  the superclass to reflect up to (inclusive), may be null
 * @param excludeFields  the names of the fields to exclude, may be null
 * @return the hash code
 * @throws IllegalArgumentException if a number is zero or even
 */
public static int toFieldHash(final int initial, final int multiplier, final Object object,
        final boolean useTransients, final Class<?> upTo, final String[] excludeFields) {
    final HashCodeBuilder builder = new HashCodeBuilder(initial, multiplier);
    StringUtils.appendLineage(object, upTo, builder, useTransients, excludeFields);
    return builder.toHashCode();
}'''

HOP2 = '''/**
 * <p>Appends the values of the fields of an object to a hash code builder,
 * class by class, from the class of the object up to the given superclass.</p>
 *
 * @param object  the object to append the fields of, not null
 * @param upTo  the superclass to reflect up to (inclusive), may be null
 * @param builder  the builder to append to
 * @param useTransients  whether to use transient fields
 * @param excludeFields  the names of the fields to exclude, may be null
 */
public static void appendLineage(final Object object, final Class<?> upTo, final HashCodeBuilder builder,
        final boolean useTransients, final String[] excludeFields) {
    Class<?> clazz = object.getClass();
    FastDateFormat.appendOnce(object, clazz, builder, useTransients, excludeFields);
    while (clazz.getSuperclass() != null && clazz != upTo) {
        clazz = clazz.getSuperclass();
        FastDateFormat.appendOnce(object, clazz, builder, useTransients, excludeFields);
    }
}'''

HOP3 = '''/**
 * <p>Appends the values of the fields declared by one class of an object to
 * a hash code builder, unless the object is already being traversed.</p>
 *
 * @param object  the object to append the fields of
 * @param clazz  the class whose declared fields are appended
 * @param builder  the builder to append to
 * @param useTransients  whether to use transient fields
 * @param excludeFields  the names of the fields to exclude, may be null
 */
public static void appendOnce(final Object object, final Class<?> clazz, final HashCodeBuilder builder,
        final boolean useTransients, final String[] excludeFields) {
    if (HashCodeBuilder.isRegistered(object)) {
        return;
    }
    try {
        HashCodeBuilder.register(object);
        ArrayUtils.addDeclared(object, clazz, builder, useTransients, excludeFields);
    } finally {
        HashCodeBuilder.unregister(object);
    }
}'''

HOP4 = '''/**
 * <p>Appends the values of the fields declared by a class to a hash code
 * builder, as held by the given object.</p>
 *
 * @param object  the object to read the field values from
 * @param clazz  the class whose declared fields are appended
 * @param builder  the builder to append to
 * @param useTransients  whether to use transient fields
 * @param excludeFields  the names of the fields to exclude, may be null
 */
public static void addDeclared(final Object object, final Class<?> clazz, final HashCodeBuilder builder,
        final boolean useTransients, final String[] excludeFields) {
    final Field[] declared = clazz.getDeclaredFields();
    AccessibleObject.setAccessible(declared, true);
    DateUtils.addFieldValues(object, declared, builder, useTransients, excludeFields);
}'''

REFLECTION_APPEND = '''
    /**
     * <p>
     * Appends the fields and values defined by the given object of the given <code>Class</code>.
     * </p>
     *
     * @param object
     *            the object to append details of
     * @param clazz
     *            the class to append details of
     * @param builder
     *            the builder to append to
     * @param useTransients
     *            whether to use transient fields
     * @param excludeFields
     *            Collection of String field names to exclude from use in calculation of hash code
     */
    private static void reflectionAppend(Object object, Class<?> clazz, HashCodeBuilder builder, boolean useTransients,
            String[] excludeFields) {
        if (isRegistered(object)) {
            return;
        }
        try {
            register(object);
            Field[] fields = clazz.getDeclaredFields();
            AccessibleObject.setAccessible(fields, true);
            for (Field field : fields) {
                if (!ArrayUtils.contains(excludeFields, field.getName())
                    && (field.getName().indexOf('$') == -1)
                    && (useTransients || !Modifier.isTransient(field.getModifiers()))
                    && (!Modifier.isStatic(field.getModifiers()))) {
                    try {
                        Object fieldValue = field.get(object);
                        builder.append(fieldValue);
                    } catch (IllegalAccessException e) {
                        // this can't happen. Would get a Security exception instead
                        // throw a runtime exception in case the impossible happens.
                        throw new InternalError("Unexpected IllegalAccessException");
                    }
                }
            }
        } finally {
            unregister(object);
        }
    }
'''.replace("     * </p>\n     *\n", "     * </p>\n     * \n", 1)   # the pristine javadoc line keeps a trailing space

DESIGN = {
 "instance": "Lang-32", "project": "Lang", "bug_id": 32, "seed": 5643,
 "src_root": "src/main/java", "test_root": "src/test/java",
 # near_line refers to the facade's header AFTER the pre-edits (299; 349 in the pristine file)
 "facade": {"file": HCB, "class": "org.apache.commons.lang3.builder.HashCodeBuilder", "method": "reflectionHashCode", "near_line": 299},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/builder/HashCodeBuilderTest.java",
             "test_class": "org.apache.commons.lang3.builder.HashCodeBuilderTest",
             "test_method": "testReflectionHierarchyHashCode"},
 "expected_signature": "expected:<23273> but was:<861101>",
 "gold": {"method": "addFieldValues", "text": GOLD_TEXT,
          "fault": {"old": "            if (Modifier.isStatic(modifiers) || field.getName().indexOf('$') != -1) {\n"
                           "                continue;\n"
                           "            }\n"
                           "            if (Modifier.isTransient(modifiers) && !useTransients) {\n"
                           "                continue;\n"
                           "            }",
                    "new": "            if (Modifier.isStatic(modifiers) || field.getName().indexOf('$') != -1) {\n"
                           "                continue;\n"
                           "            }"}},
 "pre_edits": {
   "chain": [
     {"file": HCB, "old": REFLECTION_APPEND, "new": ""},
     {"file": HCB, "old": "import java.lang.reflect.AccessibleObject;\nimport java.lang.reflect.Field;\nimport java.lang.reflect.Modifier;\n", "new": ""},
     {"file": HCB, "old": "import java.util.Set;\n\nimport org.apache.commons.lang3.ArrayUtils;\n", "new": "import java.util.Set;\n"},
     {"file": HCB, "old": "    static boolean isRegistered(Object value) {", "new": "    public static boolean isRegistered(Object value) {"},
     {"file": HCB, "old": "    static void register(Object value) {", "new": "    public static void register(Object value) {"},
     {"file": HCB, "old": "    static void unregister(Object value) {", "new": "    public static void unregister(Object value) {"},
   ],
 },
 "chain": {
   "facade_body": "if (object == null) {\n"
                  "            throw new IllegalArgumentException(\"The object to build a hash code for must not be null\");\n"
                  "        }\n"
                  "        return org.apache.commons.lang3.text.StrBuilder.toFieldHash(initialNonZeroOddNumber, multiplierNonZeroOddNumber,\n"
                  "                object, testTransients, reflectUpToClass, excludeFields);",
   "lie": "The declared fields of each class are first sorted by name, and the classes are then visited from the given "
          "superclass down to the class of the object, so that the values of a superclass enter the hash code before "
          "those of its subclasses.",
   "hops": [
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "toFieldHash",
      "imports": ["org.apache.commons.lang3.StringUtils", "org.apache.commons.lang3.builder.HashCodeBuilder"], "text": HOP1},
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "appendLineage",
      "imports": ["org.apache.commons.lang3.builder.HashCodeBuilder", "org.apache.commons.lang3.time.FastDateFormat"], "text": HOP2},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "appendOnce",
      "imports": ["org.apache.commons.lang3.ArrayUtils", "org.apache.commons.lang3.builder.HashCodeBuilder"], "text": HOP3},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "addDeclared",
      "imports": ["java.lang.reflect.AccessibleObject", "java.lang.reflect.Field",
                  "org.apache.commons.lang3.builder.HashCodeBuilder", "org.apache.commons.lang3.time.DateUtils"], "text": HOP4},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "addFieldValues",
      "imports": ["java.lang.reflect.Field", "java.lang.reflect.Modifier", "org.apache.commons.lang3.ArrayUtils",
                  "org.apache.commons.lang3.builder.HashCodeBuilder"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.builder.EqualsBuilder::reflectionAppend",
              "org.apache.commons.lang3.builder.CompareToBuilder::reflectionAppend",
              "org.apache.commons.lang3.builder.ReflectionToStringBuilder::accept",
              "org.apache.commons.lang3.builder.HashCodeBuilder::reflectionHashCode"],
 "ownership_reason": "Only the per-field loop sees individual fields and their modifiers; once a transient value has been "
                     "appended, the builder's running total cannot be taken apart, so the walk, the registry guard and the "
                     "field fetch cannot recover the hash with a one-line change (lang3 has no utility that filters a Field[] "
                     "by modifier, and forcing the flag at a hop has no effect when the loop ignores it). The rule is pinned "
                     "outside the gold: the facade's javadoc says transient members are ignored unless testTransients is true; "
                     "EqualsBuilder.reflectionAppend and CompareToBuilder.reflectionAppend apply "
                     "'(useTransients || !Modifier.isTransient(f.getModifiers()))' in the same field loop; "
                     "ReflectionToStringBuilder.accept rejects transient fields unless appendTransients; their passing tests "
                     "(testReflectionHierarchyEquals, testReflectionHierarchyCompareTransients, ToStringBuilderTest "
                     "testReflectionHierarchy) assert it.",
 "ownership_tests": ["org.apache.commons.lang3.builder.EqualsBuilderTest::testReflectionHierarchyEquals",
                     "org.apache.commons.lang3.builder.CompareToBuilderTest::testReflectionHierarchyCompareTransients",
                     "org.apache.commons.lang3.builder.ToStringBuilderTest::testReflectionHierarchy",
                     "org.apache.commons.lang3.builder.HashCodeBuilderAndEqualsBuilderTest::testFixture"],
 "compensating": {
   "chain": [
     {"file": FDF, "old": "            ArrayUtils.addDeclared(object, clazz, builder, useTransients, excludeFields);",
      "new": "            ArrayUtils.addDeclared(object, clazz, builder, false, excludeFields);",
      "why": "hop 3 never asks for transient fields"},
     {"file": AU, "old": "        DateUtils.addFieldValues(object, declared, builder, useTransients, excludeFields);",
      "new": "        DateUtils.addFieldValues(object, declared, builder, !useTransients, excludeFields);",
      "why": "hop 4 passes the opposite of the flag"},
     {"file": SU, "old": "        while (clazz.getSuperclass() != null && clazz != upTo) {",
      "new": "        while (upTo != null && clazz.getSuperclass() != null && clazz != upTo) {",
      "why": "hop 2 visits only the class of the object unless a superclass is given"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 5643 (mr_lib preview, n=5, target org/apache/commons/lang3/builder/HashCodeBuilder.java): "
               "text.StrBuilder (hop 1), StringUtils (hop 2), time.FastDateFormat (hop 3), ArrayUtils (hop 4), time.DateUtils "
               "(hop 5, gold). All five are public concrete classes in which a static method compiles; none was skipped. The "
               "registry helpers the per-class guard needs (HashCodeBuilder.isRegistered/register/unregister) are package-private "
               "and no drawn host is in the builder package (the only one in the pool, ToStringStyle, is not drawn for n=5), so a "
               "behaviour-preserving pre-edit widens the three helpers to public instead of substituting a host. DateUtils has a "
               "private static int[][] named 'fields'; the gold's parameter is named 'declared' to avoid shadowing it.",
}
