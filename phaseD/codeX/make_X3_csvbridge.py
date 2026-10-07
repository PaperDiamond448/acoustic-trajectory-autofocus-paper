from pathlib import Path
import csv, hashlib
R = Path('D:/论文集/phaseD')
C = R / 'codeX'
source = (C / 'run_phaseX3_real.m').read_text(encoding='utf-8')
source = source.replace('function run_phaseX3_real()', 'function run_phaseX3_real_csvbridge()', 1)
old = "proof=readtable(fullfile(outdir,'X3_FREEZE_MANIFEST.csv'),'TextType','string');"
new = "proof=readtable(fullfile(outdir,'X3_FREEZE_MANIFEST.csv'),'Delimiter',',','Encoding','UTF-8','ReadVariableNames',true,'VariableNamingRule','preserve','TextType','string');\nassert(isequal(proof.Properties.VariableNames,{'source_file','sha256'}),'Freeze CSV schema mismatch');"
assert source.count(old) == 1
source = source.replace(old, new)
(C / 'run_phaseX3_real_csvbridge.m').write_text(source, encoding='utf-8')
with (R / 'Y_compute/X3_CSV_READ_ADAPTER_MANIFEST.csv').open('w', encoding='utf-8', newline='') as stream:
    w = csv.writer(stream)
    w.writerow(['source_file', 'sha256'])
    w.writerows((str(C / name), hashlib.sha256((C / name).read_bytes()).hexdigest())
                for name in ['make_X3_csvbridge.py', 'run_phaseX3_real_csvbridge.m'])
with (R / 'DEVIATIONS.md').open('a', encoding='utf-8') as stream:
    stream.write('\n## 2026-10-04：X3 冻结清单读取接口修复\n\nX1/X2全部数值与完整表保存后，原X3驱动在读取X3_FREEZE_MANIFEST.csv时自动推断的列名不能识别source_file，退出发生在进程池和任何实测模块启动之前。冻结清单、筛选表、角色、105案例和16窗口、原驱动以及数值函数均保持原样。新外层驱动仅显式指定逗号、UTF-8、首行表头并保留source_file/sha256两列，增加精确模式断言；逐行指纹仍照原核对，通过才允许运行。原失败日志保留，适配源指纹另登记X3_CSV_READ_ADAPTER_MANIFEST.csv。未改变筛选规则、判定输入、方法、候选、预算或任何数值计算。\n')
print('X3 CSV-read-only interface adapter registered; all frozen sources unchanged.')
