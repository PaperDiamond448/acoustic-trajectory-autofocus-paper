from pathlib import Path
import hashlib,json,os,subprocess,sys
R=Path('D:/论文集/phaseD');S=Path('C:/Users/Lenovo/.codex/skills/nature-figure/scripts');env=os.environ.copy();env['PYTHONPATH']=str(R/'runtime')+os.pathsep+env.get('PYTHONPATH','')
def run(script,args):
 q=subprocess.run([sys.executable,'-X','utf8',str(S/script),*map(str,args)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));assert q.returncode==0,q.stdout+'\n'+q.stderr;return q.stdout
out=R/'Y_compute';qa=out/'qa';qa.mkdir(exist_ok=True);source=run('validate_figure.py',[R/'codeX/plot_phaseX.py','--json']);(qa/'figure_source_audit.json').write_text(source,encoding='utf-8');result={}
for folder in ['X1_duration','X2_frontend','X3_real']:
 O=R/folder;Q=O/'qa';Q.mkdir(exist_ok=True)
 for pdf in O.glob('fig_*.pdf'):
  name=pdf.stem;fonts=json.loads(run('audit_pdf_text.py',[pdf,'--json']));(Q/(name+'.text_audit.json')).write_text(json.dumps(fonts,indent=2),encoding='utf-8')
  collision=Q/(name+'.collision_audit.json');log=run('audit_figure_collisions.py',[pdf,'--json-out',collision,'--overlay-pdf',Q/(name+'.collision_overlay.pdf')]);(Q/(name+'.collision.log')).write_text(log,encoding='utf-8')
  alignment=json.loads((O/(name+'.alignment.json')).read_text(encoding='utf-8'));col=json.loads(collision.read_text(encoding='utf-8'));assert fonts['auditable'] and fonts['below_minimum_count']==0;assert alignment['verdict']=='PASS' and col['verdict']=='PASS',log
  result[name]={'alignment':'PASS','collision':'PASS','minimum_font_pt':fonts['minimum_found_pt'],'sha256':{ext:hashlib.sha256((O/(name+'.'+ext)).read_bytes()).hexdigest() for ext in ['png','pdf','svg']}}
(qa/'FIGURE_QA.json').write_text(json.dumps({'status':'PASS','visual_review':'pending final PNG inspection','figures':result},indent=2),encoding='utf-8');print('Automated figure QA PASS:',len(result))
