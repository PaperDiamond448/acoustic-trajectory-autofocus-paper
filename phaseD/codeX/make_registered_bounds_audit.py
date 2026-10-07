from pathlib import Path
import hashlib,csv
R=Path('D:/论文集/phaseD');C=R/'codeX'
s=(C/'audit_phaseX_saved_shard.m').read_text(encoding='utf-8')
s=s.replace('function audit_phaseX_saved_shard(stage,firstfile,lastfile)','function audit_phaseX2_registered_shard(stage,firstfile,lastfile)',1)
s=s.replace('d=S.details{k};a=d.ada;fam=d.family;check_ada(a,fam,rec.y,rec.t,idx,M.P,2);','d=S.details{k};a=d.ada;fam=d.family;check_ada(a,fam,rec.y,rec.t,idx,M.P,2,false);',1)
s=s.replace('function check_ada(a,fam,y,t,idx,PC,band)','function check_ada(a,fam,y,t,idx,PC,band,enforce_dense)\nif nargin<8,enforce_dense=true;end',1)
assert s.count('check_out(L.out,L.m,fam,y,idx,PC,band);')==1
s=s.replace('check_out(L.out,L.m,fam,y,idx,PC,band);','check_out(L.out,L.m,fam,y,idx,PC,band,enforce_dense);')
s=s.replace('function check_out(o,m,fam,y,idx,PC,band)','function check_out(o,m,fam,y,idx,PC,band,enforce_dense)\nif nargin<8,enforce_dense=true;end',1)
old='assert(max(abs(o.g-(fam.gA+fam.r*fam.Bt*o.u)))<=1e-12&&max(abs(o.g))<=band+1e-6);'
assert s.count(old)==1
s=s.replace(old,'assert(max(abs(o.g-(fam.gA+fam.r*fam.Bt*o.u)))<=1e-12);\nif enforce_dense,assert(max(abs(o.g))<=band+1e-6);end\n% For X2, registered frame/SUV-midpoint Aineq/binEq is mandatory above; dense sampled extrema are separately diagnosed, never clipped.')
(C/'audit_phaseX2_registered_shard.m').write_text(s,encoding='utf-8')
p=(C/'run_audit_shards.ps1').read_text(encoding='utf-8').replace('audit_phaseX_saved_shard','audit_phaseX2_registered_shard')
(C/'run_X2_registered_audit.ps1').write_text(p,encoding='utf-8')
with (R/'Y_compute/REGISTERED_BOUNDS_AUDIT_ADAPTER_MANIFEST.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['source_file','sha256']);w.writerows((str(C/n),hashlib.sha256((C/n).read_bytes()).hexdigest()) for n in ['make_registered_bounds_audit.py','audit_phaseX2_registered_shard.m','run_X2_registered_audit.ps1','diagnose_X2_frequency_bounds.m'])
with (R/'DEVIATIONS.md').open('a',encoding='utf-8') as f:
 f.write('\n## 2026-10-04：核验条件与方案检查点的一致性修正（实验结果不改）\n\nX2第21–30文件批的附加dense-grid频带断言失败。只读诊断定位MFT、S0−12 dB、rid31、第0轮：采样最大|g|=2.0000440341853913 Hz，保存公式重建差0，审计的乘法重关联差2.22e−16，方案指定Aineq/binEq最大违约量0。主方案§2.5明定保留Aineq/binEq，§9.2分别指定帧中心和SUV块中点；并未额外规定MFT连续轨迹每个20Hz采样点的极值都要等于检查点极值。原build_family_T针对PL中心的内部注释不能用于将MFT曲线的帧间极值假定为已认证。新增X2只读核验适配仅把超出方案的dense-grid断言改为独立诊断，规定的Aineq/binEq、盒界、候选、J、预算、起点、局部支持及所有指标/CSV检查原样；X1审计不改。冻结方法、原审计源、全部原结果不改，不裁剪、不重求解、不删除该入口不可用记录，也不根据差异调参数。全体X2附加密网格极值另行只读量化并在报告披露，不能宣称检查点约束保证所有前端的全采样轨迹严格在±2Hz内。修正发生在X2统计之前，未改变任何预注册终点、指标或判定输入。\n')
print('X2 audit uses registered checkpoints unchanged; sampled-grid bound diagnostics remain separate and fully reported.')
