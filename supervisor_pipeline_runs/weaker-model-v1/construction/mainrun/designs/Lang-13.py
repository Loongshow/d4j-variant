"""Main run Lang-13 (C10 recipe on the fixed checkout of Defects4J Lang-13; the real bug modified SerializationUtils, the target
class).

Facade: SerializationUtils.clone(T) (allowed target, BATCH4_PREREGISTRATION.md row Lang-13: clone / serialize / deserialize).
The two other allowed targets were set aside. serialize(Serializable[, OutputStream]) is a single ObjectOutputStream write with
no per-element decision (every omission there, such as the close that flushes the block buffer, fails a dozen tests at once,
and serialize(Serializable) is also reached by every clone test). deserialize(InputStream / byte[]) uses the JDK's default class
resolution, has no decision of its own, and is reached by AbstractExceptionContextTest (three subclasses), FastDateParserTest and
FastDatePrinterTest as well, so no omission there is caught by exactly one test. clone is the only target with a per-element
decision that exactly one existing test discriminates: the resolution of the class named by each class descriptor of the stream,
including the descriptors of the primitive types (int.class and so on), which Class.forName does not resolve.
Original computation of the facade: null gives null; otherwise the object is serialized to bytes, and the bytes are read back
through SerializationUtils.ClassLoaderAwareObjectInputStream, whose resolveClass tries the class loader of the object's class,
then the context class loader of the current thread, then a map of the nine primitive type names; ClassNotFoundException and
IOException are reported as SerializationException("ClassNotFoundException / IOException while reading cloned object data").

Chain (hosts in draw order for seed 3978, mr_lib preview, target org/apache/commons/lang3/SerializationUtils.java, none skipped):
  hop 1 builder.ToStringStyle.serialCopy        placement: serializes the object, passes the bytes and the class loader of the
                                                object's class, casts the copy to the object's type
  hop 2 text.StrBuilder.readObjectData          plumbing: wraps the bytes in a ByteArrayInputStream
  hop 3 time.DateUtils.readSerialData           plumbing: adds the context class loader of the current thread as the second
                                                class loader, reports ClassNotFoundException / IOException as SerializationException
  hop 4 StringUtils.readSingleObject            aggregation: opens the ObjectInputStream, sends the name of every class descriptor
                                                the stream reads to the gold, reads the single object and closes the stream
  hop 5 ArrayUtils.classNamed                   GOLD: the per-descriptor core, the class of one descriptor name (the primitive type
                                                names first, then the class loaders in the order given, the class not initialized)
The correct configuration returns the original result for every input: the same null guard, the same bytes, the same two class
loaders in the same order (Class.forName(name, false, loader)), the same nine primitive names (Class.forName never returns a
primitive class, so matching them before rather than after the class loaders changes no result), the same exception messages;
the ObjectInputStream over a ByteArrayInputStream cannot fail to close, so the original's separate close message is unreachable.

Fault (omission of a special-case step in the gold): the lookup of the primitive type names (one for statement) is dropped, so a
descriptor that names a primitive type goes to the class loaders, which cannot resolve it. Trigger: the EXISTING test
SerializationUtilsTest::testPrimitiveTypeClassSerialization (the real Defects4J Lang-13 trigger); clone(byte.class) fails with
SerializationException: ClassNotFoundException while reading cloned object data (cause ClassNotFoundException: byte). It is the
only test that serializes a Class object of a primitive type; testClone, CharSetTest, CharRangeTest, RangeTest and ObjectUtilsTest
clone objects whose descriptors name ordinary classes, and pass on the variant.

The gold's javadoc states the idiomatic contract (the class that a class descriptor read from an object stream names) and is
silent on primitive types; the descriptor of byte.class names "byte", whose class is byte.class, so the variant violates that
contract on the trigger input. External pins: SerializationUtils.ClassLoaderAwareObjectInputStream.resolveClass (the facade's
original resolution, still in the class) maps the nine primitive type names after both class loaders; ClassUtils.getClass maps the
raw primitive names to their classes (ClassUtilsTest::testGetClassRawPrimitives passes); SerializationUtils.deserialize reads with
the JDK ObjectInputStream, whose default class resolution maps the primitive type names as well.

Single owner: only the gold sees a descriptor name together with the means of resolving it; hops 1-3 hold the whole object, its
bytes or the stream, and hop 4 only passes each descriptor's name to the gold and receives a class or an exception. No choice of
class loaders at any hop resolves a primitive type name (Class.forName never returns a primitive class). Declared alternatives
(G9): hop 4 falls back to ClassUtils.getClass when the gold throws (ClassUtils has no name for void, so clone(void.class) still
fails); hop 3 passes the system class loader as the second class loader; hop 1 uses the context class loader for a class of the
bootstrap class loader. Hop 4 calls the gold from the resolveClass of its ObjectInputStream, once per class descriptor the
stream reads (the per-element loop is the stream's own), so the gold is the fifth method of the code base below the facade.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy,
defects4j test: 0 failing tests each; bypasses or test-fitted filters, not repairs):
 B-0 the facade (its original body) or any of hops 1-3 reads the copy with SerializationUtils.deserialize (the plain JDK
     ObjectInputStream), e.g. hop 2 `return org.apache.commons.lang3.SerializationUtils.deserialize(objectData);`, discarding the
     rest of the chain including the gold and both class loaders.
 B-1 hop 4's resolveClass returns `super.resolveClass(desc)` (the JDK's own resolution with its own class loader): the gold and
     both class loaders become dead.
 B-2 hop 4 wraps the gold's call and, when the gold throws, returns `super.resolveClass(desc)`
     (`try { return ArrayUtils.classNamed(...); } catch (final ClassNotFoundException ex) { return super.resolveClass(desc); }`):
     on the trigger input the gold's result is discarded and the class comes from a second implementation of its decision.
 B-3 test-fitted pre-filter: hop 1 returns a Class object of a primitive type as its own copy
     (`final T copy = object instanceof Class<?> && ((Class<?>) object).isPrimitive() ? object : (T) StrBuilder.readObjectData(...);`;
     the same test in the facade's guard behaves alike). It contradicts hop 1's documented copy through bytes, skips hops 2-5 on
     the trigger input, and a primitive type inside the graph still fails: clone(new Class<?>[] {String.class, int.class}) throws
     SerializationException caused by ClassNotFoundException: int (checked with a probe on the edited copy).

Lie: the facade's javadoc claims the object is first written to a temporary file in the directory named by java.io.tmpdir and the
copy is read back from that file; the chain writes and reads a byte array in memory and touches no file. It names neither class
resolution nor primitive types nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, the primitive-name loop, the class-loader loop, throw):
  T1 absent: name is compared with each primitive type's name and passed to Class.forName; classLoaders drives the second loop;
     both change the result.
  T2 absent: type is the first loop's element and decides its return; notFound starts null and is assigned in the class-loader
     loop, then thrown; classLoader is the loop element; ex is read into notFound; each if / try has two different outcomes.
  T3 absent: the primitive loop lists all nine Class objects of the primitive types (boolean, byte, char, short, int, long,
     float, double, void); no pair half, range end or named class is left out.
  T4 absent: the javadoc names the class a descriptor names, the order of the class loaders and that the class is not
     initialized; all are met.
 Variant gold (javadoc, signature, `ClassNotFoundException notFound = null;`, the loop over classLoaders with its try / catch,
 `throw notFound;`):
  T1 absent: name is passed to Class.forName on every iteration; classLoaders is the loop's array; each changes the returned
     class or the exception.
  T2 absent: notFound is initialised to null but assigned in the loop (`notFound = ex;`) and thrown after it; classLoader is the
     for-each element; ex reaches the thrown exception through notFound; the try returns on success and the catch records the
     failure (two different effects); no other local, branch, case or ternary.
  T3 absent: no special-case treatment of any member of any set remains (every name goes to every class loader in turn: 'No
     member handled'); the gold names no value class that it handles in part; no pair or range end.
  T4 absent: 'the class that a class descriptor read from an object stream names' and '@return the class of that name' are
     general descriptions that the loop addresses; 'tried in the order given' is met by the for-each; 'the class is not
     initialized' is met by the false argument; '@throws ClassNotFoundException if the class cannot be found' is met by the
     final throw of the last ClassNotFoundException; '@param ... not null or empty' is a caller precondition. No inline comment;
     the identifiers (classNamed, notFound, classLoader, ex) name nothing the body does not meet."""

