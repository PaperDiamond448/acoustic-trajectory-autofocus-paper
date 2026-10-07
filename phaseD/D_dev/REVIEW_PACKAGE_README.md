# Phase D 停止点 1 核对包

仅 phase 51 开发；方法 ADA_local_c04_t30_A，分支 C-A，Δ=10 s，P=31。
先核对 D_dev/DEV_REPORT.md 与 D_dev/FROZEN_METHOD.json，然后查看规则表、逐记录表和核验门。
确认 C 未启动。用户核对并另行放行后才能开始确认阶段。

大体积逐记录 MAT 分块不放入此 ZIP，保留于本机 D:\论文集\phaseD\D_dev\*_chunks。
D_dev/RESULTS_MANIFEST_sha256.csv 列出全部新结果（含 MAT）的哈希和是否进入核对包。
原始数据、既有实验结果、技能备份和 Python 本地运行库不包含在 ZIP 中。
代码使用本机预注册的既有 MATLAB 模块；源码清单明确列出其绝对路径与哈希。
qa 目录包含只读审计脚本和报告，未进行新的模拟或优化。
