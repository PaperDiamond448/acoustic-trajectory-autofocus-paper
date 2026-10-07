# Phase D 完整报告：D、C、X1–X3 与 Y

状态：**全部阶段完成，停止。确认分支 C-A1 保持不变。** 用户分别核对停止点 1、停止点 2 后放行本轮。X 阶段只作冻结方法的外部验证，没有任何方法参数回调。

## 冻结方法与证据链

最终方法 `ADA_local_c04_t30_A`，Δ=10 s，基础修正半径 0.02 Hz；最长边界驻留 ≥30 s 时，仅放宽顶边节点及其相邻节点至 0.04 Hz，完整三阶段重跑；显式保留上一轮解，仅按全长目标选择。P=T/10+1；λ=λ₀(P−2)/19·(300/T)·(15/10)³；每阶段预算 round(240·max(1,P/21)) 次迭代 / round(1000·max(1,P/21)) 次目标调用。候选选择不使用 η 或谱峰。

主方案、补充、冻结文件及核心算法指纹均保持不变，完整检查见 [Y_compute/INTEGRITY_AUDIT.json](D:/论文集/phaseD/Y_compute/INTEGRITY_AUDIT.json)。Set 5 120 dB 为推断值，浅源源级未公布。

开发记录见 [D_dev/DEV_REPORT.md](D:/论文集/phaseD/D_dev/DEV_REPORT.md)，确认记录见 [C_confirm/CONFIRM_REPORT.md](D:/论文集/phaseD/C_confirm/CONFIRM_REPORT.md)，两次独立审核见 [STOP1_audit_Claude_20261004/STOP1_AUDIT.md](D:/论文集/phaseD/STOP1_audit_Claude_20261004/STOP1_AUDIT.md) 与 [STOP2_audit_Claude_20261004/STOP2_AUDIT.md](D:/论文集/phaseD/STOP2_audit_Claude_20261004/STOP2_AUDIT.md)。

## 确认阶段保持的正式结论

phase 52 的 2800 条新记录确认四个终点全部通过：P1 ADA−F02 η +0.009348 [0.008078, 0.010685]；P2 ADA−UNB η +0.002339 [0.000059, 0.004814]，满足预注册合并非劣界 −0.005；P3 实质退化率差 −17.93 个百分点；S1 系统性退化单元 0/14。因此自适应为主方法，E4a 为旧配置对照。

**场景代价必须保留**：S0 中 ADA−UNB η −0.005982 [−0.007505, −0.004510]，固定 0.04 Hz 也优于 ADA；不可写成每个场景均不劣于去盒界。确认的非劣终点按合并值预注册。其稳健性收益主要来自有干扰场景。

## X1：积累时长仿真

phase 53；S0/S2×SNR{−20,−17,−14}×100个种子×T{150,300,450,600}=2400 条，四方法共 9600 行。P 分别为 16/31/46/61，阶段块长 20/60/T−10。统计先对各单元求均值再等权，2000次场景内种子成簇 bootstrap，seed=20261053，同簇携带所有 SNR 与 T。以下是描述性外部验证，没有通过/失败判定。

