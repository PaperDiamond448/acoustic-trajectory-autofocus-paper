"""Apply manuscript table and pagination formatting while preserving native math."""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
from zipfile import ZipFile

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph
from lxml import etree

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
# Tables 1-6, B1, B2, B3 of the 2026-10-05 revision
COL_WIDTHS = [
    [3.0, 3.7, 4.3, 2.6, 2.4], [4.1, 6.7, 5.2], [3.1, 12.9],
    [2.4, 2.0, 2.0, 3.6, 2.2, 3.8], [1.8, 3.8, 3.7, 3.6, 3.1],
    [2.4, 9.6, 4.0], [4.0, 2.8, 3.2, 3.6, 2.4],
    [4.0, 2.9, 2.6, 2.3, 3.0, 1.2], [3.2, 3.2, 3.2, 3.2, 3.2],
]
CENTRED = {3: {1,2,3,4,5}, 4: {0,3,4}, 6: {1,2,3}, 7: {1,2,5}, 8: {1,2,3,4}}

def child(parent, name):
    el = parent.find(qn(name))
    if el is None:
        el = OxmlElement(name)
        parent.append(el)
    return el

def text_font(run, size=10.5, bold=None):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    fonts.set(qn("w:eastAsia"), "宋体")
    if bold is not None:
        run.font.bold = bold

