from pathlib import Path
import hashlib,json,csv,shutil,time
R=Path('D:/论文集/phaseD');C=R/'codeX';s=(C/'run_phaseX_sim_filebridge.m').read_text(encoding='utf-8')
s=s.replace('function run_phaseX_sim_filebridge(stage,firstjob,lastjob)','function run_phaseX_sim_v7bridge(stage,firstjob,lastjob)')
old="save(partial,'results','signature','phase_id','-v7.3')";assert s.count(old)==1
s=s.replace(old,"save(partial,'results','signature','phase_id','-v7')")
s=s.replace('File bridge: unchanged worker S saved locally, then read by parent; no result structs returned through parfor','Worker S remains v7.3; parent grouped chunk uses lossless v7; all same frozen numerical function, fields and original signature')
(C/'run_phaseX_sim_v7bridge.m').write_text(s,encoding='utf-8')
ps=(C/'run_filebridge_batches.ps1').read_text(encoding='utf-8').replace('run_phaseX_sim_filebridge','run_phaseX_sim_v7bridge').replace('_filebridge_$phaseXFirst.log','_v7bridge_$phaseXFirst.log')
(C/'run_v7bridge_batches.ps1').write_text(ps,encoding='utf-8')
with (R/'Y_compute/V7BRIDGE_ADAPTER_MANIFEST.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['source_file','sha256']);w.writerows((str(C/n),hashlib.sha256((C/n).read_bytes()).hexdigest()) for n in ['phaseX_save_worker.m','run_phaseX_sim_v7bridge.m','run_v7bridge_batches.ps1'])
for p in (R/'Y_compute').glob('X1_filebridge_181.log'):shutil.copy2(p,p.with_name(p.stem+'_failed_'+str(int(time.time()))+'.log'))
with (R/'DEVIATIONS.md').open('a',encoding='utf-8') as f:f.write('\n## 2026-10-04：600秒分块保存格式适配\n\nX1在600秒的1830条累计已提交处再次堆损坏退出，工作进程的已完成S仍作为独立v7.3原始文件保留。新增父进程分块适配：仅把组合10个完整S的分块从-v7.3改为无损-v7，完整数值函数、类型、字段、签名、种子、起点、候选、预算和计时不变；每个工作记录及最终独立系数矩阵仍为预注册要求的v7.3。原已提交分块不转换、不重写，任何已有工作S不重求解。最终逐字段isequaln对照工作S与分块并全量重建指标以验证保存表示等价。此为环境存储适配，未调整方法或统计/判定输入。\n')
print('v7 parent-chunk adapter registered; individual worker records and coefficient matrices remain v7.3')
