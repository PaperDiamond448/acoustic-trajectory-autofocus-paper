"""Build the Claude condensed manuscript (2026-10-06) from ../源文件/*.md.

Run: python -X utf8 build_docx.py
Figures are placed where a source line reads "> **图 N** ..." (N = 1-12 or B1);
supplementary figures S1-S3 go at the end. Figure files are read, never modified,
from 05_图表素材/正文图_20261004 and 修订稿_20261005/_build/figs.
New numbering: old 8, 9 -> 4, 5 (Section 3.4); old 4-7 -> 6-9;
old 13, 12, 10 -> 10, 11, 12; old 11 -> B1 (Appendix B.6).
"""
import hashlib
import json
import re
import os
import shutil
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

PANDOC = os.environ.get("PANDOC") or shutil.which("pandoc") or r'C:/Users/Lenovo/AppData/Local/Pandoc/pandoc.exe'
BUILD = Path(__file__).resolve().parent
REV = BUILD.parent
MS = REV / '源文件'
ROOT = REV.parents[1]
FIGDIR = ROOT / '05_图表素材' / '正文图_20261004'
NEWFIG = REV.parent / '修订稿_20261005' / '_build' / 'figs'
CAPTIONS = MS / '图注_中文.md'
OUTPUT = REV / '论文精简稿_Claude_中文_20261006.docx'

SECTIONS = ['第1节_引言.md', '第2-3节_问题描述与方法.md', '第4节_仿真.md',
            '第5节_实测.md', '第6-7节_讨论与结论.md', '附录A.md', '附录B.md', '参考文献.md']

FIGFILES = {
    '1': FIGDIR / 'fig01_geometry_中文.png',
    '2': FIGDIR / 'fig02_error_structure_中文.png',
    '3': FIGDIR / 'fig03_流程图_中文黑白.png',
    '4': FIGDIR / 'fig04_knot_spacing_中文.png',
    '5': FIGDIR / 'fig05_radius_development_中文.png',
    '6': FIGDIR / 'fig06_confirmation_gain_中文.png',
    '7': FIGDIR / 'fig07_confirmation_tradeoff_中文.png',
    '8': FIGDIR / 'fig08_duration_gain_cost_中文.png',
    '9': NEWFIG / 'fig09_frontend_generality_中文_修订.png',
    '10': NEWFIG / 'fig13_real_trajectory_duration_中文_修订.png',
    '11': NEWFIG / 'fig12_real_spectra_中文_修订.png',
    '12': NEWFIG / 'fig10_real_all_cases_中文_修订.png',
    'B1': NEWFIG / 'fig11_real_peak_mapping_中文_修订.png',
    'S1': FIGDIR / 'figS01_knot_spectral_peak_中文.png',
    'S2': FIGDIR / 'figS02_confirmation_paired_中文.png',
    'S3': FIGDIR / 'figS03_frontend_diagnostic_中文.png',
}
WIDTH = {'3': '14cm', 'B1': '13.5cm', '11': '13cm', '10': '14.5cm'}


def read_captions():
    body = CAPTIONS.read_text(encoding='utf-8').split('\n---\n', 1)[1]
    out = {}
    for line in body.splitlines():
        m = re.match(r'^\*\*(图|补充图) (S?\d+|B\d+)\*\*\s*(.*)$', line)
        if m:
            out[m.group(2)] = f'**{m.group(1)} {m.group(2)}**　' + m.group(3).strip()
    assert set(out) == set(FIGFILES), set(FIGFILES) ^ set(out)
    return out


def figure_block(k, caps):
    dst = BUILD / 'img' / f'fig{k}.png'
    dst.parent.mkdir(exist_ok=True)
    shutil.copyfile(FIGFILES[k], dst)
    cap = caps[k].replace('[', '\\[').replace(']', '\\]')
    return f'![{cap}](img/fig{k}.png){{width={WIDTH.get(k, "15.5cm")}}}'


def normalise_math(s):
    s = re.sub(r'\\tag\{([^}]+)\}', r'\\qquad (\1)', s)
    s = re.sub(r'\{\\rm\s+([^}]+)\}', r'\\mathrm{\1}', s)
    for cmd in ('mathbf', 'mathcal', 'mathsf'):
        s = re.sub(r'\\' + cmd + r'\s+([A-Za-z0-9])', r'\\' + cmd + r'{\1}', s)
    return s


