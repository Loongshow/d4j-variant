# Timing table for CTV-E04F64/run-004 (timeout at 300.021 s; budget 300 s, 50 tool calls)

t = seconds since the 300 s timer started. request_t = when the model request was sent; result_t = when the tool output was recorded;
wait = result_t - request_t (model response time plus command time). Token counts are per model call (reasoning tokens are a count only).
gold_cov = fraction of the gold method's lines displayed so far; fault_line = the gold's faulty line has been displayed; decoy_sig = a
declared decoy's signature has been displayed; evid_cov = best coverage of the declared external-evidence methods; fail_vals = the
test's failure message has been displayed; new_methods = methods first displayed (>= 30% of lines) at this step.

| k | request_t | result_t | wait | kinds | prompt_tok | out_tok | reason_tok | gold_cov | fault_line | decoy_sig | evid_cov | fail_vals | repeat_cmd | revisit_read | new_methods |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.4 | 4.5 | 3.1 | - | 951 | 70 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 1 | 4.4 | 8.5 | 4.1 | TEST | 1507 | 224 | 128 | 0.0 | False | False | 0.0 | False | False | False |  |
| 2 | 8.4 | 11.2 | 2.8 | - | 1698 | 97 | 64 | 0.0 | False | False | 0.0 | False | False | False |  |
| 3 | 11.4 | 15.4 | 4.0 | SEARCH | 1762 | 33 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 4 | 15.4 | 19.2 | 3.8 | - | 1830 | 44 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 5 | 19.4 | 21.3 | 2.0 | - | 1956 | 62 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 6 | 21.4 | 25.1 | 3.7 | READ | 3205 | 113 | 64 | 0.0 | False | False | 0.0 | False | False | False |  |
| 7 | 25.4 | 27.4 | 2.0 | - | 3295 | 53 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 8 | 27.4 | 29.2 | 1.8 | READ | 3394 | 42 | 0 | 0.0 | False | False | 0.0 | False | False | True |  |
| 9 | 29.4 | 32.2 | 2.8 | - | 3483 | 127 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 10 | 32.4 | 34.3 | 2.0 | READ | 3689 | 82 | 0 | 0.0 | False | False | 0.0 | False | False | True |  |
| 11 | 34.4 | 47.3 | 12.9 | - | 3858 | 721 | 640 | 0.0 | False | True | 0.0 | False | False | False | Base64Variant::Base64Variant, Base64Variant::_reportBase64EOF, Base64Variant::_reportInvalidBase64, Base64Variant::decode, Base64Variant::decodeBase64Byte, Base64Variant::decodeBase64Char ... |
| 12 | 47.4 | 50.8 | 3.4 | READ | 8411 | 112 | 64 | 0.0 | False | True | 0.0 | False | False | False |  |
| 13 | 50.4 | 52.8 | 2.4 | - | 8500 | 62 | 0 | 0.0 | False | True | 0.0 | False | False | False | Base64Variants::encodeToText, Base64Variants::getDefaultVariant, Base64Variants::valueOf |
| 14 | 52.4 | 57.5 | 5.1 | READ | 10149 | 305 | 256 | 0.0 | False | True | 0.0 | False | False | False |  |
| 15 | 57.4 | 59.3 | 2.0 | - | 10240 | 63 | 0 | 0.0 | False | True | 1.0 | False | False | False | CharTypes::appendBase64Group, CharTypes::appendQuoted, CharTypes::charToHex, CharTypes::copyHexBytes, CharTypes::copyHexChars, CharTypes::get7BitOutputEscapes ... |
| 16 | 59.4 | 67.3 | 7.9 | READ | 12795 | 626 | 576 | 0.0 | False | True | 1.0 | False | False | False |  |
| 17 | 67.4 | 69.5 | 2.2 | - | 12888 | 64 | 0 | 1.0 | True | True | 1.0 | False | False | False | ByteArrayBuilder::ByteArrayBuilder, ByteArrayBuilder::_allocMore, ByteArrayBuilder::append, ByteArrayBuilder::appendThreeBytes, ByteArrayBuilder::appendTwoBytes, ByteArrayBuilder::close ... |
| 18 | 69.4 | 129.1 | 59.7 | - | 15140 | 3442 | 3392 | 1.0 | True | True | 1.0 | False | False | False |  |
| 19 | 129.4 | 130.8 | 1.4 | - | 15229 | 39 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 20 | 130.4 | 132.7 | 2.3 | - | 15302 | 54 | 0 | 1.0 | True | True | 1.0 | False | False | False | IOContext::allocBase64Buffer, JsonGenerator::writeBinary, JsonParser::getBinaryValue, JsonParser::readBinaryValue, JsonParserDelegate::getBinaryValue, ParserMinimalBase::getBinaryValue |
| 21 | 132.4 | 134.8 | 2.4 | READ | 22191 | 44 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 22 | 134.4 | 137.2 | 2.8 | - | 22284 | 64 | 0 | 1.0 | True | True | 1.0 | False | False | False | ParserMinimalBase::ParserMinimalBase, ParserMinimalBase::_constructError, ParserMinimalBase::_decodeBase64, ParserMinimalBase::_getCharDesc, ParserMinimalBase::_handleEOF, ParserMinimalBase::_handleUnrecognizedCharacterEscape ... |
| 23 | 137.4 | 179.3 | 41.9 | READ | 26073 | 2738 | 2688 | 1.0 | True | True | 1.0 | False | False | False |  |
| 24 | 179.4 | 181.3 | 2.0 | - | 26166 | 64 | 0 | 1.0 | True | True | 1.0 | False | False | False | JsonStringEncoder::JsonStringEncoder, JsonStringEncoder::_appendByteEscape, JsonStringEncoder::_appendNamedEscape, JsonStringEncoder::_appendNumericEscape, JsonStringEncoder::_convertSurrogate, JsonStringEncoder::_illegalSurrogate ... |
| 25 | 183.4 | 250.0 | 66.7 | - | 29665 | 4532 | 4480 | 1.0 | True | True | 1.0 | False | False | False |  |
| 26 | 250.4 | 251.9 | 1.6 | - | 29757 | 56 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 27 | 252.4 | 254.1 | 1.8 | - | 29885 | 41 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 28 | 254.4 | 256.1 | 1.7 | - | 29960 | 47 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 29 | 256.4 | 257.9 | 1.6 | - | 30052 | 37 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 30 | 258.4 | 259.8 | 1.4 | READ | 30140 | 45 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 31 | 260.4 | 262.2 | 1.8 | - | 30235 | 65 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |

End of run: the last tool output was recorded at t = 262.2 s; the run was killed at t = 300.021 s, so a model request had been
pending for 37.8 s with no response when the timer expired. No submission was made.
