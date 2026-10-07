from pathlib import Path
import sys, json, string
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(r'D:\论文集\phaseD\D_dev')
sys.path.insert(0,r'C:\Users\Lenovo\.codex\skills\nature-figure\scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':7,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'legend.frameon':False,'lines.linewidth':1.3})
colors={'F02':'#4C78A8','UNB':'#C07654','Control':'#8B8B8B'}

def save(fig,name):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=OUT/(name+'.alignment.json'),overlay_svg=OUT/(name+'.alignment.svg'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    fig.savefig(OUT/(name+'.pdf'),facecolor='white')
    fig.savefig(OUT/(name+'.svg'),facecolor='white')
    fig.savefig(OUT/(name+'.png'),dpi=600,facecolor='white')
    plt.close(fig)

def labels(axes):
    for i,ax in enumerate(np.ravel(axes)):
        ax.text(-.13,1.08,string.ascii_lowercase[i],transform=ax.transAxes,fontweight='bold',fontsize=8)
        ax.tick_params(length=3,width=.6)

def d1_plot(s,metric,name,runtime=False):
    fig,axes=plt.subplots(2 if runtime else 1,2,figsize=(7.2,4.5 if runtime else 2.7),squeeze=False)
    fig.subplots_adjust(left=.09,right=.98,bottom=.14,top=.84,wspace=.30,hspace=.48)
    for j,scene in enumerate(['S0','S2']):
        for method,arm,label in [('F02','scaled','F02'),('UNB','scaled','UNB'),('F02','unscaled','Control')]:
            q=s[(s.scene==scene)&(s.method==method)&(s.arm==arm)].copy()
            if label=='Control':q=pd.concat([q,s[(s.scene==scene)&(s.method=='F02')&(s.arm=='scaled')&(s.Delta_s==15)]])
            q=q.sort_values('P');x=q.P.to_numpy();y=q[metric].to_numpy()
            axes[0,j].plot(x,y,'o-' if label!='Control' else 's--',color=colors[label],markersize=3,label=label)
            axes[0,j].fill_between(x,q[metric+'_lo'].to_numpy(),q[metric+'_hi'].to_numpy(),color=colors[label],alpha=.10,linewidth=0)
            if runtime:axes[1,j].plot(x,q.runtime_median_s.to_numpy(),'o-' if label!='Control' else 's--',color=colors[label],markersize=3)
        axes[0,j].set_title(scene,pad=10)
        for ax in axes[:,j]:ax.set_xlabel('Number of knots, P');ax.set_xticks([6,11,16,21,31,41,51])
        axes[0,j].set_ylabel('Pure-target efficiency, eta' if metric=='eta' else 'Observed peak (dB)')
        if runtime:axes[1,j].set_ylabel('Median BTA runtime (s)')
    handles,leg=axes[0,0].get_legend_handles_labels();fig.legend(handles,leg,loc='upper center',ncol=3,bbox_to_anchor=(.53,.99),fontsize=7)
    labels(axes);save(fig,name)

def plot_all():
    s=pd.read_csv(OUT/'D1_summary.csv');d1_plot(s,'eta','fig_D1_eta_runtime',True);d1_plot(s,'peak_db','fig_D1_observed_peak')
    s=pd.read_csv(OUT/'D2_summary.csv');frozen=json.loads((OUT/'FROZEN_METHOD.json').read_text(encoding='utf8'))
    fig,axes=plt.subplots(2,2,figsize=(7.2,4.7));fig.subplots_adjust(left=.10,right=.98,bottom=.14,top=.87,wspace=.30,hspace=.55)
    names=['F01','F02','F04','F08','UNB'];x=np.arange(5)
    for j,scene in enumerate(['S0','S2']):
        q=s[(s.scene==scene)&s.method.isin(names)].set_index('method').loc[names]
        for i,metric in enumerate(['gain_eta_vs_F02','harm_vs_F02']):
            ax=axes[i,j];y=q[metric].to_numpy();lo=q[metric+'_lo'].to_numpy();hi=q[metric+'_hi'].to_numpy()
            ax.errorbar(x,y,yerr=[y-lo,hi-y],fmt='o-',color=colors['F02'],markersize=4,capsize=2,label='Fixed / unbounded')
            ax.set_xticks(x,['0.01','0.02','0.04','0.08','Unbounded']);ax.set_xlabel('Correction radius (Hz)')
            ax.set_ylabel('Eta gain versus F02' if i==0 else 'Harm rate versus F02')
            if frozen['developed_ADA']:
                name=frozen['decisions']['ADA_selection']['selected_ADA'];r=s[(s.scene==scene)&(s.method==name)].iloc[0]
                ax.axhline(r[metric],color=colors['UNB'],ls='--',linewidth=1.1,label='Selected ADA')
                ax.fill_between([-.3,4.3],r[metric+'_lo'],r[metric+'_hi'],color=colors['UNB'],alpha=.10,linewidth=0)
            if i==0:ax.set_title(scene,pad=10)
    handles,leg=axes[0,0].get_legend_handles_labels();fig.legend(handles,leg,loc='upper center',ncol=2,bbox_to_anchor=(.53,.99),fontsize=7)
    labels(axes);save(fig,'fig_D2_radius_gain_harm')
    captions={'fig_D1_eta_runtime':'Seven spacings on all 840 paired phase-51 records. Means are equal-weight SNR-cell means within scene; shading shows 2000 seed-cluster bootstrap 95% intervals. Bottom panels show descriptive runtime medians measured during six-worker execution; uncertainty is omitted because runtime is secondary descriptive workload evidence. Control at P=21 reuses the identical scaled/unscaled baseline.','fig_D1_observed_peak':'Observed peak is descriptive and never used to choose spacing or adaptive parameters. Same records and confidence-interval definition as efficiency panels.','fig_D2_radius_gain_harm':'Paired eta gain and harm rate relative to same-record F02. Fixed radius and unbounded points have 95% seed-cluster bootstrap intervals. Dashed line and band show selected development ADA if A3 permits adaptive development. Harm is eta lower than F02 by more than 0.01. All 840 records retained; phase-51 development evidence only.'}
    (OUT/'FIGURE_CAPTIONS.md').write_text('\n\n'.join(f'{k}\n\n{v}' for k,v in captions.items())+'\n',encoding='utf8')

if __name__=='__main__':plot_all()