SU = "src/main/java/org/apache/commons/lang3/SerializationUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"
STU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
AU = "src/main/java/org/apache/commons/lang3/ArrayUtils.java"

GOLD_TEXT = '''/**
 * <p>Finds the class that a class descriptor read from an object stream
 * names.</p>
 *
 * <p>The class loaders are tried in the order given, and the class is
 * not initialized.</p>
 *
 * @param name  the class name carried by the class descriptor, not null
 * @param classLoaders  the class loaders to try, not null or empty
 * @return the class of that name
 * @throws ClassNotFoundException if the class cannot be found
 */
public static Class<?> classNamed(final String name, final ClassLoader... classLoaders) throws ClassNotFoundException {
    for (final Class<?> type : new Class<?>[] {Boolean.TYPE, Byte.TYPE, Character.TYPE, Short.TYPE, Integer.TYPE,
            Long.TYPE, Float.TYPE, Double.TYPE, Void.TYPE}) {
        if (type.getName().equals(name)) {
            return type;
        }
    }
    ClassNotFoundException notFound = null;
    for (final ClassLoader classLoader : classLoaders) {
        try {
            return Class.forName(name, false, classLoader);
        } catch (final ClassNotFoundException ex) {
            notFound = ex;
        }
    }
    throw notFound;
}'''

