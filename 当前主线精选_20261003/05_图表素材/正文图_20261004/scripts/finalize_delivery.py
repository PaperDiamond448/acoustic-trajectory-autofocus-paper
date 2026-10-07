from pathlib import Path
import hashlib,json,html,shutil,zipfile
import pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1];P=R.parent/'phaseD';V=R/'10_论证骨架/实验设计复核_20261004'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cap=json.loads((O/'CAPTIONS.json').read_text(encoding='utf-8'))
qa=json.loads((O/'qa/AUTOMATED_QA.json').read_text(encoding='utf-8'))
source=json.loads((O/'qa/source_audit.json').read_text(encoding='utf-8'))
assert source['summary']['counts']['FAIL']==0 and source['summary']['counts']['WARN']==0
assert len(qa)==15
for n,q in qa.items():
 assert q['collision']=='PASS' and q['alignment'] in ['PASS','NOT APPLICABLE'] and q['below_minimum_count']==0 and q['auditable']
 for e,h in q['sha256'].items():assert sha(O/(n+'.'+e))==h
data=json.loads((O/'SOURCE_DATA_MANIFEST.json').read_text(encoding='utf-8'))
for n,item in data.items():assert sha(O/'source_data'/n)==item['sha256']==sha(item['source'])
F=json.loads((P/'D_dev/FROZEN_METHOD.json').read_text(encoding='utf-8'))
core=['phaseD_ada.m','phaseD_dwell.m','estimate_proposed_T.m','build_family_T.m','phaseD_regularization.m']
hashes={}
for n in core:
 entry=next(x for x in F['code_sha256_manifest'] if Path(x['source_file']).name==n)
 hashes[n]=sha(entry['source_file']);assert hashes[n]==entry['sha256']
