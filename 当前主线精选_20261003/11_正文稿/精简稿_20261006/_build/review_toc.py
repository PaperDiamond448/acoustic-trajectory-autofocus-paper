"""Generate the internal review copy, populate its native TOC, and preserve OMML."""
from copy import deepcopy
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from lxml import etree

NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}

def insert_toc(source, output):
    doc=Document(source)
    intro=next(p for p in doc.paragraphs if p.text.strip()=='1 引言')
    title=doc.styles.add_style('Research TOC Title',WD_STYLE_TYPE.PARAGRAPH)
    title.font.name='Times New Roman'
    title.font.size=Pt(14)
    title.font.bold=True
    title.font.color.rgb=RGBColor(0,0,0)
    title.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'黑体')
    pf=title.paragraph_format
    pf.alignment=WD_ALIGN_PARAGRAPH.CENTER
    pf.first_line_indent=Pt(0)
    pf.space_before=Pt(0)
    pf.space_after=Pt(8)
    pf.page_break_before=True
    pf.keep_with_next=True
    outline=OxmlElement('w:outlineLvl')
    outline.set(qn('w:val'),'9')
    title.element.get_or_add_pPr().append(outline)
    intro.insert_paragraph_before('目录',style='Research TOC Title')
    field= intro.insert_paragraph_before(style='Normal')
    field.paragraph_format.first_line_indent=Pt(0)
    for kind in ('begin','instruction','separate','end'):
        r=OxmlElement('w:r')
        if kind=='instruction':
            node=OxmlElement('w:instrText')
            node.set(qn('xml:space'),'preserve')
            node.text=' TOC \\o "1-2" \\h \\z '
        else:
            node=OxmlElement('w:fldChar')
            node.set(qn('w:fldCharType'),kind)
        r.append(node)
        field._p.append(r)
    intro.paragraph_format.page_break_before=True
    doc.save(output)

def restore_math(before, output):
    with ZipFile(output) as archive:
        files={name:archive.read(name) for name in archive.namelist()}
    xml=etree.fromstring(files['word/document.xml'])
    current=xml.xpath('//m:oMath',namespaces=NS)
    assert len(current)==len(before), 'Word changed the equation count'
    for old,new in zip(current,before):
        old.getparent().replace(old,deepcopy(new))
    files['word/document.xml']=etree.tostring(xml,encoding='UTF-8',xml_declaration=True,standalone=True)
    tmp=Path(output).with_suffix('.rewrite.tmp')
    with ZipFile(tmp,'w',ZIP_DEFLATED) as archive:
        for name,data in files.items():
            archive.writestr(name,data)
    tmp.replace(output)

def populate_toc(output, report):
    import win32com.client as wc
    with ZipFile(output) as archive:
        before=etree.fromstring(archive.read('word/document.xml')).xpath('//m:oMath',namespaces=NS)
    word=wc.dynamic.Dispatch(wc.DispatchEx('Word.Application'))
    word.Visible=False
    word.DisplayAlerts=0
    word.AutomationSecurity=3
    doc=None
    try:
        doc=word.Documents.Open(str(Path(output).resolve()),False,False)
        assert doc.TablesOfContents.Count==1, 'Native TOC was not recognized'
        for style_id,indent in ((-20,0.0),(-21,14.2)):
            st=doc.Styles.Item(style_id)
            st.Font.Name='Times New Roman'
            st.Font.NameFarEast='宋体'
            st.Font.Size=10.5
            st.Font.Color=0
            st.Font.Bold=0
            pf=st.ParagraphFormat
            pf.SpaceBefore=0
            pf.SpaceAfter=0
            pf.LineSpacingRule=4
            pf.LineSpacing=14
            pf.FirstLineIndent=0.0
            pf.LeftIndent=indent
            pf.KeepWithNext=0
            pf.KeepTogether=-1
        toc=doc.TablesOfContents.Item(1)
        toc.Update()
        doc.Repaginate()
        toc.UpdatePageNumbers()
        doc.Save()
        doc.Repaginate()
        toc.UpdatePageNumbers()
        doc.Save()
        information={'review_pages':doc.ComputeStatistics(2),'toc_text':toc.Range.Text,'toc_count':1}
    finally:
        if doc is not None:
            doc.Close(0)
        word.Quit(0)
    restore_math(before,output)
    Path(report).write_text(json.dumps(information,ensure_ascii=False,indent=2),encoding='utf-8')
    return information
