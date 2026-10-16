# Questions for the supervisor / 需要导师确认的问题 (2026-10-16)

These questions accompany `SUPERVISOR_REPORT_2026-10-16.md`. Each one is still open in the study documents; the sources are listed so that each can be checked. Items 1–3 block the next paid experiment; items 4–13 are needed for the thesis write-up; item 14 is optional.

本文件配合 `SUPERVISOR_REPORT_2026-10-16.md` 使用。每个问题在研究文档中都仍未解决，并附有出处。第 1–3 项会阻塞下一次付费实验；第 4–13 项是撰写论文所需；第 14 项为可选。

## A. Blocks the next experiment / 阻塞下一次实验

### 1. Run the decomposition block, and on which model? / 是否运行分解实验，在哪个模型上？

- **EN.** Should I run the decomposition block next? If so, on gpt-5.5 (60 runs, about US$26) or on GPT-5.6 (about US$16–17)? Or should Stage B stop here?
- **中文：** 下一步是否运行分解实验？如果运行，用 gpt-5.5（60 次，约 26 美元）还是 GPT-5.6（约 16–17 美元）？还是 Stage B 到此为止？
- **Why / 原因：** The preregistered rule recommends the decomposition after an ATTENUATED result but names no model, and the class rests on one run (26/30; 27/30 would have been ELIMINATED, which would have needed your approval for any decomposition). On gpt-5.5 there is a −0.73 drop to take apart; on GPT-5.6 only one of the four cells is measured (15/15). Nothing has been launched.
- **Options / 选项：** (a) gpt-5.5, about $26, my suggestion, which goes beyond the rule / gpt-5.5，约 26 美元（我的建议，超出规则范围）; (b) GPT-5.6, about $16–17 / GPT-5.6，约 16–17 美元; (c) both, about $42–43 / 两个都做，约 42–43 美元; (d) stop here, which departs from the preregistered recommendation / 到此为止（偏离预注册建议）.
- **Sources:** `SUPERVISOR_REPORT_2026-10-16.md` section 4; `GPT56_STAGE_B_PREREGISTRATION.md` "Decision rule fixed now"; `GPT55_VS_GPT56_ANALYSIS.md` "Decision"; `../SUPERVISOR_UPDATE_STAGE_B.md` "Proposed next block"; `../AMENDMENTS.md` W20.

### 2. Which factors should the decomposition vary? / 分解实验应改变哪些因素？

- **EN.** As described, every cell stays at 5 hops and only two factors are crossed: hops inside the facade's own class versus dispersed over five host classes, and the facade lie on versus off. Is that the design you want, or should it also vary hop count, and separate host-class size from anonymous placement?
- **中文：** 按目前的描述，所有格都是 5 跳，只交叉两个因素：跳点放在 facade 自己的类里还是分散到五个宿主类，以及 facade 谎言开还是关。这是您要的设计吗？还是也要改变跳数，并把宿主类大小和匿名插入位置分开？
- **Why / 原因：** My Stage B letter said the block would separate "the reasoning distance, the dispersal into large foreign files, or the narrative", and the preregistration's shorthand lists "hop distance", but the described 2×2 does not vary hop count. Without a hop-count factor the drop cannot be attributed to reasoning distance. Extra factors raise the cost above 60 runs and $26 (not yet estimated), and the factor set must be fixed and preregistered before any run.
- **Options / 选项：** (a) approve the 2×2 as described / 批准现有 2×2; (b) add a hop-count factor / 增加跳数因素; (c) also separate host size from anonymous placement / 另外拆开宿主类大小与匿名插入位置.
- **Sources:** `SUPERVISOR_REPORT_2026-10-16.md` section 4; `../SUPERVISOR_UPDATE_STAGE_B.md` "Proposed next block"; `../AMENDMENTS.md` W17; `GPT56_STAGE_B_PREREGISTRATION.md` "Decision rule fixed now"; `../STAGE_B_RESULTS.md` "What the block does not separate".

