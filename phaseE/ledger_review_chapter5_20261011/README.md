# 第 5 章与图 7–8 的只读复核

已完成数值核对、注入处理范围确认、自然轨迹的强线参照比较及绘图源数据导出。CHAPTER5_NUMERIC_CHECK.csv 中的明确数值比较均通过，精确取值与输入 SHA-256 在 JSON 中保留。

WEAK_GUIDED_POSITIONS_RECOMPUTED.csv 为 15 个弱线案例从保存轨迹独立计算的中位位置偏移。136HZ_REFERENCE_COMPARISON.json 同时给出 136 Hz 的逐样点差异，解释中位数接近与局部轨迹差异的关系。完整 136 Hz 输入的 CSV 已与本机 MAT 核对，可用于在线重绘；大体积 MAT 无需下载。

FIG7_SOURCE.csv 的区间复用原 BOOTSTRAP_DRAWS.npz。FIG8_ALL_CASES.csv 保存全部 105 例，示例轨迹、完整 ±1.5 Hz 谱和 LOFAR 矩阵分别保存。图 3 误差符号的更新源数据也在此。

复跑：在仓库根目录运行 `python phaseE/ledger_review_chapter5_20261011/verify_chapter5.py`。程序依赖 numpy、pandas、scipy；本机有 MAT 与 h5py 时增加原始输入读回，在线可直接用保存的复输入 CSV。source_code 是实际调用链相关代码的只读副本，用于配置追溯。无需 MATLAB 或重新运行估计器。

本轮正文与解释采用《第5章通读与复核意见_Codex_20261011》。136 Hz 的整段中位偏移接近强线参照；其完整轨迹存在较大的局部差异，声源归属继续核定。注入实验提供已知目标的定量结果，自然记录展示观测谱峰与修正现象。
