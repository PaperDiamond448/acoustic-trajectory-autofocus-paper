from pathlib import Path
import csv, hashlib, json, shutil, time
R = Path('D:/论文集/phaseD'); C = R / 'codeX'; O = R / 'X3_real'
source = (C / 'run_phaseX3_real_csvbridge.m').read_text(encoding='utf-8')
source = source.replace('function run_phaseX3_real_csvbridge()', 'function run_phaseX3_real_filebridge()', 1)
old = 'parfor j=1:numel(ids),cells{j}=phaseX3_one(tones(j),starts(j),Tvals(j),kind==1);end'
new = "wd=fullfile(outdir,'worker_records');if ~exist(wd,'dir'),mkdir(wd);end\n   fh=phaseD_hash(fullfile(outdir,'X3_TESTSET_FREEZE.json'),'SHA-256',true);records=cell(numel(ids),1);\n   for j=1:numel(ids),records{j}=fullfile(wd,sprintf('kind%d_f%d_s%d_T%d.mat',kind,tones(j),starts(j),Tvals(j)));end\n   parfor j=1:numel(ids),phaseX_save_real_worker(tones(j),starts(j),Tvals(j),kind==1,records{j},fh);end\n   for j=1:numel(ids),Q=load(records{j},'S','freeze_hash');assert(strcmp(Q.freeze_hash,fh));cells{j}=Q.S;end"
assert source.count(old) == 1; source = source.replace(old,new)
old = "save(partial,'results','freeze_hash','-v7.3')"
assert source.count(old) == 1; source = source.replace(old,"save(partial,'results','freeze_hash','-v7')")
(C / 'run_phaseX3_real_filebridge.m').write_text(source, encoding='utf-8')
with (R/'Y_compute/X3_FILEBRIDGE_ADAPTER_MANIFEST.csv').open('w',encoding='utf-8',newline='') as stream:
 w=csv.writer(stream); w.writerow(['source_file','sha256']); w.writerows((str(C/n),hashlib.sha256((C/n).read_bytes()).hexdigest()) for n in ['make_X3_filebridge.py','phaseX_save_real_worker.m','run_phaseX3_real_filebridge.m'])
archive=O/'qa'/f'pre_duration_environment_exit_{int(time.time())}';archive.mkdir()
for folder in ['tracks','spectra']:
 for p in (O/folder).glob('*_duration.csv'):
  target=archive/folder;target.mkdir(exist_ok=True);shutil.copy2(p,target/p.name)
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (O/'chunks').glob('kind1*.mat')}
(R/'Y_compute/X3_PRE_DURATION_EXIT.json').write_text(json.dumps(dict(status='105_CASES_SAVED_NO_DURATION_CHUNK_COMMITTED',sha256=hashes,orphan_duration_output_archive=str(archive),event='Observed 0xc0000374 after all case commits, during first duration batch; only complete chunks remain authoritative.'),ensure_ascii=False,indent=2),encoding='utf-8')
with (R/'DEVIATIONS.md').open('a',encoding='utf-8') as stream:
 stream.write('\n## 2026-10-04：实测时长窗口的存储/传递环境适配\n\n105个常规案例全部完整保存后，原实测进程在首个时长批次提交之前0xc0000374退出。11个常规分块逐一留存SHA，未提交时长任务仅输出的轨迹/谱另复制归档，不能据此选择候选。新增外层适配与仿真相同：不通过parfor返回复杂S，工作进程调用未修改的phaseX3_one一次并将完整S存v7.3；父进程读相同S，组合分块无损v7。冻结源、配置、候选、输入、单次预算、方法计时、主图角色、统计口径不变；常规105不重算。未提交时长任务从原起点和原预算重跑，不接续损坏状态、不合并尝试候选；所有完整worker文件后续复用。最终逐字段isequaln核对worker和组合分块，另有全量指标/预算/输入核验及独立NumPy谱GPS重算。\n')
print('X3 duration file bridge registered; all 105 case chunks preserved.')
