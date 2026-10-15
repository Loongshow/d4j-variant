# Timing table for CTV-E04F64/run-005 (timeout at 300.025 s; budget 300 s, 50 tool calls)

t = seconds since the 300 s timer started. request_t = when the model request was sent; result_t = when the tool output was recorded;
wait = result_t - request_t (model response time plus command time). Token counts are per model call (reasoning tokens are a count only).
gold_cov = fraction of the gold method's lines displayed so far; fault_line = the gold's faulty line has been displayed; decoy_sig = a
declared decoy's signature has been displayed; evid_cov = best coverage of the declared external-evidence methods; fail_vals = the
test's failure message has been displayed; new_methods = methods first displayed (>= 30% of lines) at this step.

| k | request_t | result_t | wait | kinds | prompt_tok | out_tok | reason_tok | gold_cov | fault_line | decoy_sig | evid_cov | fail_vals | repeat_cmd | revisit_read | new_methods |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.0 | 3.5 | 2.5 | - | 951 | 65 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 1 | 3.0 | 12.5 | 9.5 | TEST | 1502 | 218 | 128 | 0.0 | False | False | 0.0 | False | False | False |  |
| 2 | 12.0 | 14.8 | 2.8 | TEST | 1777 | 82 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 3 | 16.0 | 21.9 | 5.9 | READ | 1933 | 110 | 64 | 0.0 | False | False | 0.0 | False | False | False |  |
| 4 | 22.0 | 23.8 | 1.8 | - | 2022 | 25 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 5 | 24.0 | 25.3 | 1.3 | READ | 3183 | 41 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 6 | 25.0 | 28.5 | 3.5 | READ | 3937 | 108 | 64 | 0.0 | False | True | 0.0 | False | False | True | Base64Variants::encodeToText, Base64Variants::getDefaultVariant, Base64Variants::valueOf |
| 7 | 28.0 | 30.0 | 2.0 | READ | 5562 | 38 | 0 | 0.0 | False | True | 0.0 | False | False | False | Base64Variant::Base64Variant, Base64Variant::decodeBase64Byte, Base64Variant::decodeBase64Char, Base64Variant::encodeBase64BitsAsByte, Base64Variant::encodeBase64BitsAsChar, Base64Variant::encodeBase64Chunk ... |
| 8 | 30.0 | 31.6 | 1.6 | READ | 8034 | 38 | 0 | 0.0 | False | True | 0.0 | False | False | True | Base64Variant::_reportBase64EOF, Base64Variant::_reportInvalidBase64, Base64Variant::decode, Base64Variant::encode, Base64Variant::equals, Base64Variant::hashCode ... |
| 9 | 31.0 | 37.5 | 6.5 | READ | 10144 | 301 | 256 | 0.0 | False | True | 1.0 | False | False | False | CharTypes::appendBase64Group, CharTypes::appendQuoted, CharTypes::charToHex, CharTypes::copyHexBytes, CharTypes::copyHexChars, CharTypes::get7BitOutputEscapes ... |
| 10 | 37.0 | 39.1 | 2.1 | READ | 12663 | 39 | 0 | 0.0 | False | True | 1.0 | False | False | True |  |
| 11 | 39.0 | 44.9 | 5.9 | READ | 12741 | 302 | 256 | 1.0 | True | True | 1.0 | False | False | False | ByteArrayBuilder::ByteArrayBuilder, ByteArrayBuilder::append, ByteArrayBuilder::appendThreeBytes, ByteArrayBuilder::appendTwoBytes, ByteArrayBuilder::completeAndCoalesce, ByteArrayBuilder::finishCurrentSegment ... |
| 12 | 45.0 | 46.5 | 1.5 | READ | 14576 | 40 | 0 | 1.0 | True | True | 1.0 | False | False | True | ByteArrayBuilder::_allocMore, ByteArrayBuilder::close, ByteArrayBuilder::flush, ByteArrayBuilder::write |
| 13 | 46.0 | 77.8 | 31.8 | READ | 15041 | 2162 | 2112 | 1.0 | True | True | 1.0 | False | False | True |  |
| 14 | 78.0 | 79.1 | 1.1 | READ | 17475 | 42 | 0 | 1.0 | True | True | 1.0 | False | False | True |  |
| 15 | 79.0 | 129.9 | 50.9 | SEARCH | 19622 | 3108 | 3072 | 1.0 | True | True | 1.0 | False | False | False |  |
| 16 | 130.0 | 197.8 | 67.8 | READ | 19753 | 4208 | 4160 | 1.0 | True | True | 1.0 | False | False | True |  |
| 17 | 198.0 | 260.8 | 62.8 | SUBMIT | 20917 | 3752 | 3328 | 1.0 | True | True | 1.0 | False | False | False |  |

End of run: the last tool output was recorded at t = 260.8 s; the run was killed at t = 300.025 s, so a model request had been
pending for 39.2 s with no response when the timer expired. No submission was made.
