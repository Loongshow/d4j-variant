# Has gpt-5.5's accuracy dropped? / gpt-5.5 的准确率下降了吗？

Main run, batches 1–4, 16–21 October 2026. Model: gpt-5.5 (medium reasoning), on the frozen Stage B protocol.
主实验第 1–4 批，2026 年 10 月 16–21 日。模型：gpt-5.5（medium reasoning），使用冻结的 Stage B 协议。

## Short answer / 简短回答

**EN.** Yes. On our constructed Defects4J instances, gpt-5.5 ranks the faulty method first far less often than on the earlier
reference sets.

| Set | Acc@1 |
|---|---|
| Earlier held-out set | 100% |
| Stage B single-hop control | 100% |
| Main run, all four batches | 37.4% |
| Batches 3–4, built with the "no local trace" rule | 24.8% |
| Batch 4 | 20.0% |

The gold usually stays near the top. It is ranked second in most of the misranked runs, and it is in the top 3 in 92.8% of runs.

**中文。** 是的。在我们构造的 Defects4J 实例上，gpt-5.5 把故障方法排在第一位的比例，远低于此前的参照集。

| 数据集 | Acc@1 |
|---|---|
| 此前的 held-out 集 | 100% |
| Stage B 单跳对照 | 100% |
| 主实验四批合计 | 37.4% |
| 第 3–4 批（采用 "no local trace" 规则构造） | 24.8% |
| 第 4 批 | 20.0% |

故障方法通常仍排在前面：多数排错的运行里它排第二，92.8% 的运行里它在前三名。

## Acc@1 by set / 各数据集的 Acc@1

Acc@1 is the share of answered runs whose ranking puts the gold, the injected faulty method, first. No valid run timed out.
Acc@1 指已作答的运行中，把 gold（注入故障的方法）排第一的比例。所有有效运行均无超时。

| Set (gpt-5.5) / 数据集 | Acc@1 |
|---|---|
| Held-out set, 9 earlier constructed instances (recipes HA/HB/HC) / held-out 集，9 个此前构造的实例（HA/HB/HC 配方） | 27/27 = 100% |
| Stage B C00, single-hop control / 单跳对照 | 15/15 = 100% |
| Stage B C01 | 14/15 = 93.3% |
| Stage B C10, the recipe used in the main run / 主实验所用配方 | 3/15 = 20.0% |
| Stage B C11 | 4/15 = 26.7% |
| **Main run, batch 1 / 主实验第 1 批** | 19/40 = 47.5% |
| **Main run, batch 2 / 第 2 批** | 33/50 = 66.0% |
| **Main run, batch 3 ("no local trace" rule) / 第 3 批（"no local trace" 规则）** | 24/85 = 28.2% |
| **Main run, batch 4 (same rule) / 第 4 批（同一规则）** | 12/60 = 20.0% |
| **Main run, all batches / 主实验合计** | **88/235 = 37.4%** |

Where the gold landed in the 235 answered main-run runs / 主实验 235 次已作答运行中 gold 的排名：

| Gold rank / 排名 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Runs / 运行数 | 88 | 125 | 5 | 5 | 2 | 8 | 2 |

The mean reciprocal rank is 0.661. / 平均倒数排名（MRR）为 0.661。

## The supervisor's KPI / 导师设定的 KPI

**EN.**
- **Shift.** A run is a shift when the gold is not ranked first.
- **Success.** An instance succeeds when at least one of its 5 runs shifts.

**47 validated instances tested; 38 with at least one shift; 147 of 235 runs shifted.**

**中文。**
- **Shift（排名下移）：** 一次运行中 gold 没有排第一，即为一次 shift。
- **Success（成功）：** 一个实例的 5 次运行中至少有一次 shift，即为成功。

**共测试 47 个通过验证的实例，其中 38 个至少有一次 shift，235 次运行中有 147 次 shift。**

| Batch / 批次 | Validated / 验证通过 | With ≥1 shift / 至少一次 shift | Shifted / answered runs / shift 运行数 |
|---|---|---|---|
| 1 | 8 | 7 | 21/40 |
| 2 | 10 | 5 | 17/50 |
| 3 ("no local trace" rule / 规则) | 17 | 15 | 61/85 |
| 4 (same rule / 同一规则) | 12 | 11 | 48/60 |
| **Total / 合计** | **47** | **38** | **147/235** |

| Project / 项目 | Instances tested / 测试实例 | With ≥1 shift / 至少一次 shift |
|---|---|---|
| Lang | 32 | 27 |
| Math | 6 | 4 |
| Closure | 6 | 6 |
| Chart | 2 | 1 |
| JacksonCore | 1 | 0 |