### 3. Budget: the US$40 check-in was passed; what ceiling now? / 经费：已越过 40 美元检查点，之后的上限是多少？

- **EN.** The ladder preregistration says to stop and ask once this experiment's spend passes $40. That point was passed during Stage B block 1 without a check-in (I disclosed it afterwards). Recorded spend is now $64.10, about $66 with estimates. Do you accept this, and what ceiling should apply to further paid runs?
- **中文：** 预注册规定本实验累计花费超过 40 美元时要停下来请示。这个点在 Stage B 第一块运行时已越过，当时没有事先请示（事后已告知）。现在有记录的花费为 64.10 美元，含估算约 66 美元。您是否认可？之后的付费运行适用什么上限？
- **Why / 原因：** No acknowledgement and no ceiling for later blocks is recorded. A gpt-5.5 decomposition would bring this experiment to about $92; with mechanism-search-v1 ($28.83) the two experiments already total about $95.
- **Options / 选项：** (a) acknowledge it and approve the next block with a cap you set / 认可并在您设定的上限内批准下一个实验块; (b) acknowledge it and set a new overall ceiling / 认可并设定新的总上限; (c) hold all further paid runs / 暂停所有后续付费运行.
- **Sources:** `../PREREGISTRATION.md` "Cost" (Check-in); `../SUPERVISOR_UPDATE_STAGE_B.md` "Spend"; `../COST_LEDGER.csv`.

## B. Needed for the thesis write-up / 撰写论文所需

### 4. Main Stage B claim: descriptive and scoped to gpt-5.5? / Stage B 主结论：描述性、只限于 gpt-5.5？

- **EN.** Can the thesis's main Stage B claim be descriptive and scoped to gpt-5.5: the chain-plus-lie bundle drops gpt-5.5 from 29/30 to 7/30, and most of that drop does not transfer to GPT-5.6 (26/30)? It would make no capability-ladder claim and no capability explanation, would state that the bundle's parts are not yet separated, and would use Stage A only as exploratory context.
- **中文：** 论文中 Stage B 的主结论能否写成描述性的、只限于 gpt-5.5：“链 + 谎言”这一组合使 gpt-5.5 从 29/30 降到 7/30，而大部分降幅没有迁移到 GPT-5.6（26/30）？不提能力阶梯，不作能力解释，说明组合的各成分尚未分离，Stage A 只作为探索性背景。
- **Why / 原因：** The goal set earlier was a stable drop on a current model; GPT-5.6, the current model, largely recovers, so the Stage B letter's headline ("the chain-isolated drop exists on a current model") is superseded. The chain arm changes hop count, dispersal, host size, anonymous placement and the lie at once.
- **Options / 选项：** (a) accept the scoped claim / 接受限定范围的结论; (b) require the decomposition before any claim about chains / 先做分解实验再对“链”下结论; (c) frame the thesis around the failure mode (gold named and located, facade ranked first) rather than chain length / 以失败模式为主线，而不是链长度.
- **Sources:** `../AMENDMENTS.md` W5, W10; `../STAGE_B_RESULTS.md` "Stage B synthesis"; `CROSS_MODEL_FAILURE_MODES.md` "What the three models do not show".

### 5. How to report the borderline ATTENUATED result / 如何报告处于边界的 ATTENUATED 结果

- **EN.** GPT-5.6 is ATTENUATED under the preregistered rule by one run (26/30; ELIMINATED needed 27/30), and the 95% interval (0.70–0.95) spans the 0.90 threshold. Should the thesis report ATTENUATED with this caveat, or lead with "largely did not transfer, hard to tell from ELIMINATED"?
- **中文：** 按预注册规则，GPT-5.6 的结果是 ATTENUATED，但只差一次运行（26/30；ELIMINATED 需要 27/30），95% 区间（0.70–0.95）跨过 0.90 阈值。论文应报告 ATTENUATED 并附这一说明，还是以“大部分没有迁移、与 ELIMINATED 难以区分”为主？
- **Options / 选项：** (a) ATTENUATED with the one-run caveat (as written) / 按预注册报告 ATTENUATED 并说明边界（现有写法）; (b) lead with "largely did not transfer" / 以“大部分没有迁移”为主; (c) lead with the shape: plain chain at ceiling, all misses in the odd-hop chain cell / 以结果形态为主.
- **Sources:** `GPT56_STAGE_B_RESULTS.md` "Classification"; `GPT56_STAGE_B_PREREGISTRATION.md` "Classification fixed now".

