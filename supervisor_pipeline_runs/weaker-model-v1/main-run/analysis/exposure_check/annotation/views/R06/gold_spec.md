# Run R06: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.lang3.StringUtils::conformsTo`
- Gold file in the workspace: `src/main/java/org/apache/commons/lang3/StringUtils.java` (lines 1659–1686)
- Method the failing test calls (facade): `org.apache.commons.lang3.reflect.TypeUtils::typesSatisfyVariables`
- Failing test: `org.apache.commons.lang3.reflect.TypeUtilsTest::testTypesSatisfyVariables`
- Text removed from the gold (the omission): `Type fromTypeArg = TypeUtils.unrollVariableAssignments(var, fromTypeVarAssigns);             if (fromTypeArg == null) {                 continue;             }`
- The same place in the variant now reads: `Type fromTypeArg = TypeUtils.unrollVariableAssignments(var, fromTypeVarAssigns);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1659        public static boolean conformsTo(Type type, ParameterizedType toParameterizedType,
 1660                Map<TypeVariable<?>, Type> typeVarAssigns) {
 1661            if (type == null || toParameterizedType.equals(type)) {
 1662                return true;
 1663            }
 1664            Class<?> toClass = TypeUtils.getRawType(toParameterizedType, null);
 1665            Map<TypeVariable<?>, Type> fromTypeVarAssigns = TypeUtils.getTypeArguments(type, toClass);
 1666            if (fromTypeVarAssigns == null) {
 1667                return false;
 1668            }
 1669            if (fromTypeVarAssigns.isEmpty()) {
 1670                return true;
 1671            }
 1672            Map<TypeVariable<?>, Type> toTypeVarAssigns = TypeUtils.getTypeArguments(toParameterizedType, toClass,
 1673                    typeVarAssigns);
 1674            for (TypeVariable<?> var : toTypeVarAssigns.keySet()) {
 1675                Type toTypeArg = TypeUtils.unrollVariableAssignments(var, toTypeVarAssigns);
 1676 >>             Type fromTypeArg = TypeUtils.unrollVariableAssignments(var, fromTypeVarAssigns);
 1677                if (toTypeArg.equals(fromTypeArg)) {
 1678                    continue;
 1679                }
 1680                if (toTypeArg instanceof WildcardType && TypeUtils.isAssignable(fromTypeArg, toTypeArg, typeVarAssigns)) {
 1681                    continue;
 1682                }
 1683                return false;
 1684            }
 1685            return true;
 1686        }
```
