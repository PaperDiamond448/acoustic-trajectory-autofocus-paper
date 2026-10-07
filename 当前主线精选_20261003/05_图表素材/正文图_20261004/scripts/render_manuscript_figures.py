"""Paper figure revision from immutable records, with unchanged statistics."""
from pathlib import Path
import hashlib,json,shutil,sys,string
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from matplotlib.transforms import ScaledTranslation
from matplotlib.lines import Line2D

O=Path(__file__).resolve().parents[1]
ROOT=O.parents[1]
P=ROOT.parent/'phaseD'
SD=O/'source_data';QA=O/'qa'
for d in [SD,QA]:d.mkdir(exist_ok=True)
sys.path.insert(0,'C:/Users/Lenovo/.codex/skills/nature-figure/scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
 'font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':8,'ytick.labelsize':8,
 'legend.fontsize':8,'pdf.fonttype':42,'svg.fonttype':'none','savefig.dpi':600,
 'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,
 'legend.frameon':False,'lines.linewidth':1.25,'axes.unicode_minus':True})
FM='ADA_local_c04_t30_A'
COL={'SMR':'#747A80','F02':'#4477AA','F04':'#669977','UNB':'#9977AA',FM:'#C5653F'}
NAMES={'SMR':'SMR','F02':'Fixed ±0.02 Hz','F04':'Fixed ±0.04 Hz','UNB':'No correction box',FM:'Adaptive autofocus'}
SC={'S0':'No interference','S2':'Local interference'}
MARK={'SMR':'s','F02':'o','F04':'v','UNB':'^',FM:'D'}
STY={'SMR':':','F02':'-','F04':'-.','UNB':'--',FM:'-'}
provenance={};captions={};panels={}

