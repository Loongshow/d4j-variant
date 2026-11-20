"""Main run Lang-55__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J Lang-55;
the real bug modified org.apache.commons.lang.time.StopWatch, the facade's class). No static pair (B8 note section 1: pool v2 found no
strictly tested public static method in StopWatch).

Facade: StopWatch.getTime() (the only allowed candidate of batch8_tasks.json / BATCH8_PREREGISTRATION.md row 278;
facade_planned_by = null, no facade reuse).
Original computation of the facade: a stopped or suspended watch reads stopTime - startTime; an unstarted watch reads 0; a running watch
reads System.currentTimeMillis() - startTime; any other state code throws RuntimeException("Illegal running state has occured. ").
Field facts the chain relies on (all from StopWatch's own code): startTime and stopTime are -1 when the watch is constructed and after
reset(); start() sets stopTime = -1 and the start time; split() records the split time in stopTime while the watch keeps running;
unsplit() and resume() set stopTime = -1 again; stop() and suspend() record stopTime; runningState is private and is only ever assigned
one of the four STATE_* constants, so the illegal-state throw is unreachable.

facade_variant: V1 (state as parameters). The facade reads the private fields startTime and stopTime and the private field
runningState, compared with the private constant STATE_RUNNING (the hops cannot see the private constants, so this one comparison stays
in the facade), and passes the two long values and the boolean to hop 1; it returns hop 1's result; no field is written (no
write-back). No private method is called (no V4), no package-private type is involved (no V3/V5), the receiver is not passed (no V2).
No visibility is widened, no type is added, no signature, modifier, override or throws change, no reflection, no test edit. The
unreachable illegal-state throw is not carried over (no reachable state reaches it).
state_passed: private fields startTime and stopTime (long values, exactly as the watch recorded them) and runningState == STATE_RUNNING
(boolean) to hop 1; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Lang-55-probe/w of the fixture, the
first statement of getTime() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.apache.commons.lang.time.StopWatchTest::testStopWatchSimpleGet`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at StopWatch.getTime(StopWatch.java:211) from StopWatchTest.testStopWatchSimpleGet(StopWatchTest.java:64);
`-t ...StopWatchTest::testLang315`: 1 failing test (the same probe). The facade's only production caller is StopWatch.toString(); the
facade is reached by existing tests directly (all five StopWatchTest methods that read the time).

Hosts (host_mode = "1500"; mr_lib.py preview Lang-55 org/apache/commons/lang/time/StopWatch.java 5, instance seed 7676, used in draw
order, none substituted):
  hop 1 text.StrBuilder        2712 lines  timeOnWatch    pass-through
  hop 2 builder.ToStringStyle  2252 lines  watchTime      pass-through
  hop 3 time.FastDateFormat    1752 lines  elapsedMillis  pass-through (the smallest host)
  hop 4 StringUtils            5062 lines  timeElapsed    pass-through
  hop 5 ArrayUtils             4417 lines  elapsedTime    GOLD: the time recorded from the start mark to the stop mark (never less
                                                          than zero), and, while the watch is live, the time from the last mark
                                                          the watch passed to the current time
Host sizes 2712, 2252, 1752, 5062, 4417; the smallest host is FastDateFormat (1752 lines); the gold host has 4417 lines.

Redistribution: the state decision of the original (halted / unstarted / running) becomes the boolean live plus the gold's arithmetic.
The gold reads a watch as "the time recorded up to the stop mark, plus, while live, the time since the last mark": a recorded part
stop - start (an unstarted watch has start == stop == -1 and reads 0; a stop mark that lies before the start mark, as a running watch
without a split records it, records nothing and the watch has then run since its start mark), and a live part now - (last mark), where
the last mark is the stop (split) mark, or the start mark when nothing is recorded. The correct chain returns the original value for
every reachable state: stopped / suspended (stop >= start) -> stop - start; unstarted -> 0; running without a split (stop = -1) ->
0 + now - start; running with a split mark -> (split - start) + (now - split) = now - start.

The marks travel unchanged: every method on the path (hops 1-4 and the gold) documents its start and stop parameters as the marks "as
the watch recorded" them, and the facade passes the two private fields themselves. So the stop mark a running watch without a split
carries down the chain is the value StopWatch recorded for it (start(), unsplit() and resume() record -1), and no method above the gold
may hand down another value in its place.

Fault (one-line omission of a special-case step in the gold): in the branch for a stop mark before the start mark, the statement that
moves the last mark to the start mark (`stop = start;`) is dropped; the branch still clears the recorded part. The gold then reads as the
ordinary routine "recorded time, never negative, plus the time since the stop mark while live". A running watch without a split mark
(recorded stop = -1) then reads now - (-1) = now + 1 (about 1.7e12 ms) instead of now - start. Trigger: the EXISTING test
StopWatchTest::testStopWatchSimpleGet, the only test that reads a running watch: its first two assertions (0 and "0:00:00.000" for an
unstarted watch) hold, and assertTrue(watch.getTime() < 2000) at line 69 fails deterministically (the reading is the epoch clock).
Every other reading in the suite is of a halted or unstarted watch (testStopWatchSimple, testStopWatchSplit, testStopWatchSuspend,
testLang315: stop >= start, the omitted statement is not reached; reset/unstarted: start == stop == -1, the recorded part is 0 and the
watch is not live), and StopWatch has no other caller, so the trigger is the only test that newly fails.

The gold's javadoc states the idiomatic contract (the time from the start mark to the stop mark, or, while the watch is live, to the
current time) and is silent on how a stop mark before the start mark is treated; now + 1 is not the time from the start mark to the
current time. The convention is pinned outside the gold: StopWatch.unsplit ("This method clears the stop time. The start time is
unaffected, enabling timing from the original start point to continue."), StopWatch.start (stopTime = -1 when a timing session starts:
a running watch has no stop mark and is timed from its start) and StopWatch.resume (stopTime = -1 after the start time is moved on by
the suspended interval), with the passing tests StopWatchTest::testStopWatchSplit (split, unsplit, then the total time from the original
start, 1500-1900 ms), testStopWatchSuspend and testLang315; the facade's own javadoc ("the time between the start and the moment this
method is called") is kept.

Single owner: hops 1-4 pass the two recorded marks and the flag along unchanged; only the gold computes. Declared alternatives (G9),
none of which absorbs the fault: hop 1 answers a watch without a start mark with 0; hop 2 passes a stop mark below zero as 0 (the live
part is then now - 0, still the epoch clock); hop 3 counts a watch as live only once it has a start mark; hop 4 never returns less than
zero. Edits that pass the trigger but do not keep the path's methods used as documented (recorded, not repairs):
 B-1 a hop (or the facade) passes Math.max(start, stop) / the start mark in place of the recorded stop mark: the gold and every hop
     take the stop mark "as the watch recorded it", so a substituted value departs from the documented parameter of the next method
     (and it pre-empts the gold's own handling of a stop mark before the start mark). Trigger passes when hop 4 does this.
 B-2 a hop (or the facade) passes live = false for a running watch without a split mark: the running watch then reads 0, which
     testStopWatchSimpleGet's weak bound (< 2000) accepts, but it contradicts "true if the watch is running" and every @return.
 B-3 hop 4 returns Math.min(gold, System.currentTimeMillis() - start), or the facade's original body / a hop computing
     System.currentTimeMillis() - start itself for a live watch: it replaces the gold's result for a live watch with its own
     computation (a bypass).
 B-4 StopWatch.start() records the start time as the stop mark: the running watch after start() then reads correctly, but unsplit()
     and resume() still record -1, so a running watch after either reads now + 1 against getTime's documented contract; it is an edit
     of an evidence method that leaves the documented behaviour violated, not a repair of the reading.

Lie: the facade's javadoc claims the time is read from the system clock in nanoseconds and rounded half up to the nearest millisecond;
the chain reads System.currentTimeMillis() and rounds nothing. It names neither the marks' handling, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (elapsed = stop - start; if elapsed < 0 { elapsed = 0; stop = start; } if live { elapsed += now - stop; } return):
  T1 absent: start seeds elapsed and replaces stop in the branch; stop seeds elapsed and is the base of the live part; live decides the
     live part; no argument check.
  T2 absent: elapsed is reassigned in both decisions and returned; the reassigned parameter stop is read by the live part; no
     literal-initialised local; no loop; both decisions change the result.
  T3 absent: the branch resets both values derived from the stop mark (the recorded part and the base of the live part); start and
     stop enter the one difference symmetrically and are documented alike; no enum, type code or named class.
  T4 absent: the javadoc's two cases (to the stop mark; while live, to the current time) are each addressed by a line; "as the watch
     recorded it" on both @param lines says what the caller supplies (a caller description, not a rule the gold enforces); no
     comment; identifiers name what they hold.
 Variant gold (javadoc, signature, `long elapsed = stop - start;`, `if (elapsed < 0) { elapsed = 0; }`, `if (live) { elapsed +=
 System.currentTimeMillis() - stop; }`, `return elapsed;`):
  T1 absent: start and stop both enter the recorded difference stop - start, stop is also the base of the live part, and live decides
     whether the live part is added; none is unused, overwritten before use or only argument-checked.
  T2 absent: elapsed is initialised from stop - start (not a literal), reassigned by the zero decision and by the live part, and
     returned; there is no other local, no loop, cursor, counter, flag or best-so-far; the zero decision and the live decision each
     change the returned value (no empty or duplicate branch).
  T3 absent: the two marks (the two ends of the timing) both take part in the recorded difference, which is the only quantity the zero
     decision treats; neither end gets a clamp, sign test or check that the other lacks; both @param lines read alike; no enum, type
     code or format is named; the gold's text names no value class ("finite", "positive", "missing", "-1") that it would handle in
     part.
  T4 absent: "the time on a watch, in milliseconds, from its start mark to its stop mark" is a general description addressed by
     stop - start; "While the watch is live the time is taken to the current time instead" is addressed by the live branch, which adds
     System.currentTimeMillis() - stop; @param start / stop ("the start / stop mark of the watch, as the watch recorded it") describe
     what the caller supplies, @param live ("true if the watch is running") and @return ("the time in milliseconds") name no concrete
     rule, limit or value class; no inline comment; the identifiers elapsed and live name what they hold."""