### 6. Deviations from your generator recipe / 与您的生成器配方的偏差

- **EN.** The Stage B chain arm departs from your recipe in recorded ways: five host classes instead of two, hand-written omission faults and lie (the generator's LLM chain-design step was not used), added imports, and the Math facade class (StatUtils, about 900 lines) is below the recipe's 1,800-line gate. Can the thesis still call it "your recipe", or should it say "a construction derived from your recipe"?
- **中文：** Stage B 的链式臂与您的配方有记录在案的偏差：用了五个宿主类而不是两个；故障和谎言是手写的（没有用生成器的 LLM 链设计步骤）；增加了 import；Math 的 facade 类（StatUtils，约 900 行）低于配方 1800 行的门槛。论文里还能称之为“您的配方”吗？还是应写成“源自您配方的构造”？
- **Options / 选项：** (a) "your recipe, with the recorded deviations" / “您的配方（附记录的偏差）”; (b) "a construction derived from your recipe" / “源自您配方的构造”; (c) require an arm closer to the recipe in future blocks / 今后要求更接近配方的链式臂.
- **Sources:** `../AMENDMENTS.md` W11 (deviations 1–7), W15; `../STAGE_B_PREREGISTRATION.md` "Design".

### 7. The refined single-owner rule (bypass vs competing repair) / 修订后的唯一归属规则（绕过 vs 竞争性修复）

- **EN.** Before any Stage B run I refined the single-owner rule: a passing one-line edit that throws away the gold's output (a "bypass") is recorded but does not count as a second owner. Every Stage B bug has such a bypass. Do you accept this rule, and the withdrawal of the first Math bug (atanh) under it?
- **中文：** 在任何 Stage B 运行之前，我修订了唯一归属规则：能让测试通过、但丢弃 gold 输出的一行修改记为“绕过”（bypass），记录在案但不算第二个归属者；三个 bug 都有这样的绕过。您是否接受这条规则，以及据此撤回第一个 Math bug（atanh）？
- **Why / 原因：** The claim that each gold is the unique owner, and the judgement that facade-first answers are not defensible, both rest on this rule. I told you about it in the Stage B letter, but no acceptance is recorded.
- **Options / 选项：** (a) accept as is / 接受; (b) accept, but report bypass-motivated facade-first answers separately / 接受，但单独报告因绕过而排 facade 第一的答案; (c) count bypasses as owners and add a re-scored sensitivity analysis / 把绕过算作归属者并做重新评分的敏感性分析.
- **Sources:** `../AMENDMENTS.md` W13, W14; `../SUPERVISOR_UPDATE_STAGE_B.md` "Two things you should know", point 1.

### 8. Keep the Math bug (B4) in the pooled headline? / Math bug（B4）是否保留在合并主结果中？

- **EN.** In B4 the NaN rule is stated only in the facade's own javadoc, so 9 of gpt-5.5's 10 Math misses were rated partly defensible. Should B4 stay in the pooled headline (7/30 vs 29/30), or should the Lang + Chart result (7/20 vs 19/20, p = 1.4e-4) be reported beside it?
- **中文：** 在 B4 中，NaN 规则只写在 facade 自己的 javadoc 里，因此 gpt-5.5 的 10 次 Math 失败中有 9 次被评为“部分合理”。B4 是否保留在合并主结果（7/30 vs 29/30）中？还是同时报告只含 Lang + Chart 的结果（7/20 vs 19/20，p = 1.4e-4）？
- **Why / 原因：** B4 supplies gpt-5.5's 0/10 in the Math chain cells and GPT-5.6's 0/10 → 10/10 recovery. The two labelling rules applied to B4 were written by the adjudicator during block 2, not preregistered.
- **Options / 选项：** (a) keep B4 with the caveat / 保留并附说明; (b) report pooled and Lang + Chart side by side / 合并结果与 Lang + Chart 并列; (c) add a sensitivity analysis treating B4's partly-defensible answers as partly correct / 增加敏感性分析.
- **Sources:** `../STAGE_B_RESULTS.md` block-2 labels and block-1 main effects; `../AMENDMENTS.md` W15, W16.

### 9. GPT-5.6's residual in C11: report only, or follow up? / GPT-5.6 在 C11 的残余：只报告，还是做后续实验？

- **EN.** GPT-5.6's only residual is in C11 (11/15, four misses, p = 0.10, not established). Should it be reported as an unestablished signal and future work, or do you want me to design a small follow-up for the odd-hop chain cell (not yet designed or costed)?
- **中文：** GPT-5.6 唯一的残余在 C11（11/15，四次失败，p = 0.10，未确立）。只报告为未确立的信号并留作未来工作，还是希望我为“奇异跳链式格”设计一个小型后续实验（尚未设计、未估算费用）？
- **Sources:** `GPT55_VS_GPT56_ANALYSIS.md` "A caution on the interaction"; `GPT56_STAGE_B_RESULTS.md` "The class hides a different shape".

### 10. Verdict on your ambiguity hypothesis / 对您的歧义假设的结论

- **EN.** Your ambiguity hypothesis is judged NOT SUPPORTED as the reason these ten gpt-5 runs timed out, with INCONCLUSIVE for the three runs that kept deliberating after finding the gold. Do you accept this, or should the thesis call the overall answer INCONCLUSIVE, or report it split (7 with an operational account, 3 inconclusive)?
- **中文：** 您的歧义假设被判定为：作为这十次 gpt-5 超时的原因“不被支持”（NOT SUPPORTED）；其中三次找到 gold 后继续推敲的运行为“无法定论”（INCONCLUSIVE）。您是否接受？还是论文应把总体结论写成“无法定论”，或分开报告（7 次有操作层面的解释，3 次无法定论）？
- **Why / 原因：** There is no control without the ambiguity, the reasoning text is hidden, the coders were primed, and the frozen stall rule excluded five runs that had read the gold. The documents concede that weighting the three runs more heavily makes the answer INCONCLUSIVE.
- **Sources:** `../gpt5-timeouts/GPT5_AMBIGUITY_HYPOTHESIS.md`; `../analysis/verification/gpt5_timeout_docs_round2.md`; `../AMENDMENTS.md` W19.

### 11. Design a proper test of the ambiguity hypothesis? / 是否设计对歧义假设的正式检验？

- **EN.** Do you want me to design a controlled test: same-bug controls without the ambiguity, a stable serving speed, a fixed shell environment, comparing reasoning after the gold rather than wall time? Or should the thesis leave this as future work?
- **中文：** 是否需要我设计一个对照实验来正式检验歧义假设：同一 bug 去掉歧义作对照、稳定的服务速度、固定的 shell 环境，比较找到 gold 之后的推理量而不是墙钟时间？还是在论文中留作未来工作？
- **Why / 原因：** It is only outlined, not designed or costed. It needs new control instances and new paid gpt-5 runs, and conditions the frozen protocol does not provide.
- **Sources:** `../gpt5-timeouts/GPT5_TIMEOUT_ANALYSIS.md` "What would test the hypothesis properly (not run)".

### 12. Keep the harness frozen, or fix known problems? / 测试框架保持冻结，还是修复已知问题？

- **EN.** Four known problems stay unfixed under the freeze: login-shell test calls always fail on Java detection; the validator rejects a ranking that names two overloads; gpt-5 often appends a stray `}` to commands; and the frozen `gold_exposed` measure misses `nl | grep` output (3 of gpt-5.5's 24 misses). Should everything stay frozen and be reported as limitations, with the earlier "gpt-5 too weak at the frozen budget" verdict qualified? Or should some be fixed before any new block?
- **中文：** 冻结协议下有四个已知问题未修复：通过 login shell 的测试调用总是在 Java 检测上失败；校验器拒绝列出两个同名重载的排名；gpt-5 常在命令末尾多加一个 `}`；冻结的 `gold_exposed` 度量漏判 `nl | grep` 的输出（gpt-5.5 的 24 次失败中有 3 次）。是全部保持冻结、作为局限报告，并给之前“gpt-5 在冻结预算下太弱”的结论加限定？还是在新的实验块之前修复其中一部分？
- **Why / 原因：** Any fix changes guarded scripts, needs a new freeze and a re-acceptance smoke run, and weakens like-for-like comparison with every earlier block.
- **Options / 选项：** (a) keep frozen, report as limitations / 保持冻结并作为局限报告; (b) fix the validator and/or login-shell environment before the next block / 下一个实验块前修复校验器和/或 login shell 环境; (c) fix the `gold_exposed` matcher for future blocks and re-score earlier blocks as a sensitivity check / 只在今后修复匹配器并对已有结果重新评分; (d) fix the harness and re-run gpt-5 on the held-out set as a separately preregistered block / 修复后在留出集上重跑 gpt-5.
- **Sources:** `../AMENDMENTS.md` W4, W16, W19; `../gpt5-timeouts/GPT5_TIMEOUT_ANALYSIS.md` "Protocol findings".

### 13. Status of the preregistered model ladder / 预注册模型阶梯的状态

- **EN.** The preregistered weaker-model ladder was paused after gpt-5.5 and gpt-5 without reaching a stop rule; its next step, a gpt-5.4 pilot (27 runs, audit estimate about $3), was never run. Should the ladder be formally closed as a deviation, resumed, or reported as paused?
- **中文：** 预注册的弱模型阶梯在 gpt-5.5 和 gpt-5 之后暂停，没有触发停止规则；下一步 gpt-5.4 试点（27 次，审计估算约 3 美元）从未运行。应作为偏差正式关闭、恢复运行，还是以“暂停”状态报告？
- **Why / 原因：** The thesis must state the ladder's status accurately, and Study 1 now makes the gpt-5 "too weak" verdict that triggered the next step partly a statement about serving speed and the harness. The gpt-5 pilot cost $6.06 against an audit estimate of $1.6, so the gpt-5.4 estimate may also be low.
- **Options / 选项：** (a) close it, reported as stopped by a change of direction / 正式关闭，报告为方向调整而停止; (b) resume with the gpt-5.4 pilot / 恢复并运行 gpt-5.4 试点; (c) leave it paused as future work / 保持暂停，列为未来工作.
- **Sources:** `../PREREGISTRATION.md` "Stage procedure" step 4; `../MODEL_SELECTION_AUDIT.md`; `../WEAKER_MODEL_RESULTS.md` section 1; `../AMENDMENTS.md` W4, W5.

## C. Optional / 可选

### 14. Free extra analyses before the write-up? / 写论文前是否做免费的补充分析？

- **EN.** Do you want any of these before the write-up? They need no new model runs: (a) blind-label the 26 correct GPT-5.6 chain runs and compare them with the 4 misses (uses labeller agents); (b) count stray-brace commands and login-shell tests for gpt-5.5 and GPT-5.6; (c) check offline whether the validator would accept the replayed gpt-5 ranking; (d) measure whether GPT-5.6's chain runs displayed the facade lie.
- **中文：** 写论文前是否需要以下不需新模型运行的分析：(a) 给 GPT-5.6 的 26 次正确链式运行做盲标并与 4 次失败对比（会用到标注代理）；(b) 统计 gpt-5.5 和 GPT-5.6 的多余 `}` 命令和 login shell 测试；(c) 离线检查重放的 gpt-5 排名能否通过校验器；(d) 测量 GPT-5.6 的链式运行是否显示了 facade 谎言。
