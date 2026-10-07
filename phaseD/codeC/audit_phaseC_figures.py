from pathlib import Path
import hashlib, json, os, subprocess, sys

ROOT=Path(r'D:\论文集\phaseD');OUT=ROOT/'C_confirm';QA=OUT/'qa';QA.mkdir(exist_ok=True)
SCRIPTS=Path(r'C:\Users\Lenovo\.codex\skills\nature-figure\scripts')
env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'runtime')+os.pathsep+env.get('PYTHONPATH','')
names=['fig_C_paired_eta','fig_C_gain_harm']
report={'status':'PASS','visual_review':'pending manual inspection of final PNGs','adaptation':'New confirmation evidence layout; style-only inheritance of typography and alignment/export helper from the locally authored development plots. No development statistical values reused.','figures':{}}
def execute(script,args):
    r=subprocess.run([sys.executable,'-X','utf8',str(SCRIPTS/script),*map(str,args)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert r.returncode==0,r.stdout+'\n'+r.stderr
    return r.stdout
source=execute('validate_figure.py',[ROOT/'codeC/plot_phaseC.py','--json'])
(QA/'plot_source_audit.json').write_text(source,encoding='utf8')
for name in names:
    pdf=OUT/(name+'.pdf')
    text=json.loads(execute('audit_pdf_text.py',[pdf,'--json']))
    (QA/(name+'.text_audit.json')).write_text(json.dumps(text,ensure_ascii=False,indent=2),encoding='utf8')
    path=QA/(name+'.collision_audit.json')
    log=execute('audit_figure_collisions.py',[pdf,'--json-out',path,'--overlay-pdf',QA/(name+'.collision_overlay.pdf')])
    (QA/(name+'.collision_audit.log')).write_text(log,encoding='utf8')
    collision=json.loads(path.read_text(encoding='utf8'))
    alignment=json.loads((OUT/(name+'.alignment.json')).read_text(encoding='utf8'))
    assert text['auditable'] and text['below_minimum_count']==0
    assert alignment['verdict']=='PASS' and collision['verdict']=='PASS',log
    report['figures'][name]={'alignment':'PASS','minimum_font_pt':text['minimum_found_pt'],'collision':'PASS','file_sha256':{ext:hashlib.sha256((OUT/(name+'.'+ext)).read_bytes()).hexdigest() for ext in ['pdf','svg','png']}}
(QA/'FIGURE_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Both C figures automated QA PASS; visual review pending.')
