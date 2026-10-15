# Timing table for CTV-9EB2B7/run-003 (timeout at 300.033 s; budget 300 s, 50 tool calls)

t = seconds since the 300 s timer started. request_t = when the model request was sent; result_t = when the tool output was recorded;
wait = result_t - request_t (model response time plus command time). Token counts are per model call (reasoning tokens are a count only).
gold_cov = fraction of the gold method's lines displayed so far; fault_line = the gold's faulty line has been displayed; decoy_sig = a
declared decoy's signature has been displayed; evid_cov = best coverage of the declared external-evidence methods; fail_vals = the
test's failure message has been displayed; new_methods = methods first displayed (>= 30% of lines) at this step.

| k | request_t | result_t | wait | kinds | prompt_tok | out_tok | reason_tok | gold_cov | fault_line | decoy_sig | evid_cov | fail_vals | repeat_cmd | revisit_read | new_methods |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.4 | 32.9 | 31.4 | - | 975 | 30 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 1 | 33.4 | 58.0 | 24.6 | - | 1065 | 75 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 2 | 58.4 | 107.1 | 48.7 | - | 1255 | 77 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 3 | 107.4 | 159.6 | 52.2 | - | 1436 | 285 | 256 | 0.0 | False | False | 0.0 | False | False | False |  |
| 4 | 159.4 | 180.7 | 21.3 | - | 1486 | 194 | 128 | 0.0 | False | False | 0.0 | False | False | False |  |
| 5 | 180.4 | 215.3 | 34.8 | - | 1616 | 669 | 640 | 0.0 | False | False | 0.0 | False | False | False |  |
| 6 | 215.4 | 225.7 | 10.3 | - | 1708 | 223 | 192 | 0.0 | False | False | 0.0 | False | False | False |  |
| 7 | 226.4 | 252.3 | 25.9 | - | 1768 | 479 | 448 | 0.0 | False | False | 0.0 | False | False | False |  |
| 8 | 252.4 | 266.6 | 14.2 | READ | 2527 | 32 | 0 | 0.0 | False | False | 0.0 | False | False | False |  |
| 9 | 266.4 | 271.3 | 4.9 | READ | 2595 | 33 | 0 | 0.0 | False | False | 0.0 | True | False | False |  |
| 10 | 271.4 | 276.5 | 5.1 | - | 3462 | 42 | 0 | 0.0 | False | False | 0.0 | True | False | False |  |
| 11 | 276.4 | 279.3 | 2.9 | READ | 3584 | 48 | 0 | 0.0 | False | False | 0.0 | True | False | False |  |
| 12 | 279.4 | 281.9 | 2.5 | READ | 3684 | 49 | 0 | 0.0 | False | True | 0.0 | True | False | True | EarthMoversDistance::compute |

End of run: the last tool output was recorded at t = 281.9 s; the run was killed at t = 300.033 s, so a model request had been
pending for 18.1 s with no response when the timer expired. No submission was made.
