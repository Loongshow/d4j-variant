# Run R44: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.joda.time.format.DateTimeFormatterBuilder::javaDayStart`
- Gold file in the workspace: `src/main/java/org/joda/time/format/DateTimeFormatterBuilder.java` (lines 794–803)
- Method the failing test calls (facade): `org.joda.time.LocalDate::toDate`
- Failing test: `org.joda.time.TestLocalDate_Basics::testToDate_springDST_2Hour40Savings`
- Text removed from the gold (the omission): `start.setTime(start.getTime() + 3600000);         }         while (LocalDate.fromDateFields(new Date(start.getTime() - 1000)).equals(day)) {             start.setTime(start.getTime() - 1000);         }`
- The same place in the variant now reads: `start.setTime(start.getTime() + 3600000);         }`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  794        @SuppressWarnings("deprecation")
  795        public static Date javaDayStart(int year, int month, int dom) {
  796            Date start = new Date(year, month, dom, 12, 0, 0);
  797            LocalDate day = LocalDate.fromDateFields(start);
  798            start.setTime(start.getTime() - 86400000);
  799            while (LocalDate.fromDateFields(start).equals(day) == false) {
  800 >>             start.setTime(start.getTime() + 3600000);
  801            }
  802            return start;
  803        }
```