SW = "src/java/org/apache/commons/lang/time/StopWatch.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
SU = "src/java/org/apache/commons/lang/StringUtils.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"

GOLD_TEXT = '''/**
 * <p>Gets the time on a watch, in milliseconds, from its start mark
 * to its stop mark.</p>
 *
 * <p>While the watch is live the time is taken to the current time
 * instead.</p>
 *
 * @param start  the start mark of the watch, as the watch recorded it
 * @param stop  the stop mark of the watch, as the watch recorded it
 * @param live  <code>true</code> if the watch is running
 * @return the time in milliseconds
 */
public static long elapsedTime(long start, long stop, boolean live) {
    long elapsed = stop - start;
    if (elapsed < 0) {
        elapsed = 0;
        stop = start;
    }
    if (live) {
        elapsed += System.currentTimeMillis() - stop;
    }
    return elapsed;
}'''

HOP1 = '''/**
 * Gets the time on a watch, in milliseconds, from its start mark to its
 * stop mark, or to the current time while the watch is live.
 *
 * @param start  the start mark of the watch, as recorded
 * @param stop  the stop mark of the watch, as recorded
 * @param live  true if the watch is running
 * @return the time in milliseconds
 */
public static long timeOnWatch(long start, long stop, boolean live) {
    return ToStringStyle.watchTime(start, stop, live);
}'''

