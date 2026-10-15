# Timing table for CTV-7CE456/run-003 (timeout at 300.031 s; budget 300 s, 50 tool calls)

t = seconds since the 300 s timer started. request_t = when the model request was sent; result_t = when the tool output was recorded;
wait = result_t - request_t (model response time plus command time). Token counts are per model call (reasoning tokens are a count only).
gold_cov = fraction of the gold method's lines displayed so far; fault_line = the gold's faulty line has been displayed; decoy_sig = a
declared decoy's signature has been displayed; evid_cov = best coverage of the declared external-evidence methods; fail_vals = the
test's failure message has been displayed; new_methods = methods first displayed (>= 30% of lines) at this step.

| k | request_t | result_t | wait | kinds | prompt_tok | out_tok | reason_tok | gold_cov | fault_line | decoy_sig | evid_cov | fail_vals | repeat_cmd | revisit_read | new_methods |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.9 | 13.6 | 12.7 | - | 963 | 30 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 1 | 12.9 | 21.6 | 8.6 | - | 1053 | 148 | 64 | 0.0 | False | False | 0.0 | False | False | False |  |
| 2 | 20.9 | 24.1 | 3.2 | - | 1173 | 67 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 3 | 23.9 | 37.6 | 13.7 | - | 1306 | 347 | 256 | 0.0 | False | False | 0.0 | False | False | False |  |
| 4 | 37.9 | 43.9 | 6.0 | READ | 2561 | 115 | 64 | 0.0 | False | False | 0.0 | False | False | False |  |
| 5 | 43.9 | 46.6 | 2.6 | - | 2655 | 24 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 6 | 45.9 | 49.5 | 3.5 | - | 2745 | 63 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 7 | 49.9 | 52.2 | 2.2 | - | 3537 | 40 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 8 | 51.9 | 54.4 | 2.4 | - | 3623 | 41 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 9 | 53.9 | 58.7 | 4.7 | - | 3710 | 43 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 10 | 58.9 | 60.9 | 2.0 | - | 3781 | 39 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 11 | 60.9 | 87.3 | 26.3 | TEST | 3853 | 991 | 896 | 0.0 | False | False | 0.0 | False | False | False |  |
| 12 | 86.9 | 99.8 | 12.9 | - | 4042 | 413 | 384 | 0.0 | False | False | 0.0 | False | False | False |  |
| 13 | 99.9 | 108.9 | 9.0 | - | 4132 | 351 | 320 | 0.0 | False | False | 0.0 | False | False | False |  |
| 14 | 108.9 | 128.8 | 19.9 | - | 4192 | 735 | 704 | 0.0 | False | False | 0.0 | False | False | False |  |
| 15 | 128.9 | 132.3 | 3.3 | - | 4709 | 72 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 16 | 131.9 | 134.7 | 2.8 | - | 4874 | 41 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 17 | 134.9 | 136.9 | 2.0 | READ | 7964 | 43 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 18 | 136.9 | 139.1 | 2.1 | - | 8046 | 48 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 19 | 138.9 | 141.5 | 2.5 | - | 8143 | 49 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 20 | 140.9 | 145.8 | 4.8 | - | 9117 | 118 | 64 | 0.0 | False | False | 0.0 | False | False | False |  |
| 21 | 145.9 | 147.2 | 1.3 | - | 9214 | 48 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 22 | 146.9 | 149.8 | 2.9 | - | 9349 | 49 | 0 | 0.0 | False | True | 0.0 | False | False | False | JsonStringEncoder::JsonStringEncoder, JsonStringEncoder::_appendByteEscape, JsonStringEncoder::_appendNamedEscape, JsonStringEncoder::_appendNumericEscape, JsonStringEncoder::_convertSurrogate, JsonStringEncoder::_illegalSurrogate ... |
| 23 | 149.9 | 171.3 | 21.3 | - | 12816 | 1077 | 1024 | 0.0 | False | True | 0.0 | False | False | False |  |
| 24 | 170.9 | 173.5 | 2.5 | - | 12911 | 48 | 0 | 0.0 | False | True | 1.0 | False | False | False | CharTypes::appendQuoted, CharTypes::charToHex, CharTypes::combineSurrogates, CharTypes::copyHexBytes, CharTypes::copyHexChars, CharTypes::get7BitOutputEscapes ... |
| 25 | 172.9 | 211.0 | 38.0 | - | 15770 | 1717 | 1664 | 1.0 | True | True | 1.0 | False | False | False | JsonEncoding::JsonEncoding, JsonEncoding::getJavaName, JsonEncoding::isBigEndian, JsonEncoding::supplementaryCodePoint |
| 26 | 210.9 | 243.8 | 32.9 | - | 16517 | 1844 | 1792 | 1.0 | True | True | 1.0 | False | False | False |  |
| 27 | 243.9 | 282.7 | 38.8 | - | 16594 | 1911 | 1856 | 1.0 | True | True | 1.0 | False | False | False | UTF8Writer::UTF8Writer, UTF8Writer::append, UTF8Writer::close, UTF8Writer::convertSurrogate, UTF8Writer::flush, UTF8Writer::illegalSurrogate ... |

End of run: the last tool output was recorded at t = 282.7 s; the run was killed at t = 300.031 s, so a model request had been
pending for 17.3 s with no response when the timer expired. No submission was made.
