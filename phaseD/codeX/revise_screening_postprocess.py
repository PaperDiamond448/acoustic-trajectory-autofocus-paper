from pathlib import Path
import shutil,json,csv,hashlib
R=Path('D:/论文集/phaseD');C=R/'codeX';A=R/'Y_compute/preanalysis_v1_sources';A.mkdir(exist_ok=True)
rows=list(csv.DictReader((C/'POSTPROCESS_MANIFEST_sha256.csv').open(encoding='utf-8-sig')))
for row in rows:
 p=Path(row['source_file']);assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];shutil.copy2(p,A/p.name)
shutil.copy2(C/'POSTPROCESS_MANIFEST_sha256.csv',A/'POSTPROCESS_MANIFEST_sha256.csv')
changes={
 'analyze_phaseX.py': [('assert len(d)==106*8','assert len(d)==len(vis)*8'),("{'cases':106,","{'cases':len(vis),")],
 'audit_phaseX.py': [('assert len(p)==106',"assert len(p)==json.loads((R/'X3_real/X3_TESTSET_FREEZE.json').read_text(encoding='utf-8'))['passed_cases']"),('assert len(c)==106*8','assert len(c)==len(p)*8'),("'X3_passed_cases':106","'X3_passed_cases':len(p)")],
 'audit_phaseX3_saved.m': [('assert(nr==122);',"F=jsondecode(fileread(fullfile(root,'X3_TESTSET_FREEZE.json')));assert(nr==F.passed_cases+F.duration_windows);")],
 'plot_phaseX.py': [('All 106 passed','All 105 passed')],
 'write_phaseX_report.py': [('LOFAR Hann L200/D20/NFFT8192，每段291个完整支撑帧。原 A3 连续 LOFAR 帧集合有所不同，全部数值与翻转均列出，阈值未调整。','LOFAR Hann L200/D20/NFFT8192，在完整0–3000 s拼接记录上计算，按帧中心归属300 s时段，与原A3帧支撑一致；初版逐段291帧遗漏跨段帧，在任何实测模块运行前纠正并留档。全部与旧A3的数值对照及翻转均列出，阈值未调整。')]
}
for name,replacements in changes.items():
 p=C/name;s=p.read_text(encoding='utf-8')
 for old,new in replacements:assert old in s,(name,old);s=s.replace(old,new)
 p.write_text(s,encoding='utf-8')
for p in C.glob('*.py'):
 s=p.read_text(encoding='utf-8');s=s.replace(".read_text()",".read_text(encoding='utf-8')")
 p.write_text(s,encoding='utf-8')
note='\n## 2026-10-04：实测模块前纠正筛选帧支撑\n\n复核原A3发现连续记录LOFAR包含跨300秒边界的帧，初版逐窗口实现只有291帧。尚无任何实测模块运行或输出。保留初版完整筛选/冻结表/指纹及其105?记录说明于X3_real/qa/initial_independent_window_screen，原数值代码不改；新增连续筛选接口，把完全相同的已提取基带按原A3拼接并计算LOFAR，按帧中心归属每时段，保持原阈值。最终105个通过案例，16个时长窗口，主图角色不变，并在实测模块前重新冻结。这是纠正未提交实测测试集的接口实现，使最终筛选与方案及原A3一致；未按任何BTA输出调整测试集或方法。初版实际通过106个案例，最终105个；两者均保存，任何新增/减少均由同一原判据决定。后处理仅更新测试集大小断言和图注/报告的帧支撑说明，统计公式、种子、估计量不变，初版源码与清单另行留档。\n'
note=note.replace('及其105?记录说明','及其记录说明')
with (R/'DEVIATIONS.md').open('a',encoding='utf-8') as f:f.write(note)
(R/'X3_real/FINAL_SCREENING_CONTRACT.md').write_text('最终筛选严格沿用A3连续LOFAR的帧支撑，取代新驱动初稿EXECUTION_CONTRACT中逐窗口291帧的表述。105个通过案例、16个时长窗口；阈值、原始输入和方法完全不变。初版106案例完整留档。重新冻结发生在任何实测模块之前。X1短批次期间有约一分钟连续筛选CPU负载，计时均明确为受负载影响的墙钟而非串行基准。',encoding='utf-8')
print('Preanalysis sources archived; count assertions and frame-support descriptions corrected; statistical methods unchanged')
