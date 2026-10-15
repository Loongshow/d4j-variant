# Timing table for CTV-9CE7EA/run-003 (timeout at 300.035 s; budget 300 s, 50 tool calls)

t = seconds since the 300 s timer started. request_t = when the model request was sent; result_t = when the tool output was recorded;
wait = result_t - request_t (model response time plus command time). Token counts are per model call (reasoning tokens are a count only).
gold_cov = fraction of the gold method's lines displayed so far; fault_line = the gold's faulty line has been displayed; decoy_sig = a
declared decoy's signature has been displayed; evid_cov = best coverage of the declared external-evidence methods; fail_vals = the
test's failure message has been displayed; new_methods = methods first displayed (>= 30% of lines) at this step.

| k | request_t | result_t | wait | kinds | prompt_tok | out_tok | reason_tok | gold_cov | fault_line | decoy_sig | evid_cov | fail_vals | repeat_cmd | revisit_read | new_methods |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.5 | 6.0 | 4.6 | - | 1076 | 30 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 1 | 5.5 | 9.2 | 3.7 | - | 1166 | 32 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 2 | 9.5 | 15.3 | 5.8 | - | 1301 | 101 | 64 | 0.0 | False | False | 0.0 | False | False | False |  |
| 3 | 15.5 | 26.5 | 11.1 | - | 1364 | 292 | 256 | 0.0 | False | False | 0.0 | False | False | False |  |
| 4 | 26.5 | 28.7 | 2.3 | READ | 1922 | 50 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 5 | 28.5 | 31.0 | 2.5 | - | 2026 | 35 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 6 | 30.5 | 78.6 | 48.2 | - | 2107 | 1074 | 1024 | 0.0 | False | False | 0.0 | False | False | False |  |
| 7 | 78.5 | 82.4 | 4.0 | SEARCH | 2176 | 33 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 8 | 82.5 | 86.9 | 4.4 | SEARCH | 2244 | 36 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 9 | 86.5 | 92.2 | 5.7 | - | 2396 | 62 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 10 | 92.5 | 95.2 | 2.7 | - | 2508 | 42 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 11 | 95.5 | 98.0 | 2.5 | - | 2584 | 45 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 12 | 97.5 | 131.1 | 33.7 | SEARCH | 2675 | 686 | 640 | 0.0 | False | False | 0.0 | False | False | False |  |
| 13 | 131.5 | 135.5 | 4.1 | READ | 2765 | 48 | 0 | 0.0 | False | False | 0.0 | False | False | True |  |
| 14 | 135.5 | 141.4 | 5.9 | - | 2852 | 68 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 15 | 141.5 | 148.2 | 6.8 | - | 4122 | 74 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 16 | 148.5 | 151.9 | 3.4 | READ | 4264 | 48 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 17 | 151.5 | 155.8 | 4.4 | - | 4364 | 62 | 0 | 0.0 | False | True | 0.0 | False | False | False | TarUtils::computeCheckSum, TarUtils::getCheckSumOctalBytes, TarUtils::getLongOctalBytes, TarUtils::getNameBytes, TarUtils::getOctalBytes, TarUtils::parseName ... |
| 18 | 155.5 | 159.6 | 4.2 | - | 5970 | 58 | 0 | 1.0 | True | True | 0.0 | False | False | False | IOUtils::copy, IOUtils::putOctalDigits, IOUtils::terminateChecksum |
| 19 | 159.5 | 179.6 | 20.1 | SEARCH | 7011 | 346 | 256 | 1.0 | True | True | 1.0 | False | False | False | TarArchiveEntry::TarArchiveEntry, TarArchiveEntry::equals, TarArchiveEntry::getDirectoryEntries, TarArchiveEntry::getFile, TarArchiveEntry::getGroupId, TarArchiveEntry::getGroupName ... |
| 20 | 179.5 | 226.6 | 47.2 | READ | 11810 | 886 | 832 | 1.0 | True | True | 1.0 | False | False | False |  |
| 21 | 226.5 | 230.2 | 3.7 | - | 11910 | 62 | 0 | 1.0 | True | True | 1.0 | False | False | False |  |
| 22 | 230.5 | 260.0 | 29.6 | - | 12927 | 873 | 832 | 1.0 | True | True | 1.0 | False | False | False |  |
| 23 | 260.5 | 293.1 | 32.6 | READ | 13096 | 904 | 832 | 1.0 | True | True | 1.0 | False | False | False |  |

End of run: the last tool output was recorded at t = 293.1 s; the run was killed at t = 300.035 s, so a model request had been
pending for 6.9 s with no response when the timer expired. No submission was made.
