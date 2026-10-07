"""Build both current manuscript variants from one canonical Markdown source.

Run: python -X utf8 build_docx.py [--variant both|manuscript|review]
Sources: ../源文件/*.md. Default outputs: 2026-10-06 manuscript and internal review.
Figure numbering follows the reordered Section 4: old 6,7,8,9,4,5 -> new 4,5,6,7,8,9.
Section 5 gains the 15-case peak-mapping figure as Fig. 11; old 11, 12 -> 12, 13.
Figures 7 and 10-13 come from ./figs (render_revised.py); the rest are the
original 2026-10-04 Chinese figures. Historical Word outputs are never overwritten.
"""
import argparse
import hashlib
import json
import re
import os
import shutil
import subprocess
from datetime import date
from pathlib import Path
from zipfile import ZipFile

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
NEWFIG = BUILD / 'figs'
CAPTIONS = MS / '图注_中文.md'

SECTIONS = ['第1节_引言.md', '第2-3节_问题描述与方法.md', '第4节_仿真.md',
            '第5节_实测.md', '第6-7节_讨论与结论.md', '附录A.md', '附录B.md', '参考文献.md']

FIGFILES = {
    '1': FIGDIR / 'fig01_geometry_中文.png', '2': FIGDIR / 'fig02_error_structure_中文.png',
    '3': FIGDIR / 'fig03_流程图_中文黑白.png', '4': FIGDIR / 'fig06_confirmation_gain_中文.png',
    '5': FIGDIR / 'fig07_confirmation_tradeoff_中文.png', '6': FIGDIR / 'fig08_duration_gain_cost_中文.png',
    '7': NEWFIG / 'fig09_frontend_generality_中文_修订.png', '8': FIGDIR / 'fig04_knot_spacing_中文.png',
    '9': FIGDIR / 'fig05_radius_development_中文.png', '10': NEWFIG / 'fig10_real_all_cases_中文_修订.png',
    '11': NEWFIG / 'fig11_real_peak_mapping_中文_修订.png', '12': NEWFIG / 'fig12_real_spectra_中文_修订.png',
    '13': NEWFIG / 'fig13_real_trajectory_duration_中文_修订.png',
    'S1': FIGDIR / 'figS01_knot_spectral_peak_中文.png', 'S2': FIGDIR / 'figS02_confirmation_paired_中文.png',
    'S3': FIGDIR / 'figS03_frontend_diagnostic_中文.png',
}
# figure -> beginning of the paragraph after which it is placed
ANCHORS = {
    '4': '在独立确认仿真的 2800 条记录上', '5': '修正的增益可以分成两部分',
    '6': '在所测的 150–600 s 记录中，修正相对 LPS 的增益随记录时长增加', '7': '图 7(a)–(d) 按修正前',
    '8': '节点间隔取 60、30、20', '9': '节点间隔取 10 s 后', '10': '最大观测谱峰是搜索带内的最大值',
    '11': '弱线组中，自适应扩张在 5 个案例上触发', '12': '133 Hz、1200–1500 s 案例展示了前端轨迹失去谱线', '13': '100 Hz 线在 600–2100 s 内连续 5 个时段',
}
WIDTH = {'3': '14cm', '11': '13.5cm', '12': '13cm', '13': '14.5cm'}


def read_captions():
    text = CAPTIONS.read_text(encoding='utf-8')
    body = text.split('\n---\n', 1)[1]
    caps, key, buf = {}, None, []
    for line in body.splitlines():
        m = re.match(r'^\*\*(?:图|补充图) (S?\d+)\*\*\s*(.*)$', line)
        if m:
            if key:
                caps[key] = buf
            key, buf = m.group(1), [m.group(2)]
        elif key is not None:
            buf.append(line)
    caps[key] = buf
    out = {}
    for k, lines in caps.items():
        parts = [re.sub(r'^\s*-\s+', '', l).strip() for l in lines if l.strip()]
        label = f'补充图 {k}' if k.startswith('S') else f'图 {k}'
        out[k] = f'**{label}**　' + ''.join(parts)
    return out


