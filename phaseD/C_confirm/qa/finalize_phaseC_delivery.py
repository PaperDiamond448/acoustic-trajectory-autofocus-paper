"""Output-only report additions documenting the saved-output exit incident and scene limits."""
from pathlib import Path
import csv, hashlib, json, subprocess, sys

ROOT=Path(r'D:\论文集\phaseD');OUT=ROOT/'C_confirm'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def finalize():
    native=json.loads((OUT/'SAVED_OUTPUTS_AUDIT.json').read_text(encoding='utf8'))
    independent=json.loads((OUT/'INDEPENDENT_AUDIT.json').read_text(encoding='utf8'))
    cross=json.loads((OUT/'CSV_MAT_RECONCILIATION.json').read_text(encoding='utf8'))
    assert native['status']==independent['status']==cross['status']=='PASS'
    raw=list(csv.DictReader((OUT/'RAW_OUTPUTS_AFTER_NUMERIC_RUN_sha256.csv').open(encoding='utf8')))
    assert len(raw)==282
    for r in raw:assert sha(Path(r['source_file']))==r['sha256'],r['source_file']
    p=OUT/'ENVIRONMENT_EXIT_INCIDENT.json';incident=json.loads(p.read_text(encoding='utf8'))
    incident.update(validation_status='PASS_all_saved_outputs_and_decision_inputs_unchanged',native_audit=native,independent_statistical_audit=independent,raw_file_hashes_verified=282,solver_retries=0)
    p.write_text(json.dumps(incident,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/'codeC/write_confirm_report.py')],check=True)
    report=OUT/'CONFIRM_REPORT.md';text=report.read_text(encoding='utf8')
    d=json.loads((OUT/'CONFIRM_DECISION.json').read_text(encoding='utf8'))
    s0=d['by_scene']['S0']['FM_minus_UNB'];s2=d['by_scene']['S2']['FM_minus_UNB']
    scene_note=(f"**合并通过不表示所有场景均不劣于 UNB。** S0 中 FM−UNB 平均 Δη={s0['mean']:.6f}，95% CI [{s0['lo']:.6f}, {s0['hi']:.6f}]；S2 中为 {s2['mean']:.6f}，95% CI [{s2['lo']:.6f}, {s2['hi']:.6f}]。P2 的预登记判定单位是合并值，因此正式分支仍为 C-A1；论文须同时交代无干扰场景下的 η 代价，不能写成逐场景均优于或非劣于去盒界。\n\n")
    text=text.replace('## 5. S1 完整单元核对',scene_note+'## 5. S1 完整单元核对',1)
    text=text.replace('2,000 次配对 bootstrap；2.5/97.5 百分位。','所有判定使用未四舍五入数值；表中均值与区间显示六位小数。\n\n2,000 次配对 bootstrap；2.5/97.5 百分位。',1)
    stop='**已到停止点 2。确认后未调整方法，也未执行 X1–X3。请用户核对本报告与逐条记录后决定是否放行后续阶段。**'
    environment=("### 数值进程退出异常及验证\n\n全部 280 个 MAT 检查点、14,000 行逐条 CSV 与最终运行配置写入完成后，MATLAB 数值批处理进程退出时报 `0xc0000374`（heap corruption）。不能据此声称整个进程无异常。未重新运行任何求解器，也未追加预算；另开 MATLAB 进程作只读复核，退出正常。\n\n"
        f"- 280 个 MAT 文件包含全部 2,800 条记录及五种方法。独立重建输入并复算全部指标通过；最大指标差 {native['metric_max_abs_difference']:.3g}，轨迹重构最大差 {native['track_max_abs_difference']:.3g}，均不超过预先声明的 10⁻¹² 容差。\n"
        f"- 14,000 行 CSV 的每个字段与原始 MAT 对照通过；最大数值差 {cross['numeric_max_abs_difference']:.3g}，符合 CSV 十进制输出精度。字符串、键、方法和种子一致。\n"
        "- 全部 282 个原始输出文件（280 MAT、CSV、运行配置）的事后指纹保持不变；独立 Python 从原始 η 重算终点、CI 和分支一致。\n"
        "- 原始退出异常及上述证据保存在 `ENVIRONMENT_EXIT_INCIDENT.json`、`CSV_MAT_RECONCILIATION.json`、`RAW_OUTPUTS_AFTER_NUMERIC_RUN_sha256.csv`；新增复核仅作只读输出验证，没有改变判定输入。\n\n")
    assert stop in text;text=text.replace(stop,environment+stop,1)
    report.write_text(text,encoding='utf8')
    d['execution_environment_incident']=dict(exit_code=incident['exit_code'],saved_outputs_validation='PASS',optimizer_retries=0,incident_record='ENVIRONMENT_EXIT_INCIDENT.json')
    (OUT/'CONFIRM_DECISION.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    p=OUT/'FINAL_STATUS.json';status=json.loads(p.read_text(encoding='utf8'))
    status.update(report_sha256=sha(report),raw_outputs_unchanged=True,execution_exit_incident_verified=True,output_notes_source_sha256=sha(Path(__file__)))
    p.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    with (OUT/'IMPLEMENTATION_NOTES.md').open('a',encoding='utf8') as f:
        f.write('\n退出异常之后新增只读 CSV/MAT 逐字段复核与输出报告补充脚本，登记源文件随核对包交付。全量指标重算、逐字段对照、原始输出指纹及独立终点重算全部通过；仅在报告中补充该异常及 S0 相对 UNB 的代价，没有更改已登记科学源码、原始输出或判定。\n')
    print('Final report includes scene tradeoff and verified exit incident; stop 2.')

if __name__=='__main__':finalize()
