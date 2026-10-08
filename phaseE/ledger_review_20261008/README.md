# 成果台账复核（2026-10-08）

[成果台账 v2](../../当前主线精选_20261003/14_第二批实验分析_20261008/成果台账_v2_Claude_20261008.md) 已归档。新增两项点估计已复核：[核对记录及原文指纹](LEDGER_V2_CHECK.json)。无实质异议，原文未改。

补交的 R1/R2/R4 计算已复跑：[补充复核及 M6 处理结论](supplement_R/README.md)。五张表全部复现，原件、重算结果及说明分别保存。

用户提供 Claude 成果台账后，对现有数据进行只读复算。未运行新的 MATLAB 实验或诊断优化。

- [复核意见](../../当前主线精选_20261003/14_第二批实验分析_20261008/成果台账_独立复核_Codex_20261008.md)
- [原台账](../../当前主线精选_20261003/14_第二批实验分析_20261008/成果台账_Claude_20261008.md)
- [数值结果](ledger_numeric_checks.json)
- [复算程序](verify_ledger.py)
- [读取文件指纹](READ_SOURCES_SHA256.json)
- [台账原文件来源与指纹](LEDGER_SOURCE.json)

复算入口：`D:\python\python.exe -X utf8 D:\论文集\phaseE\ledger_review_20261008\verify_ledger.py`。输出只写入本目录。

数值结果中 D 的原始 target_kind=1、2 分别映射为 GEO、GPS。仿真差值区间使用 2000 次 record_id 簇抽样、种子 20261008；D 差值区间引用相邻 `analysis_review_20261008/D_paired_comparison_checks.json` 的独立背景窗簇抽样结果。

本目录的 JSON 复现现有逐记录指标的汇总，未重算所有导出轨迹指标。T1/T3 从误差曲线直接积分；R4 补算从保存轨迹出发。哪些数字缺原计算入口见复核意见第四节。
