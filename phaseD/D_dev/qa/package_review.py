"""Package completed stop-point-one evidence; large MAT chunks remain local."""
from pathlib import Path
import csv,hashlib,json,zipfile
ROOT=Path(r'D:\论文集\phaseD');OUT=ROOT/'D_dev'
assert (OUT/'STOP_POINT_1.txt').exists()
for filename in ['development_audit.json','saved_outputs_audit.json']:
    assert json.loads((OUT/'qa'/filename).read_text(encoding='utf8'))['status']=='PASS'
figure_qa=json.loads((OUT/'qa/FIGURE_QA.json').read_text(encoding='utf8'))
assert figure_qa['status']=='PASS' and figure_qa.get('visual_review_passed') is True
f=json.loads((OUT/'FROZEN_METHOD.json').read_text(encoding='utf8'))
assert f['confirmation_started'] is False
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
files=[p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='RESULTS_MANIFEST_sha256.csv']
with (OUT/'RESULTS_MANIFEST_sha256.csv').open('w',encoding='utf8',newline='') as stream:
    writer=csv.writer(stream);writer.writerow(['relative_path','bytes','sha256','in_review_zip'])
    for p in sorted(files):writer.writerow([p.relative_to(ROOT).as_posix(),p.stat().st_size,sha(p),p.suffix.lower()!='.mat'])
readme=f'''# Phase D 停止点 1 核对包

仅 phase 51 开发；方法 {f['method']}，分支 {f['branch']}，Δ={f['Delta_s']} s，P={f['P']}。
先核对 D_dev/DEV_REPORT.md 与 D_dev/FROZEN_METHOD.json，然后查看规则表、逐记录表和核验门。
确认 C 未启动。用户核对并另行放行后才能开始确认阶段。

大体积逐记录 MAT 分块不放入此 ZIP，保留于本机 D:\\论文集\\phaseD\\D_dev\\*_chunks。
D_dev/RESULTS_MANIFEST_sha256.csv 列出全部新结果（含 MAT）的哈希和是否进入核对包。
原始数据、既有实验结果、技能备份和 Python 本地运行库不包含在 ZIP 中。
代码使用本机预注册的既有 MATLAB 模块；源码清单明确列出其绝对路径与哈希。
qa 目录包含只读审计脚本和报告，未进行新的模拟或优化。
'''
(OUT/'REVIEW_PACKAGE_README.md').write_text(readme,encoding='utf8')
selected=[p for p in OUT.rglob('*') if p.is_file() and p.suffix.lower()!='.mat' and '__pycache__' not in p.parts]
selected += [p for folder in ['code','G_gates'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
selected += [ROOT/name for name in ['PREREGISTRATION_PhaseD_20261003.md','PREREGISTRATION_PhaseD_ADDENDUM_20261003.md','00_给GPT的执行消息.md','DEVIATIONS.md','SOURCE_REVISION_HISTORY.json','BASELINE_MANIFEST_sha256.csv','machine_info.json'] if (ROOT/name).exists()]
selected += [ROOT/'skill_audit'/name for name in ['comparison.json','update_result.json','INPUT_PACKAGE_AUDIT.json'] if (ROOT/'skill_audit'/name).exists()]
target=ROOT/'PhaseD_停止点1_核对包_20261004.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in sorted(set(selected)):archive.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(target) as archive:assert archive.testzip() is None
(ROOT/'PhaseD_停止点1_核对包_20261004.sha256.txt').write_text(sha(target)+'  '+target.name+'\n',encoding='utf8')
print(json.dumps({'zip':str(target),'bytes':target.stat().st_size,'entries':len(set(selected))},ensure_ascii=False))