HOP1 = '''/**
 * <p>Copies a {@code Serializable} object by serializing it to bytes and
 * reading the bytes back with the class loader of its class.</p>
 *
 * @param <T> the type of the object
 * @param object  the object to copy, not null
 * @return the copy
 */
public static <T extends Serializable> T serialCopy(final T object) {
    @SuppressWarnings("unchecked") // the copy is read back from the bytes of the object itself
    final T copy = (T) StrBuilder.readObjectData(SerializationUtils.serialize(object), object.getClass().getClassLoader());
    return copy;
}'''

HOP2 = '''/**
 * <p>Reads an object back from the bytes it was serialized to.</p>
 *
 * @param objectData  the serialized object, not null
 * @param classLoader  the class loader of the class of the serialized object
 * @return the object read
 */
public static Object readObjectData(final byte[] objectData, final ClassLoader classLoader) {
    return DateUtils.readSerialData(new ByteArrayInputStream(objectData), classLoader);
}'''

HOP3 = '''/**
 * <p>Reads a serialized object from a stream.</p>
 *
 * <p>The context class loader of the current thread is passed on as a
 * second class loader, and a failure to read the object is reported as
 * a {@code SerializationException}.</p>
 *
 * @param inputStream  the serialized object input stream, not null
 * @param classLoader  the class loader of the class of the serialized object
 * @return the object read
 * @throws SerializationException (runtime) if the object cannot be read
 */
public static Object readSerialData(final InputStream inputStream, final ClassLoader classLoader) {
    try {
        return StringUtils.readSingleObject(inputStream, classLoader, Thread.currentThread().getContextClassLoader());
    } catch (final ClassNotFoundException ex) {
        throw new SerializationException("ClassNotFoundException while reading cloned object data", ex);
    } catch (final IOException ex) {
        throw new SerializationException("IOException while reading cloned object data", ex);
    }
}'''

HOP4 = '''/**
 * <p>Reads a single object from an object stream, finding the class of
 * each class descriptor in the stream from the name it carries.</p>
 *
 * <p>The stream is closed once the object is read.</p>
 *
 * @param inputStream  the serialized object input stream, not null
 * @param classLoader  the class loader to try first for a class
 * @param contextLoader  the class loader to try next for a class
 * @return the object read
 * @throws IOException if the stream cannot be read
 * @throws ClassNotFoundException if the class of a class descriptor cannot be found
 */
public static Object readSingleObject(final InputStream inputStream, final ClassLoader classLoader,
        final ClassLoader contextLoader) throws IOException, ClassNotFoundException {
    final ObjectInputStream in = new ObjectInputStream(inputStream) {
        @Override
        protected Class<?> resolveClass(final ObjectStreamClass desc) throws IOException, ClassNotFoundException {
            return ArrayUtils.classNamed(desc.getName(), classLoader, contextLoader);
        }
    };
    try {
        return in.readObject();
    } finally {
        in.close();
    }
}'''

FAULT_OLD = ("        for (final Class<?> type : new Class<?>[] {Boolean.TYPE, Byte.TYPE, Character.TYPE, Short.TYPE, Integer.TYPE,\n"
             "                Long.TYPE, Float.TYPE, Double.TYPE, Void.TYPE}) {\n"
             "            if (type.getName().equals(name)) {\n"
             "                return type;\n"
             "            }\n"
             "        }\n"
             "        ClassNotFoundException notFound = null;")
FAULT_NEW = "        ClassNotFoundException notFound = null;"

