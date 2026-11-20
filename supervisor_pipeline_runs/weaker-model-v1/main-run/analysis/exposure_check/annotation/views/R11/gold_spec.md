# Run R11: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.cli.Parser::convertValue`
- Gold file in the workspace: `src/main/java/org/apache/commons/cli/Parser.java` (lines 97–137)
- Method the failing test calls (facade): `org.apache.commons.cli.TypeHandler::createValue`
- Failing test: `org.apache.commons.cli.TypeHandlerTest::testCreateValueInteger_failure`
- Text removed from the gold (the omission): `value = TypeHandler.createURL(str);         }         else         {             throw new ParseException("Unable to handle the class: " + clazz);         }         return value;`
- The same place in the variant now reads: `value = TypeHandler.createURL(str);         }         return value;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
   97        public static Object convertValue(final String str, final Class<?> clazz) throws ParseException
   98        {
   99            Object value = null;
  100            if (PatternOptionBuilder.STRING_VALUE == clazz)
  101            {
  102                value = str;
  103            }
  104            else if (PatternOptionBuilder.OBJECT_VALUE == clazz)
  105            {
  106                value = TypeHandler.createObject(str);
  107            }
  108            else if (PatternOptionBuilder.NUMBER_VALUE == clazz)
  109            {
  110                value = TypeHandler.createNumber(str);
  111            }
  112            else if (PatternOptionBuilder.DATE_VALUE == clazz)
  113            {
  114                value = TypeHandler.createDate(str);
  115            }
  116            else if (PatternOptionBuilder.CLASS_VALUE == clazz)
  117            {
  118                value = TypeHandler.createClass(str);
  119            }
  120            else if (PatternOptionBuilder.FILE_VALUE == clazz)
  121            {
  122                value = TypeHandler.createFile(str);
  123            }
  124            else if (PatternOptionBuilder.EXISTING_FILE_VALUE == clazz)
  125            {
  126                value = TypeHandler.openFile(str);
  127            }
  128            else if (PatternOptionBuilder.FILES_VALUE == clazz)
  129            {
  130                value = TypeHandler.createFiles(str);
  131            }
  132            else if (PatternOptionBuilder.URL_VALUE == clazz)
  133            {
  134 >>             value = TypeHandler.createURL(str);
  135            }
  136 >>         return value;
  137        }
```