def assemble():
    caps = read_captions()
    abstract = (MS / '摘要.md').read_text(encoding='utf-8').split('\n')
    title = abstract[0].lstrip('# ').strip()
    subtitle = abstract[2].strip().strip('*')
    abstract_body = '\n'.join(abstract[3:]).strip()
    placed = []

    def place(m):
        placed.append(m.group(1))
        return figure_block(m.group(1), caps)

    parts = []
    for name in SECTIONS:
        t = (MS / name).read_text(encoding='utf-8')
        t = re.sub(r'^> \*\*图 (\d+|B\d+)\*\*.*$', place, t, flags=re.M)
        t = '\n'.join(l for l in t.split('\n') if l.strip() != '---')
        parts.append(t.strip())
    expected = [k for k in FIGFILES if not k.startswith('S')]
    assert placed == expected, placed
    supp = ['# 补充图', ''] + [figure_block(k, caps) + '\n' for k in ('S1', 'S2', 'S3')]
    md = normalise_math('\n\n'.join([abstract_body] + parts + ['\n'.join(supp)]))
    meta = f'---\ntitle: "{title}"\nsubtitle: "{subtitle}"\nlang: zh-CN\n---\n\n'
    out = BUILD / '全文.md'
    out.write_text(meta + md + '\n', encoding='utf-8')
    return out


def set_font(style, size, east='宋体', west='Times New Roman', bold=None):
    style.font.name = west
    style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = rpr.makeelement(qn('w:rFonts'), {})
        rpr.append(rfonts)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs'):
        rfonts.set(qn(a), west)
    rfonts.set(qn('w:eastAsia'), east)


def make_reference():
    ref = BUILD / 'reference.docx'
    with open(ref, 'wb') as fh:
        subprocess.run([PANDOC, '--print-default-data-file', 'reference.docx'], stdout=fh, check=True)
    doc = Document(ref)
    st = doc.styles
    for name in ('Normal', 'Body Text', 'First Paragraph', 'Block Text'):
        if name in st:
            set_font(st[name], 12)
            pf = st[name].paragraph_format
            pf.line_spacing = 1.5
            pf.space_before, pf.space_after = Pt(0), Pt(0)
            if name in ('Body Text', 'First Paragraph'):
                pf.first_line_indent = Pt(24)
    if 'Compact' in st:
        set_font(st['Compact'], 10.5)
        st['Compact'].paragraph_format.line_spacing = 1.2
    for name, size in (('Title', 18), ('Subtitle', 13), ('Heading 1', 15), ('Heading 2', 13.5), ('Heading 3', 12)):
        if name in st:
            set_font(st[name], size, east='黑体', bold=(name != 'Subtitle'))
            st[name].font.color.rgb = RGBColor(0, 0, 0)
            st[name].paragraph_format.space_before = Pt(12 if name.startswith('Heading 1') else 6)
            st[name].paragraph_format.space_after = Pt(6)
    if 'Subtitle' in st:
        st['Subtitle'].font.italic = True
    for name in ('Caption', 'Image Caption', 'Table Caption'):
        if name in st:
            set_font(st[name], 10.5)
            st[name].font.italic = False
            st[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            st[name].paragraph_format.space_after = Pt(9)
    if 'Captioned Figure' in st:
        st['Captioned Figure'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for sec in doc.sections:
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
        for side in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'):
            setattr(sec, side, Cm(2.5))
    doc.save(ref)
    return ref


def main():
    md = assemble()
    ref = make_reference()
    raw = BUILD / '论文精简稿_Claude_中文_20261006_未排版.docx'
    subprocess.run([PANDOC, md.name, '-f', 'markdown', '-t', 'docx', f'--reference-doc={ref.name}',
                    '-o', str(raw)], cwd=BUILD, check=True)
    from polish_docx_layout import format_document
    preservation = format_document(raw, OUTPUT)
    print('written', OUTPUT)
    inputs = sorted(MS.glob('*.md')) + [Path(__file__), BUILD / 'polish_docx_layout.py']
    manifest = {'sources': {str(p.relative_to(REV)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                'figures': {k: str(v) for k, v in FIGFILES.items()},
                'output': str(OUTPUT), 'preservation': preservation}
    (BUILD / '构建清单.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