def figure_block(k, caps):
    src = FIGFILES[k]
    dst = BUILD / 'img' / f'fig{k}.png'
    dst.parent.mkdir(exist_ok=True)
    shutil.copyfile(src, dst)
    width = WIDTH.get(k, '15.5cm')
    cap = caps[k].replace('[', '\\[').replace(']', '\\]')
    return f'![{cap}](img/fig{k}.png){{width={width}}}'


def insert_after_paragraph(text, anchor, block):
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line.startswith(anchor):
            j = i
            while j + 1 < len(lines) and lines[j + 1].strip():
                j += 1
            lines[j + 1:j + 1] = ['', block, '']
            return '\n'.join(lines)
    raise ValueError(f'anchor not found: {anchor}')


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

    parts = []
    for name in SECTIONS:
        t = (MS / name).read_text(encoding='utf-8')
        # figures 1-3: replace the quoted captions in sections 2-3
        for k in ('1', '2', '3'):
            t = re.sub(r'^> \*\*图 ' + k + r'\*\*.*$', figure_block(k, caps), t, flags=re.M)
        for k, anchor in ANCHORS.items():
            if re.search('^' + re.escape(anchor), t, flags=re.M):
                t = insert_after_paragraph(t, anchor, figure_block(k, caps))
        t = '\n'.join(l for l in t.split('\n') if l.strip() != '---')
        parts.append(t.strip())

    supp = ['# 补充图', ''] + [figure_block(k, caps) + '\n' for k in ('S1', 'S2', 'S3')]
    md = '\n\n'.join([abstract_body] + parts + ['\n'.join(supp)])
    md = normalise_math(md)
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
    for name in ('Compact',):
        if name in st:
            set_font(st[name], 10.5)
            st[name].paragraph_format.line_spacing = 1.2
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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--variant', choices=('both', 'manuscript', 'review'), default='both')
    ap.add_argument('--output-dir', type=Path, default=REV)
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    md = assemble()
    ref = make_reference()
    out = BUILD / '论文修订稿_中文_20261006_未排版.docx'
    subprocess.run([PANDOC, md.name, '-f', 'markdown', '-t', 'docx', f'--reference-doc={ref.name}',
                    '-o', str(out)], cwd=BUILD, check=True)
    print('written', out)
    from polish_docx_layout import format_document
    formatted = args.output_dir / '论文修订稿_中文_20261006_正文版.docx'
    review = args.output_dir / '论文修订稿_中文_20261006_审阅目录版.docx'
    # A review-only run uses the same formatted body in the build directory.
    base = formatted if args.variant in ('both', 'manuscript') else BUILD / '当前正文_构建中间稿.docx'
    preservation = format_document(out, base)
    outputs = []
    if args.variant in ('both', 'manuscript'):
        outputs.append(str(formatted))
        print('written', formatted, flush=True)
    if args.variant in ('both', 'review'):
        from review_toc import insert_toc, populate_toc
        insert_toc(base, review)
        print('populating review TOC', flush=True)
        populate_toc(review, BUILD / '当前审阅版目录核查.json')
        outputs.append(str(review))
        print('written', review, flush=True)
    # Paragraph locators are regenerated together with each current Word output.
    from lxml import etree
    locator_dir = args.output_dir / '回复审稿'
    locator_dir.mkdir(exist_ok=True)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
          'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
    for output in outputs:
        with ZipFile(output) as archive:
            root = etree.fromstring(archive.read('word/document.xml'))
        label = '审阅目录版' if output == str(review) else '正文版'
        paragraphs = []
        for i, p in enumerate(root.xpath('./w:body/w:p', namespaces=ns), 1):
            text = ''.join(p.xpath('.//w:t/text() | .//m:t/text()', namespaces=ns))
            if text.strip():
                paragraphs.append(f'[P{i:04d}] {text}')
        (locator_dir / f'{label}Word正文段落_20261006.txt').write_text('\n\n'.join(paragraphs)+'\n', encoding='utf-8')
    inputs = list(MS.glob('*.md')) + [Path(__file__), BUILD / 'polish_docx_layout.py', BUILD / 'review_toc.py']
    manifest = {'sources':{str(p.relative_to(REV)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                'outputs':outputs,'preservation':preservation,'variant':args.variant}
    (BUILD / '当前构建清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
