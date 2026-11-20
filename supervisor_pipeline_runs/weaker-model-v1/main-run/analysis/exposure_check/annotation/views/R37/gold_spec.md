# Run R37: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.joda.time.Period::zoneForOffset`
- Gold file in the workspace: `src/main/java/org/joda/time/Period.java` (lines 237–265)
- Method the failing test calls (facade): `org.joda.time.DateTimeZone::forID`
- Failing test: `org.joda.time.TestDateTimeZone::testForID_String`
- Text removed from the gold (the omission): `rest -= seconds * DateTimeConstants.MILLIS_PER_SECOND;             if (rest != 0) {                 buf.append('.');                 FormatUtils.appendPaddedInteger(buf, rest, 3);             }         }`
- The same place in the variant now reads: `rest -= seconds * DateTimeConstants.MILLIS_PER_SECOND;             buf.append('.');             FormatUtils.appendPaddedInteger(buf, rest, 3);         }`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  237        public static DateTimeZone zoneForOffset(int offset) {
  238            StringBuffer buf = new StringBuffer();
  239            int rest = offset;
  240            if (rest >= 0) {
  241                buf.append('+');
  242 >>         } else {
  243                buf.append('-');
  244                rest = -rest;
  245            }
  246    
  247            int hours = rest / DateTimeConstants.MILLIS_PER_HOUR;
  248            FormatUtils.appendPaddedInteger(buf, hours, 2);
  249            rest -= hours * DateTimeConstants.MILLIS_PER_HOUR;
  250    
  251            int minutes = rest / DateTimeConstants.MILLIS_PER_MINUTE;
  252            buf.append(':');
  253            FormatUtils.appendPaddedInteger(buf, minutes, 2);
  254            rest -= minutes * DateTimeConstants.MILLIS_PER_MINUTE;
  255    
  256            if (rest != 0) {
  257                int seconds = rest / DateTimeConstants.MILLIS_PER_SECOND;
  258                buf.append(':');
  259                FormatUtils.appendPaddedInteger(buf, seconds, 2);
  260 >>             rest -= seconds * DateTimeConstants.MILLIS_PER_SECOND;
  261 >>             buf.append('.');
  262 >>             FormatUtils.appendPaddedInteger(buf, rest, 3);
  263            }
  264            return DateTimeZone.fixedOffsetZone(buf.toString(), offset);
  265        }
```
