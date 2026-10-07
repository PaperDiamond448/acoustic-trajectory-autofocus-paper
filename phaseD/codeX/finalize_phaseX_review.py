"""Finalize output prose, visual-review record and read-only delivery checks."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, re
import pandas as pd

R = Path('D:/论文集/phaseD')
Y = R/'Y_compute'
now = datetime.now(timezone.utc).isoformat()

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        while b:=f.read(4*1024*1024): h.update(b)
    return h.hexdigest()

qa_path=Y/'qa/FIGURE_QA.json'
qa=json.loads(qa_path.read_text(encoding='utf-8'))
assert qa['status']=='PASS'
qa['visual_review']='PASS'
qa['visual_review_utc']=now
qa['visual_review_scope']='All five final PNGs inspected: readable labels, no clipping or legend collisions, SMR white overlay outlined, negative duration gains visible, all passed cases retained; trajectory LOFAR segment gaps visible. Corresponding PDF/SVG hashes and automatic checks recorded below.'
qa_path.write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
(Y/'FIGURES_READY.json').write_text(json.dumps(dict(status='PASS',figures=5,formats=['PNG600dpi','PDF','SVG'],automatic_and_visual_review='qa/FIGURE_QA.json',completed_utc=now),ensure_ascii=False,indent=2),encoding='utf-8')

v=pd.read_csv(R/'X3_real/X3_visibility.csv')
coverage=v.groupby(['group','set_number'],dropna=False).agg(screened=('passed','size'),passed=('passed','sum')).reset_index()
assert coverage.screened.sum()==330 and coverage.passed.sum()==105
coverage.to_csv(R/'X3_real/X3_source_set_coverage.csv',index=False)
table='| 分组 | Set | 筛选候选数 | 通过数 |\n| --- | --- | --- | --- |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in coverage.itertuples(index=False,name=None))
p=R/'PHASE_D_REPORT.md'
s=p.read_text(encoding='utf-8')
s=re.sub(r'^- X[123] 最终驱动墙钟：.*\n','',s,flags=re.M)
s=s.replace('各X阶段顺序执行。','数值模块按阶段执行，X3 只读筛选复核曾与少量 X1 任务并行，见环境记录。')
anchor='| 组 | 配对 | 总数 | 谱峰增量中位(dB) | Q1 | Q3 | 正值个数 |'
coverage_text='各源级的可见性覆盖如下。弱线结果仅涵盖通过筛选的15个案例，其中 Set5 只有1个通过案例，120 dB 仍为推断源级；不能推广为全部弱线或每个源级均已验证。\n\n'+table+'\n\n详细覆盖见 [X3_source_set_coverage.csv](D:/论文集/phaseD/X3_real/X3_source_set_coverage.csv)。正值个数按原指标严格 >0 计数，接近浮点舍入量级的正值不能解释为实质改善。\n\n'
assert s.count(anchor)==1
s=s.replace(anchor,coverage_text+anchor)
s=s.replace('![实测轨迹与时长]', '轨迹图的 LOFAR 背景逐300 s段独立生成，每段291帧，段间留白明确显示缺失跨段帧；这是展示方式，可见性筛选使用上述全长连续 LOFAR。GPS 为参考而非真值。时长图保留全部16个冻结窗口，150 s窗口存在负增益，增益随时长也不必单调。\n\n![实测轨迹与时长]')
s=s.replace('若另有退出事件，均列于同目录事件日志。','后续环境退出、文件接口适配与恢复均留存于同目录事件日志及 DEVIATIONS；工作文件与提交分块逐字段等价核验通过。')
s=s.replace('## 完整性、环境事件与停止', '## 交付范围\n\n本轮交付 `PhaseD_X阶段完整核对包_20261004.zip`：X1–X3 与 Y 的逐记录结果、保存分块、独立系数矩阵、筛选与冻结表、图件三种格式、驱动与审计源码、日志、方案、冻结方法和确认摘要。它是供原工作目录配套使用的 X 阶段核对包，原始 SIO 航次数据、全部旧阶段原始结果与旧算法目录继续保留在本机原路径，不重复打包。逐文件 SHA-256 见 [FINAL_DELIVERY_MANIFEST.json](D:/论文集/phaseD/Y_compute/FINAL_DELIVERY_MANIFEST.json)，包内条目 SHA-256 与 CRC 见 [PACKAGE_VERIFICATION.json](D:/论文集/phaseD/Y_compute/PACKAGE_VERIFICATION.json)。\n\n## 完整性、环境事件与停止')
p.write_text(s,encoding='utf-8')

state=R/'codeX/RUN_STATE.md'
manifests=['codeX/SOURCE_MANIFEST_X_sha256.csv','codeX/PROTECTED_STOP2_sha256.csv','X3_real/X3_FREEZE_MANIFEST.csv','Y_compute/ENVIRONMENT_ADAPTER_MANIFEST.csv','codeX/POSTPROCESS_MANIFEST_sha256.csv','Y_compute/FILEBRIDGE_ADAPTER_MANIFEST.csv','Y_compute/V7BRIDGE_ADAPTER_MANIFEST.csv','Y_compute/X3_CSV_READ_ADAPTER_MANIFEST.csv','Y_compute/X3_FILEBRIDGE_ADAPTER_MANIFEST.csv','Y_compute/SHARDED_AUDIT_ADAPTER_MANIFEST.csv','Y_compute/REGISTERED_BOUNDS_AUDIT_ADAPTER_MANIFEST.csv','X3_real/CANONICAL_SCREEN_SOURCE_MANIFEST.csv','BASELINE_MANIFEST_sha256.csv']
for name in manifests:
    rows=list(csv.DictReader((R/name).open(encoding='utf-8-sig')))
    assert all(Path(row['source_file']).resolve()!=state.resolve() for row in rows),name
state.write_text('''# Phase D 最终状态

X1、X2、X3 与 Y 已全部完成并停止；C-A1 保持。最终方法 ADA_local_c04_t30_A，Δ=10 s，参数随 P 按冻结公式缩放。方案、补充、冻结文件、核心算法及旧阶段结果保持原样。不得依据 X 结果反调方法，不开启新实验或论文改写。

- X1：2400 条记录、9600 方法行，全部原生核验通过。
- X2：1400 条记录、5600 前端行，全部注册检查点及其他规则核验通过。
- X3：330 候选先筛选并冻结；105 通过案例×8方法，16 时长窗口×3方法，共888行。全部保存核验及独立谱/GPS重算通过。
- 无硬失败或预算触顶标记；所有负值及预定案例保留。
- 独立 v7.3 系数矩阵9份；模拟工作文件/分块2880条、实测时长16条逐字段等价。
- 5幅图的 PNG600dpi/PDF/SVG 自动检查及最终PNG目检通过。

X2 附加采样诊断：196条记录×前端、290轮均为入口不可用的MFT，20Hz极值最大2.009949748744Hz；注册Aineq/bineq最大违约3.47e−18Hz。这里 PASS 限于方案指定检查点，不宣称全采样严格±2Hz；未裁剪、删记录、改指标或调参。MFT原轨迹是分段线性，非网格折点的采样回插可能平滑折点。

环境适配、崩溃恢复、筛选接口纠正与计时范围见 DEVIATIONS.md、PHASE_D_REPORT.md 及 Y_compute 日志。最终报告为 phaseD/PHASE_D_REPORT.md；核对包为 phaseD/PhaseD_X阶段完整核对包_20261004.zip。完整文件与包验证见 Y_compute/FINAL_DELIVERY_MANIFEST.json、PACKAGE_VERIFICATION.json。没有正在运行的数值实验。
''',encoding='utf-8')

aux=Y/'AUXILIARY_DELIVERY_MANIFEST.csv'
rows=list(csv.DictReader(aux.open(encoding='utf-8-sig')))
for row in rows:
    if Path(row['source_file']).name=='render_phaseX_final.py': row['sha256']=sha(row['source_file'])
assert not any(Path(row['source_file']).name==Path(__file__).name for row in rows)
rows.append(dict(source_file=str(Path(__file__).resolve()),sha256=sha(__file__)))
with aux.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['source_file','sha256']);w.writeheader();w.writerows(rows)
manifests.append('Y_compute/AUXILIARY_DELIVERY_MANIFEST.csv')
checks={}
for name in manifests:
    rows=list(csv.DictReader((R/name).open(encoding='utf-8-sig')))
    for row in rows: assert sha(row['source_file'])==row['sha256'],row['source_file']
    checks[name]=len(rows)
audit_paths=['Y_compute/INTEGRITY_AUDIT.json','Y_compute/SUPPLEMENT_INTEGRITY_AUDIT.json','Y_compute/WORKER_CHUNK_BRIDGE_AUDIT.json','Y_compute/REAL_WORKER_CHUNK_BRIDGE_AUDIT.json','X1_duration/SAVED_OUTPUTS_AUDIT.json','X2_frontend/SAVED_OUTPUTS_AUDIT.json','X3_real/SAVED_OUTPUTS_AUDIT.json','X3_real/INDEPENDENT_REAL_METRICS_AUDIT.json','Y_compute/qa/FIGURE_QA.json']
for name in audit_paths: assert json.loads((R/name).read_text(encoding='utf-8'))['status']=='PASS',name
assert pd.read_csv(Y/'SOLVER_STATUS_BY_METHOD.csv')[['hard_fail_marked_rows','budget_cap_marked_rows']].to_numpy().sum()==0
(Y/'FINAL_REVIEW_CHECKS.json').write_text(json.dumps(dict(status='PASS',completed_utc=now,protected_manifest_counts=checks,all_required_audits=audit_paths,report_sha256=sha(p),numeric_or_method_changes=0,source_set_coverage='X3_real/X3_source_set_coverage.csv'),ensure_ascii=False,indent=2),encoding='utf-8')
print('Final report, coverage, visual-review record and all delivery source checks PASS.')
