# 第二批实验任务书（Phase E，给 Codex）

日期：2026-10-07。用户已明确授权本批新实验。背景和理由见 `第一批分析结果_20261007.md`。

## 0 总则

1. 遵守仓库 `AGENTS.md`：冻结方案、`FROZEN_METHOD.json`、核心 MATLAB 算法及已保存的实验结果一律不改。新代码与新输出全部放在新目录 `D:\论文集\phaseE\`（仓库内对应 `phaseE/`）。
2. **不要直接调用会写入冻结目录的驱动。** `phaseX3_one.m` 会写入 `phaseD/X3_real/tracks/` 和 `spectra/`，新驱动需要复制它的逻辑，并把输出路径改到 `phaseE/`。`phaseX2_one.m`、`phaseX1_one.m` 不写文件，可以参照它们写新的单条驱动。
3. 冻结的修正模块只按原样调用：`phaseD_ada(y,fe,fam,u0,idx,M.P,t,30,.04,'local','A')`。不设幅度界的版本按 `phaseX1_one.m` 中 `fu.lb=-Inf; fu.ub=Inf` 加 `estimate_proposed_T` 的写法。族用 `build_family_T(t,checks,anchor,M.B2,10,T,1)`。所有参数取自 `phaseX_settings`。
4. 任务 B–F 运行前，先写 `phaseE/PREREGISTRATION_PhaseE_20261007.md`，写定种子规则、记录数、方法列表、指标和统计口径，之后不再改动；任务 A 只导出已有结果，不需要预注册。
5. 每个任务目录包含 `run_config.json`、逐条 CSV、`README.md`（说明各列）和 SHA-256 清单。CSV、MD 和脚本提交到仓库；大体积的 MAT/H5 留在本机，在 README 中写明路径和 SHA-256。
6. 统计口径沿用 Phase D/X：同记录配对；场景与信噪比组合等权；以种子为单位在场景内成簇重抽样 2000 次，给出逐项 95% 区间。

## 0.1 预检

在本机用当前环境重跑 X2 的 3 条记录（如 S0/−16 dB/rid 1、S2/−20 dB/rid 7、S0/−8 dB/rid 50），确认 `input_hash`、`eta_in`、`eta_out` 与 `phaseD/X2_frontend/X2_records.csv` 一致（η 差 < 1e-9）。不一致就停下，报告差异。

## 任务 A：导出逐记录轨迹并计算理论指标（最先做，不需要新仿真）

目的：用冻结代码产生的真实前端轨迹，检验"增益取决于前端误差中的慢分量"这一预测（第一批报告 1.4 节）。

1. 从本机 `D:\论文集\phaseD\X2_frontend\chunks\` 读取每条记录的 `S.details{k}`（k = VS, MFT, SUV, V0），取 `input_g`（模块输入）和 `ada.out.g`（模块输出）。
2. 用同一种子重新生成真值：`seed=cfg.master_seed+54e6+1e4*cfg.scene_code.(scene)+rid; rec=simulate_baseband_T(cfg,scene,snr,seed,'eval',300)`，取 `rec.truth.gtrue`，并检查 `input_hash` 与 X2_records 一致。
3. 写出：
   - `phaseE/E1_trajexport/traj_export_X2.h5`：数据集 `/truth`（1400 × 6000）、`/input`（5600 × 6000）、`/output`（5600 × 6000），float64，单位 Hz（基带），20 Hz 网格，t = n/20；
   - `phaseE/E1_trajexport/traj_export_X2_index.csv`：每行一个（记录，前端），列为 `row, truth_row, scene, snr_db, record_id, seed, frontend, eta_in, eta_out, input_usable`。`row` 和 `truth_row` 从 0 开始。
4. 运行 `python phaseE/scripts/theory_metrics.py phaseE/E1_trajexport/traj_export_X2`（脚本随本任务书提供）。脚本会重算 η，并与保存值比较，差值必须 < 1e-6，否则说明导出或评价窗口与冻结代码不一致，需要排查。
5. 提交 `traj_export_X2_theory_metrics.csv` 和 `traj_export_X2_theory_summary.csv`；H5 文件留在本机。
6. 如果 X1 的分块里也保存了逐记录轨迹，用同样的格式导出 `traj_export_X1_T{150,300,450,600}`。

## 任务 B：跨前端扩展（使用与 X2 完全相同的 1400 条记录）

目的：(1) 比较 PC-TBD 的两种频率读出；(2) 加入一个更强的功率型前端；(3) 用真值起点检验估计下限。

- **记录**：种子规则与 X2（phase 54）完全相同，逐条核对 `input_hash` 与 X2_records 一致。这是在同一批记录上的扩展，目的是配对比较，不是独立确认，README 中写明。
- **新前端**（全部从 u = 0 出发，接冻结的 ADA 模块）：
  1. `SUV_GRID`：PC-TBD 按原文用状态网格读出频率。`suv=estimate_suvorova_D(...)` 中已有 `suv.g_bin`；锚轨迹 = `suv.g_bin`，检查点 = `suv.t_block`。
  2. `DHMM`：文献 [12]（罗昕炜等 2022，PDF 在 `06_文献/PDF_讨论与背景/`）的单线谱版本。新写 `estimate_dhmm.m`：在 LOFAR 上用一维 HMM，状态转移矩阵按序列一阶导数实时调整（按原文公式）；多线谱循环提取和生灭判断不需要（单线谱场景），在实现说明表中逐项标明"同 [12]"或"本文改编"。分帧与观测得分尽量与 VIT 一致。原文没有给定的参数，只在新的开发记录上确定（种子 phase 56：S0/S2 × {−18, −16, −14} dB × 20 条），准则是 DHMM 轨迹本身的 η 中位数，不看接模块之后的增益；确定后冻结，再运行任务 B。
  3. `ORACLE`：锚轨迹 = `rec.truth.gtrue`，检查点 = `fe.tc`。只用于检验估计下限，不作为可比较的前端。
- **回归检查**：在每个场景 × 信噪比单元的前 5 条记录上，按原样重跑 VS 和 SUV，确认与 X2_records 一致。
- **输出**：`phaseE/E2_frontend_ext/E2_records.csv`，列与 X2_records 相同。同时按任务 A 的格式导出这三种前端的 `traj_export_E2`，并运行 `theory_metrics.py`。

## 任务 C：积累时长扩展（使用与 X1 完全相同的记录）

目的：检验 PC-TBD 在更长记录上的表现，以及真值起点下限随时长的变化。

- **记录**：种子规则与 X1（phase 53）相同；T ∈ {150, 300, 450, 600} s；S0/S2；−20、−17、−14 dB；每个场景 100 个种子；逐条核对 `input_hash` 与 X1_records 一致。
- **新增**：`SUV`（锚轨迹 = `suv.g`，检查点为相邻块中点，与 `phaseX3_one.m` 一致，从 u = 0 出发接 ADA）和 `ORACLE`（同任务 B）。PC-TBD 的块长保持冻结的 8 s。
- **输出**：`phaseE/E3_duration_ext/E3_records.csv`，并导出 `traj_export_E3_T*`、运行理论指标。

## 任务 D：真实背景注入（重做）

**重要：旧的注入实验不能再用。** 旧 `real_config.m` 把参考频率设在 100 Hz，并认为 98–102 Hz 内没有发射线谱，但它只核对了第 1 组。100 Hz 属于深源第 3 组（128 dB），而旧实验的 900、1200、1800 s 三个背景窗正好是 100 Hz 线谱通过可见性筛选的时段。

- **背景频带**：避开深源全部 5 组（第 1 组 49 64 79 94 112 130 148 166 201 235 283 338 388 Hz，第 2–5 组依次加 3、6、9、12 Hz）和浅源（109 127 145 163 198 232 280 335 385 Hz）。主用中心频率 263.5 Hz 和 315 Hz，这两处 ±10 Hz 的基带范围内没有任何发射频点。可选 188 Hz：±2 Hz 内无发射频点，但 ±10 Hz 的边缘有 178 和 198 Hz。用 `phaseA_load_baseband` 提取（320 s 的段长使这些中心频率落在 DFT 频点上），通道 9，与论文相同。
- **背景窗**：每个频带取 10 个不重叠的 300 s 窗（0–300 至 2700–3000 s）。预注册一条筛查规则，在注入之前执行：在 10 s Hann 窗、1 s 帧移的 LOFAR 上，中心 ±2.5 Hz 内的最大 dB 值减去 ±(3–8) Hz 环带的中位数，小于 8 dB 才保留；不通过的窗口记录在案并排除。
- **归一化**：缩放背景，使 |FFT(z)|²/N 在 |f| ≤ 2 Hz 各频点上的均值为 1，与仿真中单位功率白噪声的谱密度相同。注入幅度 A = 10^(SNR/20)，与仿真相同。
- **目标**：两类，都取 a(t) = 1。
  1. 仿真几何：与 `simulate_baseband` 相同的生成器和抽样范围。
  2. GPS 形状：基带频率 g(t) = f_gps_100(t0 + t) − 100 + c，其中 f_gps_100 取自 `当前主线精选_20261003/04_实测数据/表/A4_groundtruth.csv`，t0 为该背景窗的起点，c 在 ±0.05 Hz 内均匀抽取；相位为 2π 乘以 g 的累积梯形积分，再加上 [0, 2π) 内均匀抽取的初相。这一类给出真实航迹下的非匀速频率变化。
- **规模**：信噪比 −20 至 −14 dB，间隔 1 dB；每个窗口、每类目标注入 20 次，几何、偏移和初相在各信噪比之间配对。种子用新的 phase 57，并检查与已用种子不相交。
- **前端与方法**：VS（VIT–LPS）、V0、MFT、SUV，各接 ADA 模块；任务 B 完成后加入 SUV_GRID 和 DHMM。
- **指标**：用已知的注入目标计算 η，与仿真相同；同时报告观测谱峰和 `input_usable`。统计时以背景窗为成簇单位重抽样。按任务 A 的格式导出轨迹并运行 `theory_metrics.py`。
- **输出**：`phaseE/E5_inject/`。README 中写明：注入信号没有经过真实信道，这一实验检验的是真实噪声下的表现，不能检验信道相位起伏。

## 任务 E：实测强线引导锚定

目的：把弱线的锚轨迹放到发射线谱的预测位置，再由模块逐线修正，检验能否在前端丢线的案例上得到增益。

1. 在仓库根目录运行 `python phaseE/scripts/guided_anchors.py`，生成 15 个弱线案例的引导轨迹（`phaseG_guided/anchors/*.csv`，绝对频率，20 Hz 网格）。生成后把该目录移到 `phaseE/E4_guided_real/anchors/`。
2. 新驱动参照 `phaseX3_one.m`：读取 `screen_inputs/f*_s*.mat` 中的 y，运行 `phaseX_front`，令锚轨迹 = `guided_med_abs_hz − fref`，检查点 = `fe.tc`，族用 `build_family_T(...)`，从 u = 0 出发分别运行：
   - `G_ADA`：冻结的 ADA；
   - `G_UNB`：不设幅度界的版本。第一批分析显示，各线相对引导轨迹有 20–60 mHz 的频率特有偏离，±0.02/0.04 Hz 的幅度界可能不够。
   - 另用 `guided94_abs_hz` 作锚轨迹再跑一遍 `G94_ADA`。
3. 指标沿用 `phaseX3_metrics`（相对未补偿周期图的谱峰、峰值频率、突出度、−3 dB 宽度）。另外报告零残余频率 ±0.01 Hz 内的峰值：引导轨迹就在发射线谱的预测位置，这个值直接对应发射线谱本身。
4. 输出写到 `phaseE/E4_guided_real/`（records、tracks、spectra），不要写进 `phaseD/X3_real/`。

## 任务 F（可选）：分阶段与单阶段求解的消融

在任务 B 的 VS 记录上，只用 h = T − 10 一个阶段，迭代与目标计算的上限取三个阶段之和，其余条件不变。比较 η 和耗时。修订稿自己承认没有做过这一比较，审稿人可能会问。

## 交付与回传

- 目录：`phaseE/{E0_preflight, E1_trajexport, E2_frontend_ext, E3_duration_ext, E4_guided_real, E5_inject, E6_staging, scripts}`。
- 把本任务书放到 `phaseE/TASKS_PhaseE_20261007.md`，`theory_metrics.py` 和 `guided_anchors.py` 放到 `phaseE/scripts/`。
- 建议执行顺序：0.1 → A → E（快，只用已有输入）→ B → C → D（需要原始 SIO 文件和预注册）→ F。
- 每完成一个任务就推送一次，在提交说明里写清任务编号。我从仓库读取 CSV 和报告继续分析，不需要 H5 文件。
- 遇到与本任务书不一致的地方（函数签名、分块里缺字段、种子核对失败），先停下来，把情况写进对应任务的 README 并推送，不要自行改冻结代码去适配。
