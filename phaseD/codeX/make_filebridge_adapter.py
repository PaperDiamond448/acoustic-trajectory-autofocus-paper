from pathlib import Path
import hashlib,csv,json
R=Path('D:/论文集/phaseD');C=R/'codeX';s=(C/'run_phaseX_sim_short.m').read_text(encoding='utf-8')
s=s.replace('function run_phaseX_sim_short(stage,firstjob,lastjob)','function run_phaseX_sim_filebridge(stage,firstjob,lastjob)')
old="""cells=cell(10,1);scene=J.scene;snr=J.snr;T=J.T;
  parfor k=1:10,if strcmp(stage,'X1'),cells{k}=phaseX1_one(scene,snr,ids(k),T);else,cells{k}=phaseX2_one(scene,snr,ids(k));end,end"""
new="""scene=J.scene;snr=J.snr;T=J.T;records=cell(10,1);
  wd=fullfile(O,'worker_records');if ~exist(wd,'dir'),mkdir(wd);end
  for k=1:10,records{k}=fullfile(wd,sprintf('T%d_%s_%+03ddB_r%03d.mat',T,scene,snr,ids(k)));end
  parfor k=1:10,phaseX_save_worker(stage,scene,snr,ids(k),T,records{k},sig,phase);end
  cells=cell(10,1);for k=1:10,Q=load(records{k});assert(strcmp(Q.signature,sig)&&Q.phase_id==phase);cells{k}=Q.S;end"""
assert old in s;s=s.replace(old,new).replace('run_phaseX_sim_short: same frozen numerical function, original signature and v7.3 output schema; fresh MATLAB process','File bridge: unchanged worker S saved locally, then read by parent; no result structs returned through parfor')
(C/'run_phaseX_sim_filebridge.m').write_text(s,encoding='utf-8')
ps=(C/'run_short_batches.ps1').read_text(encoding='utf-8').replace('run_phaseX_sim_short','run_phaseX_sim_filebridge').replace('_short_$phaseXFirst.log','_filebridge_$phaseXFirst.log')
(C/'run_filebridge_batches.ps1').write_text(ps,encoding='utf-8')
with (R/'Y_compute/FILEBRIDGE_ADAPTER_MANIFEST.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['source_file','sha256']);w.writerows((str(C/n),hashlib.sha256((C/n).read_bytes()).hexdigest()) for n in ['phaseX_save_worker.m','run_phaseX_sim_filebridge.m','run_filebridge_batches.ps1'])
files=[p for p in (R/'X1_duration/chunks').glob('*.mat') if not p.name.endswith('.partial.mat')]
(R/'Y_compute/PRE_FILEBRIDGE_CHUNKS.json').write_text(json.dumps({'committed_records':len(files)*10,'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},ensure_ascii=False,indent=2),encoding='utf-8')
with (R/'DEVIATIONS.md').open('a',encoding='utf-8') as f:f.write('\n## 2026-10-04：并行结果文件桥接（环境适配）\n\n短批次在完成71–80批后退出、随后在累计920条记录处再次退出。冻结数值函数和算法断言没有变化。为检查并行结果传递的环境风险，新增文件桥：工作进程调用完全相同的数值函数后，将完整原生S写为v7.3文件；主进程只读取这个完全相同的S，不通过parfor返回复杂结构。输入、数值函数、起点、候选、正则、预算、结果类型和计时函数不变；保存/传递发生在方法计时结束后。已保存工作记录和已提交分块均直接复用。此前所有完整分块指纹留档，不丢弃记录，不根据结果挑选版本。适配器另附指纹。堆损坏原因仍未确定，此措施是环境恢复而非声称诊断成功。\n')
print('Filebridge adapter registered; preserved records:',len(files)*10)
