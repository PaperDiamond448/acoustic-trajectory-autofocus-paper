"""Record completed stop-point-one checks; leave frozen method untouched."""
from pathlib import Path
import csv,hashlib,json
ROOT=Path(r'D:\论文集\phaseD');OUT=ROOT/'D_dev';QA=OUT/'qa'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
f=read(OUT/'FROZEN_METHOD.json');a=read(QA/'development_audit.json');m=read(QA/'saved_outputs_audit.json');v=read(QA/'FIGURE_QA.json')
assert a['status']==m['status']==v['status']=='PASS' and v['visual_review_passed']
sha=hashlib.sha256((OUT/'FROZEN_METHOD.json').read_bytes()).hexdigest()
assert sha==a['frozen_method_sha256'] and f['confirmation_started'] is False
assert not (ROOT/'C_confirm').exists() and not any(p.name.startswith('X') for p in ROOT.iterdir() if p.is_dir())
assert (OUT/'STOP_POINT_1.txt').exists() and not (OUT/'EXECUTION_ERROR.txt').exists()
rows=sum(x['configuration_rows'] for x in m['stages'].values());failures=sum(x['hard_fail_count'] for x in m['stages'].values())
assert rows==39480 and failures==0
with (ROOT/'BASELINE_MANIFEST_sha256.csv').open(encoding='utf-8-sig',newline='') as stream:nold=len(list(csv.DictReader(stream)))
report=(OUT/'DEV_REPORT.md').read_text(encoding='utf8').split('\n## 最终完成核验')[0]
english='计时定义：'+f['provenance']['runtime_definition']+'。'
report=report.replace(english,'计时定义：6 个工作进程并发负载下的 BTA 求解调用墙钟。ADA 累计复用的 F02 求解时间与各扩张轮求解时间，不含前端、族/SMR 构建和驻留判定开销；没有进行串行基准测试。')
report+='\n## 最终完成核验\n\n'
report+=f'- G1–G8：全部通过。\n- 逐记录/规则/区间与哈希审计：{a["check_count"]} 项通过；{nold} 个原文件保持原哈希。\n- 全部 420 个 MATLAB 分块、{rows:,} 条配置记录通过保存输出审计；hard fail 为 {failures}。这些来自同一套 840 个配对输入，不是独立扩大的样本。\n- 三张最终图的 1.5 pt 面板对齐、最小字号（均 7 pt）、碰撞（无 FAIL/WARN）和逐面板目视核验全部通过。\n- FROZEN_METHOD.json 最终 SHA-256：`{sha}`。\n- 当前仅达到停止点 1；C_confirm 与 X 结果目录均未生成。\n'
(OUT/'DEV_REPORT.md').write_text(report,encoding='utf8')
status={'status':'stop_point_1_complete_awaiting_user_rule_audit','method':f['method'],'branch':f['branch'],'Delta_s':f['Delta_s'],'P':f['P'],'ADA':f['ADA'],'frozen_method_sha256':sha,'gates':'PASS','development_audit_checks':a['check_count'],'saved_configuration_rows':rows,'hard_fail_count':failures,'figure_QA':'PASS','original_files_unchanged':nold,'confirmation_started':False,'resolved_representation_issue':'CSV binary flags; original data and numerical solvers unchanged; evidence retained in DEVIATIONS.md'}
(OUT/'FINAL_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(status,ensure_ascii=False))
