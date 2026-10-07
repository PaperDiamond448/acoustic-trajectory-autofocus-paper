"""Output-only additions: environment accounting, approved C evidence, coefficients."""
from pathlib import Path
import csv, hashlib, json, re
import pandas as pd

R = Path('D:/论文集/phaseD')
Y = R / 'Y_compute'
rows, inventory, hashes_seen = [], [], set()
for p in sorted(Y.glob('*.log')):
    if not re.match(r'(X_numeric|X[12]_(short|filebridge|v7bridge|assemble)|X3_numeric)', p.name):
        continue
    raw = p.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    duplicate = digest in hashes_seen
    hashes_seen.add(digest)
    text = raw.decode('utf-8', errors='replace')
    span = p.stat().st_mtime - p.stat().st_ctime
    inventory.append(dict(file=p.name, bytes=len(raw), sha256=digest,
                          duplicate_content=duplicate,
                          descriptive_log_span_seconds=span if span >= 0 else None,
                          completed_progress_lines=len(re.findall(r'\d+/\d+ records', text)),
                          heap_exit_mentioned=('Heap corruption' in text or '0xc0000374' in text)))
for stage, folder in [('X1', 'X1_duration'), ('X2', 'X2_frontend')]:
    configs = [json.loads(p.read_text(encoding='utf-8')) for p in (R / folder).glob('short_batch_*.json')]
    run = json.loads((R / folder / (stage + '_run_config.json')).read_text(encoding='utf-8'))
    logs = [q for q in inventory if q['file'].startswith(stage + '_') and '_assemble' not in q['file'] and not q['duplicate_content']]
    rows.append(dict(stage=stage, completed_short_batches=len(configs),
                     records_newly_committed_in_completed_batches=sum(q['new_records'] for q in configs),
                     completed_batch_work_seconds=sum(q['elapsed_wall_seconds'] for q in configs),
                     unique_environment_log_files=len(logs),
                     descriptive_log_span_seconds=sum(q['descriptive_log_span_seconds'] or 0 for q in logs),
                     log_spans_unavailable=sum(q['descriptive_log_span_seconds'] is None for q in logs),
                     assembly_only_seconds=run['elapsed_wall_seconds']))
pd.DataFrame(rows).to_csv(Y / 'Y_batch_runtime.csv', index=False)
pd.DataFrame(inventory).to_csv(Y / 'ENVIRONMENT_LOG_INVENTORY.csv', index=False)
runtime = dict(status='COMPLETE', batch_summary=rows,
               log_inventory='ENVIRONMENT_LOG_INVENTORY.csv',
               x3_final_resume_seconds=json.loads((R/'X3_real/X3_run_config.json').read_text(encoding='utf-8'))['elapsed_wall_seconds'],
               x3_first_105_case_commit_seconds=385.5917989,
               timing_scope='Method times are saved six-worker loaded call wall times. Completed short-batch work includes numerical calls, cached reads and saving, excludes MATLAB/pool startup, and excludes work committed before an incomplete batch exited. Log spans are descriptive estimates with gaps/overwrites, not a measured total execution wall time. Identical archived logs are deduplicated. Original final X1/X2 driver times are read-only assembly times. No restart cost is charged to a method.')
(Y / 'ENVIRONMENT_RUNTIME_SUMMARY.json').write_text(json.dumps(runtime, ensure_ascii=False, indent=2), encoding='utf-8')

fm = 'ADA_local_c04_t30_A'
c = pd.read_csv(R / 'C_confirm/C_summary.csv')
cells = pd.read_csv(R / 'C_confirm/C_cell_statistics.csv')
def cvalue(metric):
    q = c[(c.scope == 'ALL') & (c.method == fm) & (c.metric == metric)]
    assert len(q) == 1, metric
    return q.iloc[0]
eta = cvalue('gain_eta_vs_SMR')
peak = cvalue('gain_peak_vs_SMR_db')
q = cells[(cells.method == fm) & (cells.metric == 'gain_eta_vs_SMR')]
assert len(q) == 14
positive = int((q.lo > 0).sum())
solver_rows = []
for stage, names in [('X1',['X1_duration/X1_records.csv']),('X2',['X2_frontend/X2_records.csv']),('X3',['X3_real/X3_cases.csv','X3_real/X3_duration.csv'])]:
    data = pd.concat([pd.read_csv(R/name) for name in names], ignore_index=True)
    for method, g in data.groupby('method' if stage != 'X2' else 'frontend'):
        solver_rows.append(dict(stage=stage, method_or_frontend=method, method_rows=len(g), hard_fail_marked_rows=int(g.hard_fail.sum()), budget_cap_marked_rows=int(g.budget_cap.sum())))
