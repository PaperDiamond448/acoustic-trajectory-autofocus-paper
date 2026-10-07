from pathlib import Path
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
REV = Path(r'D:/论文集/当前主线精选_20261003/11_正文稿/修订稿_20261005')

def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8-sig'))

def link(label, path):
    return f'[{label}]({Path(path).as_posix()})'

sim = read('simulation_cell_reproduction.json')
real = read('real_case_reproduction.json')
geo = read('归属与敏感性独立核查.json')
layout = read('段落与版面核查.json')
environment = read('MATLAB_environment.json')
assert all(x['status'] == 'PASS' for x in (sim, real, geo, layout))
before = read('protected_inputs_before.json')
after = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before}
changed = [p for p in before if before[p] != after[p]]
assert not changed, changed
(OUT / 'protected_inputs_after.json').write_text(json.dumps(after, ensure_ascii=False, indent=2), encoding='utf-8')
with zipfile.ZipFile(REV / '论文修订稿_中文_20261005.docx') as z:
    root = ET.fromstring(z.read('word/document.xml'))
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    table_count = len(root.findall('.//w:body/w:tbl', ns))

metric_labels = {'eta_LPS': 'LPS 相干效率', 'eta_final': '修正后相干效率',
    'gain_eta': '相干效率增量', 'gain_peak_db': '谱峰增量（dB）'}