def format_tables(doc):
    assert len(doc.tables) == len(COL_WIDTHS)
    for i, (table, widths) in enumerate(zip(doc.tables, COL_WIDTHS)):
        assert len(table.columns) == len(widths)
        table.autofit = False
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        pr = table._tbl.tblPr
        child(pr, "w:tblW").set(qn("w:type"), "dxa")
        child(pr, "w:tblW").set(qn("w:w"), str(sum(Cm(x).twips for x in widths)))
        child(pr, "w:tblInd").set(qn("w:w"), "0")
        child(pr, "w:tblInd").set(qn("w:type"), "dxa")
        borders = child(pr, "w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            edge_el = child(borders, "w:" + edge)
            for k, v in {"val": "single", "sz": "4", "color": "D9D9D9", "space": "0"}.items():
                edge_el.set(qn("w:" + k), v)
        margins = child(pr, "w:tblCellMar")
        for edge, value in {"top": 70, "bottom": 70, "left": 90, "right": 90}.items():
            e = child(margins, "w:" + edge)
            e.set(qn("w:w"), str(value))
            e.set(qn("w:type"), "dxa")
        for col, width in zip(table.columns, widths):
            col.width = Cm(width)
        keep_whole = len(table.rows) <= 12
        for ri, row in enumerate(table.rows):
            trpr = row._tr.get_or_add_trPr()
            child(trpr, "w:cantSplit")
            for e in list(trpr.findall(qn("w:trHeight"))):
                trpr.remove(e)
            if ri == 0:
                child(trpr, "w:tblHeader").set(qn("w:val"), "1")
            for ci, (cell, width) in enumerate(zip(row.cells, widths)):
                cell.width = Cm(width)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                tcpr = cell._tc.get_or_add_tcPr()
                shade = child(tcpr, "w:shd")
                shade.set(qn("w:val"), "clear")
                shade.set(qn("w:fill"), "F2F2F2" if ri == 0 else "FFFFFF")
                # Override the inherited header border as well as table borders.
                cell_borders = child(tcpr, "w:tcBorders")
                for edge in ("top", "left", "bottom", "right"):
                    e = child(cell_borders, "w:" + edge)
                    e.set(qn("w:val"), "single")
                    e.set(qn("w:sz"), "4")
                    e.set(qn("w:color"), "D9D9D9")
                for para in cell.paragraphs:
                    pf = para.paragraph_format
                    pf.first_line_indent = Pt(0)
                    pf.left_indent = pf.right_indent = Pt(0)
                    pf.space_before = pf.space_after = Pt(0)
                    pf.line_spacing = 1.12
                    pf.keep_together = True
                    pf.keep_with_next = ri == 0 or (keep_whole and ri < len(table.rows) - 1)
                    center = ri == 0 or ci in CENTRED.get(i, set())
                    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
                    for run in para.runs:
                        text_font(run, bold=True if ri == 0 else None)
        before = table._tbl.getprevious()
        if before is not None and before.tag == qn("w:p"):
            cap = Paragraph(before, doc._body)
            if re.match(r"^表\s*B?\d+\s", cap.text.strip()):
                cap.paragraph_format.first_line_indent = Pt(0)
                cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap.paragraph_format.space_before = Pt(6)
                cap.paragraph_format.space_after = Pt(5)
                cap.paragraph_format.keep_with_next = True
                cap.paragraph_format.keep_together = True
                for run in cap.runs:
                    text_font(run)
        after = table._tbl.getnext()
        if after is not None and after.tag == qn("w:p"):
            Paragraph(after, doc._body).paragraph_format.space_before = Pt(6)

def format_figures(doc):
    for para in doc.paragraphs:
        if re.match(r"^算法\s*\d+\s", para.text.strip()):
            pf = para.paragraph_format
            pf.first_line_indent = Pt(0)
            pf.keep_with_next = True
            pf.keep_together = True
        elif para._p.xpath(".//w:drawing"):
            pf = para.paragraph_format
            pf.first_line_indent = pf.left_indent = pf.right_indent = Pt(0)
            pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf.keep_with_next = True
            pf.space_before = Pt(6)
            pf.space_after = Pt(3)
        elif para.style.name == "Image Caption":
            pf = para.paragraph_format
            pf.first_line_indent = Pt(0)
            pf.space_before = Pt(1)
            pf.space_after = Pt(8)
            pf.line_spacing = 1.15
            pf.keep_together = True

def repair_collapsed_lists(doc):
    count = 0
    for para in doc.paragraphs:
        # Move literal Markdown item markers to a new line without changing
        # any text node content or any native equation.
        nodes = list(para._p.xpath(".//w:t"))
        value = "".join(node.text or "" for node in nodes)
        if para.style.name == "Image Caption":
            continue
        markers = [m.start() + 1 for m in re.finditer(r" - ", value)]
        if " 1. " in value and " 2. " in value:
            markers += [m.start() + 1 for m in re.finditer(r" [1-9]\. ", value)]
        cursor = 0
        for node in nodes:
            original = node.text or ""
            positions = sorted(p - cursor for p in markers
                               if cursor <= p < cursor + len(original))
            cursor += len(original)
            if not positions:
                continue
            parent = node.getparent()
            offset = parent.index(node)
            pieces, start = [], 0
            for pos in positions:
                if pos > start:
                    piece = deepcopy(node)
                    piece.text = original[start:pos]
                    piece.set(qn("xml:space"), "preserve")
                    pieces.append(piece)
                pieces.append(OxmlElement("w:br"))
                start = pos
                count += 1
            piece = deepcopy(node)
            piece.text = original[start:]
            piece.set(qn("xml:space"), "preserve")
            pieces.append(piece)
            parent.remove(node)
            for j, piece in enumerate(pieces):
                parent.insert(offset + j, piece)
    return count

def format_header_wrap(doc):
    # Keep a meaningful phrase together in the narrow numeric header.
    for para in doc.tables[4].rows[0].cells[-1].paragraphs:
        for node in list(para._p.xpath(".//w:t")):
            value = node.text or ""
            if "谱峰超出量中位数" in value:
                pos = value.index("中位数")
                tail = deepcopy(node)
                tail.text = value[pos:]
                node.text = value[:pos]
                node.addnext(tail)
                node.addnext(OxmlElement("w:br"))

def verify_preservation(src, dst):
    with ZipFile(src) as a, ZipFile(dst) as b:
        old = etree.fromstring(a.read("word/document.xml"))
        new = etree.fromstring(b.read("word/document.xml"))
        old_text = "".join(old.xpath("//w:body//w:t/text()", namespaces=NS))
        new_text = "".join(new.xpath("//w:body//w:t/text()", namespaces=NS))
        assert old_text.replace("【页码待核】", "") == new_text, "Unexpected manuscript text change"
        def math_hash(root):
            return [sha256(etree.tostring(el, method="c14n", exclusive=True)).hexdigest()
                    for el in root.xpath("//m:oMath", namespaces=NS)]
        assert math_hash(old) == math_hash(new), "Native equation changed"
        images = [n for n in a.namelist() if n.startswith("word/media/")]
        assert all(a.read(n) == b.read(n) for n in images), "Figure changed"
        return {"tables": len(new.xpath("//w:tbl", namespaces=NS)),
                "native_equations_preserved": len(math_hash(new)),
                "image_files_preserved": len(images),
                "body_text_preserved_except_verified_reference_note": True}

def format_document(source, output):
    source, output = Path(source), Path(output)
    assert source.resolve() != output.resolve(), "Keep the source document intact"
    doc = Document(source)
    format_tables(doc)
    format_header_wrap(doc)
    format_figures(doc)
    breaks = repair_collapsed_lists(doc)
    for para in doc.paragraphs:
        if para.text.startswith("[7]") and "10.12395/0371-0025.2025271" in para.text:
            for run in para.runs:
                if "【页码待核】" in run.text:
                    run.text = run.text.replace("【页码待核】", "")
    # Page numbers aid review of this long manuscript without adding a header.
    for section in doc.sections:
        para = section.footer.paragraphs[0]
        pf = para.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.first_line_indent = Pt(0)
        pf.space_before = pf.space_after = Pt(0)
        run = para.add_run()
        text_font(run, size=9)
        field = OxmlElement("w:fldSimple")
        field.set(qn("w:instr"), "PAGE")
        field_run = OxmlElement("w:r")
        props = OxmlElement("w:rPr")
        size = OxmlElement("w:sz")
        size.set(qn("w:val"), "18")
        props.append(size)
        field_run.append(props)
        text = OxmlElement("w:t")
        text.text = "1"
        field_run.append(text)
        field.append(field_run)
        para._p.append(field)
    doc.save(output)
    result = verify_preservation(source, output)
    result["literal_list_markers_moved_to_new_lines"] = breaks
    return result

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    result = format_document(args.source, args.output)
    if args.report:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
