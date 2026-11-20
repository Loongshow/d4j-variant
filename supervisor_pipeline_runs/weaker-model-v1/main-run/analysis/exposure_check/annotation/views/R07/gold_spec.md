# Run R07: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `com.google.gson.JsonPrimitive::typeAssignedTo`
- Gold file in the workspace: `gson/src/main/java/com/google/gson/JsonPrimitive.java` (lines 401–413)
- Method the failing test calls (facade): `com.google.gson.TypeInfoFactory::getTypeInfoForField`
- Failing test: `com.google.gson.functional.TypeVariableTest::testSingle`
- Text removed from the gold (the omission): `while (rawParentClass != null && rawParentClass != variable.getGenericDeclaration()) {         parentType = rawParentClass.getGenericSuperclass();         rawParentClass = rawParentClass.getSuperclass();       }       if (parentType instanceof ParameterizedType) {         TypeVariable<?>[] variables = rawParentClass.getTypeParameters();`
- The same place in the variant now reads: `if (parentType instanceof ParameterizedType) {         TypeVariable<?>[] variables = rawParentClass.getTypeParameters();`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  401        public static Type typeAssignedTo(TypeVariable<?> variable, Type parentType,
  402            Class<?> rawParentClass) {
  403 >>       if (parentType instanceof ParameterizedType) {
  404 >>         TypeVariable<?>[] variables = rawParentClass.getTypeParameters();
  405            Type[] arguments = ((ParameterizedType) parentType).getActualTypeArguments();
  406            for (int i = 0; i < variables.length; i++) {
  407              if (variables[i].equals(variable)) {
  408                return arguments[i];
  409              }
  410            }
  411          }
  412          return variable;
  413        }
```
