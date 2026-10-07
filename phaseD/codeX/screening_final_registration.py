from pathlib import Path
import csv,hashlib,json
R=Path('D:/论文集/phaseD');C=R/'codeX';O=R/'X3_real'
files=[C/'run_phaseX3_continuous_screen.m',C/'freeze_phaseX3.py',O/'FINAL_SCREENING_CONTRACT.md',O/'X3_TESTSET_FREEZE.json']
with (O/'CANONICAL_SCREEN_SOURCE_MANIFEST.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['source_file','sha256']);w.writerows((str(p),hashlib.sha256(p.read_bytes()).hexdigest()) for p in files)
A=R/'Y_compute/preanalysis_v1_sources'
with (A/'ARCHIVED_COPY_MANIFEST.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['archived_file','sha256']);w.writerows((str(p),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(A.iterdir()) if p.is_file() and p.name!='ARCHIVED_COPY_MANIFEST.csv')
(A/'README.md').write_text('此目录保留分析尚未执行时的初版11个源码及其原清单。原清单的source_file是初版工作路径；对应完整字节副本现位于此目录同名文件，ARCHIVED_COPY_MANIFEST提供归档后的绝对路径和指纹。最终执行版见codeX/POSTPROCESS_MANIFEST_sha256.csv，仅修正最终测试集大小断言、帧支撑说明与UTF-8读取，统计定义不变。',encoding='utf-8')
print('Canonical screening source and preanalysis archive registered')
