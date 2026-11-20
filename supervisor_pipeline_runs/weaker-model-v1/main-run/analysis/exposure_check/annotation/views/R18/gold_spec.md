# Run R18: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `com.fasterxml.jackson.databind.ObjectMapper::typeWithParameters`
- Gold file in the workspace: `src/main/java/com/fasterxml/jackson/databind/ObjectMapper.java` (lines 1629–1634)
- Method the failing test calls (facade): `com.fasterxml.jackson.databind.type.TypeFactory::constructParametrizedType`
- Failing test: `com.fasterxml.jackson.databind.type.TestTypeFactory::testParametricTypes`
- Text removed from the gold (the omission): `if (Map.class.isAssignableFrom(raw)) return factory.constructMapType((Class<Map<?,?>>) raw, parameterTypes[0], parameterTypes[1]);         if (Collection.class.isAssignableFrom(raw)) return factory.constructCollectionType((Class<Collection<?>>) raw, parameterTypes[0]);`
- The same place in the variant now reads: `if (Map.class.isAssignableFrom(raw)) return factory.constructMapType((Class<Map<?,?>>) raw, parameterTypes[0], parameterTypes[1]);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1629        public static JavaType typeWithParameters(TypeFactory factory, Class<?> raw, Class<?> parametersFor,
 1630                JavaType[] parameterTypes)
 1631        {
 1632 >>         if (Map.class.isAssignableFrom(raw)) return factory.constructMapType((Class<Map<?,?>>) raw, parameterTypes[0], parameterTypes[1]);
 1633            return factory.constructSimpleType(raw, parametersFor, parameterTypes);
 1634        }
```