def read(path,name=None):
 path=Path(path);dest=SD/(name or path.name)
 if path.resolve()!=dest.resolve():shutil.copy2(path,dest)
 provenance[dest.name]={'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 return pd.read_csv(dest)

def axes(nr=1,nc=1,height=3.0,sharey=False,top=.80):
 fig,ax=plt.subplots(nr,nc,figsize=(7.2,height),squeeze=False,sharey=sharey)
 fig.subplots_adjust(left=.105,right=.975,bottom=.16 if nr==1 else .105,top=top,
                     wspace=.35 if nc==2 else .53,hspace=.62)
 return fig,ax

def letters(fig,axs):
 for i,ax in enumerate(np.ravel(axs)):
  ax.text(0,1,string.ascii_lowercase[i],transform=ax.transAxes+ScaledTranslation(-27/72,13/72,fig.dpi_scale_trans),fontsize=10,fontweight='bold',va='bottom')
  ax.tick_params(length=3,width=.65)

def save(fig,axs,name,caption,roles,exclude=None):
 if len(np.ravel(axs))>1:letters(fig,axs)
 fig.canvas.draw()
 require_matplotlib_panel_alignment(fig,json_out=QA/(name+'.alignment.json'),overlay_svg=QA/(name+'.alignment.svg'),
  tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True,exclude_axes=exclude or [])
 fig.savefig(O/(name+'.pdf'),facecolor='white',dpi=600)
 fig.savefig(O/(name+'.svg'),facecolor='white',dpi=600)
 fig.savefig(O/(name+'.png'),facecolor='white',dpi=600)
 fig.savefig(O/(name+'.tiff'),facecolor='white',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
 plt.close(fig);captions[name]=caption;panels[name]=roles
 print(name,flush=True)

def ci(ax,x,q,mean='mean',lo='lo',hi='hi',color=None,marker='o',label=None,scale=1):
 y=q[mean].to_numpy()*scale;l=q[lo].to_numpy()*scale;h=q[hi].to_numpy()*scale
 ax.errorbar(x,y,yerr=np.maximum(0,np.array([y-l,h-y])),fmt=marker,color=color,ms=3.8,capsize=2,lw=1,label=label)

def fig01():
 fig,a=axes(1,2,3.45,top=.83);left,right=a[0]
 # Exact causal propagation equation and the original illustrative geometry.
 t=np.arange(6000)/20;c=1500;v=5;dc=1000;f0=100;tc=150-dc/c
 tau=(c*c*t-v*v*tc-np.sqrt(c*c*v*v*(t-tc)**2+(c*c-v*v)*dc*dc))/(c*c-v*v)
 dist=np.sqrt(dc*dc+v*v*(tau-tc)**2);fr=f0/(1+v*v*(tau-tc)/dist/c)
 pd.DataFrame({'time_s':t,'emission_time_s':tau,'received_frequency_hz':fr}).to_csv(SD/'geometry_curve.csv',index=False)
 assert abs(fr[3000]-100)<1e-10
 left.plot([-900,750],[1000,1000],color=COL['SMR']);left.scatter([0],[0],marker='v',s=40,c='#333333')
 left.plot([0,0],[0,1000],ls=':',c=COL['SMR']);left.scatter([0],[1000],s=22,c=COL['SMR'])
 left.plot([0,-560],[0,1000],color=COL['F02']);left.scatter([-560],[1000],s=28,c=COL[FM],zorder=5)
 left.annotate('',xy=(-200,1000),xytext=(-560,1000),arrowprops={'arrowstyle':'->','color':'#333333','lw':1.4})
 left.text(-580,1280,'Moving source',ha='center');left.text(-360,1110,'v = 5 m/s',ha='center')
 left.text(75,1100,'Closest approach');left.text(65,490,'d = 1000 m')
 left.text(-850,460,'Range R(τ)',color=COL['F02']);left.text(80,-55,'Fixed hydrophone')
 left.set(xlim=(-1050,850),ylim=(-180,1450),xlabel='Along-track position (m)',ylabel='Cross-track distance (m)',title='Motion and propagation delay')
 left.set_xticks([-1000,-500,0,500]);left.set_yticks([0,500,1000])
 right.plot(t,fr,c=COL[FM]);right.axhline(100,c=COL['SMR'],ls='--',lw=.8);right.axvline(150,c=COL['SMR'],ls=':',lw=.8)
 right.text(.15,.90,'Approaching',transform=right.transAxes);right.text(.60,.10,'Receding',transform=right.transAxes)
 right.set(xlim=(0,300),ylim=(99.77,100.23),xlabel='Reception time (s)',ylabel='Received frequency (Hz)',title='Received Doppler trajectory')
 save(fig,a,'fig01_geometry','图1 运动几何与接收频率。示意参数为声源频率100 Hz、速度5 m/s、最近距离1000 m、声速1500 m/s；接收端最近通过时刻150 s。频率按原因果传播方程计算，横轴为接收时间。此图解释信号模型，不是估计结果或性能试验。', ['Geometry schematic, not to scale','Exact deterministic Doppler curve'])

def fig02():
 q=read(ROOT.parent/'研究工作台/MATLAB实验/mft_week4_module/results/expA/expA_curves.csv')
 m=read(ROOT/'03_实验证据/C_原稿批次P60_表/T21_expA_mechanism.csv')
 fig,a=axes(1,3,3.25,top=.77);mask=(q.t_s>=5)&(q.t_s<295);n=int(mask.sum());freq=np.fft.fftshift(np.fft.fftfreq(65536,.05));out={'frequency_hz':freq}
 for k,col in [('A',COL['F02']),('B',COL[FM])]:
  r=m[m.case_tag==k].iloc[0];e=q.loc[mask,'e_'+k+'_hz'];ph=q.loc[mask,'phi_'+k+'_rad']
  sp=abs(np.fft.fftshift(np.fft.fft(np.exp(1j*ph),65536)))**2/n**2
  assert abs(np.sqrt(np.mean(e**2))-r.rmse_hz)<1e-8
  assert abs(sp[abs(freq)<=2].max()-r.eta_max)<1e-8
  a[0,0].plot(q.t_s[mask],e*1000,c=col,label=k)
  a[0,1].plot(q.t_s[mask],ph/(2*np.pi),c=col)
  a[0,2].plot(freq,sp,c=col);out[k]=sp
 pd.DataFrame(out).to_csv(SD/'mechanism_spectra.csv',index=False)
 for ax in a[0,:2]:ax.set_xlim(5,295);ax.set_xlabel('Time (s)');ax.axhline(0,c='#BBBBBB',ls=':',lw=.7)
 a[0,0].set(ylabel='Frequency error (mHz)',title='Frequency error',ylim=(-12,12))
 a[0,1].set(ylabel='Integrated error (cycles)',title='Residual phase',ylim=(-.07,.63))
 a[0,2].set(xlabel='Residual frequency (Hz)',ylabel='Normalized power',xlim=(-.03,.03),ylim=(0,1.04),title='Coherent output')
 fig.legend([Line2D([],[],color=COL['F02']),Line2D([],[],color=COL[FM])],['A: RMSE 4.28 mHz; η 0.363','B: RMSE 5.73 mHz; η 0.970'],loc='upper center',bbox_to_anchor=(.52,.99),ncol=2,fontsize=8)
 save(fig,a,'fig02_error_structure','图2 频率误差的时间结构决定残余相位。完整复用原21节点无噪声构造，不运行估计器。误差A幅度较小但变化缓慢，B幅度较大且交替变号。评价区间[5,295) s，η为±2 Hz内离散FFT最大值；图中仅放大±0.03 Hz。所有绘制曲线及RMSE、η重建与原表差小于1e−8。该例说明RMSE不能唯一决定相干输出，不代表实际前端普遍反序。',['Two fixed errors','Their time integrals','Resulting normalized spectra'])

def fig03():
 fig,ax=plt.subplots(figsize=(7.2,5.35));fig.subplots_adjust(left=.035,right=.98,bottom=.04,top=.95)
 ax.set(xlim=(0,10),ylim=(0,10));ax.axis('off')
 def box(x,y,w,h,text,accent=False):
  ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.06,rounding_size=0.06',facecolor='#FBF2EC' if accent else '#F5F7F9',edgecolor=COL[FM] if accent else '#72808C',lw=1))
  ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=8)
 def arrow(xy,uv):ax.add_patch(FancyArrowPatch(xy,uv,arrowstyle='-|>',mutation_scale=10,color='#64717C',lw=1))
 box(.2,8.4,2.35,1.05,'Complex baseband\nrecord y(t)')
 box(3.15,8.4,2.7,1.05,'Trajectory frontend\nVIT / MFT / phase-continuous TBD')
 box(6.45,8.4,3.1,1.05,'Anchor trajectory and start\nVIT–SMR, or zero correction')
 arrow((2.62,8.93),(3.08,8.93));arrow((5.92,8.93),(6.38,8.93))
 box(.2,6.30,2.75,1.1,'Frequency correction\n10 s knot spacing\nInitial range ±0.02 Hz',True)
 box(3.6,6.30,2.7,1.1,'Integrate correction\nAffine phase in coefficients\nContinuous phase',True)
 box(6.95,6.30,2.6,1.1,'Block coherence − penalty\nAnalytic gradient\nSQP: 20, 60, T−10 s',True)
 arrow((2.95,6.85),(3.53,6.85));arrow((6.37,6.85),(6.88,6.85))
 arrow((8,8.34),(8,7.47))
 ax.plot([6.7,6.7,1.57,1.57],[8.34,8.06,8.06,7.47],c='#64717C',lw=1)
 arrow((1.57,7.75),(1.57,7.47))
 ax.text(4.95,7.79,'Coherence-driven trajectory refinement',ha='center',fontsize=10,color=COL[FM],weight='bold')
 box(6.95,4.25,2.6,1.1,'Near-boundary dwell\n≥95% of current bound\nLongest run ≥30 s?',True)
 arrow((8.25,6.23),(8.25,5.42))
 box(3.60,4.25,2.7,1.1,'Local expansion to ±0.04 Hz\nIntersecting support + neighbors\nWarm start; full three-stage rerun',True)
 arrow((6.88,4.80),(6.37,4.80));ax.text(6.64,5.02,'Yes',ha='center')
 box(.2,4.25,2.75,1.1,'Keep previous solution\nSelect highest full-record J\nAt most one expansion',True)
 arrow((3.53,4.80),(3.02,4.80))
 ax.plot([9.62,9.88,9.88,1.57,1.57],[4.80,4.80,3.50,3.50,4.18],c='#64717C',lw=1)
 arrow((1.57,3.88),(1.57,4.18));ax.text(8.8,3.65,'No expansion',ha='center')
 box(.2,1.80,2.75,1.0,'Refined frequency trajectory')
 box(3.6,1.80,2.7,1.0,'Phase compensation\nand full-record FFT')
 box(6.95,1.80,2.6,1.0,'Output spectrum\nPeak, prominence, width')
 arrow((1.57,4.18),(1.57,2.87));arrow((3.02,2.30),(3.53,2.30));arrow((6.37,2.30),(6.88,2.30))
 ax.text(5,.75,'J selects candidates; evaluation metrics do not select the solution.',ha='center',color='#515A63')
 save(fig,[ax],'fig03_adaptive_method','图3 最终方法的处理结构。修正族为10 s节点的分段线性频率残差，积分得到系数的仿射相位。基础系数盒界对应±0.02 Hz；在20 Hz评价网格上，达到当前局部边界95%的最长连续驻留≥30 s时，放宽与相应时段相交的帽函数节点及其邻居至±0.04 Hz，仅扩张一次。扩张后由上一轮解起步重跑三个阶段，显式保留上一轮解，按全长正则目标J选择。频率检查点约束同时保留。', ['Entire algorithm schematic; no quantitative comparison'])

def d1(metric='eta',runtime=True):
 s=read(P/'D_dev/D1_summary.csv');fig,a=axes(2 if runtime else 1,2,5.0 if runtime else 3.5,sharey=False,top=.82 if runtime else .72)
 choices=[('F02','scaled',NAMES['F02'],COL['F02'],'o','-'),('UNB','scaled',NAMES['UNB'],COL['UNB'],'^','--'),('F02','unscaled','Fixed ±0.02 Hz; unscaled penalty','#999999','s',':')]
 for j,sc in enumerate(SC):
  for m,arm,label,col,mark,ls in choices:
   q=s[(s.scene==sc)&(s.method==m)&(s.arm==arm)]
   if arm=='unscaled':q=pd.concat([q,s[(s.scene==sc)&(s.method=='F02')&(s.arm=='scaled')&(s.Delta_s==15)]])
   q=q.sort_values('P');assert len(q)==7
   a[0,j].plot(q.P,q[metric],c=col,ls=ls,marker=mark,ms=3.6,label=label)
   a[0,j].fill_between(q.P,q[metric+'_lo'],q[metric+'_hi'],color=col,alpha=.09,lw=0)
   if runtime:a[1,j].plot(q.P,q.runtime_median_s,c=col,ls=ls,marker=mark,ms=3.6)
  a[0,j].set_title(SC[sc],pad=14)
  for ax in a[:,j]:ax.set_xlabel('Number of knots');ax.set_xticks([6,11,16,21,31,41,51]);ax.axvline(31,c=COL[FM],lw=.9,ls=':')
  a[0,j].set_ylabel('Coherent efficiency, η' if metric=='eta' else 'Observed peak power (dB)')
  if runtime:a[1,j].set_ylabel('Median solver time (s)')
 h,l=a[0,0].get_legend_handles_labels();fig.legend(h,l,loc='upper center',bbox_to_anchor=(.53,.99),ncol=2,fontsize=8)
 fig.text(.53,.015,'Dotted vertical line: selected 31 knots (10 s spacing)',ha='center',fontsize=8,color=COL[FM])
 name='fig04_knot_spacing' if runtime else 'figS01_knot_spectral_peak'
 save(fig,a,name,'图4（补图S1同数据）开发集节点扫描。每个设置使用相同840条记录；每场景7个SNR单元等权均值，阴影为2000次场景内种子成簇bootstrap的95%区间。下方求解耗时为六工作进程负载下的描述性中位数，不是串行基准或置信区间。未缩放正则对照在21节点复用相同基线。31节点由预定95%收益规则选出，不宣称数学最优；更密节点仍可有小幅差别。',['Efficiency or peak in no-interference scene','Same in local interference']+(['Cost in no-interference scene','Cost in local interference'] if runtime else []))

def fig05():
 s=read(P/'D_dev/D2_summary.csv');fig,a=axes(2,2,5.0,sharey='row',top=.86)
 methods=['F01','F02','F04','F08','UNB',FM];labels=['0.01','0.02','0.04','0.08','No box','Adaptive']
 for j,sc in enumerate(SC):
  q=s[(s.scene==sc)&s.method.isin(methods)].set_index('method').loc[methods]
  for i,met in enumerate(['gain_eta_vs_F02','harm_vs_F02']):
   ax=a[i,j]
   for k,m in enumerate(methods):ci(ax,[k],q.iloc[[k]],met,met+'_lo',met+'_hi',COL[FM] if m==FM else COL['F02'],'D' if m==FM else 'o',scale=100 if i else 1)
   ax.axhline(0,c='#BBBBBB',lw=.7);ax.set_xticks(range(6),labels);ax.set_xlim(-.6,5.6);ax.set_xlabel('Correction radius (Hz) / adaptive rule')
   ax.set_ylabel('η gain over fixed ±0.02 Hz' if i==0 else 'Substantial degradation (%)')
  a[0,j].set_title(SC[sc],pad=14)
 save(fig,a,'fig05_radius_development','图5 开发集修正范围比较。全部840条配对记录均保留，均值及95%种子成簇区间沿用审核结果。上排为相对固定±0.02 Hz的η差；下排为η低于同记录固定±0.02 Hz超过0.01的比例。No box仅移除修正系数盒界，保留频率检查点约束。Adaptive为开发规则选出的局部扩张方法。开发结果用于选参数，正式性能见确认集。',['Development gain without interference','Development gain with interference','Development degradation without interference','Development degradation with interference'])

def fig06():
 s=read(P/'C_confirm/C_cell_statistics.csv');fig,a=axes(2,2,4.9,sharey='row',top=.86)
 for j,sc in enumerate(SC):
  for i,met in enumerate(['gain_eta_vs_SMR','gain_peak_vs_SMR_db']):
   q=s[(s.scene==sc)&(s.method==FM)&(s.metric==met)].sort_values('snr_db');assert len(q)==7 and (q.lo>0).all()
   ci(a[i,j],q.snr_db,q,color=COL[FM]);a[i,j].axhline(0,c='#999999',lw=.8);a[i,j].set_xticks(range(-20,-13));a[i,j].set_xlabel('Baseband SNR (dB)')
   a[i,j].set_ylabel('Adaptive autofocus − SMR, Δη' if i==0 else 'Peak gain over SMR (dB)')
  a[0,j].set_title(SC[sc],pad=14)
 save(fig,a,'fig06_confirmation_gain','图6 独立确认集的同起点增益。两场景×7个SNR，每单元200条，共2800条；点为最终自适应方法相对同记录SMR的配对均值，误差棒为预先计算的2000次配对bootstrap逐单元95%区间，不是14单元同时置信带。上排为纯目标相干效率增量，下排为含噪观测谱峰增量。全部14单元的两个指标区间下界均为正。合并η+0.193628、谱峰+2.259411 dB。',['Paired efficiency gain without interference','Paired efficiency gain with interference','Paired peak gain without interference','Paired peak gain with interference'])

def fig07():
 s=read(P/'C_confirm/C_summary.csv');fig,a=axes(2,2,5.0,sharey='row',top=.86)
 methods=['F02','F04','UNB',FM];labels=['Fixed\n±0.02 Hz','Fixed\n±0.04 Hz','No correction\nbox','Adaptive\nautofocus']
 for j,sc in enumerate(SC):
  for i,met in enumerate(['gain_eta_vs_SMR','harm_vs_F02']):
   q=s[(s.scope==sc)&(s.metric==met)].set_index('method')
   for k,m in enumerate(methods):ci(a[i,j],[k],q.loc[[m]],color=COL[m],marker=MARK[m],scale=100 if i else 1)
   a[i,j].set_xticks(range(4),labels);a[i,j].set_xlim(-.6,3.6);a[i,j].axhline(0,c='#AAAAAA',lw=.7)
   a[i,j].set_ylabel('Efficiency gain over SMR, Δη' if i==0 else 'Substantial degradation (%)')
  a[0,j].set_title(SC[sc],pad=14)
 save(fig,a,'fig07_confirmation_tradeoff','图7 确认集的修正范围取舍。每场景7个SNR单元等权汇总，点与误差棒为配对均值或比例及2000次种子成簇95%区间。上排相对SMR，下排退化定义为η_method < η_fixed0.02−0.01。无干扰下自适应相对去盒界η低0.005982；有干扰下自适应退化率约2.0%，固定0.04与去盒界约33.6%和35.9%。合并非劣结论不代表逐场景非劣。',['Confirmation gain without interference','Confirmation gain with interference','Confirmation degradation without interference','Confirmation degradation with interference'])

def fig08():
 s=read(P/'X1_duration/X1_summary.csv');fig,a=axes(2,2,5.1,sharey='row',top=.81)
 for j,sc in enumerate(SC):
  for m in ['SMR','F02','UNB',FM]:
   q=s[(s.scope==sc)&(s.method==m)&(s.metric=='eta')].sort_values('duration_s')
   a[0,j].plot(q.duration_s,q['mean'],c=COL[m],ls=STY[m],marker=MARK[m],ms=3.5,label=NAMES[m]);a[0,j].fill_between(q.duration_s,q.lo,q.hi,color=COL[m],alpha=.1,lw=0)
   if m!='SMR':
    q=s[(s.scope==sc)&(s.method==m)&(s.metric=='runtime_s')].sort_values('duration_s')
    a[1,j].plot(q.duration_s,q['median'],c=COL[m],ls=STY[m],marker=MARK[m],ms=3.5);a[1,j].fill_between(q.duration_s,q['median'],q.p90,color=COL[m],alpha=.09,lw=0)
  a[0,j].set_title(SC[sc],pad=14)
  for ax in a[:,j]:ax.set_xlabel('Accumulation duration (s)');ax.set_xticks([150,300,450,600])
  a[0,j].set_ylabel('Coherent efficiency, η');a[1,j].set_ylabel('Solver call time (s)')
 h,l=a[0,0].get_legend_handles_labels();fig.legend(h,l,loc='upper center',bbox_to_anchor=(.54,.99),ncol=2)
 save(fig,a,'fig08_duration_gain_cost','图8 积累时长与计算量。2400条记录，场景内100个种子同时携带3个SNR及4个时长。上排点和阴影为SNR单元等权均值与2000次种子成簇95%区间；下排线为中位数，阴影为中位数到90%分位，不是置信区间。时间为六工作进程负载下的求解调用耗时。所有时长节点间隔固定10 s，节点数、正则和预算按冻结规则缩放。局部干扰持续时间按协议不随T同比增长，因此该图支持所测设计下的时长收益，不能单独归因于累积相位误差。',['Efficiency versus duration without interference','Efficiency versus duration with interference','Solver time without interference','Solver time with interference'])

def fig09():
 s=read(P/'X2_frontend/X2_eta_bins.csv');pool=read(P/'X2_frontend/X2_pooled.csv');fig,a=axes(2,2,5.15,top=.80)
 front=['VS','V0','MFT','SUV'];lab=['VIT–SMR','VIT','MFT','Phase-continuous TBD'];colors=[COL['F02'],'#6A8494',COL['F04'],COL[FM]]
 for j,f in enumerate(front):
  q=s[s.frontend==f].sort_values('bin_left')
  assert (q.n>0).all(), 'Log count axis requires strictly positive occupied-bin counts'
  for i,met in enumerate(['gain_eta','recovery_fraction']):a[0,i].plot(q.bin_center,q[met],color=colors[j],marker=['o','D','s','^'][j],ls=['-',':','--','-.'][j],ms=3.4,label=lab[j])
  a[1,1].plot(q.bin_center,q.n,c=colors[j],marker=['o','D','s','^'][j],ls=['-',':','--','-.'][j],ms=3)
  r=pool[(pool.frontend==f)&(pool.group=='all')];ci(a[1,0],[j],r,mean='equal_cell_mean',color=colors[j],marker=['o','D','s','^'][j])
 for ax in [a[0,0],a[0,1],a[1,1]]:ax.set_xlim(0,1);ax.set_xlabel('Input coherent efficiency, η')
 for ax in a[0]:ax.axhline(0,c='#AAAAAA',lw=.7)
 a[0,0].set_ylabel('Efficiency increment, Δη');a[0,1].set_ylabel('Recovered fraction of remaining η')
 a[1,0].set_xticks(range(4),['VIT–SMR','VIT','MFT','Phase-cont.\nTBD']);a[1,0].set_ylabel('All-record mean increment, Δη');a[1,0].axhline(0,c='#AAAAAA',lw=.7)
 a[1,1].set_ylabel('Records per input-efficiency bin');a[1,1].set_yscale('log')
 h,l=a[0,0].get_legend_handles_labels();fig.legend(h,l,loc='upper center',bbox_to_anchor=(.54,.99),ncol=2)
 save(fig,a,'fig09_frontend_generality','图9 四种前端后的收益。每种前端同样使用1400条记录，所有记录保留。a,b为预定0.1宽入口η分箱的描述性均值，连接线只引导阅读，不是拟合；b仅对入口η<0.95计算(η_out−η_in)/(1−η_in)，未显示推断区间。c为全部14个场景×SNR单元等权配对增量及2000次场景内种子成簇95%区间，来自审核汇总。d显示每箱记录数以说明样本分布，纵轴为对数。MFT入口可用子集仅6/14非空单元，不能给出预定14单元等权区间；另见汇总表。相位连续TBD增益较小且区间为正，不证明各前端收益相同。',['Descriptive binned increment','Descriptive normalized recovery','All-record paired uncertainty','Bin support counts'])

def fig10():
 s=read(P/'X3_real/X3_increments.csv');fig,a=axes(1,3,3.45,sharey=True,top=.78)
 for j,(g,title,col) in enumerate([('weak','Weak-source set',COL[FM]),('strong','Strong-source set',COL['F02']),('shallow','Shallow source',COL['F04'])]):
  q=s[(s.group==g)&(s.pair=='VS_FM-SMR')].sort_values(['segment_start_s','tone_hz']);y=q.gain_peak_db.to_numpy();x=np.arange(1,len(q)+1);ax=a[0,j]
  ax.scatter(x,y,s=15,color=col,edgecolors='white',linewidths=.3);ax.axhline(0,c='#999999',lw=.7);ax.axhline(np.median(y),color=col,ls='--',lw=.9)
  ax.set_title(f'{title}\n{len(q)} cases; {(y>0).sum()} positive',pad=13,fontsize=8.5)
  ax.set_xlabel('Case index (time, frequency order)');ax.set_ylabel('Spectral-maximum gain over SMR (dB)')
  ax.text(.05,.92,f'Median {np.median(y):+.2f} dB',transform=ax.transAxes,fontsize=8,color=col)
 save(fig,a,'fig10_real_all_cases','图10 预筛通过的全部105个实测频点×时段。点为搜索频带内最大观测谱峰相对SMR的增量，虚线为组中位数，灰线为零。弱/强/浅源分别15/60/30例；弱线组按预列源级Set2–5定义，不是估计的接收SNR；Set5的120 dB为推断且只有1个通过案例。所有案例共享同一航次，故不做独立重复解释或显著性检验。正峰增量并不自动确认目标身份，预定133 Hz案例的边缘峰见图11。',['All weak-source cases','All strong-source cases','All shallow-source cases'])

def clipped_polyline(x,y,bounds):
 # Geometrically clip straight rendering segments before PDF export. This is
 # identical to an axes clipping path, but PDF geometry auditors can see it.
 # Interior source samples are unchanged; boundary intersections are visual only.
 xmin,xmax,ymin,ymax=bounds;out=[]
 for k in range(len(x)-1):
  p=np.array([x[k],y[k]]);d=np.array([x[k+1]-x[k],y[k+1]-y[k]])
  lo,hi=0.,1.
  for dim,mn,mx in [(0,xmin,xmax),(1,ymin,ymax)]:
   if d[dim]==0:
    if not mn<=p[dim]<=mx:lo,hi=1.,0.;break
   else:
    u,v=sorted([(mn-p[dim])/d[dim],(mx-p[dim])/d[dim]])
    lo=max(lo,u);hi=min(hi,v)
  if lo<=hi:
   begin=p+lo*d;end=p+hi*d
   if not out or not np.allclose(out[-1],begin,atol=1e-12,rtol=0):out.extend([[np.nan,np.nan],begin])
   out.append(end)
 return np.asarray(out).T

def fig11():
 cases=read(P/'X3_real/X3_cases.csv');fig,a=axes(2,2,5.2,sharey=False,top=.79)
 methods=[('Periodogram','#333333',':','Uncompensated'),('SMR',COL['SMR'],'--','SMR'),('F02',COL['F02'],'-.','Fixed ±0.02 Hz'),('VS_FM',COL[FM],'-','Adaptive autofocus')]
 diag=[]
 for j,tone in enumerate([133,49]):
  q=read(P/f'X3_real/spectra/f{tone}_s1200_T300.csv');x=q.frequency_Hz.to_numpy()-tone;ref=q.Periodogram.max()
  peaks={m:(float(x[q[m].to_numpy().argmax()]),float(10*np.log10(q[m].max()/ref))) for m,*_ in methods}
  gain=peaks['VS_FM'][1]-peaks['SMR'][1]
  peak=peaks['VS_FM'][0];zoom=(max(-1.5,peak-.018),min(1.5,peak+.018))
  row=cases[(cases.tone_hz==tone)&(cases.segment_start_s==1200)&(cases.method=='VS_FM')].iloc[0]
  assert abs(gain-row.gain_peak_vs_SMR_db)<1e-9
  for m,col,ls,label in methods:
   y=10*np.log10(np.maximum(q[m].to_numpy()/ref,np.finfo(float).tiny))
   for i,bounds in enumerate([(-1.5,1.5,-45,13),(*zoom,-10,13)]):
    xx,yy=clipped_polyline(x,y,bounds);a[i,j].plot(xx,yy,c=col,ls=ls,lw=1 if i else .75,label=label)
   diag.append({'tone_hz':tone,'method':m,'peak_offset_hz':peaks[m][0],'peak_relative_periodogram_db':peaks[m][1],'gain_ADA_vs_SMR_db':gain})
  a[0,j].set(xlim=(-1.5,1.5),ylim=(-45,13),title=f'{tone} Hz; 1200–1500 s',xlabel='Residual frequency (Hz)',ylabel='Power / uncompensated peak (dB)')
  a[0,j].set_xticks([-1.5,0,1.5])
  if tone==133:
   for m,col,tx,label in [('SMR',COL['SMR'],.65,'SMR max.'),('VS_FM',COL[FM],-.88,'Adaptive max.')]:
    a[0,j].scatter(*peaks[m],s=18,facecolor='white',edgecolor=col,zorder=6)
    a[0,j].annotate(label,xy=peaks[m],xytext=(tx,8),ha='center',fontsize=7.8,color=col,arrowprops={'arrowstyle':'->','color':col,'lw':.65})
  a[1,j].set(xlim=zoom,ylim=(-10,13),xlabel='Residual frequency (Hz)',ylabel='Power / uncompensated peak (dB)')
  a[1,j].set_title('Search-edge peak detail' if tone==133 else 'Central peak detail',pad=13)
  a[1,j].text(.03,.91,f'Full-band maximum gain: {gain:+.3f} dB',transform=a[1,j].transAxes,fontsize=7.8)
  a[0,j].axvspan(*zoom,color=COL[FM],alpha=.12,lw=0)
 h,l=a[0,0].get_legend_handles_labels();fig.legend(h,l,loc='upper center',bbox_to_anchor=(.54,.99),ncol=2)
 pd.DataFrame(diag).to_csv(SD/'prespecified_peak_locations.csv',index=False)
 save(fig,a,'fig11_real_spectra','图11 运行前按可见性冻结的133 Hz弱源案例与同时段49 Hz强源对照。上排保留完整±1.5 Hz搜索带，下排以最终方法的最大值为中心放大±0.018 Hz并截在候选带内；阴影指示放大范围。各曲线均为原始、无平滑、整段矩形FFT |FFT|²/N，以同案例未补偿周期图的候选带最大值为0 dB。标注增量按各方法全频带最大值之差计算，不是同一频率处的纵向差。133 Hz案例SMR最大值在+1.399231 Hz，自适应最大值在−1.487732 Hz，不能把+2.915560 dB解释为已确认同一目标主瓣增强；同时自适应比固定0.02的峰值低0.191917 dB。49 Hz自适应与固定0.02重合，相对SMR仅+0.022533 dB。案例没有按增益替换。',['Weak case full search band','Strong case full search band','Weak edge-peak zoom, not target identification','Strong central-peak zoom'])

def fig12():
 freq=np.loadtxt(SD/'continuous_lofar_frequency.csv',delimiter=',');time=np.loadtxt(SD/'continuous_lofar_time.csv',delimiter=',');power=np.loadtxt(SD/'continuous_lofar_power_db.csv',delimiter=',')
 assert power.shape==(len(freq),len(time)) and len(time)==1500
 # One global transform and scale over all displayed pixels; no selective edits.
 bg=float(np.median(power));z=power-bg;vmin,vmax=np.quantile(z,[.08,.995])
 fig,a=axes(3,1,7.3,top=.93);fig.subplots_adjust(left=.12,right=.855,bottom=.08,top=.93,hspace=.66)
 a=a[:,0];im=a[0].pcolormesh(time,freq-100,z,cmap='magma',vmin=vmin,vmax=vmax,shading='nearest',rasterized=True)
 a[0].set(xlim=(600,2100),ylim=(-.25,.35),xlabel='Voyage time (s)',ylabel='Offset from 100 Hz (Hz)',title='Continuous LOFAR: preselected weak-source interval')
 ca=fig.add_axes([.89,.708,.016,.215],label='<colorbar>');fig.colorbar(im,cax=ca,label='Power / global median (dB)')
 for j,s in enumerate(range(600,2100,300)):
  t=read(P/f'X3_real/tracks/f100_s{s}_T300.csv')
  for m,col,ls,label in [('GPS_Hz','#8296A2',':','GPS reference'),('SMR',COL['SMR'],'--','SMR'),('VS_FM',COL[FM],'-','Adaptive autofocus')]:a[1].plot(t.time_s,t[m]-100,c=col,ls=ls,lw=1.0,label=label if j==0 else None)
 a[1].set(xlim=(600,2100),ylim=(-.25,.35),xlabel='Voyage time (s)',ylabel='Offset from 100 Hz (Hz)')
 a[1].legend(loc='upper center',bbox_to_anchor=(.5,1.28),ncol=3,fontsize=8)
 d=read(P/'X3_real/X3_duration.csv');q=d.pivot(index=['tone_hz','segment_start_s','duration_s'],columns='method',values='peak_relative_periodogram_db')
 for i,((tone,s),v) in enumerate(q.groupby(level=[0,1])):a[2].plot(v.index.get_level_values('duration_s'),v.VS_FM-v.SMR,c=[COL['F02'],COL['F04'],COL[FM],COL['UNB']][i],marker=['o','s','^','D'][i],ms=4,label=f'{tone} Hz, start {s} s')
 a[2].axhline(0,c='#888888',lw=.8);a[2].set(xlabel='Accumulation duration (s)',ylabel='Spectral-maximum gain (dB)',xticks=[150,300,450,600]);a[2].legend(loc='upper center',bbox_to_anchor=(.5,1.40),ncol=2,fontsize=8)
 (SD/'lofar_display.json').write_text(json.dumps({'global_median_db':bg,'display_limits_relative_db':[vmin,vmax],'limit_rule':'global 8th and 99.5th percentiles; all 1500 frames and full ±0.5 Hz source used','frequency_view_hz':[-.25,.35],'smoothing':False,'interpolation':False},indent=2),encoding='utf-8')
 save(fig,a,'fig12_real_trajectory_duration','图12 连续时频背景、估计轨迹及嵌套时长窗口。a为预定100 Hz、600–2100 s案例的连续LOFAR，从已冻结0–3000 s基带按原Hann200、步长20、NFFT8192计算，1500帧中原有1455帧与旧值最大差4.98e−14 dB，新增45个真实边界窗口，没有插值或平滑填空。颜色相对整幅原矩阵全局中位数，色限取全局8%与99.5%分位，频率显示−0.25至+0.35 Hz。b分段显示原SMR、自适应轨迹及GPS参考，GPS不是真值。c保留全部4个预定起点×4个时长，含103 Hz竞争脊案例以及100 Hz、900 s旧窗口替换；150 s两负两正，300–600 s均为正但曲线非单调。100 Hz两个起点重叠，共涉及3个频点，并非4个独立样本。',['Continuous observed LOFAR','Saved trajectories and GPS reference','All sixteen duration windows'],exclude=[ca])

def supp_paired():
 s=read(P/'C_confirm/C_cell_statistics.csv');fig,a=axes(2,2,4.9,sharey='row',top=.86)
 for j,sc in enumerate(SC):
  for i,met in enumerate(['gain_eta_vs_F02','gain_eta_vs_UNB']):
   q=s[(s.scene==sc)&(s.method==FM)&(s.metric==met)].sort_values('snr_db');ci(a[i,j],q.snr_db,q,color=COL[FM])
   a[i,j].axhline(0,c='#888888',lw=.7);a[i,j].axhline(-.005,c='#AA5555',lw=.8,ls='--');a[i,j].set_xlabel('Baseband SNR (dB)');a[i,j].set_xticks(range(-20,-13));a[i,j].set_ylabel('Adaptive − fixed ±0.02 Hz, Δη' if i==0 else 'Adaptive − no-box, Δη')
  a[0,j].set_title(SC[sc],pad=14)
 save(fig,a,'figS02_confirmation_paired','补图S2 14单元配对修正范围比较，均值与逐单元配对95%区间。虚线−0.005在上排为单元系统性退化阈值，在下排仅作合并非劣界的数值参考；正式P1/P2判定使用合并种子成簇区间，不要求各单元通过，也不宣称逐单元非劣。',['Adaptive versus fixed without interference','Adaptive versus fixed with interference','Adaptive versus no box without interference','Adaptive versus no box with interference'])

def supp_e0():
 s=read(ROOT/'03_实验证据/D_前端诊断_E0修正版/E0_phase_corrected_perrecord.csv')
 fig,a=axes(1,2,3.5,top=.71,sharey=True)
 for m,col in [('MFT',COL['F02']),('VIT',COL[FM])]:
  for sc,mk in [('S0','o'),('S2','^')]:
   q=s[(s.estimator==m)&(s.scene==sc)]
   for j,x in enumerate(['rmse_eval_hz','rms_slow_eval_T60']):
    assert (q[x]>0).all(), 'Log axis requires strictly positive errors'
    a[0,j].scatter(q[x],q.eta_full,s=9,marker=mk,c=col,alpha=.6,linewidths=0,label=f'{m}; '+SC[sc].lower())
 for j,ax in enumerate(a[0]):
  ax.set_xscale('log');ax.set_ylim(0,1);ax.set_ylabel('Coherent efficiency, η')
  ax.set_xlabel('Frequency RMSE (Hz)' if j==0 else 'Slow-error RMS, 60 s scale (Hz)')
 h,l=a[0,0].get_legend_handles_labels();fig.legend(h,l,loc='upper center',bbox_to_anchor=(.55,.99),ncol=2)
 save(fig,a,'figS03_frontend_diagnostic','补图S3 已修正E0的全部400对MFT/VIT轨迹，800个估计器输出；左为评价区间内频率RMSE，右为60 s尺度慢误差RMS，横轴均为对数以展开较小误差处的点，未抽样、未抖动、未拟合。颜色分前端，形状分场景。η使用修正后纯目标计算，来自旧前端诊断而非最终模块试验。此前端质量差异很大的集合未观察到配对RMSE–η反序，因此图2构造例只能说明可能性。',['All historical frontend errors','All historical slow-error values'])

if __name__=='__main__':
 funcs={'1':fig01,'2':fig02,'3':fig03,'4':d1,'5':fig05,'6':fig06,'7':fig07,'8':fig08,'9':fig09,'10':fig10,'11':fig11,'12':fig12,'S1':lambda:d1('peak_db',False),'S2':supp_paired,'S3':supp_e0}
 for key in sys.argv[1:] or funcs:funcs[key]()
 # Merge metadata when only selected figures are re-rendered.
 for name,obj in [('CAPTIONS.json',captions),('PANELS.json',panels),('SOURCE_DATA_MANIFEST.json',provenance)]:
  dest=O/name;prior=json.loads(dest.read_text(encoding='utf-8')) if dest.exists() else {};prior.update(obj);dest.write_text(json.dumps(prior,ensure_ascii=False,indent=2),encoding='utf-8')
 cap=json.loads((O/'CAPTIONS.json').read_text(encoding='utf-8'));(O/'图注.md').write_text('# 图注\n\n'+'\n\n'.join('## '+k+'\n\n'+v for k,v in sorted(cap.items()))+'\n',encoding='utf-8')