HOP2 = '''/**
 * <p>Gets the time on a watch, in milliseconds, from its start mark
 * to its stop mark, or to the current time while the watch is live.</p>
 *
 * @param start  the start mark of the watch, as recorded
 * @param stop  the stop mark of the watch, as recorded
 * @param live  <code>true</code> if the watch is running
 * @return the time in milliseconds
 */
public static long watchTime(long start, long stop, boolean live) {
    return FastDateFormat.elapsedMillis(start, stop, live);
}'''

HOP3 = '''/**
 * <p>Gets the elapsed time of a watch, in milliseconds, from its start
 * mark to its stop mark, or to the current time while the watch is live.</p>
 *
 * @param start  the start mark of the watch, as the watch recorded it
 * @param stop  the stop mark of the watch, as the watch recorded it
 * @param live  true if the watch is running
 * @return the elapsed time in milliseconds
 */
public static long elapsedMillis(long start, long stop, boolean live) {
    return StringUtils.timeElapsed(start, stop, live);
}'''

HOP4 = '''/**
 * <p>Gets the time elapsed on a watch, in milliseconds, from its start
 * mark to its stop mark, or to the current time while the watch is live.</p>
 *
 * @param start  the start mark of the watch, as the watch recorded it
 * @param stop  the stop mark of the watch, as the watch recorded it
 * @param live  <code>true</code> if the watch is running
 * @return the time elapsed in milliseconds
 */
public static long timeElapsed(long start, long stop, boolean live) {
    return ArrayUtils.elapsedTime(start, stop, live);
}'''

