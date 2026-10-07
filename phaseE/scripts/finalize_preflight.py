from pathlib import Path
import csv
import hashlib
import json
import shutil

ROOT = Path('D:/论文集')
LOCAL = ROOT / 'phaseE'
REPO = ROOT / 'GitHub整理_20261007/acoustic-trajectory-autofocus-paper'
out = LOCAL / 'E0_preflight'
status = json.loads((out / 'preflight_status.json').read_text(encoding='utf-8'))
assert status['passed'] and status['checked_records'] == 3 and status['checked_frontend_rows'] == 12
with (out / 'preflight_records.csv').open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 12 and all(r['passed'] in ('1','true') for r in rows)
with (out / 'PROTECTED_FILES_before.csv').open(encoding='utf-8-sig', newline='') as f:
    protected = list(csv.DictReader(f))
for r in protected:
    p = ROOT / r['path']
    assert p.stat().st_size == int(r['bytes']) and hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256'], p
(out / 'PROTECTED_FILES_check.json').write_text(json.dumps({'files': len(protected), 'all_unchanged': True}, indent=2)+'\n', encoding='utf-8')
incident = {'incident': 'MATLAB exit 0xc0000374 (heap corruption) during process shutdown',
            'numerical_preflight_passed': True, 'complete_csv_rows': 12,
            'saved_mat_files': [p.name for p in out.glob('rerun_*.mat')],
            'recovery': 'Read saved MAT structures back against all 12 CSV rows before trajectory export; do not replay completed optimizations.'}
(out / 'ENVIRONMENT_EXIT_INCIDENT.json').write_text(json.dumps(incident, indent=2)+'\n', encoding='utf-8')
note = f'''# 0.1 复现预检

结果：通过。原样调用冻结的 `phaseX2_one`，复跑 S0/−16 dB/记录 1、S2/−20 dB/记录 7、S0/−8 dB/记录 50，共 3 条记录、12 个前端结果。

- 12 行输入 MD5 均与原 X2 表一致。
- 输入相干效率最大绝对差：{status['max_eta_in_abs_diff']:.17g}。
- 输出相干效率最大绝对差：{status['max_eta_out_abs_diff']:.17g}。
- 判定阈值：相干效率绝对差 < 1e-9。
- {len(protected)} 个冻结方案、参数、调用源码和结果表的 SHA-256 均未变化。

`preflight_records.csv` 的每行是一个记录与前端配对。`*_saved` 为原 X2 CSV 值，`*_replayed` 为本次复跑值，`*_abs_diff` 为两者绝对差，`passed` 是指纹和两项相干效率检查的共同结果。`run_config.json` 列明样本和环境。

环境事件：全部三条记录的结果、12 行 CSV 和通过状态保存后，MATLAB 在退出时报告 0xc0000374 堆损坏。任务 A 启动前将从三个已保存 MAT 结构回读全部 12 行，逐行核对 CSV；已完成求解不重跑。事件单独记录在 `ENVIRONMENT_EXIT_INCIDENT.json`。

原始复跑 MAT 与运行日志仅保存在本机 `D:\\论文集\\phaseE\\E0_preflight\\`；指纹见 `OUTPUT_MANIFEST_sha256.csv`。本次驱动的新输出全部在 Phase E。
'''
(out / 'README.md').write_text(note, encoding='utf-8')
files=[p for p in out.iterdir() if p.is_file() and p.name!='OUTPUT_MANIFEST_sha256.csv']
with (out / 'OUTPUT_MANIFEST_sha256.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['file','bytes','sha256','storage']);w.writeheader()
    for p in sorted(files):
        w.writerow({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                    'storage':'local_only' if p.suffix in ('.mat','.log') else 'repository_and_local'})
for p in out.iterdir():
    if p.is_file() and p.suffix not in ('.mat','.log'):
        shutil.copy2(p,REPO/'phaseE/E0_preflight'/p.name)
for p in (LOCAL/'scripts').glob('*'):
    if p.is_file(): shutil.copy2(p,REPO/'phaseE/scripts'/p.name)
readme='''# Phase E 补充分析

本次执行范围：0.1 复现预检与任务 A。完整任务书保持收到的原文，后续任务尚未启动。

- [任务书](TASKS_PhaseE_20261007.md)
- [0.1 预检结果](E0_preflight/README.md)：三条记录、四种前端，共 12 行通过。
- [任务 A：轨迹导出与理论指标](E1_trajexport/README.md)
- 第一批报告、图、逐例 CSV 和工作清单位于 `当前主线精选_20261003/13_第一批补充分析_20261007/`。

本机新输出：`D:\\论文集\\phaseE\\`。已有轨迹取自原 X1/X2 分块，重新生成同一种子的记录仅用于核对真值与输入指纹；任务 A 不重新运行前端与修正求解器。
'''
for p in (LOCAL/'README.md',REPO/'phaseE/README.md'):p.write_text(readme,encoding='utf-8')
placeholder='''# 任务 A：轨迹导出与理论指标

状态：待执行。0.1 三条记录的数值预检已通过。将先回读预检的已保存文件，再导出已有 X2 轨迹；H5 留在本机，逐条理论指标和汇总表提交到仓库。
'''
for p in (LOCAL/'E1_trajexport/README.md',REPO/'phaseE/E1_trajexport/README.md'):p.write_text(placeholder,encoding='utf-8')
index=REPO/'README.md'
s=index.read_text(encoding='utf-8')
if '## 补充分析（2026-10-07）' not in s:
    s+='\n## 补充分析（2026-10-07）\n\n[Phase E 任务与进度](phaseE/README.md)：先执行复现预检和已有轨迹的理论分析。第一批材料见 `当前主线精选_20261003/13_第一批补充分析_20261007/`。正文和冻结实验保持原样。\n'
    index.write_text(s,encoding='utf-8')
print(json.dumps({'preflight_passed':True,'checked_rows':12,'protected_files_unchanged':len(protected)},ensure_ascii=False))
