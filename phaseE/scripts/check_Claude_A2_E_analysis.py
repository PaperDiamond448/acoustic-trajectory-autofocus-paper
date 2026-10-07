"""Read-only checks of the author's A2/E analysis; no experiment is rerun."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

root=Path(__file__).resolve().parents[2]
folder=root/'phaseE/E1_trajexport'
data=pd.read_csv(folder/'traj_export_X2_diagA2.csv')
theory=pd.read_csv(folder/'traj_export_X2_theory_metrics.csv')
cols=['row','in_sigma2']
data=data.merge(theory[cols],on='row',validate='one_to_one')
summaries=[]
for frontend,rows in data.groupby('frontend'):
    excess=rows.gain-rows.ceiling_gain_m1
    summaries.append({'frontend':frontend,'n':len(rows),
        'rho_reachable_gain_actual_gain':rows.ceiling_gain_m1.corr(rows.gain,method='spearman'),
        'actual_above_reachable_n':int((excess>0).sum()),
        'actual_above_reachable_0p01_n':int((excess>.01).sum()),
        'actual_above_reachable_0p01_fraction':float((excess>.01).mean())})
subsets=[]
for frontend in ('VS','SUV'):
    fe=data[data.frontend==frontend]
    masks={'S0_input_usable':(fe.scene=='S0')&(fe.input_usable==1),
           'S0_sigma2_lt0p5':(fe.scene=='S0')&(fe.in_sigma2<.5)}
    for label,mask in masks.items():
        q=fe[mask];available=q.ceiling_gain_m1.mean();realized=q.gain.mean()
        subsets.append({'frontend':frontend,'subset':label,'n':len(q),
            'eta_in_mean':q.eta_in.mean(),'eta_clean_m1_mean':q.eta_clean_m1.mean(),
            'eta_out_mean':q.eta_out.mean(),'available_gain_mean':available,
            'realized_gain_mean':realized,'realized_over_available':realized/available})
events=[]
for frontend in ('VS','V0','SUV'):
    q=data[(data.frontend==frontend)&(data.in_sigma2>=.5)&(data.in_sigma2<5)]
    events.append({'frontend':frontend,'subset':'sigma2_0p5_to_5','n':len(q),
        'candidate_event_rows':int((q.n_slip_runs>0).sum()),
        'candidate_event_fraction':float((q.n_slip_runs>0).mean())})
pc=data[(data.frontend=='SUV')&(data.scene=='S0')]
for has in (True,False):
    q=pc[(pc.n_slip_runs>0)==has]
    events.append({'frontend':'SUV','subset':f'S0_candidate_event_{has}','n':len(q),
        'eta_in_mean':q.eta_in.mean(),'in_sigma2_median':q.in_sigma2.median()})
guided=pd.read_csv(root/'phaseE/E4_guided_real/E4_records.csv')
g=guided[guided.method=='G_ADA']
comparison={'cases':len(g),'gain_full_peak_vs_original_median_db':float(g.gain_peak_vs_VS_FM_db.median()),
    'gain_full_peak_vs_original_positive_cases':int((g.gain_peak_vs_VS_FM_db>0).sum()),
    'gain_full_peak_vs_original_negative_cases':int((g.gain_peak_vs_VS_FM_db<0).sum()),
    'case133':g[(g.tone_hz==133)&(g.segment_start_s==1200)].to_dict('records')}
out=folder/'Claude_analysis_check_20261007';out.mkdir(exist_ok=True)
pd.DataFrame(summaries).to_csv(out/'prediction_checks.csv',index=False)
pd.DataFrame(subsets).to_csv(out/'subset_checks.csv',index=False)
pd.DataFrame(events).to_csv(out/'candidate_event_checks.csv',index=False)
(out/'guided_checks.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(pd.DataFrame(summaries).to_string(index=False),flush=True)
print(pd.DataFrame(subsets).to_string(index=False),flush=True)
print(pd.DataFrame(events).to_string(index=False),flush=True)
print(json.dumps(comparison,ensure_ascii=False),flush=True)