comparison_rows = '\n'.join(f"| {metric_labels[x['metric']]} | {x['expected_mean']:.12f} | {x['reproduced_mean']:.12f} | {x['difference']:.3g} |" for x in sim['comparisons'])
report = f'''# 第二轮修订验收意见（2026-10-06）

致作者及协助修订者

本轮以更新后的修订稿和 P 编号快照为准，逐项验收上一轮的六项最小修改清单。第 1 至 5 项已闭合；第 6 项的本地运行材料和选定处理链复现通过，公开获取方式按作者决定暂缓。当前收窄主张下，本轮未发现仍需强制新增实验才能消除的科学内容阻碍，可以进入定刊和投稿整理。P0241 的占位符仍需在正式提交前由作者确定。此结论是投稿前模拟复核意见，不是期刊录用决定。

## 一、材料与对位

- {link('更新后的 Word 修订稿', REV / '论文修订稿_中文_20261005.docx')}。
- {link('第二轮修改说明', REV / '回复审稿' / '第二轮修改说明_20261006.md')}。
- {link('新稿 P 编号快照', REV / '回复审稿' / '修订稿Word正文段落.txt')}。

Word XML 与快照的 {layout['paragraph_count']} 段非空正文逐字一致，正文包含 {table_count} 张表。下文使用新稿 P 编号，不沿用上一轮位置。排版检查 PDF 为 {layout['pdf_pages']} 页。本轮保护的 {len(before)} 个文件，包括原稿、修订稿、作者回复、原结果表及三份独立审稿报告，运行前后 SHA-256 均未变化。所有新结果另存于本验收目录。

## 二、六项修改的验收

| 上轮清单编号 | 新稿位置 | 验收意见 | 状态 |
|---|---|---|---|
| 1. 有限实测定位 | P0003、P0018、P0175、P0192、P0232、P0233、P0238 | 摘要、贡献、实测开头、讨论与结论统一以 100 Hz 五个时段为主要实测证据。保留全部 15 例及事后形成的 8 例描述性子集，未把带内最大峰的增长统一解释为目标增益。 | 已闭合 |
| 2. 几何类别及敏感性 | P0187、P0189、P0190、P0192、P0198、P0296 至 P0299，表 6 与表 B2 | 类别与正文解释已统一。明确几何判据不确认声源身份，补充逐帧偏差分位、帧比例、阈值与峰值窗口敏感性。独立重算全部通过。 | 在有限主张下闭合 |
| 3. 唯一性、目标对准与常值偏差 | P0076、P0218、P0219 | 已删除唯一解与必然对准预定目标的暗示，不再用输出改变量反推输入偏差。常值分量占用修正预算，较大常值偏差未经单独检验，均已写明。 | 有条件闭合 |
| 4. 跨前端实测比较 | P0195、P0224 | 改用两条链路修正前后均满足几何判据的同一组 100 Hz 五个时段。1.74 dB 与 0.065 dB 的配对描述成立，也明确追加增量不等于完整链路最终性能排序。 | 已闭合 |
| 5. 图 13 与 Hann 宽度 | P0210、P0214、P0297 | Word 内嵌图 13 与新版 PNG 相同，PDF 中 103 Hz 的 450 s 点为半实心。第一零点约 ±0.20 Hz、零点间全宽约 0.40 Hz 的表述正确，0.05 Hz 未再解释为校准定位精度。 | 已闭合 |
| 6. 获取方式与运行材料 | P0241、表 B1（P0285）、P0291、P0298 | 随机发生器和抽取顺序、转移核离散化与归一化、频率读出截断已补。归属脚本及其基带输入在本工作区运行通过；选定仿真单元与实测案例完整重跑通过。P0241 仍由作者暂缓。 | 技术核验通过，公开方式待作者定稿 |

第 3 项的有条件闭合以不恢复“较大常值偏差也可靠”的主张为前提，不代表已完成 E1。第 2 项的闭合以有限几何验证为边界，不代表已取得真实目标身份标签。

## 三、独立数值检查

使用作者当前的归属脚本，保留默认基带读取规则，只将输出目录指向本验收目录，未重筛案例或修改原归属判据。15 例最大峰归属表及 16 个嵌套时长窗口表与作者文件逐项相同。另从基带 LOFAR 与保存轨迹重算表 B2 的逐帧统计，最大数值差为 {geo['max_numeric_difference_by_table']['逐帧偏差统计_15例.csv']:.3g}。

| 检查项 | 重算结果 | 判断 |
|---|---|---|
| 100 Hz 五个时段的谱峰增量 | {geo['hundred_hz']['gain_min_db']:.5f} 至 {geo['hundred_hz']['gain_max_db']:.5f} dB，中位数 {geo['hundred_hz']['gain_median_db']:.5f} dB | 支持正文 1.03 至 2.74 dB、中位 1.74 dB |
| 100 Hz 五个时段的局部对应 | 0.05 Hz 内帧比例为 95.67% 至 100%，偏差 90% 分位数为 0.02343 至 0.03955 Hz | 支持作为主要有限实测证据 |
| 接受阈值为 0.025、0.040、0.050、0.075 Hz | 满足判据的例数为 5、7、8、9，中位增量为 1.74、1.74、1.82、1.89 dB | 原规则与敏感性结果应并列，不能将 8 例称为已确认目标集合 |
| 同一 100 Hz 五时段的跨前端追加增量 | VIT-LPS 后中位数 {geo['hundred_hz']['paired_LPS_median_gain_db']:.5f} dB，相位连续 TBD 后 {geo['hundred_hz']['paired_TBD_median_gain_db']:.5f} dB | 支持配对描述，不建立普遍性能排序 |
| 61 Hz、2100 s 起点的峰值窗口 | ±0.10 Hz 为 +2.57839 dB，±0.05 Hz 为 −0.71336 dB；只有 54% 的帧在 0.05 Hz 以内 | 保留窗口与局部偏离限制，不据此确认目标退化或实测扩张收益 |

新稿已明确 100 Hz 五个时段来自同一航次、同一阵元、同一频点，嵌套时长窗口还存在数据重叠。它们提供重复时段的观察，不能作为跨目标或跨航次验证。

数值记录见 {link('归属与敏感性独立核查', OUT / '归属与敏感性独立核查.json')}。

## 四、补做的处理链复现

本次实际调用 MATLAB {environment['release']} 的原有处理函数，参数冻结文件与现有源文件清单核对通过。以下结果来自重算，不只是重新汇总 CSV。核验入口的列映射与运行目录在启动阶段作过修正，原算法、参数、原结果表均未改动；最终判断以 PASS 记录为准。

### 4.1 一个完整仿真单元

选择 S0、−17 dB、scaled 参数规则下的 {sim['records']} 个随机种子，逐条从生成复基带、运行 VIT 和 LPS 到执行完整冻结修正。逐条核对种子、输入哈希、效率、谱峰、触发状态和扩张轮数。效率差容限为 {sim['eta_tolerance']:.0e}，谱峰及增量差容限为 {sim['db_tolerance']:.0e} dB，全部通过。

| 指标 | 原结果均值 | 重算均值 | 差值 |
|---|---|---|---|
{comparison_rows}

修正后效率的逐记录最大绝对差为 {sim['max_per_record_eta_difference']:.3g}；谱峰增量逐记录最大绝对差为 {sim['max_per_record_gain_db_difference']:.3g} dB。

### 4.2 一个实测案例

选择 100 Hz、900 s 起点、300 s 窗口、第 9 通道，从原始声学文件重新提取带保护段的复基带，所得序列与保存输入逐样点一致，再运行 VIT、LPS 与完整冻结修正。LPS 和修正后相对原始周期图的谱峰增量分别为 {real['rows'][0]['peak_relative_periodogram_db']:.12f} 和 {real['rows'][1]['peak_relative_periodogram_db']:.12f} dB，修正相对 LPS 的增量为 **{real['gain_db']:.12f} dB**。轨迹与原结果的最大绝对差为 {max(x['max_abs_track_difference_hz'] for x in real['rows']):.3g} Hz，两种输出的最大峰频率均为 100 Hz。

这两个检查支持所选主链路的本地计算复现。没有重跑全部 2800 条确认记录、所有前端或全部实测案例，也没有完成外部机器或公开下载材料的复现。重跑同一案例不会增加独立实测样本，更不能据此确认其物理身份。

完整核验记录见 {link('处理链复现结果', OUT / 'end_to_end_reproduction.json')}。逐条仿真输出见 {link('仿真单元重算表', OUT / 'simulation_cell_reproduction.csv')}，实测核验见 {link('实测案例重算记录', OUT / 'real_case_reproduction.json')}。

## 五、对作者四个复核问题的直接回答

1. **实测定位是否与证据强度一致**。一致。保留目前摘要与结论即可，不必再次改回 15 例或 8 例的宽泛增强结论。主要依据仍是 100 Hz 的五个时段，方法定量有效性主要由仿真支持。
2. **是否足以闭合 S-M1 中几何判据与身份的区分**。在目前有限主张下可以闭合。P0187、P0192 与表 B2 已把判据、局部偏离和事后子集说清楚。真实声源身份仍不由这些统计确认，此边界应保留。
3. **P0076、P0219 是否可闭合 R1-M1**。可以有条件闭合。新稿不再声称唯一解、必然对准目标或从输出改变量得知输入偏差。较大常值偏差的性能仍是未经单独检验的适用条件。
4. **除 P0241 与处理链复现外是否还有阻碍投稿的事项**。本轮没有发现需要新增实验才能解决的科学内容阻碍；所建议的选定处理链复现现已完成。P0241 按作者决定暂缓，正式提交前仍需填入真实获取方式。定刊后再按期刊要求调整篇幅和版式。

E1 至 E5 仍未完成，也无需因本轮验收再将其全部列为必做。若以后扩大较大频偏、未知干扰、三阶段优势、真实背景目标效率或跨目标泛化等主张，对应实验需重新评估。E5 仍是最有帮助的补强方向，当前 P0233 将其写为进一步检验是合适的。

## 六、版面与剩余事项

查看了当前 {link('排版检查 PDF', REV / '_build' / '排版检查' / '修订稿.pdf')} 第 30、31 和 35 页。第 30 页的下半页留白与紧接着的图 11 大图有关，没有造成文字缺失或图注断裂，当前不构成科学内容问题。第 31 页完整展示 15 个案例和图注，第 35 页的图 13 三类标记与正文对应。图 11 较密，定刊后若缩小到单栏，应再核对最终字号；本轮无需为消除留白而移动论证结构。这里只核查了相关页面，未声称全 52 页的最终印刷版式均已验收。

作者后续只需按既定安排完成 P0241，并按目标期刊整理篇幅和格式。本报告没有修改原稿、修订稿或作者回复，也未改写先前冻结的独立审稿报告。没有重做全部外部参考文献核验，也没有独立认证开发记录及归属规则最初锁定的历史时点。上一轮关于中文文献的判断不变，无需按比例继续增加中文引用。
'''
target = OUT / '第二轮修订验收意见_20261006.md'
target.write_text(report, encoding='utf-8')
summary = dict(status='PASS', checklist_1_to_5='closed within bounded claims',
    checklist_6_local_reproduction='PASS', code_availability='author-deferred; P0241 placeholder retained',
    simulation_cell=sim, real_case=real, geometry=geo, layout=layout,
    protected_file_count=len(before), changed_protected_files=changed, report=str(target))
(OUT / '第二轮验收汇总.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(target))
print('ACCEPTANCE_REPORT_PASS')
