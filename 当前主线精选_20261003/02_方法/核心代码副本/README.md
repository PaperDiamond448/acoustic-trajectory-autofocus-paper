# 核心代码副本（只读）

这里的 `.m` 文件是 2026-10-03 从原位置复制的**阅读副本**，用来对照公式。**不要在这里运行或修改。** 实验一律使用原路径的代码（Phase D 的 GPT 也按原路径调用），原路径如下。

## 公式 ↔ 函数

| 内容 | 函数 | 原位置 |
|---|---|---|
| 仿真记录生成（几何、场景、SNR） | `simulate_baseband.m`、`geometry_tau.m`、`envelope_h.m` | `phaseC/E4a_track_only_pilot_20260925/source_snapshot/` |
| 配置、种子、任务列表 | `mft_config.m`、`mft_seed.m`、`make_jobs.m` | 同上 |
| 共用分帧前端、噪声尺度 | `common_frontend.m`、`czt_match.m` | 同上 |
| VIT 锚轨迹 | `estimate_b1.m`、`dp_viterbi.m`、`band_logT.m`、`interp_const.m` | 同上 |
| 修正族、频带约束、相位基 $\mathbf h(t)$ | `build_family.m`、`second_difference_matrix.m` | 同上 |
| SMR 起点 | `estimate_b2.m` | 同上 |
| 分块相干目标 $J_h$ 与解析梯度 | `coherence_objective.m` | `研究工作台/MATLAB实验/mft_week4_module/` |
| 分块 | `make_blocks.m` | 同上 |
| 分阶段 SQP + 候选选择（模块本体） | `estimate_proposed.m`（起点标签 B2）、`estimate_refine.m`（同一算法，起点标签 initial，用于其他前端） | 同上 |
| MFT 前端 | `estimate_b0.m` | 同上 |
| 相位连续 TBD 前端 | `estimate_suvorova.m`、`suvorova_config.m`、`suvorova_transition.m` | 同上 |
| 原 P60 批次的指标（η、关联、Z） | `evaluate_record.m` | 同上 |
| E4a 批处理与指标函数 `measure`（η、谱峰、突出度、宽度、RMSE） | `run_e4a_formal_paired_batch.m` | `phaseC/E4a_formal_paired_20260925/` |
| 实测：原始记录读取、基带提取、LOFAR | `sio_read_channel.m`、`real_config.m`、`phaseA_load_baseband.m`、`compute_lofar.m` | `研究工作台/MATLAB实验/mft_real_inject/`、`phaseA/code/` |
| 实测：处理链与谱指标 `spectrum_metrics` | `run_B1_realtone.m` | `phaseA/exp/B_realtone/` |

## 注意

- `build_family.m` 把节点写死为 `0:knot_ds:300`。已有 600 s 实测结果是用时间缩放让 21 个节点铺满 600 s（30 s 间隔）。Phase D 会另写 `build_family_T`，不改这里的文件。
- `estimate_proposed.m` 与 `estimate_refine.m` 算法完全相同，只有起点标签与输出字段名不同。
- 原始数据：`D:\论文集\J1312340.hla.north.sio\J1312340.hla.north.sio`（530 MB，未复制）。

## Phase D 新增（`PhaseD新增/`，原位置 `phaseD/code/`、`phaseD/codeC/`）

| 内容 | 函数 |
|---|---|
| 任意时长的仿真记录（几何、干扰中心随 T 调整；T=300 时与原生成器逐样点相同） | `simulate_baseband_T.m` |
| 任意节点间隔与时长的修正族、逐节点上下界 | `build_family_T.m` |
| 正则物理缩放 | `phaseD_regularization.m` |
| 模块本体（与原 `estimate_proposed.m` 相同，另加候选可行性检查） | `estimate_proposed_T.m` |
| 自适应扩张（最终方法） | `phaseD_ada.m` |
| 边界驻留时长 | `phaseD_dwell.m` |
| 指标（推广到任意 T 的 `measure`） | `phaseD_measure.m` |
| 相位连续 TBD 的改名副本（供跨前端实验） | `estimate_suvorova_D.m` |
| 单条记录的流程（开发 / 确认） | `phaseD_setup.m`、`phaseD_record.m`、`phaseD_row.m`、`phaseC_record52.m`、`phaseC_one.m` |
| 外部验证的设置与单条流程（读取冻结文件并断言其指纹；时长、跨前端、实测） | `phaseX_settings.m`、`phaseX_front.m`、`phaseX1_one.m`、`phaseX2_one.m`、`phaseX3_one.m`、`phaseX3_metrics.m` |
| 实测可见性筛选（全长 LOFAR，与 A3 一致） | `run_phaseX3_continuous_screen.m` |