## How the accuracy drops / 准确率如何下降

**EN.**
- **One error pattern.** In all 147 misranked runs, gpt-5.5 ranked the entry-point (facade) method first, that is, the existing method
  the failing test calls. In almost all of them it had already displayed and read the faulty method.
- **What it goes with** (pattern seen after batch 2, then checked on new instances). Shifts concentrate where the injected
  omission leaves no visible trace inside the faulty method, for example a parameter that cannot change the result, a dead local
  or decision, a visibly incomplete set of cases, or a contradiction with its own documentation. We froze this as a construction rule before building batches 3 and 4. The pre-registered readings were met: batch 3
  shifted on 15 of 17 instances (SUPPORTED), and batch 4 on 11 of 12 (REPLICATES).

**中文。**
- **单一错误模式。** 在全部 147 次排错的运行中，gpt-5.5 都把入口（facade）方法排在第一，也就是失败测试调用的那个已有方法。几乎所有这些运行里，它其实已经显示并读过故障方法。
- **相关规律**（第 2 批后观察到，随后在新实例上检验）。shift 集中出现在注入的遗漏没有在故障方法内部留下可见痕迹的情况，可见痕迹例如：不会影响结果的参数、无用的局部变量或判断、明显不完整的分支集合，或与自身文档的矛盾。我们在构造第 3、4 批之前把这一点冻结为构造规则。预注册的判定都达到了：第 3 批 17 个实例中 15 个 shift（SUPPORTED），第 4 批 12 个中 11 个（REPLICATES）。

## Important caveats / 重要说明

**EN.**
1. **Different instance sets.** The 100% figures come from other instance sets, not from these same 47 bugs without the
   transformation. As instructed, the main run has no baseline arm, so it cannot show how much of the drop on these bugs the
   construction causes, or which part of it: the hop chain, the misleading facade comment, or the omission type. The only same-bug
   comparison is Stage B (3 bugs): the single-hop control C00 scored 15/15, against 3/15 for C10.
2. **Consistency checks, not causal tests.** The batch-3 and batch-4 readings are consistency checks of a hypothesis, made without a
   control arm.
3. **Constructed instances.** The instances are real Defects4J bug identities with a synthetic injected fault, not the original
   Defects4J bugs.

**中文。**
1. **实例集不同。** 100% 来自其他实例集，而不是这 47 个 bug 未经变换时的结果。按要求，主实验没有设置基线组，所以无法说明这些 bug 上的下降有多少由构造造成，或由构造中的哪一部分造成：调用链、误导性的 facade 注释，还是遗漏类型。唯一的同一 bug 对比来自 Stage B（3 个 bug）：单跳对照 C00 为 15/15，C10 为 3/15。
2. **一致性检验，而非因果检验。** 第 3、4 批的判定是对一个假设的一致性检验，并没有对照组。
3. **构造的实例。** 实例使用真实的 Defects4J bug 身份，但故障是人工注入的，并不是 Defects4J 原有的 bug。

## Cost and next steps / 成本与下一步

**EN.**
- **Cost.** Total spend is $159.58 recorded, $163.95 including estimates, within the $200 ceiling.
- **Candidate pool.** The pool of eligible bugs is used up. Of the 23 left, 9 could only reuse a facade method already in use, and 14
  have only targets that already failed to build in a sibling bug.
- **Decisions needed.**
  1. Whether to widen the pool, for example to the projects excluded for slow test suites.
  2. Whether to add a baseline arm, so the drop can be attributed to a component.
  3. Whether to run GPT-5.6.

**中文。**
- **成本。** 总花费为 $159.58（已记录），含估算为 $163.95，在 $200 上限之内。
- **候选池。** 符合条件的 bug 池已经用完。剩下的 23 个中，9 个只能复用已用过的 facade 方法，14 个的目标方法已在共享该方法的其他 bug 中构造失败。
- **需要决定。**
  1. 是否扩大候选池，例如纳入因测试太慢而排除的项目。
  2. 是否加入基线组，以确定准确率下降由哪个部分造成。
  3. 是否运行 GPT-5.6。

Sources: `main-run/MAIN_RUN_RUNS.csv`, `main-run/MAIN_RUN_RESULTS.csv`, `analysis/per_run.json`, `main-run/SUPERVISOR_PROGRESS_UPDATE.md`
and `AMENDMENTS.md` (W23–W41).
数据来源：`main-run/MAIN_RUN_RUNS.csv`、`main-run/MAIN_RUN_RESULTS.csv`、`analysis/per_run.json`、`main-run/SUPERVISOR_PROGRESS_UPDATE.md` 和
`AMENDMENTS.md`（W23–W41）。
