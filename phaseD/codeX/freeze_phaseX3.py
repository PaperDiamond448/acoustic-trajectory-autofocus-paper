from pathlib import Path
import pandas as pd,json,hashlib,csv
R=Path('D:/论文集/phaseD');O=R/'X3_real'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
screen=json.loads((O/'SCREEN_COMPLETE.json').read_text(encoding='utf-8'));assert screen['status']=='ALL_330_SCREENED_BEFORE_ANY_REAL_MODULE'
v=pd.read_csv(O/'X3_visibility.csv');p=v[v.passed.eq(1)].copy();assert len(v)==330
eligible=p[~p.competing_ridge.eq(1)];weak=eligible[eligible.group=='weak']
roles={};dur=[];runs=[]
if len(weak):
 a=weak.sort_values(['peak_excess_dB','tone_hz','segment_start_s']).iloc[0];roles['a']={'tone_hz':int(a.tone_hz),'start_s':int(a.segment_start_s),'selection':'lowest visible weak peak_excess; ties smallest tone/earliest start'}
 strong=eligible[(eligible.group=='strong')&(eligible.segment_start_s==a.segment_start_s)]
 if len(strong):
  c=strong.sort_values('tone_hz').iloc[0];roles['c']={'tone_hz':int(c.tone_hz),'start_s':int(c.segment_start_s),'selection':'smallest passed strong tone at role-a interval'}
for tone,g in p[p.group=='weak'].groupby('tone_hz'):
 starts=sorted(g.segment_start_s.astype(int));chunks=[]
 for s in starts:
  if not chunks or s!=chunks[-1][-1]+300:chunks.append([s])
  else:chunks[-1].append(s)
 for chunk in chunks:
  run={'tone_hz':int(tone),'start_s':chunk[0],'end_s':chunk[-1]+300,'segments':len(chunk)};runs.append(run)
  if len(chunk)>=2:
   for T in [150,300,450,600]:dur.append({'tone_hz':int(tone),'segment_start_s':chunk[0],'duration_s':T,'visible_run_end_s':chunk[-1]+300})
# Protocol 10.4 explicitly requires replacement of the old 100-Hz 900-1500
# interval when its two constituent windows pass, in addition to maximal-run starts.
oldcase=p[(p.tone_hz==100)&p.segment_start_s.isin([900,1200])]
if len(oldcase)==2:
 for T in [150,300,450,600]:
  if not any(x['tone_hz']==100 and x['segment_start_s']==900 and x['duration_s']==T for x in dur):
   dur.append({'tone_hz':100,'segment_start_s':900,'duration_s':T,'visible_run_end_s':1500})
if runs:
 candidates=sorted(runs,key=lambda x:(-x['segments'],x['tone_hz'],x['start_s']))
 candidates=[x for x in candidates if not(x['tone_hz']==103 and x['start_s']==900)]
 if candidates:roles['b']={**candidates[0],'selection':'longest maximal visible weak run; ties smallest tone/earliest start'}
pd.DataFrame(dur,columns=['tone_hz','segment_start_s','duration_s','visible_run_end_s']).to_csv(O/'X3_FROZEN_DURATION_TESTSET.csv',index=False)
manifest_files=[O/'X3_visibility.csv',O/'X3_FROZEN_TESTSET.csv',O/'X3_FROZEN_DURATION_TESTSET.csv',O/'X3_A3_comparison.csv',O/'SCREEN_COMPLETE.json',R/'codeX/phaseX3_one.m',R/'codeX/phaseX3_metrics.m',R/'codeX/run_phaseX3_real.m']
freeze={'status':'FROZEN_BEFORE_ANY_REAL_MODULE','passed_cases':len(p),'duration_windows':len(dur),'roles':roles,'all_maximal_weak_runs':runs,'tie_rule':'smallest frequency then earliest start; no module output inspected','files':{str(f):sha(f) for f in manifest_files},'created_at':pd.Timestamp.now().isoformat()}
(O/'X3_TESTSET_FREEZE.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2),encoding='utf-8')
with (O/'X3_FREEZE_MANIFEST.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['source_file','sha256']);w.writerows((str(p),sha(p)) for p in [*manifest_files,O/'X3_TESTSET_FREEZE.json',*sorted((O/'screen_inputs').glob('*.mat'))])
print(json.dumps(freeze,ensure_ascii=False,indent=2))
