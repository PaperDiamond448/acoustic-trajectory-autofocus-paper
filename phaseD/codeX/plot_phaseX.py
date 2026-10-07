from pathlib import Path
import json,sys,string
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path('D:/论文集/phaseD');FM='ADA_local_c04_t30_A'
sys.path.insert(0,'C:/Users/Lenovo/.codex/skills/nature-figure/scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':7,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'legend.frameon':False,'lines.linewidth':1.2})
STYLE={'SMR':('#888888',':','s'),'F02':('#4C78A8','-','o'),'UNB':('#8C6D9F','--','^'),FM:('#C07654','-','D')}
def save(fig,O,name):
 fig.canvas.draw();require_matplotlib_panel_alignment(fig,json_out=O/(name+'.alignment.json'),overlay_svg=O/(name+'.alignment.svg'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
 fig.savefig(O/(name+'.pdf'),facecolor='white');fig.savefig(O/(name+'.svg'),facecolor='white');fig.savefig(O/(name+'.png'),dpi=600,facecolor='white');plt.close(fig)
def letters(axs):
 for i,ax in enumerate(np.ravel(axs)):ax.text(-.15,1.08,string.ascii_lowercase[i],transform=ax.transAxes,fontweight='bold',fontsize=8);ax.tick_params(length=3,width=.6)
def captions(O,d): (O/'FIGURE_CAPTIONS.md').write_text('\n\n'.join(k+'\n\n'+v for k,v in d.items()),encoding='utf-8')
def x1():
 O=R/'X1_duration';s=pd.read_csv(O/'X1_summary.csv');fig,axs=plt.subplots(2,2,figsize=(7.2,4.8),sharey='row');fig.subplots_adjust(left=.10,right=.98,bottom=.13,top=.82,wspace=.35,hspace=.62)
 for j,sc in enumerate(['S0','S2']):
  for method,(c,ls,mark) in STYLE.items():
   q=s[(s.scope==sc)&(s.method==method)&(s.metric=='eta')].sort_values('duration_s');x=q.duration_s.to_numpy();axs[0,j].plot(x,q['mean'],color=c,ls=ls,marker=mark,ms=3,label='ADA' if method==FM else method);axs[0,j].fill_between(x,q.lo,q.hi,color=c,alpha=.12,lw=0)
   if method!='SMR':
    q=s[(s.scope==sc)&(s.method==method)&(s.metric=='runtime_s')].sort_values('duration_s');axs[1,j].plot(x,q['median'],color=c,ls=ls,marker=mark,ms=3);axs[1,j].fill_between(x,q['median'],q.p90,color=c,alpha=.08,lw=0)
  axs[0,j].set_title(sc,pad=12)
  for ax in axs[:,j]:ax.set_xlabel('Accumulation duration (s)');ax.set_xticks([150,300,450,600])
  axs[0,j].set_ylabel('Pure-target efficiency, η');axs[1,j].set_ylabel('Loaded BTA call time (s)')
 h,l=axs[0,0].get_legend_handles_labels();fig.legend(h,l,ncol=4,loc='upper center',bbox_to_anchor=(.54,.99));letters(axs);save(fig,O,'fig_X1_duration_efficiency_cost')
 captions(O,{'fig_X1_duration_efficiency_cost':'All 2,400 phase-53 records, 100 seeds per scene carried across three SNRs and four durations. Upper panels: equal-SNR-cell mean pure-target efficiency with 95% scene-stratified seed-cluster percentile intervals, 2,000 draws, seed 20261053. Lower panels: median BTA optimizer call wall time; shading spans median to 90th percentile and is not a confidence interval. Timing is measured with six Processes workers under load, not a serial benchmark. SMR is the same-duration bounded quadratic start; ADA is the frozen local 0.04-Hz/30-s/full-rerun method. Spacing remains 10 s; nodes, regularization and fixed per-stage budgets scale with duration. All records and negative gains are retained.'})
def x2():
 O=R/'X2_frontend';s=pd.read_csv(O/'X2_eta_bins.csv');fig,axs=plt.subplots(1,2,figsize=(7.2,2.8),sharex=True);fig.subplots_adjust(left=.10,right=.98,bottom=.23,top=.74,wspace=.35)
 colors=['#4C78A8','#6F8D68','#C07654','#888888'];marks=['o','s','^','D'];styles=['-','--','-.',':']
 for i,f in enumerate(['VS','MFT','SUV','V0']):
  q=s[s.frontend==f].sort_values('bin_left')
  for j,met in enumerate(['gain_eta','recovery_fraction']):axs[j].plot(q.bin_center,q[met],color=colors[i],marker=marks[i],ls=styles[i],ms=3,label=f)
 for ax in axs:ax.axhline(0,color='#777777',lw=.7);ax.set_xlim(0,1);ax.set_xlabel('Input pure-target efficiency, η')
 axs[0].set_ylabel('Module efficiency increment, Δη');axs[1].set_ylabel('Recovered fraction of remaining η');h,l=axs[0].get_legend_handles_labels();fig.legend(h,l,ncol=4,loc='upper center',bbox_to_anchor=(.54,.99));letters(axs);save(fig,O,'fig_X2_frontend_recovery')
 captions(O,{'fig_X2_frontend_recovery':'All 1,400 phase-54 records for each of four frontends are retained. Descriptive means within ten preregistered 0.1-wide input-efficiency bins, shown at bin centers; empty bins remain gaps. Right panel includes only input η<0.95 and averages the paired recovery fraction (η_out−η_in)/(1−η_in). No uncertainty bars imply independent bins or records; equal-cell all-record and input-usable seed-cluster intervals, as well as bin counts, are supplied in companion tables. VS starts from SMR around VIT, MFT and SUV start at zero around their final readout, and V0 starts from unrefined VIT. Every module uses the unchanged frozen ADA method. Negative output increments are included.'})
def x3():
 O=R/'X3_real';F=json.loads((O/'X3_TESTSET_FREEZE.json').read_text(encoding='utf-8'));roles=F['roles'];cap={}
 if 'a' in roles:
  chosen=[roles['a']]+([roles['c']] if 'c' in roles else []);fig,axs=plt.subplots(1,len(chosen),figsize=(7.2,2.8),squeeze=False,sharey=True);fig.subplots_adjust(left=.10,right=.98,bottom=.23,top=.72,wspace=.35)
  for j,b in enumerate(chosen):
   tone=b['tone_hz'];q=pd.read_csv(O/'spectra'/f"f{tone}_s{b['start_s']}_T300.csv");ref=q.Periodogram.max();ax=axs[0,j]
   for name,c,ls in [('Periodogram','#333333',':'),('SMR','#888888','--'),('F02','#4C78A8','-.'),('VS_FM','#C07654','-')]:ax.plot(q.frequency_Hz-tone,10*np.log10(np.maximum(q[name]/ref,np.finfo(float).tiny)),color=c,ls=ls,label='ADA' if name=='VS_FM' else name)
   ax.set_xlim(-.5,.5);ax.set_xlabel(f'Offset from {tone} Hz (Hz)');ax.set_ylabel('Power / Periodogram peak (dB)');ax.set_title(f"{tone} Hz, {b['start_s']}–{b['start_s']+300} s",pad=12)
  h,l=axs[0,0].get_legend_handles_labels();fig.legend(h,l,ncol=4,loc='upper center',bbox_to_anchor=(.54,.99));letters(axs);save(fig,O,'fig_X3_prespecified_spectra');cap['fig_X3_prespecified_spectra']='Cases frozen before any real-data module: lowest peak-excess visible weak case (133 Hz, 1200–1500 s), and lowest-frequency passed strong tone at that interval (49 Hz). Unsmooth rectangular full-record periodograms use |FFT|²/N and one FFT grid, each case normalized by its own uncorrected candidate-band peak. Display zoom is the preregistered ±0.5-Hz visibility core; full ±1.5-Hz spectra are supplied. Cases are not selected by module gain. ADA uses the frozen method. All passed cases, including the flagged competing-ridge case, enter the companion tables.'
 if 'b' in roles:
  b=roles['b'];tone=b['tone_hz'];freq=np.loadtxt(O/'role_b_LOFAR_frequency_hz.csv',delimiter=',');time=np.loadtxt(O/'role_b_LOFAR_time_s.csv',delimiter=',');P=np.loadtxt(O/'role_b_LOFAR_power_db.csv',delimiter=',');base=np.median(P)
  fig,axs=plt.subplots(2,1,figsize=(7.2,4.8));fig.subplots_adjust(left=.12,right=.86,bottom=.13,top=.88,hspace=.68)
  # Plot each independent frame block separately; preserve unsupported boundary gaps.
  for j,s in enumerate(range(b['start_s'],b['end_s'],300)):
   ts=time[j*291:(j+1)*291];v=P[:,j*291:(j+1)*291];im=axs[0].pcolormesh(ts,freq-tone,v-base,cmap='viridis',vmin=-25,vmax=25,shading='nearest',rasterized=True)
   q=pd.read_csv(O/'tracks'/f'f{tone}_s{s}_T300.csv')
   for name,c,ls in [('GPS_Hz','#F2D45C',':'),('SMR','#F8F8F8','--'),('VS_FM','#D76151','-')]:axs[0].plot(q.time_s,q[name]-tone,color=c,ls=ls,lw=1,label=name if j==0 else None)
  axs[0].set_xlim(b['start_s'],b['end_s']);axs[0].set_ylim(-.5,.5);axs[0].set_xlabel('Voyage time (s)');axs[0].set_ylabel('Offset from 100 Hz (Hz)');axs[0].set_title('Longest continuously visible weak-tone run',pad=12)
  cax=fig.add_axes([.90,.56,.018,.30],label='<colorbar>');fig.colorbar(im,cax=cax,label='LOFAR / median (dB)')
  d=pd.read_csv(O/'X3_duration.csv');p=d.pivot(index=['tone_hz','segment_start_s','duration_s'],columns='method',values='peak_relative_periodogram_db');colors=['#4C78A8','#6F8D68','#C07654','#8C6D9F'];markers=['o','s','^','D']
  for j,((f,s),g) in enumerate(p.groupby(level=[0,1])):axs[1].plot(g.index.get_level_values('duration_s'),g.VS_FM-g.SMR,color=colors[j%4],marker=markers[j%4],ms=3,label=f'{f} Hz, start {s} s')
  axs[1].axhline(0,color='#777777',lw=.7);axs[1].set_xlabel('Accumulation duration (s)');axs[1].set_ylabel('ADA − SMR peak gain (dB)');axs[1].set_xticks([150,300,450,600]);axs[1].legend(loc='upper center',bbox_to_anchor=(.5,1.43),ncol=2,fontsize=7)
  axs[0].legend(loc='upper center',bbox_to_anchor=(.5,1.32),ncol=3,fontsize=7);letters(axs);save(fig,O,'fig_X3_trajectory_duration');cap['fig_X3_trajectory_duration']='Top: the longest weak-tone visible run, 100 Hz, 600–2100 s, selected using visibility only. Original Hann 10-s/hop-1-s LOFAR relative to its median, overlaid with GPS (scaled from 100-Hz reference), SMR and ADA. Independent 300-s frame support leaves boundary gaps; gaps are not interpolated. GPS is a descriptive reference and never screens cases; discrepancies are not truth errors. Bottom: all four frozen weak-tone run/start sets, including the explicitly required old 100-Hz 900-s case replacement, at all four durations. Each point is a paired full-record spectral-peak gain over same-duration SMR. No significance test or independence claim. The flagged 103-Hz 900-s competing ridge remains in the duration data.'
 inc=pd.read_csv(O/'X3_increments.csv');fig,axs=plt.subplots(1,3,figsize=(7.2,2.8),sharey=True);fig.subplots_adjust(left=.10,right=.98,bottom=.24,top=.82,wspace=.40)
 for j,group in enumerate(['weak','strong','shallow']):
  q=inc[(inc.group==group)&(inc.pair=='VS_FM-SMR')].sort_values(['segment_start_s','tone_hz']);x=np.arange(len(q));ax=axs[j];ax.scatter(x,q.gain_peak_db,s=10,color=['#C07654','#4C78A8','#6F8D68'][j]);ax.axhline(0,color='#777777',lw=.7);ax.axhline(q.gain_peak_db.median(),color='#333333',ls='--',lw=.8);ax.set_title(f'{group.capitalize()} (n={len(q)})',pad=12);ax.set_xlabel('All cases (time, tone order)');ax.set_ylabel('ADA − SMR peak gain (dB)')
 letters(axs);save(fig,O,'fig_X3_all_case_gains');cap['fig_X3_all_case_gains']='All 105 passed frequency×300-s cases, with no deletion based on gain. Dots show paired VS ADA−SMR spectral-peak increments; dashed lines mark group medians. Weak, strong and shallow groups follow the preregistered source-level grouping; Set 5 120 dB is inferred from the stated 4-dB step and lacks independent confirmation, while shallow source level is unpublished. Cases share voyage and time, so no significance test or independent-replication interpretation is applied. The 103-Hz 900-s competing ridge is retained and flagged in the full table.'
 captions(O,cap)
if __name__=='__main__':
 for stage in sys.argv[1:] or ['X1','X2','X3']:{'X1':x1,'X2':x2,'X3':x3}[stage]();print(stage+' plots exported')