solver = pd.DataFrame(solver_rows)
solver.to_csv(Y/'SOLVER_STATUS_BY_METHOD.csv',index=False)
solver_table = '| '+' | '.join(solver.columns)+' |\n| '+' | '.join(['---']*len(solver.columns))+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in solver.itertuples(index=False,name=None))
bounds = pd.read_csv(Y/'X2_BOUND_DIAGNOSTIC_001_140.csv')
bound_keys = ['scene','snr_db','record_id','frontend']
assert len(bounds.drop_duplicates(bound_keys)) == 5600
assert bounds.saved_formula_max_abs_difference.max() <= 1e-12
assert bounds.registered_Aineq_max_excess.max() <= 1e-6
outside = bounds[bounds.max_abs_g > 2+1e-6]
bound_scope = json.loads((R/'X2_frontend/SAVED_OUTPUTS_AUDIT.json').read_text(encoding='utf-8'))
assert bound_scope['status']=='PASS'
bound_scope['scope']='All preregistered input/metric/CSV/budget/candidate/local-support/warm-start/J/nontrigger and Aineq/binEq checkpoint checks passed in complete 100-record shards. The extra all-20Hz-sample band assertion is not a preregistered X2 condition; sampled extrema independently quantified, reported without clipping, exclusion, optimization or tuning.'
bound_scope['additional_dense_grid_diagnostic']='Y_compute/X2_BOUND_DIAGNOSTIC_001_140.csv'
(R/'X2_frontend/SAVED_OUTPUTS_AUDIT.json').write_text(json.dumps(bound_scope,ensure_ascii=False,indent=2),encoding='utf-8')
coeffs = sorted(p for folder in ['X1_duration', 'X2_frontend', 'X3_real'] for p in (R / folder).glob('coefficients_T*.mat'))
assert len(coeffs) == 9
links = '、'.join(f'[{p.parent.name}/{p.name}](D:/论文集/phaseD/{p.relative_to(R).as_posix()})' for p in coeffs)
notes = f'''

## 正式主结果、系数交付与环境计时补充

确认阶段最终主方法相对 SMR 的合并 η 增量为 **+{eta['mean']:.6f}**，95% 区间 [{eta.lo:.6f}, {eta.hi:.6f}]；谱峰增量为 **+{peak['mean']:.6f} dB**，95% 区间 [{peak.lo:.6f}, {peak.hi:.6f}]；{positive}/14 单元 η 增量区间下界大于零。这里取自已核对的 phase 52 确认结果，不使用开发集或旧 E4a 的值；S0 相对 UNB 的负差限制仍如正文所述。

独立系数、起点与边界矩阵均为 v7.3：{links}；同目录各 `*_keys.csv` 标识阶段、窗口、前端与方法。环境适配仅改变父进程组合分块的保存表示；每个工作记录原始 S 保留 v7.3，所有已有提交文件保持原样。逐字段保存等价性见 [WORKER_CHUNK_BRIDGE_AUDIT.json](D:/论文集/phaseD/Y_compute/WORKER_CHUNK_BRIDGE_AUDIT.json)，适配器和旧数据指纹见 [SUPPLEMENT_INTEGRITY_AUDIT.json](D:/论文集/phaseD/Y_compute/SUPPLEMENT_INTEGRITY_AUDIT.json)。

计算量表中的方法时间为六工作进程同时负载下的单次调用墙钟。完成短批次的工作时间包含数值调用、缓存读取和保存，不含 MATLAB/进程池启动，也不能覆盖失败批次已提交而尚未生成完成标记的工作。最终原驱动 X1/X2 配置中的 elapsed_wall_seconds 在本轮仅为只读组装时间，不是整个阶段执行时长。日志跨度受重启间隔、归档和覆盖影响，仅作环境开销描述，不能作为精确总耗时或充入方法时间。唯一日志内容已去重，见 [Y_batch_runtime.csv](D:/论文集/phaseD/Y_compute/Y_batch_runtime.csv)、[ENVIRONMENT_LOG_INVENTORY.csv](D:/论文集/phaseD/Y_compute/ENVIRONMENT_LOG_INVENTORY.csv) 和 [ENVIRONMENT_RUNTIME_SUMMARY.json](D:/论文集/phaseD/Y_compute/ENVIRONMENT_RUNTIME_SUMMARY.json)。X3 连续 LOFAR 筛选复核曾与少量 X1 任务并行，属于已记录的临时 CPU 负载。

X3 首次提交全部 105 个常规案例用了 385.59 s；最终配置的 96.98 s 是重新读取这些完整案例并完成 16 个时长窗口的恢复驱动耗时，不能解释为完整 X3 总耗时。首个时长批次未提交的工作、进程启动及退出开销单独留存。原 105 个常规分块逐一指纹保持，见 [X3_PRE_DURATION_EXIT.json](D:/论文集/phaseD/Y_compute/X3_PRE_DURATION_EXIT.json)；16 个时长工作文件与提交分块逐字段相同，见 [REAL_WORKER_CHUNK_BRIDGE_AUDIT.json](D:/论文集/phaseD/Y_compute/REAL_WORKER_CHUNK_BRIDGE_AUDIT.json)。已观察到的完成标记之后的退出码见 [ENVIRONMENT_EXIT_EVENTS.csv](D:/论文集/phaseD/Y_compute/ENVIRONMENT_EXIT_EVENTS.csv)，X1 组装完成后的退出见 [X1_ASSEMBLY_EXIT.json](D:/论文集/phaseD/Y_compute/X1_ASSEMBLY_EXIT.json)。

求解状态按保存的方法行列出如下；复用的 F02 结果可同时出现在自适应未触发行中，这些行数不是独立求解次数。预算触顶与硬失败分别列示，不删除相应结果，也不追加预算。完整键表见 [SOLVER_STATUS_BY_METHOD.csv](D:/论文集/phaseD/Y_compute/SOLVER_STATUS_BY_METHOD.csv)。

{solver_table}

## X2 频率约束的检查点范围与附加采样诊断

§2.5 保留原 `Aineq/bineq`，§9.2 指定 VS/MFT/V0 的帧中心及 SUV 块中点。全量规定检查点的最大违约量为 {bounds.registered_Aineq_max_excess.max():.10g} Hz，符合原 1e−6 求解可行性容差；保存轨迹按原公式重建的最大差为 {bounds.saved_formula_max_abs_difference.max():.10g} Hz。原只读审计另加了“所有 20 Hz 采样点都在 ±2 Hz 内”的条件，它比注册的检查点条件严格。MFT 原实现也是分段线性插值；冻结族从 20 Hz 采样轨迹再次插值到检查点，非网格帧折点可能被平滑，故指定检查点通过不能直接认证全部采样点极值。最先发现的例子为 S0、−12 dB、rid31、MFT：采样极值 2.0000440341853913 Hz，但检查点违约为0，该入口不可用记录保留。

独立扫描覆盖 5600 个记录×前端及全部自适应轮：{len(outside)} 个轮记录、{len(outside.drop_duplicates(bound_keys))} 个记录×前端的采样极值超过 2+1e−6 Hz，最大 |g| 为 {bounds.max_abs_g.max():.12f} Hz。全部越界均为 MFT，且入口均不可用。完整位置、轮次、入口分组和增量见 [X2_BOUND_DIAGNOSTIC_001_140.csv](D:/论文集/phaseD/Y_compute/X2_BOUND_DIAGNOSTIC_001_140.csv)。**这里没有裁剪轨迹、删记录、改指标或重调方法；X2 的 PASS 指方案规定的检查点与其他规则通过，不宣称所有前端的全部采样点都被严格 ±2 Hz 认证。** 这项附加限制也应在后续论文方法说明中明确，不能用图或合并指标掩盖。
'''
report = R / 'PHASE_D_REPORT.md'
s = report.read_text(encoding='utf-8')
assert '## 正式主结果、系数交付与环境计时补充' not in s
s = s.replace('## 完整性、环境事件与停止', notes + '\n## 完整性、环境事件与停止')
report.write_text(s, encoding='utf-8')
print('Final approved-C, coefficient and environment notes appended.')