review_expected={'review_1_method.md':'d029ad2f872e3e33db836b3842b5342cdc3696e3994a6a8b8624c259f71340c7','review_2_statistics.md':'7f2fe74be1139180fd75780fa6f14907afd7d0fcdedcdab11f9bcf86c737a9f0','review_3_realdata.md':'fa94df7edf045d82b152836e4dd10f47f04554df9c13f33589a4be8e928323a1'}
for n,h in review_expected.items():assert sha(V/n)==h
(V/'FINAL_INTEGRITY.json').write_text(json.dumps({'status':'PASS','core_frozen_algorithms':hashes,'independent_reviews_unchanged':review_expected,'figure_source_copies_verified':len(data),'figures_verified':len(qa),'manuscript_skeleton_v1_sha256':sha(R/'10_论证骨架/论证骨架_v1.md')},ensure_ascii=False,indent=2),encoding='utf-8')
titles=['运动与传播几何','误差结构与相干输出','局部自适应处理结构','节点间隔与计算量','开发集修正范围比较','独立确认集主结果','确认集收益与退化取舍','积累时长与计算量','四种前端的配对收益','全部105个实测案例','预定实测谱：全带与局部','连续LOFAR、轨迹与时长','补图S1：开发集观测谱峰','补图S2：确认逐单元配对差','补图S3：前端RMSE诊断']
names=sorted(cap);assert len(names)==len(titles)
intro='保留12张正文图，另附3张补图。使用Nature Figure从既有数据重绘，完整图注及来源随图交付。PDF/SVG为可编辑矢量版，PNG/TIFF为600 dpi；实测LOFAR为高分辨率栅格图层。图11保留133 Hz例真实的峰位转换，不把带内最大值增量误写成已确认同一目标的增强。'
md=['# 新版图集（2026-10-04）','',intro,'','[图注](图注.md) · [质量核验](qa/FINAL_QA.md) · [网页浏览](图集.html)','']
web=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>论文图集 · 2026-10-04</title><style>body{margin:0;background:#edf1f3;color:#273440;font-family:Arial,"Microsoft YaHei",sans-serif;line-height:1.7}main{max-width:1080px;margin:40px auto;padding:0 24px}section{background:white;border-radius:12px;padding:26px;margin:24px 0}img{width:100%;height:auto}a{color:#226887}h1{font-size:30px}h2{font-size:21px}nav{display:flex;gap:15px;flex-wrap:wrap}p{max-width:980px}@media print{section{break-inside:avoid}body{background:white}}</style><main><h1>论文图集 · 2026-10-04</h1><p>'+html.escape(intro)+'</p><nav>']
web.extend(f'<a href="#f{i}">{i if i<=12 else "S"+str(i-12)}</a>' for i in range(1,16));web.append('</nav>')
table=['| 图 | 内容 | 当前文件 |','|---|---|---|']
for i,(n,title) in enumerate(zip(names,titles),1):
 label=f'图{i}' if i<=12 else f'补图S{i-12}'
 links=' · '.join(f'[{e.upper()}]({n}.{e})' for e in ['pdf','svg','png','tiff'])
 md.extend([f'## {label}　{title}','',links,'',f'![{title}]({(O/(n+".png")).as_posix()})','',cap[n],''])
 web.append(f'<section id="f{i}"><h2>{html.escape(label+"　"+title)}</h2><nav>'+''.join(f'<a href="{n}.{e}">{e.upper()}</a>' for e in ['pdf','svg','png','tiff'])+f'</nav><img loading="lazy" src="{n}.png" alt="{html.escape(title)}"><p>{html.escape(cap[n])}</p></section>')
 table.append(f'| {label} | {title} | [{n}](正文图_20261004/{n}.pdf) |')
(O/'图集.md').write_text('\n'.join(md),encoding='utf-8');(O/'图集.html').write_text(''.join(web)+'</main></html>',encoding='utf-8')
listing=R/'05_图表素材/图表清单.md';backup=V/'before_revision/05_图表素材/图表清单.md';backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists():shutil.copy2(listing,backup)
listing.write_text('# 当前图表清单\n\n2026-10-04。正文保留12张，不合并。当前使用下列新版，原稿、新初稿与Phase D报告图作为来源留档。\n\n[完整图集](正文图_20261004/图集.md) · [网页浏览](正文图_20261004/图集.html) · [完整图注](正文图_20261004/图注.md)\n\n'+'\n'.join(table)+'''\n\n## 历史材料的处理

- 原P60的 `原稿图/fig5_detection`、`figS1_false_alarm` 及T0/T1/T3/T4/T17仅代表旧配置，默认不纳入新稿，不重命名为最终方法。原文件保留；若后续选入历史补充，须写清21节点、固定0.02、60/250预算。
- E4a逐单元图、旧100 Hz B240谱/轨迹图、旧跨前端图由本轮图6–12取代，不再作为当前主结果图。
- E0修正版原散点图的低误差点过度挤在轴边，已重绘为补图S3：全部800个点保留，横轴采用明确标示的对数尺度。
- `新初稿图/figS9-1_measured_background` 已目检，当前图形与文字可读，可作为注明旧配置的历史补充候选；没有必要仅为统一形式再画一遍。其固定背景窗口条件区间不代表跨航次推断。
- 原稿、09-27新初稿、Phase D报告内全部原图保留；原图表清单在本轮复核目录 `before_revision/05_图表素材/` 留档，旧“还要画”和“需要合并”建议不再作为当前任务。

## 使用要点

图4、5为开发结果，图6、7为独立确认结果；图8、9为冻结方法的仿真扩展；图10–12只作同航次实测描述。图11的最大峰位置变化必须与增量一起说明；图12的GPS不是真值，16窗口含重叠。对应数据、图注、可编辑PDF/SVG、600 dpi PNG/TIFF和检查记录均在新版目录。
''',encoding='utf-8')
qarows=['| 图件 | 对齐 | PDF文字/碰撞 | 目检 |','|---|---|---|---|']
for n,q in qa.items():qarows.append(f'| {n} | {q["alignment"]} | PASS | PASS |')
(O/'qa/FINAL_QA.md').write_text('''# 最终图件检查

2026-10-04。12张正文图及3张补图均已逐张打开PNG检查。最终导出的PDF文字、碰撞和运行时面板对齐也已检查；示意图3只有单坐标容器，对齐检查不适用，其文字/碰撞检查通过。源代码检查21项通过，无警告或失败。

'''+ '\n'.join(qarows)+'''

## 目检与数据说明

- 图1移动了与频率曲线相交的“Approaching”标注；图3明确目标是相干项减惩罚，完整保留不触发支路与前解候选。
- 图2保留原构造例；图4–9保留全部单元、已审核区间、负值与不同场景，不按效果筛选。
- 图9补充全记录区间与分箱数量；分箱线只引导阅读，不作为机制拟合。
- 图10全部105例；图11保留完整搜索带与边缘峰细节，最大值增量不是同频率垂直差。所有原谱点保留，不平滑。矢量曲线在图框边界做几何裁切，与正常坐标裁切等效，未修改数据。
- 图12连续LOFAR含1500帧；新增45个真实跨段窗口，重叠1455帧与原值最大差4.98e−14 dB。统一全局颜色映射，无插值填空或局部加强。轨迹与参考分开清楚展示。
- 补图S1图例与标题间距已修正；补图S2完整展示无干扰下相对去盒界的负差；补图S3对数轴展开小误差点，未抽样或抖动。
- 最小导出字号5.6 pt，仅为对数指数；主体8 pt、谱图增量注释7.8 pt。所有图宽7.2 in（182.88 mm），PNG/TIFF均600 dpi；PDF/SVG文字可编辑。
- 实测候选谱峰的声源归属未全部确认。图件质量通过不代表这一科学解释问题已经得到物理验证；最新图注与骨架采用限定表述。

输入CSV复制指纹与原件逐项相符，见 `../SOURCE_DATA_MANIFEST.json`；派生LOFAR、几何与构造谱见 `../source_data/`，方法原件不变。来源适用范围与旧配置边界已经写入每图图注。最终文件指纹见 `AUTOMATED_QA.json`。
''',encoding='utf-8')
(O/'README.md').write_text('''# 当前正文图与补图

首先打开[图集](图集.md)或[网页图集](图集.html)。正文图1–12全部保留，补图S1–S3另列。所有图提供PDF、SVG、600 dpi PNG与TIFF；正文图数量没有缩减。

图注见[图注.md](图注.md)，核验见[最终检查](qa/FINAL_QA.md)。既有区间和判定沿用已审核结果；原始结果不变。`source_data/`为绘图输入副本与明确标示的派生数据，`SOURCE_DATA_MANIFEST.json`记录直接来源及指纹，`scripts/`保留重绘过程。

应用的技能为本机 `C:/Users/Lenovo/.codex/skills/nature-figure/SKILL.md`，使用其配色/排版、运行时面板对齐、源代码、导出文字与碰撞检查。不是用生成式图像模型生成数据曲线。源代码自动检查与导出检查均通过，全部15图已目检。当前能力足够，本轮未改动技能包。

实测预定133 Hz例存在最大峰位置转换，图11保留该事实，不换例、不删数据；相应解释见实验设计复核。原图与冻结实验仍在原位置，新图不覆盖原报告图件。
''',encoding='utf-8')
# Portable gallery package; no original multi-GB experiment chunks or runtime.
dest=R/'05_图表素材/新版论文图集_20261004.zip'
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(O.rglob('*')):
  if p.is_file() and 'runtime' not in p.parts and p.suffix.lower() in ['.pdf','.svg','.png','.tiff','.json','.csv','.py','.m','.md','.html'] and not (p.parent.name=='qa' and p.suffix in ['.pdf','.svg']):z.write(p,p.relative_to(O))
print(json.dumps({'status':'PASS','figures':15,'source_copies':len(data),'core_algorithms':len(hashes),'zip_mb':round(dest.stat().st_size/1e6,1)},ensure_ascii=False))
