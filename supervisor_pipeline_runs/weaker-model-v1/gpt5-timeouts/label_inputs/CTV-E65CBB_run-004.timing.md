# Timing table for CTV-E65CBB/run-004 (timeout at 300.031 s; budget 300 s, 50 tool calls)

t = seconds since the 300 s timer started. request_t = when the model request was sent; result_t = when the tool output was recorded;
wait = result_t - request_t (model response time plus command time). Token counts are per model call (reasoning tokens are a count only).
gold_cov = fraction of the gold method's lines displayed so far; fault_line = the gold's faulty line has been displayed; decoy_sig = a
declared decoy's signature has been displayed; evid_cov = best coverage of the declared external-evidence methods; fail_vals = the
test's failure message has been displayed; new_methods = methods first displayed (>= 30% of lines) at this step.

| k | request_t | result_t | wait | kinds | prompt_tok | out_tok | reason_tok | gold_cov | fault_line | decoy_sig | evid_cov | fail_vals | repeat_cmd | revisit_read | new_methods |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.2 | 22.6 | 21.4 | - | 945 | 30 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 1 | 22.2 | 35.6 | 13.5 | READ | 1703 | 56 | 0 | 0.0 | False | True | 0.0 | False | False | False | Segment::Segment, Segment::Segment, Segment::distance, Segment::getEnd, Segment::getLine, Segment::getLine ... |
| 2 | 35.2 | 88.9 | 53.8 | READ | 2420 | 56 | 0 | 0.0 | False | True | 0.0 | False | False | False | Line::Line, Line::copySelf, Line::getOffset, Line::getPointAt, Line::getReverse, Line::intersection ... |
| 3 | 89.2 | 137.7 | 48.6 | READ | 4958 | 50 | 0 | 0.0 | False | True | 0.0 | False | False | True | Line$LineTransform::LineTransform, Line$LineTransform::apply, Line::chordDistance, Line::contains, Line::distance, Line::getAngle ... |
| 4 | 137.2 | 178.4 | 41.3 | READ | 6825 | 186 | 128 | 1.0 | True | True | 0.0 | False | False | False | Vector2D::Vector2D, Vector2D::add, Vector2D::chordFraction, Vector2D::distance, Vector2D::distance1, Vector2D::distanceInf ... |
| 5 | 178.2 | 223.6 | 45.5 | READ | 9920 | 52 | 0 | 1.0 | True | True | 1.0 | False | False | True | Vector2D::chordPoint, Vector2D::equals, Vector2D::hashCode, Vector2D::toString |
| 6 | 223.2 | 285.9 | 62.7 | READ | 10960 | 631 | 576 | 1.0 | True | True | 1.0 | False | False | False | Interval::Interval, Interval::checkPoint, Interval::getBarycenter, Interval::getInf, Interval::getLength, Interval::getLower ... |

End of run: the last tool output was recorded at t = 285.9 s; the run was killed at t = 300.031 s, so a model request had been
pending for 14.1 s with no response when the timer expired. No submission was made.
