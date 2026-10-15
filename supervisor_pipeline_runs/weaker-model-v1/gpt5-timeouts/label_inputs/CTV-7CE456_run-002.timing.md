# Timing table for CTV-7CE456/run-002 (timeout at 300.023 s; budget 300 s, 50 tool calls)

t = seconds since the 300 s timer started. request_t = when the model request was sent; result_t = when the tool output was recorded;
wait = result_t - request_t (model response time plus command time). Token counts are per model call (reasoning tokens are a count only).
gold_cov = fraction of the gold method's lines displayed so far; fault_line = the gold's faulty line has been displayed; decoy_sig = a
declared decoy's signature has been displayed; evid_cov = best coverage of the declared external-evidence methods; fail_vals = the
test's failure message has been displayed; new_methods = methods first displayed (>= 30% of lines) at this step.

| k | request_t | result_t | wait | kinds | prompt_tok | out_tok | reason_tok | gold_cov | fault_line | decoy_sig | evid_cov | fail_vals | repeat_cmd | revisit_read | new_methods |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.7 | 4.6 | 3.0 | - | 963 | 130 | 64 | 0.0 | False | False | 0.0 | False | False | False |  |
| 1 | 4.7 | 6.9 | 2.2 | SEARCH | 1515 | 100 | 64 | 0.0 | False | False | 0.0 | False | False | False |  |
| 2 | 6.7 | 8.3 | 1.6 | READ | 1595 | 40 | 0 | 0.0 | False | False | 0.0 | False | False | False | JsonStringEncoder::JsonStringEncoder, JsonStringEncoder::getInstance, JsonStringEncoder::quoteAsString, JsonStringEncoder::quoteAsUTF8 |
| 3 | 8.7 | 9.7 | 1.0 | READ | 3467 | 40 | 0 | 0.0 | False | True | 0.0 | False | False | True | JsonStringEncoder::_appendByteEscape, JsonStringEncoder::_appendNamedEscape, JsonStringEncoder::_appendNumericEscape, JsonStringEncoder::_convertSurrogate, JsonStringEncoder::_illegalSurrogate, JsonStringEncoder::encodeAsUTF8 |
| 4 | 9.7 | 12.2 | 2.5 | TEST | 5125 | 90 | 0 | 0.0 | False | True | 0.0 | False | False | False |  |
| 5 | 12.7 | 14.4 | 1.8 | TEST | 5405 | 82 | 0 | 0.0 | False | True | 0.0 | False | False | False |  |
| 6 | 14.7 | 31.9 | 17.2 | READ | 5560 | 1197 | 1152 | 0.0 | False | True | 1.0 | False | False | False | CharTypes::appendQuoted, CharTypes::charToHex, CharTypes::copyHexBytes, CharTypes::copyHexChars, CharTypes::get7BitOutputEscapes, CharTypes::getInputCodeComment ... |
| 7 | 31.7 | 33.3 | 1.6 | READ | 8085 | 39 | 0 | 0.0 | False | True | 1.0 | False | False | True | CharTypes::combineSurrogates |
| 8 | 32.7 | 40.7 | 8.0 | READ | 8476 | 556 | 512 | 1.0 | True | True | 1.0 | False | False | False | JsonEncoding::JsonEncoding, JsonEncoding::getJavaName, JsonEncoding::isBigEndian, JsonEncoding::supplementaryCodePoint |
| 9 | 40.7 | 44.3 | 3.6 | READ | 9214 | 195 | 128 | 1.0 | True | True | 1.0 | True | False | False |  |
| 10 | 44.7 | 61.1 | 16.4 | READ | 9930 | 1134 | 1088 | 1.0 | True | True | 1.0 | True | False | False | UTF8Writer::UTF8Writer, UTF8Writer::append, UTF8Writer::close, UTF8Writer::flush, UTF8Writer::write |
| 11 | 61.7 | 63.0 | 1.3 | READ | 12089 | 40 | 0 | 1.0 | True | True | 1.0 | True | False | True | UTF8Writer::convertSurrogate, UTF8Writer::illegalSurrogate, UTF8Writer::illegalSurrogateDesc |
| 12 | 62.7 | 107.4 | 44.7 | SEARCH | 13374 | 3456 | 3392 | 1.0 | True | True | 1.0 | True | False | False |  |
| 13 | 107.7 | 161.9 | 54.2 | READ | 13917 | 3568 | 3520 | 1.0 | True | True | 1.0 | True | False | True |  |
| 14 | 161.7 | 205.2 | 43.5 | READ | 14896 | 3442 | 3392 | 1.0 | True | True | 1.0 | True | False | True |  |
| 15 | 205.7 | 206.7 | 1.0 | READ | 17455 | 44 | 0 | 1.0 | True | True | 1.0 | True | False | True |  |
| 16 | 206.7 | 240.6 | 33.9 | READ | 19655 | 2606 | 2560 | 1.0 | True | True | 1.0 | True | False | False |  |

End of run: the last tool output was recorded at t = 240.6 s; the run was killed at t = 300.023 s, so a model request had been
pending for 59.4 s with no response when the timer expired. No submission was made.
