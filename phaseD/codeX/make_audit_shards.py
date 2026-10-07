from pathlib import Path
import csv, hashlib
R=Path('D:/论文集/phaseD');C=R/'codeX'
s=(C/'audit_phaseX_saved.m').read_text(encoding='utf-8')
s=s.replace('function audit_phaseX_saved(stage)','function audit_phaseX_saved_shard(stage,firstfile,lastfile)',1)
anchor="csv=readtable(fullfile(O,[stage '_records.csv']),'TextType','string');nr=0;"
new="""assert(firstfile>=1&&lastfile<=numel(files));files=files(firstfile:lastfile);total=numel(files)*10;
outdir=fullfile(O,'qa_shards');if ~exist(outdir,'dir'),mkdir(outdir);end;tag=sprintf('shard_%03d_%03d',firstfile,lastfile);
csv=readtable(fullfile(O,[stage '_records.csv']),'TextType','string');keep=false(height(csv),1);
for fi=1:numel(files)
 token=regexp(files(fi).name,'^T(\\d+)_(S[02])_([+-]\\d+)dB_chunk_(\\d+)\\.mat$','tokens','once');assert(numel(token)==4);
 Tmask=str2double(token{1});snrmask=str2double(token{3});chmask=str2double(token{4});
 match=csv.scene==string(token{2})&csv.snr_db==snrmask&csv.record_id>(chmask-1)*10&csv.record_id<=chmask*10;
 if phase==53,match=match&csv.duration_s==Tmask;end;keep=keep|match;
end
csv=csv(keep,:);assert(height(csv)==4*total);nr=0;"""
assert s.count(anchor)==1;s=s.replace(anchor,new)
for old,new in [
 ("fullfile(O,[stage '_ADA_rounds.csv'])","fullfile(outdir,[tag '_ADA_rounds.csv'])"),
 ("fullfile(O,'X1_SMR_F02_dwell.csv')","fullfile(outdir,[tag '_SMR_F02_dwell.csv'])"),
 ("fullfile(O,'SAVED_OUTPUTS_AUDIT.json')","fullfile(outdir,[tag '_AUDIT.json'])")]:
 assert s.count(old)==1;s=s.replace(old,new)
(C/'audit_phaseX_saved_shard.m').write_text(s,encoding='utf-8')
with (R/'Y_compute/SHARDED_AUDIT_ADAPTER_MANIFEST.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['source_file','sha256']);w.writerows((str(C/n),hashlib.sha256((C/n).read_bytes()).hexdigest()) for n in ['make_audit_shards.py','audit_phaseX_saved_shard.m','run_audit_shards.ps1','merge_audit_shards.py'])
with (R/'DEVIATIONS.md').open('a',encoding='utf-8') as f:
 f.write('\n## 2026-10-04：只读核验环境退出后的分批恢复\n\n原全量X1只读核验在打印600/2400通过进度后堆损坏退出，未出现数值/规则断言失败，实验求解不重跑。新增分批核验复制原被登记的审计源码，所有逐记录、指标、预算、候选、起点、局部支持、全长J和不触发一致性检查原样；仅每进程读取10个分块100条，并按这些分块的预注册键匹配CSV，生成独立PASS和明细。全局合并另检查24/14分批覆盖、记录/方法行总数、键唯一性和明细覆盖，再生成原下游路径；原审计源/统计定义/原实验结果不改。任何未完成核验批可重新只读核验，不调用求解器、不增加求解预算。新增源码指纹SHARDED_AUDIT_ADAPTER_MANIFEST.csv。\n')
print('Original per-record audit checks copied unchanged; only input/output partitioning added.')
