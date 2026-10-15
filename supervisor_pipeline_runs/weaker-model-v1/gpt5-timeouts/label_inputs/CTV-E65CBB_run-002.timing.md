# Timing table for CTV-E65CBB/run-002 (timeout at 300.024 s; budget 300 s, 50 tool calls)

t = seconds since the 300 s timer started. request_t = when the model request was sent; result_t = when the tool output was recorded;
wait = result_t - request_t (model response time plus command time). Token counts are per model call (reasoning tokens are a count only).
gold_cov = fraction of the gold method's lines displayed so far; fault_line = the gold's faulty line has been displayed; decoy_sig = a
declared decoy's signature has been displayed; evid_cov = best coverage of the declared external-evidence methods; fail_vals = the
test's failure message has been displayed; new_methods = methods first displayed (>= 30% of lines) at this step.

| k | request_t | result_t | wait | kinds | prompt_tok | out_tok | reason_tok | gold_cov | fault_line | decoy_sig | evid_cov | fail_vals | repeat_cmd | revisit_read | new_methods |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.4 | 6.0 | 4.6 | - | 945 | 30 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 1 | 6.4 | 9.1 | 2.7 | - | 1035 | 96 | 64 | 0.0 | False | False | 0.0 | False | False | False |  |
| 2 | 9.4 | 12.1 | 2.8 | - | 1836 | 103 | 64 | 0.0 | False | False | 0.0 | False | False | False |  |
| 3 | 12.4 | 13.8 | 1.4 | - | 1902 | 37 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 4 | 14.4 | 16.0 | 1.6 | READ | 2089 | 50 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 5 | 15.4 | 17.7 | 2.3 | READ | 2193 | 50 | 0 | 0.0 | False | True | 0.0 | False | False | True | Segment::Segment, Segment::Segment, Segment::distance, Segment::getEnd, Segment::getLine, Segment::getLine ... |
| 6 | 17.4 | 20.8 | 3.4 | READ | 2910 | 184 | 128 | 0.0 | False | True | 0.0 | False | False | False |  |
| 7 | 21.4 | 23.0 | 1.6 | READ | 3014 | 50 | 0 | 0.0 | False | True | 0.0 | False | False | True | Line::Line, Line::copySelf, Line::getOffset, Line::getPointAt, Line::getReverse, Line::intersection ... |
| 8 | 23.4 | 25.1 | 1.7 | READ | 5552 | 50 | 0 | 0.0 | False | True | 0.0 | False | False | True | Line$LineTransform::LineTransform, Line$LineTransform::apply, Line::chordDistance, Line::contains, Line::distance, Line::getAngle ... |
| 9 | 25.4 | 28.1 | 2.8 | READ | 7419 | 186 | 128 | 0.0 | False | True | 0.0 | False | False | False |  |
| 10 | 28.4 | 29.9 | 1.5 | READ | 7527 | 52 | 0 | 0.0 | False | True | 0.0 | False | False | True | Vector2D::Vector2D, Vector2D::add, Vector2D::distance1, Vector2D::distanceInf, Vector2D::getNorm, Vector2D::getNorm1 ... |
| 11 | 29.4 | 31.7 | 2.3 | READ | 9869 | 52 | 0 | 1.0 | True | True | 1.0 | False | False | True | Vector2D::chordFraction, Vector2D::chordPoint, Vector2D::distance, Vector2D::distanceSq, Vector2D::dotProduct, Vector2D::equals ... |
| 12 | 31.4 | 37.2 | 5.8 | READ | 11667 | 311 | 256 | 1.0 | True | True | 1.0 | False | False | False |  |
| 13 | 37.4 | 40.2 | 2.8 | - | 11769 | 43 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 14 | 40.4 | 42.3 | 2.0 | - | 11845 | 47 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 15 | 42.4 | 44.3 | 1.9 | READ | 11986 | 49 | 0 | 1.0 | True | True | 1.0 | False | False | True | Interval::Interval, Interval::checkPoint, Interval::getBarycenter, Interval::getInf, Interval::getLength, Interval::getLower ... |
| 16 | 44.4 | 46.8 | 2.4 | READ | 13162 | 57 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 17 | 46.4 | 48.8 | 2.4 | READ | 13268 | 51 | 0 | 1.0 | True | True | 1.0 | False | False | True |  |
| 18 | 48.4 | 51.9 | 3.5 | TEST | 13891 | 96 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 19 | 51.4 | 87.1 | 35.7 | - | 14082 | 2160 | 2112 | 1.0 | True | True | 1.0 | False | False | False |  |
| 20 | 87.4 | 89.2 | 1.8 | - | 14170 | 38 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 21 | 89.4 | 91.2 | 1.8 | - | 14242 | 48 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 22 | 91.4 | 93.0 | 1.6 | - | 14336 | 40 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 23 | 93.4 | 95.2 | 1.8 | - | 14409 | 54 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 24 | 96.4 | 106.8 | 10.4 | READ | 14507 | 569 | 512 | 1.0 | True | True | 1.0 | False | False | False |  |
| 25 | 106.4 | 109.4 | 3.0 | - | 14613 | 39 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 26 | 109.4 | 111.2 | 1.8 | - | 14703 | 41 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 27 | 111.4 | 113.9 | 2.5 | READ | 14809 | 50 | 0 | 1.0 | True | True | 1.0 | False | False | False | IntervalsSet::IntervalsSet, IntervalsSet::asList, IntervalsSet::buildNew, IntervalsSet::buildTree, IntervalsSet::computeGeometricalProperties, IntervalsSet::getInf ... |
| 28 | 114.4 | 115.8 | 1.4 | READ | 17120 | 50 | 0 | 1.0 | True | True | 1.0 | False | False | True |  |
| 29 | 116.4 | 118.0 | 1.6 | READ | 17224 | 49 | 0 | 1.0 | True | True | 1.0 | False | False | True | IntervalsSet::recurseList |
| 30 | 118.4 | 129.8 | 11.4 | READ | 17585 | 695 | 640 | 1.0 | True | True | 1.0 | False | False | True | Segment::getEnd, Segment::getStart |
| 31 | 130.4 | 154.2 | 23.8 | - | 18109 | 1522 | 1472 | 1.0 | True | True | 1.0 | False | False | False |  |
| 32 | 154.4 | 156.5 | 2.1 | - | 18190 | 59 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 33 | 156.4 | 158.4 | 2.0 | - | 18295 | 50 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 34 | 158.4 | 185.6 | 27.2 | - | 18388 | 1982 | 1920 | 1.0 | True | True | 1.0 | False | False | False |  |
| 35 | 185.4 | 187.9 | 2.5 | - | 18490 | 55 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 36 | 188.4 | 190.6 | 2.2 | - | 18591 | 55 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 37 | 190.4 | 193.3 | 3.0 | READ | 18692 | 53 | 0 | 1.0 | True | True | 1.0 | False | False | True |  |
| 38 | 193.4 | 195.5 | 2.1 | - | 18804 | 57 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 39 | 195.4 | 197.5 | 2.1 | - | 18900 | 55 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 40 | 197.4 | 199.3 | 1.9 | - | 19001 | 53 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 41 | 199.4 | 225.5 | 26.1 | - | 19100 | 1526 | 1472 | 1.0 | True | True | 1.0 | False | False | False |  |
| 42 | 225.4 | 227.7 | 2.4 | SEARCH | 19182 | 34 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 43 | 227.4 | 270.0 | 42.6 | SEARCH | 19252 | 3067 | 3008 | 1.0 | True | True | 1.0 | False | False | False |  |
| 44 | 270.4 | 292.1 | 21.7 | SEARCH | 19361 | 1701 | 1664 | 1.0 | True | True | 1.0 | False | False | False |  |

End of run: the last tool output was recorded at t = 292.1 s; the run was killed at t = 300.024 s, so a model request had been
pending for 7.9 s with no response when the timer expired. No submission was made.
