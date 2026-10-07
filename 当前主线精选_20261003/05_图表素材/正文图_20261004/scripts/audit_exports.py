from pathlib import Path
import hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parents[1];Q=O/'qa'
S=Path('C:/Users/Lenovo/.codex/skills/nature-figure/scripts')
env=os.environ.copy();env['PYTHONPATH']='D:/论文集/phaseD/runtime'+os.pathsep+env.get('PYTHONPATH','')
def run(script,args):
 p=subprocess.run([sys.executable,'-X','utf8',str(S/script),*map(str,args)],env=env,capture_output=True,text=True,encoding='utf-8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 return p.returncode,p.stdout,p.stderr
code,out,err=run('validate_figure.py',[O/'scripts/render_manuscript_figures.py','--json'])
(Q/'source_audit.json').write_text(out,encoding='utf-8')
results={}
for pdf in sorted(O.glob('fig*.pdf')):
 name=pdf.stem
 code,out,err=run('audit_pdf_text.py',[pdf,'--json'])
 (Q/(name+'.text_audit.json')).write_text(out,encoding='utf-8')
 fonts=json.loads(out)
 code,out,err=run('audit_figure_collisions.py',[pdf,'--json-out',Q/(name+'.collision_audit.json'),'--overlay-pdf',Q/(name+'.collision_overlay.pdf')])
 (Q/(name+'.collision.log')).write_text(out+'\n'+err,encoding='utf-8')
 collision=json.loads((Q/(name+'.collision_audit.json')).read_text(encoding='utf-8'))
 alignment=json.loads((Q/(name+'.alignment.json')).read_text(encoding='utf-8'))
 results[name]={'alignment':alignment.get('verdict'),'collision':collision.get('verdict'),'minimum_font_pt':fonts.get('minimum_found_pt'),'below_minimum_count':fonts.get('below_minimum_count'),'auditable':fonts.get('auditable'),'sha256':{e:hashlib.sha256((O/(name+'.'+e)).read_bytes()).hexdigest() for e in ['pdf','png','svg','tiff']}}
 print(name,json.dumps({k:v for k,v in results[name].items() if k!='sha256'}),flush=True)
(Q/'AUTOMATED_QA.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
