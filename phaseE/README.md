# Phase E：补充分析与扩展实验

已完成：0.1 复现预检、A 轨迹导出、A2 8000行直接η诊断、E 15个实测引导案例。D的新背景筛选已在任何注入之前标定并冻结：门槛1.9 dB，18/20通过。

- [任务书](TASKS_PhaseE_20261007.md)
- [运行前约定与作者D筛选修订](PREREGISTRATION_PhaseE_20261007.md)
- [0.1 预检](E0_preflight/README.md)
- [A：已有轨迹导出](E1_trajexport/README.md)
- [A2：新量定义、8000行结果与解释](E1_trajexport/README_A2.md)
- [理论和数值诊断的解释](METRIC_SCOPE.md)
- [作者的A2/E分析](E1_trajexport/A2与E结果分析_Claude_20261007.md)与[数字核对](E1_trajexport/Claude_analysis_check_20261007/README.md)
- [E：全部实测引导结果](E4_guided_real/README.md)
- [D：原筛选存档、新门槛及18个通过窗口](E5_inject/README.md)

B的DHMM参数选择已完成（120个新开发输入、9组候选，只看前端自身η），参数与实现已冻结。70个输入的VS/SUV回归检查已经全部通过，共140条方法输出。后续顺序为B、C、D；每完成一项，按原任务书验证输入、η及原冻结文件指纹后推送，并在文末增加完整报告的链接。尚未完成的任务不作为完整结果汇总。

长批次执行器的状态保存在本机 `D:\论文集\phaseE\REMAINING_RUN_STATUS.json`。新任务逐输入保存，发生接口/输入/数值不一致时停止并写对应README；已完成结果保留。MAT/H5留本机，CSV、MD、配置、脚本及指纹清单上传。正文、原冻结方法和原实验结果不改动。

按作者要求，本机另启动一次性完成提醒：B/C/D全部完成、独立核验通过且推送确认后提交Windows桌面通知；实际停止时提示查看原因，等待期间保持安静。通知接口和对象已验证，本轮未显示测试通知。通知状态只保存在本机 `phaseE/_completion_notification/`，不会修改实验输入、参数或数值输出。

任务 B：完整结果已生成并核对，见 [E2_frontend_ext](E2_frontend_ext/README.md)。

运行监控已按作者要求补为系统每5分钟自动检查，聊天结束后继续。检查主执行进程、正式保存的CSV/MAT配对和最近输出活动；进程退出、明确停止、保存配对缺失或连续15分钟无运行活动时提交Windows桌面提醒。相同异常只提醒一次，恢复后继续检查；C核验并上传后也提醒。按作者最新要求，正常运行时每次检查也提交进度桌面通知，写明已保存数量、完成比例和自上次检查以来新增的数量。

定时任务为 `AcousticPaper_PhaseE_Health_5min`，首次实际执行返回0，间隔核对为 `PT5M`。本机检查记录在 `D:\论文集\phaseE\_health_monitor\STATUS.json` 和 `checks.jsonl`；这些运行记录不上传。脚本仅读取实验结果，不更改算法、种子、预算或保存数据。B/C/D全部完成后自动注销定时任务，最终完成提醒仍由原一次性提醒程序负责。
