from pathlib import Path
from zipfile import ZipFile
import hashlib,json,re
from lxml import etree

ROOT=Path(__file__).resolve().parent.parent
MS=ROOT/'源文件'
LOG=ROOT/'审阅记录'
OLD=ROOT.parent/'修订稿_20261005'
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected=json.loads((LOG/'原修订稿保护校验.json').read_text(encoding='utf-8'))
for p,h in protected.items():assert hashfile(OLD/p)==h,p
manifest=json.loads((ROOT/'_build'/'当前构建清单.json').read_text(encoding='utf-8'))
for p,h in manifest['sources'].items():assert hashfile(ROOT/p)==h,p
files={p.name:p.read_text(encoding='utf-8') for p in MS.glob('*.md')}
with ZipFile(LOG/'本轮精简前源文件.zip') as z:
    initial={n:z.read(n).decode('utf-8-sig').replace('\r\n','\n') for n in z.namelist()}
def displays(s):
    return {int(m.group(1)):m.group(0) for m in re.finditer(r'\$\$[^$]*?\\tag\{(\d+)\}[^$]*?\$\$',s,re.S)}
assert displays(initial['第2-3节_问题描述与方法.md'])==displays(files['第2-3节_问题描述与方法.md'])
assert initial['附录A.md']==files['附录A.md']
assert initial['参考文献.md']==files['参考文献.md']
combined='\n'.join(v for k,v in files.items() if k not in ('图注_中文.md','参考文献.md'))
headings=set(re.findall(r'^## ([\dAB]+\.\d+) ',combined,re.M))
refs=set(re.findall(r'([2-6]\.\d+) 节',combined))
assert refs<=headings, refs-headings
figs=set(re.findall(r'\*\*(?:图|补充图) ([BS]?\d+)\*\*',files['图注_中文.md']))
figrefs=set(re.findall(r'图 ([BS]?\d+)',combined+files['图注_中文.md']))
assert figrefs<=figs,figrefs-figs
assert '【待作者确认：公开方式、仓库地址或获取途径】' in combined
expected=[str(x) for x in range(1,13)]+['B1','S1','S2','S3']
assert figs==set(expected)
mainnames=['第1节_引言.md','第2-3节_问题描述与方法.md','第4节_仿真.md','第5节_实测.md','第6-7节_讨论与结论.md']
def count(s):
    s=re.sub(r'\$\$.*?\$\$|\$[^$\n]*\$','',s,flags=re.S)
    s=re.sub(r'[#*|>]','',s)
    return {'Chinese_characters':len(re.findall(r'[\u4e00-\u9fff]',s)),
            'non_whitespace_characters_excluding_math':len(re.sub(r'\s','',s))}
counts={n:{'original_revision':count((OLD/'源文件'/n).read_text(encoding='utf-8')),
           'shortened':count(files[n])} for n in mainnames}
counts['total']={'original_revision':count('\n'.join((OLD/'源文件'/n).read_text(encoding='utf-8') for n in mainnames)),
                 'shortened':count('\n'.join(files[n] for n in mainnames))}
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
report={'protected_revision_files_unchanged':len(protected), 'source_build_hashes_match':True,
        'numbered_equations_1_to_16_unchanged':True,'appendix_A_unchanged':True,
        'references_unchanged':30,'headings':sorted(headings), 'counts':counts,'outputs':{}}
reference_images=None
with ZipFile(OLD/'论文修订稿_中文_20261006_正文版.docx') as z:
    reference_images=sorted(hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
math_by_variant={}
for variant in ('正文版','审阅目录版'):
    path=ROOT/f'论文精简稿_中文_20261006_{variant}.docx'
    with ZipFile(path) as z:
        doc=etree.fromstring(z.read('word/document.xml'))
        images=sorted(hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
        assert images==reference_images,variant
        math_by_variant[variant]=[tuple(el.xpath('.//m:t/text()',namespaces=ns)) for el in doc.xpath('//m:oMath',namespaces=ns)]
        report['outputs'][variant]={'sha256':hashfile(path),'images':len(images),
            'native_equations':len(math_by_variant[variant]),'tables':len(doc.xpath('//w:tbl',namespaces=ns))}
        assert report['outputs'][variant]['tables']==9
assert math_by_variant['正文版']==math_by_variant['审阅目录版']
(LOG/'精简稿核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'protected_files':len(protected),'counts':counts['total'],'outputs':report['outputs']},ensure_ascii=False,indent=2))