| 场景 | T(s) | P | η_SMR | η_F02 | η_UNB | η_ADA | ADA−SMR η [95%CI] | ADA调用中位(s) | p90(s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | 150 | 16 | 0.5813 | 0.6634 | 0.6787 | 0.6671 | 0.0858 [0.0715, 0.1009] | 0.6471 | 1.2044 |
| S0 | 300 | 31 | 0.4901 | 0.6475 | 0.6563 | 0.6522 | 0.1621 [0.1469, 0.1774] | 3.4323 | 8.4845 |
| S0 | 450 | 46 | 0.4520 | 0.6462 | 0.6550 | 0.6507 | 0.1986 [0.1826, 0.2163] | 7.0498 | 25.5271 |
| S0 | 600 | 61 | 0.4058 | 0.6521 | 0.6599 | 0.6553 | 0.2496 [0.2338, 0.2657] | 15.0645 | 52.2238 |
| S2 | 150 | 16 | 0.3536 | 0.3432 | 0.3336 | 0.3636 | 0.0100 [0.0013, 0.0186] | 0.8660 | 1.6492 |
| S2 | 300 | 31 | 0.4135 | 0.5676 | 0.5740 | 0.5784 | 0.1649 [0.1539, 0.1762] | 3.5349 | 6.8337 |
| S2 | 450 | 46 | 0.4078 | 0.6406 | 0.6485 | 0.6493 | 0.2414 [0.2285, 0.2547] | 7.4195 | 16.9030 |
| S2 | 600 | 61 | 0.3907 | 0.6457 | 0.6571 | 0.6584 | 0.2677 [0.2517, 0.2844] | 17.9170 | 39.6454 |

η、观测谱峰、相对 SMR 的谱峰和 η 增量、各部分时间与完整区间见 [X1_duration/X1_summary.csv](D:/论文集/phaseD/X1_duration/X1_summary.csv) 和 [X1_duration/X1_cell_stats.csv](D:/论文集/phaseD/X1_duration/X1_cell_stats.csv)。所有记录见 [X1_duration/X1_records.csv](D:/论文集/phaseD/X1_duration/X1_records.csv)。时长同时增加样本数和节点数，约 T² 只是方案粗估，实际计时见表与曲线，不据此虚构测得的复杂度。

![X1](D:/论文集/phaseD/X1_duration/fig_X1_duration_efficiency_cost.png)

## X2：跨前端仿真

phase 54；1400 条新记录，四前端共 5600 行。VS 为 VIT→SMR 起步，MFT/SUV 从其最终轨迹的零修正起步，V0 为 VIT 直接接入；SUV 的检查点是相邻块中心之间的相位读出中点。入口可用性只依赖输入误差去均值后 ±0.1 Hz 覆盖率≥0.9，不删除任何记录。2000 次场景内种子成簇 bootstrap，seed=20261054。

| 前端 | 集合 | 记录数 | 等权单元Δη | CI下界 | CI上界 | 区间可估计 | 非空单元/14 | 记录加权Δη（描述） |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MFT | all | 1400 | 0.1060 | 0.1024 | 0.1099 | True | 14 | 0.1060 |
| MFT | input_usable | 474 | 不可估计 | 不可估计 | 不可估计 | False | 6 | 0.1168 |
| SUV | all | 1400 | 0.0079 | 0.0064 | 0.0094 | True | 14 | 0.0079 |
| SUV | input_usable | 1248 | 0.0078 | 0.0059 | 0.0097 | True | 14 | 0.0075 |
| V0 | all | 1400 | 0.1228 | 0.1175 | 0.1285 | True | 14 | 0.1228 |
| V0 | input_usable | 1256 | 0.1466 | 0.1391 | 0.1544 | True | 14 | 0.1320 |
| VS | all | 1400 | 0.1114 | 0.1055 | 0.1175 | True | 14 | 0.1114 |
| VS | input_usable | 1251 | 0.1364 | 0.1286 | 0.1445 | True | 14 | 0.1192 |

入口可用集合若有空单元或 bootstrap 抽样空单元，预定十四单元等权区间标为不可估计；记录加权均值作为另一个描述量明确列出，不代替预定估计量。SUV 只有入口可用合并区间上界<0才判定不适合接模块。

SUV 未满足“入口可用合并区间上界<0”的不适配条件；按实际方向和区间报告，不能由增益较小推成与其他前端等效。

逐前端×单元的入口/出口 η、谱峰增量、正值比例、扩张比例见 [X2_frontend/X2_summary.csv](D:/论文集/phaseD/X2_frontend/X2_summary.csv)；固定入口 η 分箱及计数见 [X2_frontend/X2_eta_bins.csv](D:/论文集/phaseD/X2_frontend/X2_eta_bins.csv)。

![X2](D:/论文集/phaseD/X2_frontend/fig_X2_frontend_recovery.png)

## X3：多线谱实测

先完成全部 33×10=330 候选的可见性筛选，再冻结全部 105 个通过案例、16 个时长窗口与主图角色，之后才运行任何实测模块。通过条件严格为 peak_excess>10 dB 且 ridge_continuity>0.6。每段独立提取频点中心 ±10 Hz/20 Hz 复基带，守护段 10 s，两端不足为0；LOFAR Hann L200/D20/NFFT8192，在完整0–3000 s拼接记录上计算，按帧中心归属300 s时段，与原A3帧支撑一致；初版逐段291帧遗漏跨段帧，在任何实测模块运行前纠正并留档。全部与旧A3的数值对照及翻转均列出，阈值未调整。

[X3_real/X3_visibility.csv](D:/论文集/phaseD/X3_real/X3_visibility.csv)、[X3_real/X3_FROZEN_TESTSET.csv](D:/论文集/phaseD/X3_real/X3_FROZEN_TESTSET.csv)、[X3_real/X3_TESTSET_FREEZE.json](D:/论文集/phaseD/X3_real/X3_TESTSET_FREEZE.json) 记录冻结证据；与旧 A3 对照见 [X3_real/X3_A3_comparison.csv](D:/论文集/phaseD/X3_real/X3_A3_comparison.csv)。103 Hz、900–1200 s 竞争脊案例保留且标注，不作为主图角色。

分组按预先列出的源级：弱线=Set2–5、强线=Set1、浅源单列；**Set5 120 dB 由每组低4dB推算，未见独立确认；浅源源级未公布**。实测主结论以弱线为准。不同频点与时间共享同一航次，全部汇总为中位数/IQR/正值个数，不做显著性检验。

各源级的可见性覆盖如下。弱线结果仅涵盖通过筛选的15个案例，其中 Set5 只有1个通过案例，120 dB 仍为推断源级；不能推广为全部弱线或每个源级均已验证。

| 分组 | Set | 筛选候选数 | 通过数 |
| --- | --- | --- | --- |
| shallow | 0 | 30 | 30 |
| strong | 1 | 60 | 60 |
| weak | 2 | 60 | 4 |
| weak | 3 | 60 | 7 |
| weak | 4 | 60 | 3 |
| weak | 5 | 60 | 1 |

详细覆盖见 [X3_source_set_coverage.csv](D:/论文集/phaseD/X3_real/X3_source_set_coverage.csv)。正值个数按原指标严格 >0 计数，接近浮点舍入量级的正值不能解释为实质改善。

| 组 | 配对 | 总数 | 谱峰增量中位(dB) | Q1 | Q3 | 正值个数 |
| --- | --- | --- | --- | --- | --- | --- |
| shallow | MFT_FM-MFT | 30 | 0.2566 | 0.0117 | 1.0856 | 30 |
| shallow | SUV_FM-SUV | 30 | 0.0160 | 0.0078 | 0.0222 | 26 |
| shallow | VS_FM-F02 | 30 | 0.0000 | 0.0000 | 0.0000 | 0 |
| shallow | VS_FM-MFT | 30 | 0.2290 | -0.0151 | 1.0222 | 18 |
| shallow | VS_FM-SMR | 30 | 0.0687 | 0.0241 | 0.2910 | 30 |
| shallow | VS_FM-UNB | 30 | 0.0000 | -0.0000 | 0.0000 | 6 |
| strong | MFT_FM-MFT | 60 | 0.7031 | 0.0304 | 1.4356 | 57 |
| strong | SUV_FM-SUV | 60 | 0.0254 | 0.0137 | 0.0643 | 57 |
| strong | VS_FM-F02 | 60 | 0.0000 | 0.0000 | 0.0000 | 4 |
| strong | VS_FM-MFT | 60 | 0.4449 | 0.0180 | 1.3449 | 48 |
| strong | VS_FM-SMR | 60 | 0.1771 | 0.0516 | 0.7274 | 58 |
| strong | VS_FM-UNB | 60 | 0.0000 | -0.0078 | 0.0000 | 23 |
| weak | MFT_FM-MFT | 15 | 3.2709 | 2.3733 | 4.4401 | 14 |
| weak | SUV_FM-SUV | 15 | 0.1430 | 0.0509 | 0.3807 | 15 |
| weak | VS_FM-F02 | 15 | 0.0000 | 0.0000 | 0.0547 | 4 |
| weak | VS_FM-MFT | 15 | 2.4274 | 1.5652 | 4.0598 | 12 |
| weak | VS_FM-SMR | 15 | 1.7437 | 0.9286 | 2.8288 | 15 |
| weak | VS_FM-UNB | 15 | -0.0000 | -0.1263 | 0.0146 | 7 |

所有指标沿用 B1：矩形、无平滑、完整记录 FFT 功率 |FFT|²/N，候选带±1.5 Hz；谱峰相对于同案例周期图峰，突出度底为离峰0.5–1.5 Hz候选带内中位数，3dB宽度线性插值。GPS 按频点/100缩放，只给 [5,T−5) 的平均偏移与去均值 RMS，不参与筛选，也不是接收轨迹真值。完整突出度/宽度、负案例和GPS结果见 [X3_real/X3_cases.csv](D:/论文集/phaseD/X3_real/X3_cases.csv)、[X3_real/X3_increments.csv](D:/论文集/phaseD/X3_real/X3_increments.csv)、[X3_real/X3_summary.csv](D:/论文集/phaseD/X3_real/X3_summary.csv)。

主图按可见性冻结为 {"a": {"tone_hz": 133, "start_s": 1200, "selection": "lowest visible weak peak_excess; ties smallest tone/earliest start"}, "c": {"tone_hz": 49, "start_s": 1200, "selection": "smallest passed strong tone at role-a interval"}, "b": {"tone_hz": 100, "start_s": 600, "end_s": 2100, "segments": 5, "selection": "longest maximal visible weak run; ties smallest tone/earliest start"}}。全部最大连续弱线段均取预定嵌套窗口，并另保留方案明确指定的 100 Hz、900–1500 s 旧案例替换；旧文件不覆盖，新方法结果见 [X3_real/X3_duration.csv](D:/论文集/phaseD/X3_real/X3_duration.csv)。

![实测预定谱图](D:/论文集/phaseD/X3_real/fig_X3_prespecified_spectra.png)

轨迹图的 LOFAR 背景逐300 s段独立生成，每段291帧，段间留白明确显示缺失跨段帧；这是展示方式，可见性筛选使用上述全长连续 LOFAR。GPS 为参考而非真值。时长图保留全部16个冻结窗口，150 s窗口存在负增益，增益随时长也不必单调。

![实测轨迹与时长](D:/论文集/phaseD/X3_real/fig_X3_trajectory_duration.png)

![实测全案例](D:/论文集/phaseD/X3_real/fig_X3_all_case_gains.png)

## Y：计算量与运行环境

CPU 12th Gen Intel(R) Core(TM) i5-1235U；10 核/12 逻辑处理器，MATLAB R2023a。数值计算用6个Processes workers，数值模块按阶段执行，X3 只读筛选复核曾与少量 X1 任务并行，见环境记录。单次调用时间为并行负载下墙钟，不能解释为孤立串行基准；批次墙钟另列。

| component | n | median | p90 |
| --- | --- | --- | --- |
| frontend | 2800 | 0.2170 | 0.2767 |
| VIT | 2800 | 0.1225 | 0.1545 |
| family | 2800 | 0.0095 | 0.0125 |
| SMR | 2800 | 0.2001 | 0.2976 |
| BTA_round0 | 2800 | 2.6526 | 3.8205 |
| BTA_expansion_given_trigger | 661 | 2.4538 | 3.9849 |
| BTA_total | 2800 | 2.7990 | 5.8556 |
| BTA_extra_over_SMR_fraction_T | 2800 | 0.0093 | 0.0195 |

C 扩张率、X1 时间–T 曲线、全部 X3 案例时间分别见 [Y_compute/Y_summary.csv](D:/论文集/phaseD/Y_compute/Y_summary.csv)、[Y_compute/Y_TIMING.json](D:/论文集/phaseD/Y_compute/Y_TIMING.json) 和逐记录表。D1 时间–P 曲线保留于 [D_dev/fig_D1_eta_runtime.png](D:/论文集/phaseD/D_dev/fig_D1_eta_runtime.png)，数据汇总见 [Y_compute/D1_time_vs_P.csv](D:/论文集/phaseD/Y_compute/D1_time_vs_P.csv)。




## 正式主结果、系数交付与环境计时补充

确认阶段最终主方法相对 SMR 的合并 η 增量为 **+0.193628**，95% 区间 [0.186519, 0.201102]；谱峰增量为 **+2.259411 dB**，95% 区间 [2.191569, 2.330290]；14/14 单元 η 增量区间下界大于零。这里取自已核对的 phase 52 确认结果，不使用开发集或旧 E4a 的值；S0 相对 UNB 的负差限制仍如正文所述。

独立系数、起点与边界矩阵均为 v7.3：[X1_duration/coefficients_T150.mat](D:/论文集/phaseD/X1_duration/coefficients_T150.mat)、[X1_duration/coefficients_T300.mat](D:/论文集/phaseD/X1_duration/coefficients_T300.mat)、[X1_duration/coefficients_T450.mat](D:/论文集/phaseD/X1_duration/coefficients_T450.mat)、[X1_duration/coefficients_T600.mat](D:/论文集/phaseD/X1_duration/coefficients_T600.mat)、[X2_frontend/coefficients_T300.mat](D:/论文集/phaseD/X2_frontend/coefficients_T300.mat)、[X3_real/coefficients_T150.mat](D:/论文集/phaseD/X3_real/coefficients_T150.mat)、[X3_real/coefficients_T300.mat](D:/论文集/phaseD/X3_real/coefficients_T300.mat)、[X3_real/coefficients_T450.mat](D:/论文集/phaseD/X3_real/coefficients_T450.mat)、[X3_real/coefficients_T600.mat](D:/论文集/phaseD/X3_real/coefficients_T600.mat)；同目录各 `*_keys.csv` 标识阶段、窗口、前端与方法。环境适配仅改变父进程组合分块的保存表示；每个工作记录原始 S 保留 v7.3，所有已有提交文件保持原样。逐字段保存等价性见 [WORKER_CHUNK_BRIDGE_AUDIT.json](D:/论文集/phaseD/Y_compute/WORKER_CHUNK_BRIDGE_AUDIT.json)，适配器和旧数据指纹见 [SUPPLEMENT_INTEGRITY_AUDIT.json](D:/论文集/phaseD/Y_compute/SUPPLEMENT_INTEGRITY_AUDIT.json)。

计算量表中的方法时间为六工作进程同时负载下的单次调用墙钟。完成短批次的工作时间包含数值调用、缓存读取和保存，不含 MATLAB/进程池启动，也不能覆盖失败批次已提交而尚未生成完成标记的工作。最终原驱动 X1/X2 配置中的 elapsed_wall_seconds 在本轮仅为只读组装时间，不是整个阶段执行时长。日志跨度受重启间隔、归档和覆盖影响，仅作环境开销描述，不能作为精确总耗时或充入方法时间。唯一日志内容已去重，见 [Y_batch_runtime.csv](D:/论文集/phaseD/Y_compute/Y_batch_runtime.csv)、[ENVIRONMENT_LOG_INVENTORY.csv](D:/论文集/phaseD/Y_compute/ENVIRONMENT_LOG_INVENTORY.csv) 和 [ENVIRONMENT_RUNTIME_SUMMARY.json](D:/论文集/phaseD/Y_compute/ENVIRONMENT_RUNTIME_SUMMARY.json)。X3 连续 LOFAR 筛选复核曾与少量 X1 任务并行，属于已记录的临时 CPU 负载。

X3 首次提交全部 105 个常规案例用了 385.59 s；最终配置的 96.98 s 是重新读取这些完整案例并完成 16 个时长窗口的恢复驱动耗时，不能解释为完整 X3 总耗时。首个时长批次未提交的工作、进程启动及退出开销单独留存。原 105 个常规分块逐一指纹保持，见 [X3_PRE_DURATION_EXIT.json](D:/论文集/phaseD/Y_compute/X3_PRE_DURATION_EXIT.json)；16 个时长工作文件与提交分块逐字段相同，见 [REAL_WORKER_CHUNK_BRIDGE_AUDIT.json](D:/论文集/phaseD/Y_compute/REAL_WORKER_CHUNK_BRIDGE_AUDIT.json)。已观察到的完成标记之后的退出码见 [ENVIRONMENT_EXIT_EVENTS.csv](D:/论文集/phaseD/Y_compute/ENVIRONMENT_EXIT_EVENTS.csv)，X1 组装完成后的退出见 [X1_ASSEMBLY_EXIT.json](D:/论文集/phaseD/Y_compute/X1_ASSEMBLY_EXIT.json)。

求解状态按保存的方法行列出如下；复用的 F02 结果可同时出现在自适应未触发行中，这些行数不是独立求解次数。预算触顶与硬失败分别列示，不删除相应结果，也不追加预算。完整键表见 [SOLVER_STATUS_BY_METHOD.csv](D:/论文集/phaseD/Y_compute/SOLVER_STATUS_BY_METHOD.csv)。

| stage | method_or_frontend | method_rows | hard_fail_marked_rows | budget_cap_marked_rows |
| --- | --- | --- | --- | --- |
| X1 | ADA_local_c04_t30_A | 2400 | 0 | 0 |
| X1 | F02 | 2400 | 0 | 0 |
| X1 | SMR | 2400 | 0 | 0 |
| X1 | UNB | 2400 | 0 | 0 |
| X2 | MFT | 1400 | 0 | 0 |
| X2 | SUV | 1400 | 0 | 0 |
| X2 | V0 | 1400 | 0 | 0 |
| X2 | VS | 1400 | 0 | 0 |
| X3 | F02 | 121 | 0 | 0 |
| X3 | MFT | 105 | 0 | 0 |
| X3 | MFT_FM | 105 | 0 | 0 |
| X3 | SMR | 121 | 0 | 0 |
| X3 | SUV | 105 | 0 | 0 |
| X3 | SUV_FM | 105 | 0 | 0 |
| X3 | UNB | 105 | 0 | 0 |
| X3 | VS_FM | 121 | 0 | 0 |

## X2 频率约束的检查点范围与附加采样诊断

§2.5 保留原 `Aineq/bineq`，§9.2 指定 VS/MFT/V0 的帧中心及 SUV 块中点。全量规定检查点的最大违约量为 3.469446952e-18 Hz，符合原 1e−6 求解可行性容差；保存轨迹按原公式重建的最大差为 0 Hz。原只读审计另加了“所有 20 Hz 采样点都在 ±2 Hz 内”的条件，它比注册的检查点条件严格。MFT 原实现也是分段线性插值；冻结族从 20 Hz 采样轨迹再次插值到检查点，非网格帧折点可能被平滑，故指定检查点通过不能直接认证全部采样点极值。最先发现的例子为 S0、−12 dB、rid31、MFT：采样极值 2.0000440341853913 Hz，但检查点违约为0，该入口不可用记录保留。

独立扫描覆盖 5600 个记录×前端及全部自适应轮：290 个轮记录、196 个记录×前端的采样极值超过 2+1e−6 Hz，最大 |g| 为 2.009949748744 Hz。全部越界均为 MFT，且入口均不可用。完整位置、轮次、入口分组和增量见 [X2_BOUND_DIAGNOSTIC_001_140.csv](D:/论文集/phaseD/Y_compute/X2_BOUND_DIAGNOSTIC_001_140.csv)。**这里没有裁剪轨迹、删记录、改指标或重调方法；X2 的 PASS 指方案规定的检查点与其他规则通过，不宣称所有前端的全部采样点都被严格 ±2 Hz 认证。** 这项附加限制也应在后续论文方法说明中明确，不能用图或合并指标掩盖。

## 交付范围

本轮交付 `PhaseD_X阶段完整核对包_20261004.zip`：X1–X3 与 Y 的逐记录结果、保存分块、独立系数矩阵、筛选与冻结表、图件三种格式、驱动与审计源码、日志、方案、冻结方法和确认摘要。它是供原工作目录配套使用的 X 阶段核对包，原始 SIO 航次数据、全部旧阶段原始结果与旧算法目录继续保留在本机原路径，不重复打包。逐文件 SHA-256 见 [FINAL_DELIVERY_MANIFEST.json](D:/论文集/phaseD/Y_compute/FINAL_DELIVERY_MANIFEST.json)，包内条目 SHA-256 与 CRC 见 [PACKAGE_VERIFICATION.json](D:/论文集/phaseD/Y_compute/PACKAGE_VERIFICATION.json)。

## 完整性、环境事件与停止

X1 初次进程在440条已提交记录后出现 Windows 0xc0000374 堆损坏退出。原44分块指纹逐一保持；原驱动在新 MATLAB 进程复用这些分块，仅对未提交任务从预注册种子和原预算起步，不接续损坏中间状态、不合并重试候选、不追加单次求解预算。环境事件记录 [Y_compute/X_INITIAL_ENVIRONMENT_EXIT.json](D:/论文集/phaseD/Y_compute/X_INITIAL_ENVIRONMENT_EXIT.json)；后续环境退出、文件接口适配与恢复均留存于同目录事件日志及 DEVIATIONS；工作文件与提交分块逐字段等价核验通过。核心、冻结文件、旧结果与两次独立审核文件保持不变。

全量只读核验覆盖种子、输入指纹、每行MAT/CSV、指标、缩放预算、局部支持与邻居、起点、显式上一轮候选、全长目标单调、未触发一致性。实测谱指标与GPS还由独立 NumPy 实现重算；所有负值和通过案例均保留。核验结果见 [Y_compute/INTEGRITY_AUDIT.json](D:/论文集/phaseD/Y_compute/INTEGRITY_AUDIT.json)、[X1_duration/SAVED_OUTPUTS_AUDIT.json](D:/论文集/phaseD/X1_duration/SAVED_OUTPUTS_AUDIT.json)、[X2_frontend/SAVED_OUTPUTS_AUDIT.json](D:/论文集/phaseD/X2_frontend/SAVED_OUTPUTS_AUDIT.json)、[X3_real/SAVED_OUTPUTS_AUDIT.json](D:/论文集/phaseD/X3_real/SAVED_OUTPUTS_AUDIT.json)、[X3_real/INDEPENDENT_REAL_METRICS_AUDIT.json](D:/论文集/phaseD/X3_real/INDEPENDENT_REAL_METRICS_AUDIT.json)。

图件调用已更新的 Nature Figure 2.8.0，PNG600dpi/PDF/SVG，面板对齐、字体、碰撞与最终视觉检查见 [Y_compute/qa/FIGURE_QA.json](D:/论文集/phaseD/Y_compute/qa/FIGURE_QA.json)。方案与补充不改；输出语义和恢复记录见 [DEVIATIONS.md](D:/论文集/phaseD/DEVIATIONS.md)。

**本轮工作到此停止，不再调整方法，不继续开展未经放行的新实验或改写论文。**
