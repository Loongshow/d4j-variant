# Run R25: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `com.fasterxml.jackson.databind.ObjectMapper::standardDeserializerFor`
- Gold file in the workspace: `src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java` (lines 969–984)
- Method the failing test calls (facade): `com.fasterxml.jackson.databind.deser.std.JdkDeserializers::find`
- Failing test: `com.fasterxml.jackson.databind.deser.jdk.JDKStringLikeTypesTest::testByteBuffer`
- Text removed from the gold (the omission): `return new AtomicBooleanDeserializer();         }         if (rawType == java.nio.ByteBuffer.class) {             return new com.fasterxml.jackson.databind.deser.std.ByteBufferDeserializer();         }         if (rawType == Void.class) {`
- The same place in the variant now reads: `return new AtomicBooleanDeserializer();         }         if (rawType == Void.class) {`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  969        public static JsonDeserializer<?> standardDeserializerFor(Class<?> rawType)
  970        {
  971            if (rawType == UUID.class) {
  972                return new UUIDDeserializer();
  973            }
  974            if (rawType == StackTraceElement.class) {
  975                return new StackTraceElementDeserializer();
  976            }
  977            if (rawType == AtomicBoolean.class) {
  978 >>             return new AtomicBooleanDeserializer();
  979            }
  980 >>         if (rawType == Void.class) {
  981                return NullifyingDeserializer.instance;
  982            }
  983            return null;
  984        }
```
