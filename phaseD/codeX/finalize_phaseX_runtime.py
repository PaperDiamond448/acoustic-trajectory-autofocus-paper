from pathlib import Path
import json,hashlib,pandas as pd
R=Path('D:/论文集/phaseD');rows=[]
for stage,folder in [('X1','X1_duration'),('X2','X2_frontend')]:
 configs=[json.loads(p.read_text(encoding='utf-8')) for p in (R/folder).glob('short_batch_*.json')]
 numeric=sum(q['elapsed_wall_seconds'] for q in configs)
 logs=list((R/'Y_compute').glob(stage+'_short_*.log'))
 logged_wall=sum(max(0,p.stat().st_mtime-p.stat().st_ctime) for p in logs)
 rows.append(dict(stage=stage,short_batches=len(configs),new_records=sum(q['new_records'] for q in configs),short_batch_work_seconds=numeric,process_log_span_seconds=logged_wall,assembly_only_seconds=json.loads((R/folder/(stage+'_run_config.json')).read_text(encoding='utf-8'))['elapsed_wall_seconds']))
pd.DataFrame(rows).to_csv(R/'Y_compute/Y_batch_runtime.csv',index=False)
events=[]
for p in (R/'Y_compute').glob('*.log'):
 text=p.read_text(encoding='utf-8',errors='replace')
 if 'Heap corruption' in text or '0xc0000374' in text:events.append(str(p))
result={'status':'COMPLETE','short_batch_summary':rows,'heap_exit_logs':events,'timing_scope':'Single optimizer wall times stored per record. Short-batch work seconds exclude MATLAB/pool startup; process-log spans are descriptive environment overhead estimates, not isolated method timing. Original interrupted runs add 315.0434638 and 468.9265359 seconds of completed progress plus uncommitted and startup time. Assembly-only driver times are not total numerical execution time.'}
(R/'Y_compute/ENVIRONMENT_RUNTIME_SUMMARY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
report=R/'PHASE_D_REPORT.md';s=report.read_text(encoding='utf-8');addition='\n\n环境短批次的工作时间与进程日志时跨度另见 [Y_batch_runtime.csv](D:/论文集/phaseD/Y_compute/Y_batch_runtime.csv)。原驱动的最终完整运行配置在此为只读组装耗时，不是全部数值计算时间。两次已知中断的已提交进度分别为315.04 s和468.93 s；未提交任务与进程启动开销另计，不能充入某方法的求解时长。完整事件及口径见 [ENVIRONMENT_RUNTIME_SUMMARY.json](D:/论文集/phaseD/Y_compute/ENVIRONMENT_RUNTIME_SUMMARY.json)。\n'
s=s.replace('## 完整性、环境事件与停止',addition+'\n## 完整性、环境事件与停止');report.write_text(s,encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
