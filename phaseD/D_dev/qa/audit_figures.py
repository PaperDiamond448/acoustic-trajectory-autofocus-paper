"""Audit final figure files and record their exact identities."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
ROOT=Path(r'D:\论文集\phaseD');OUT=ROOT/'D_dev';QA=OUT/'qa'
SCRIPTS=Path(r'C:\Users\Lenovo\.codex\skills\nature-figure\scripts')
env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'runtime')+os.pathsep+env.get('PYTHONPATH','')
names=['fig_D1_eta_runtime','fig_D1_observed_peak','fig_D2_radius_gain_harm']
report={'status':'PASS','visual_review':'pending manual inspection of these exact final renders','figures':{}}
def execute(script,arguments):
    result=subprocess.run([sys.executable,'-X','utf8',str(SCRIPTS/script),*map(str,arguments)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    return result.stdout
for name in names:
    pdf=OUT/(name+'.pdf')
    text=json.loads(execute('audit_pdf_text.py',[pdf,'--json']))
    (QA/(name+'.text_audit.json')).write_text(json.dumps(text,ensure_ascii=False,indent=2),encoding='utf8')
    collision_path=QA/(name+'.collision_audit.json')
    log=execute('audit_figure_collisions.py',[pdf,'--json-out',collision_path,'--overlay-pdf',QA/(name+'.collision_overlay.pdf')])
    (QA/(name+'.collision_audit.log')).write_text(log,encoding='utf8')
    collision=json.loads(collision_path.read_text(encoding='utf8'))
    alignment=json.loads((OUT/(name+'.alignment.json')).read_text(encoding='utf8'))
    assert text['auditable'] and text['below_minimum_count']==0
    assert alignment['verdict']=='PASS'
    assert collision['verdict']=='PASS',log
    report['figures'][name]={'alignment':'PASS','minimum_font_pt':text['minimum_found_pt'],'collision':'PASS','file_sha256':{ext:hashlib.sha256((OUT/(name+'.'+ext)).read_bytes()).hexdigest() for ext in ['pdf','svg','png']}}
(QA/'FIGURE_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'status':'PASS','figures':len(names),'visual_review':'pending'}))