DESIGN = {
 "instance": "Lang-13", "project": "Lang", "bug_id": 13, "seed": 3978,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": SU, "class": "org.apache.commons.lang3.SerializationUtils", "method": "clone", "near_line": 78},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/SerializationUtilsTest.java",
             "test_class": "org.apache.commons.lang3.SerializationUtilsTest",
             "test_method": "testPrimitiveTypeClassSerialization"},
 "expected_signature": "SerializationException: ClassNotFoundException while reading cloned object data",
 "gold": {"method": "classNamed", "text": GOLD_TEXT, "fault": {"old": FAULT_OLD, "new": FAULT_NEW}},
 "chain": {
   "facade_body": "if (object == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.lang3.builder.ToStringStyle.serialCopy(object);",
   "lie": "The object is first written to a temporary file in the directory named by the {@code java.io.tmpdir} system "
          "property, and the copy is then read back from that file.",
   "hops": [
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "serialCopy",
      "imports": ["org.apache.commons.lang3.SerializationUtils", "org.apache.commons.lang3.text.StrBuilder"], "text": HOP1},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "readObjectData",
      "imports": ["java.io.ByteArrayInputStream", "org.apache.commons.lang3.time.DateUtils"], "text": HOP2},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "readSerialData",
      "imports": ["java.io.IOException", "java.io.InputStream", "org.apache.commons.lang3.SerializationException",
                  "org.apache.commons.lang3.StringUtils"], "text": HOP3},
     {"file": STU, "class": "org.apache.commons.lang3.StringUtils", "method": "readSingleObject",
      "imports": ["java.io.IOException", "java.io.InputStream", "java.io.ObjectInputStream", "java.io.ObjectStreamClass"],
      "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang3.ArrayUtils", "method": "classNamed", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.SerializationUtils.ClassLoaderAwareObjectInputStream::resolveClass",
              "org.apache.commons.lang3.ClassUtils::getClass",
              "org.apache.commons.lang3.SerializationUtils::deserialize"],
 "ownership_reason": "Only the gold sees the name of a class descriptor together with the means of resolving it; hops 1-3 hold "
                     "the whole object, its bytes or the stream, and hop 4 only passes the name of each descriptor to the gold "
                     "(from the resolveClass of its ObjectInputStream, once per class descriptor the stream reads) and receives "
                     "a class or an exception. No choice of class loaders at any hop can resolve a primitive type "
                     "name, because Class.forName never returns a primitive class. The gold's javadoc promises the class that a "
                     "class descriptor read from an object stream names; the descriptor of byte.class names \"byte\", whose "
                     "class is byte.class. The convention is pinned outside the gold: SerializationUtils' own "
                     "ClassLoaderAwareObjectInputStream.resolveClass (the facade's original resolution) maps the nine primitive "
                     "type names after both class loaders; ClassUtils.getClass maps the raw primitive names to their classes "
                     "(ClassUtilsTest testGetClassRawPrimitives); SerializationUtils.deserialize reads with the JDK "
                     "ObjectInputStream, whose default class resolution maps the primitive type names too. A fallback at hop 4 "
                     "to ClassUtils.getClass still fails on void.class (ClassUtils has no name for void); a fallback to the "
                     "JDK's own resolveClass replaces the gold's result with a second implementation of its decision. A "
                     "pre-filter at hop 1 (or in the facade's guard) that returns a Class object of a primitive type as its own "
                     "copy passes the existing tests, but it contradicts hop 1's documented copy through bytes and still fails "
                     "for a primitive type inside the object graph: clone(new Class<?>[] {String.class, int.class}) throws "
                     "SerializationException caused by ClassNotFoundException: int.",
 "ownership_tests": ["org.apache.commons.lang3.ClassUtilsTest::testGetClassRawPrimitives",
                     "org.apache.commons.lang3.SerializationUtilsTest::testClone",
                     "org.apache.commons.lang3.CharSetTest::testSerialization",
                     "org.apache.commons.lang3.RangeTest::testSerializing"],
 "compensating": {
   "chain": [
     {"file": STU, "old": "                return ArrayUtils.classNamed(desc.getName(), classLoader, contextLoader);",
      "new": "                try { return ArrayUtils.classNamed(desc.getName(), classLoader, contextLoader); } "
             "catch (final ClassNotFoundException ex) { return ClassUtils.getClass(classLoader, desc.getName(), false); }",
      "why": "hop 4 falls back to ClassUtils.getClass when no class loader finds the class"},
     {"file": DU, "old": "            return StringUtils.readSingleObject(inputStream, classLoader, Thread.currentThread().getContextClassLoader());",
      "new": "            return StringUtils.readSingleObject(inputStream, classLoader, ClassLoader.getSystemClassLoader());",
      "why": "hop 3 passes the system class loader as the second class loader"},
     {"file": TSS, "old": "        final T copy = (T) StrBuilder.readObjectData(SerializationUtils.serialize(object), object.getClass().getClassLoader());",
      "new": "        final T copy = (T) StrBuilder.readObjectData(SerializationUtils.serialize(object), object.getClass().getClassLoader() == null ? Thread.currentThread().getContextClassLoader() : object.getClass().getClassLoader());",
      "why": "hop 1 uses the context class loader for a class of the bootstrap class loader"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 3978 (mr_lib preview, target org/apache/commons/lang3/SerializationUtils.java): "
               "builder.ToStringStyle (hop 1), text.StrBuilder (hop 2), time.DateUtils (hop 3), StringUtils (hop 4), "
               "ArrayUtils (hop 5, gold; the last remaining host of the five-class pool). All five are public top-level classes "
               "in which a static method compiles (ToStringStyle is abstract, which does not affect a static method); every "
               "preview anchor lies in the outer class; none was skipped. The facade calls hop 1 by its fully-qualified name; "
               "each hop imports the next host and the java.io types it uses (hop 4 and the gold share the lang3 package).",
}
