from pathlib import Path
import re, shutil

BUILD=Path(__file__).resolve().parent
ROOT=BUILD.parent
OLD=ROOT.parent/'修订稿_20261005'/'_build'
s=(OLD/'build_docx.py').read_text(encoding='utf-8')
s=s.replace("NEWFIG = BUILD / 'figs'", "NEWFIG = REV.parent / '修订稿_20261005' / '_build' / 'figs'")
start=s.index('FIGFILES = {')
end=s.index('\n\ndef read_captions', start)
s=s[:start]+'''FIGFILES = {
    '1': FIGDIR / 'fig01_geometry_中文.png', '2': FIGDIR / 'fig02_error_structure_中文.png',
    '3': FIGDIR / 'fig03_流程图_中文黑白.png',
    '4': FIGDIR / 'fig04_knot_spacing_中文.png', '5': FIGDIR / 'fig05_radius_development_中文.png',
    '6': FIGDIR / 'fig06_confirmation_gain_中文.png', '7': FIGDIR / 'fig07_confirmation_tradeoff_中文.png',
    '8': FIGDIR / 'fig08_duration_gain_cost_中文.png', '9': NEWFIG / 'fig09_frontend_generality_中文_修订.png',
    '10': NEWFIG / 'fig13_real_trajectory_duration_中文_修订.png',
    '11': NEWFIG / 'fig12_real_spectra_中文_修订.png',
    '12': NEWFIG / 'fig10_real_all_cases_中文_修订.png',
    'B1': NEWFIG / 'fig11_real_peak_mapping_中文_修订.png',
    'S1': FIGDIR / 'figS01_knot_spectral_peak_中文.png', 'S2': FIGDIR / 'figS02_confirmation_paired_中文.png',
    'S3': FIGDIR / 'figS03_frontend_diagnostic_中文.png',
}
ANCHORS = {
    '4': '节点间隔控制残差表示', '5': '图 5 展示修正范围',
    '6': '修正以 LPS 为起点', '7': '固定 ±0.02 Hz 已贡献',
    '8': '无干扰时，LPS 补偿后的平均相干效率',
    '9': '三种依据逐帧功率形成轨迹的前端，接上修正后',
    '10': '100 Hz 线在 600–2100 s', '11': '图 11 第一列给出',
    '12': '图 12 汇总全部预筛案例',
    'B1': '图 B1 给出与表 B4 同序',
}
WIDTH = {'3': '14cm', '10': '14.5cm', '11': '13cm', 'B1': '13.5cm'}
''' + s[end:]
s=s.replace('(S?\\d+)', '([BS]?\\d+)')
s=s.replace('论文修订稿_中文_20261006', '论文精简稿_中文_20261006')
s=s.replace("    md = normalise_math(md)", "    md = normalise_math(md)\n    for key in FIGFILES:\n        assert md.count(f'](img/fig{key}.png)') == 1, f'Figure missing or duplicated: {key}'")
(BUILD/'build_docx.py').write_text(s, encoding='utf-8')
shutil.copyfile(OLD/'review_toc.py',BUILD/'review_toc.py')
p=(OLD/'polish_docx_layout.py').read_text(encoding='utf-8')
widths='''COL_WIDTHS = [
    [3.0, 3.7, 4.3, 2.6, 2.4], [4.1, 6.7, 5.2], [3.1, 12.9],
    [2.4, 2.0, 2.0, 3.6, 2.2, 3.8], [1.8, 3.8, 3.7, 3.6, 3.1],
    [2.4, 9.6, 4.0], [4.0, 2.8, 3.2, 3.6, 2.4],
    [4.0, 2.9, 2.6, 2.3, 3.0, 1.2], [3.2, 3.2, 3.2, 3.2, 3.2],
]
CENTRED = {3: {1,2,3,4,5}, 4: {0,3,4}, 6: {1,2,3}, 7: {1,2,5}, 8: {1,2,3,4}}
'''
p=re.sub(r'COL_WIDTHS = \[.*?CENTRED = .*?\n', widths, p, count=1, flags=re.S)
(BUILD/'polish_docx_layout.py').write_text(p, encoding='utf-8')

# Short reproducibility note retained from the removed Discussion.
appendix=ROOT/'源文件'/'附录B.md'
b=appendix.read_text(encoding='utf-8')
needle='**评价。**'
b=b.replace(needle, '**噪声模型。** 仿真使用白色圆对称复高斯噪声，式（11）的最大似然解释以此为前提。非高斯海洋噪声下的线谱增强已有专门研究 [30]；本文实测包含真实海洋背景，但没有单独检验噪声统计特性对修正的影响。\n\n'+needle, 1)
appendix.write_text(b,encoding='utf-8')
intro=ROOT/'源文件'/'第1节_引言.md'
t=intro.read_text(encoding='utf-8').replace('对单水听器接收的弱线谱，', '对单水听器接收的弱线谱 [5]，', 1)
intro.write_text(t,encoding='utf-8')
print('Prepared independent shortened-manuscript build')