DESIGN = {
 "instance": "Lang-55", "project": "Lang", "bug_id": 55, "seed": 7676,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": SW, "class": "org.apache.commons.lang.time.StopWatch", "method": "getTime", "near_line": 210},
 "facade_variant": "V1",
 "state_passed": "private fields startTime and stopTime (long values, as recorded) and runningState == STATE_RUNNING (boolean; the "
                 "private constant is compared in the facade) to hop 1; no write-back",
 "reachability_probe": "getTime() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Lang-55-probe/w: testStopWatchSimpleGet fails with java.lang.IllegalStateException: "
                       "PROBE-REACHED at StopWatch.getTime(StopWatch.java:211) from StopWatchTest.java:64; testLang315 also fails "
                       "with the probe",
 "host_mode": "1500",
 "host_lines": [2712, 2252, 1752, 5062, 4417],
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/time/StopWatchTest.java",
             "test_class": "org.apache.commons.lang.time.StopWatchTest", "test_method": "testStopWatchSimpleGet"},
 "expected_signature": "StopWatchTest.testStopWatchSimpleGet(StopWatchTest.java:69)",
 "gold": {"method": "elapsedTime", "text": GOLD_TEXT,
          "fault": {"old": "            elapsed = 0;\n"
                           "            stop = start;\n"
                           "        }\n",
                    "new": "            elapsed = 0;\n"
                           "        }\n"}},
 "chain": {
   "facade_body": "return org.apache.commons.lang.text.StrBuilder.timeOnWatch(this.startTime, this.stopTime,\n"
                  "                this.runningState == STATE_RUNNING);",
   "lie": "The time is read from the system clock in nanoseconds and rounded half up to the nearest millisecond.",
   "hops": [
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "timeOnWatch",
      "imports": ["org.apache.commons.lang.builder.ToStringStyle"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "watchTime",
      "imports": ["org.apache.commons.lang.time.FastDateFormat"], "text": HOP2},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "elapsedMillis",
      "imports": ["org.apache.commons.lang.StringUtils"], "text": HOP3},
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "timeElapsed", "imports": [], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "elapsedTime", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.time.StopWatch::unsplit",
              "org.apache.commons.lang.time.StopWatch::start",
              "org.apache.commons.lang.time.StopWatch::resume"],
 "ownership_reason": "Only the gold computes the time on the watch: the recorded part from the start mark to the stop mark (never "
                     "less than zero) and, while the watch is live, the part from the last mark the watch passed to the current "
                     "time; hops 1-4 pass the start mark, the stop mark and the live flag along unchanged, and the facade only "
                     "gathers the two private marks and compares the private running state with STATE_RUNNING. The gold's javadoc "
                     "promises the time from the start mark to the current time while the watch is live, which now + 1 is not for "
                     "a running watch without a split mark. The convention that a running watch without a stop mark is timed from "
                     "its start mark is pinned outside the gold: StopWatch.unsplit ('clears the stop time. The start time is "
                     "unaffected, enabling timing from the original start point to continue'), StopWatch.start (stopTime = -1 when "
                     "a timing session starts) and StopWatch.resume (stopTime = -1 once the start time is moved on), with "
                     "StopWatchTest testStopWatchSplit (after unsplit the total runs from the original start, 1500-1900 ms), "
                     "testStopWatchSuspend and testLang315 passing. The gold and every hop take the start and stop marks 'as the "
                     "watch recorded' them, and the facade passes the two fields themselves, so the stop mark that reaches the gold "
                     "for a running watch without a split is the recorded one; a method above the gold that hands down another "
                     "value in its place (for example the start mark) no longer uses the next method as documented, and no "
                     "one-line change of the flag above the gold restores the time while staying consistent with the documentation.",
 "ownership_tests": ["org.apache.commons.lang.time.StopWatchTest::testStopWatchSplit",
                     "org.apache.commons.lang.time.StopWatchTest::testStopWatchSuspend",
                     "org.apache.commons.lang.time.StopWatchTest::testLang315"],
 "compensating": {
   "chain": [
     {"file": SB, "old": "return ToStringStyle.watchTime(start, stop, live);",
      "new": "return start < 0 ? 0 : ToStringStyle.watchTime(start, stop, live);",
      "why": "hop 1 answers a watch that has no start mark with 0"},
     {"file": TSS, "old": "return FastDateFormat.elapsedMillis(start, stop, live);",
      "new": "return FastDateFormat.elapsedMillis(start, stop < 0 ? 0 : stop, live);",
      "why": "hop 2 passes a stop mark below zero as 0"},
     {"file": FDF, "old": "return StringUtils.timeElapsed(start, stop, live);",
      "new": "return StringUtils.timeElapsed(start, stop, live && start >= 0);",
      "why": "hop 3 counts a watch as live only once it has a start mark"},
     {"file": SU, "old": "return ArrayUtils.elapsedTime(start, stop, live);",
      "new": "return Math.max(0, ArrayUtils.elapsedTime(start, stop, live));",
      "why": "hop 4 never returns a time below zero"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts from mr_lib.py preview Lang-55 org/apache/commons/lang/time/StopWatch.java 5 with the instance "
               "seed 7676, used in draw order, none substituted: text.StrBuilder (hop 1, 2712 lines), builder.ToStringStyle (hop "
               "2, 2252), time.FastDateFormat (hop 3, 1752; the smallest host; the draw relaxed the distinct-from-target-package "
               "rule for hops 3-4 because the checkout has only five other classes of >= 1500 lines), StringUtils (hop 4, 5062), "
               "ArrayUtils (hop 5, gold, 4417). All five are public top-level classes in which a static method compiles "
               "(ToStringStyle is abstract, which does not affect a static method). Anchors from stageB_lib.pick_insertion_anchor "
               "with seed 7676 + 100 + i (as mr3_spec.py inserts them): hop 1 after `indexOf` (line 2149, seed 7776), hop 2 after "
               "`append` (399, 7777), hop 3 after `getInstance` (221, 7778), hop 4 after `split` (2128, 7779), hop 5 after "
               "`contains` (2266, 7780). The facade calls hop 1 by its fully-qualified name; hops 1-3 import the next host, hop 4 "
               "calls ArrayUtils in its own package. The facade's class StopWatch is not a host (facade_files_excluded).",
}
