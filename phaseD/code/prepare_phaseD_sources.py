from pathlib import Path
import hashlib, csv, json, subprocess, sys
root=Path(r'D:\论文集'); code=root/'phaseD/code'; code.mkdir(parents=True,exist_ok=True)
snap=root/'phaseC/E4a_track_only_pilot_20260925/source_snapshot'
wk=root/'研究工作台/MATLAB实验/mft_week4_module'
src=(snap/'simulate_baseband.m').read_text(encoding='utf8')
src=src.replace('simulate_baseband(cfg, scene, snr_db, seed, geo_mode)','simulate_baseband_T(cfg, scene, snr_db, seed, geo_mode, T)',1)
src=src.replace('B  = cfg.B;','B  = cfg.B;\nassert(T>60 && T*B.fs==round(T*B.fs));\nB.eval_geo.t_cpa_rx = [T/2-30 T/2+30];\nB.fade.center_s=T/2; B.intf.center_s=T/2;',1).replace('N = B.N;','N = T*B.fs;',1)
(code/'simulate_baseband_T.m').write_text(src,encoding='utf8')
src=(snap/'build_family.m').read_text(encoding='utf8').replace('build_family(t, tc, gA, mcfg)','build_family_T(t, tc, gA, mcfg, Delta, T, ubvec)',1)
src=src.replace('knots = (0:mcfg.knot_ds:300)\';',"assert(abs(T/Delta-round(T/Delta))<1e-10);\nknots = (0:Delta:T)';",1)
src=src.replace('fam.r = mcfg.radius;','fam.r = 0.02;',1)
src=src.replace('fam.lb = mcfg.u_bounds(1)*ones(P,1);\nfam.ub = mcfg.u_bounds(2)*ones(P,1);',"if isscalar(ubvec), ubvec=ubvec*ones(P,1); end\nassert(numel(ubvec)==P && all(ubvec>=0));\nfam.lb = -ubvec(:);\nfam.ub = ubvec(:);",1)
(code/'build_family_T.m').write_text(src,encoding='utf8')
src=(wk/'estimate_proposed.m').read_text(encoding='utf8').replace('estimate_proposed(y, fe, fam, u0, evalIdx, mcfg)','estimate_proposed_T(y, fe, fam, u0, evalIdx, mcfg)',1)
# An infeasible SMR start must not be selected for F01. All baseline feasible
# starts retain the original candidate list and numerical operations exactly.
src=src.replace('J(i) = -coherence_objective(cands{i}, ctxF);',"if is_feasible(cands{i},fam)\n        J(i) = -coherence_objective(cands{i}, ctxF);\n    else\n        J(i) = -Inf;\n    end",1)
src=src.replace('[Jbest, ib] = max(J);',"[Jbest, ib] = max(J);\nassert(isfinite(Jbest),'No feasible candidate; no retry permitted.');",1)
(code/'estimate_proposed_T.m').write_text(src,encoding='utf8')
src=(wk/'estimate_suvorova.m').read_text(encoding='utf8').replace('estimate_suvorova(y, t, noise_hat, s, evalIdx)','estimate_suvorova_D(y, t, noise_hat, s, evalIdx)',1)
(code/'estimate_suvorova_D.m').write_text(src,encoding='utf8')
src=(root/'phaseC/E4a_formal_paired_20260925/run_e4a_formal_paired_batch.m').read_text(encoding='utf8')
part=src[src.index('function m=measure('):src.index('\nfunction x=band_violation')]
part=part.replace('function m=measure(','function m=phaseD_measure(',1)
cross=src[src.index('function x=crossing('):src.index('\nfunction h=input_hash')]
(code/'phaseD_measure.m').write_text(part+'\n'+cross+'\n',encoding='utf8')
# Preserve hashes of every inherited source and every existing result file.
dirs=[root/'phaseA',root/'phaseC',wk,root/'研究工作台/MATLAB实验/mft_real_inject']
files=set()
for d in dirs:
    files.update(p for p in d.rglob('*') if p.is_file())
rows=[{'source_file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
with (root/'phaseD/BASELINE_MANIFEST_sha256.csv').open('w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['source_file','sha256']);w.writeheader();w.writerows(rows)
print('Prepared compatibility sources; baseline files hashed:',len(rows))
audit=root/'phaseD/skill_audit'; r=json.loads((audit/'update_result.json').read_text(encoding='utf8'))
installed=Path(r'C:\Users\Lenovo\.codex\skills')
for v in r['validation']:
    p=subprocess.run([sys.executable,'-X','utf8',str(installed/'.system/skill-creator/scripts/quick_validate.py'),str(installed/v['skill'])],capture_output=True,text=True,encoding='utf8')
    v.update(exit_code=p.returncode,output=p.stdout+p.stderr)
(audit/'update_result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print('Skill validation:',[(v['skill'],v['exit_code']) for v in r['validation']])
