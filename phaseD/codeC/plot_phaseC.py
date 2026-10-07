"""Confirmation evidence plots: complete prespecified cells, no selected cases."""
from pathlib import Path
import json, sys, string
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(r'D:\论文集\phaseD\C_confirm')
sys.path.insert(0, r'C:\Users\Lenovo\.codex\skills\nature-figure\scripts')
from audit_panel_alignment import require_matplotlib_panel_alignment
FM = 'ADA_local_c04_t30_A'
plt.rcParams.update({'font.family':'sans-serif', 'font.sans-serif':['Arial','DejaVu Sans'], 'font.size':7, 'pdf.fonttype':42, 'svg.fonttype':'none', 'axes.spines.top':False, 'axes.spines.right':False, 'axes.linewidth':.7, 'legend.frameon':False, 'lines.linewidth':1.2})

def save(fig, name):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig, json_out=OUT/(name+'.alignment.json'), overlay_svg=OUT/(name+'.alignment.svg'), tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True)
    fig.savefig(OUT/(name+'.pdf'), facecolor='white')
    fig.savefig(OUT/(name+'.svg'), facecolor='white')
    fig.savefig(OUT/(name+'.png'), dpi=600, facecolor='white')
    plt.close(fig)

def labels(axes):
    for i, ax in enumerate(axes.flat):
        ax.text(-.15, 1.08, string.ascii_lowercase[i], transform=ax.transAxes, fontsize=8, fontweight='bold')
        ax.tick_params(length=3, width=.6)

def plots():
    cells=pd.read_csv(OUT/'C_cell_statistics.csv')
    summary=pd.read_csv(OUT/'C_summary.csv')
    fig,axes=plt.subplots(2,2,figsize=(7.2,4.8),sharey='row')
    fig.subplots_adjust(left=.10,right=.98,bottom=.13,top=.86,wspace=.35,hspace=.62)
    for j,scene in enumerate(['S0','S2']):
        for i,metric in enumerate(['gain_eta_vs_F02','gain_eta_vs_UNB']):
            q=cells[cells.scene.eq(scene)&cells.method.eq(FM)&cells.metric.eq(metric)].sort_values('snr_db')
            ax=axes[i,j]
            ax.axhline(0,color='#888888',lw=.8)
            ax.axhline(-.005,color='#B24745',ls='--',lw=.9)
            ax.errorbar(q.snr_db,q['mean'],yerr=[q['mean']-q.lo,q.hi-q['mean']],fmt='o',color='#C07654',markersize=3.5,capsize=2)
            ax.set_xticks(range(-20,-13));ax.set_xlabel('SNR (dB)')
            ax.set_ylabel('ADA − F02, Δη' if i==0 else 'ADA − UNB, Δη')
            if i==0:ax.set_title(scene + (' (no interference)' if j==0 else ' (local interference)'),pad=12)
    labels(axes);save(fig,'fig_C_paired_eta')

    fig,axes=plt.subplots(2,2,figsize=(7.2,4.8),sharey='row')
    fig.subplots_adjust(left=.10,right=.98,bottom=.13,top=.86,wspace=.35,hspace=.62)
    methods=['F02','F04','UNB',FM];names=['F02','F04','UNB','ADA']
    colors=['#4C78A8','#6F8D68','#8C6D9F','#C07654'];markers=['o','s','^','D']
    for j,scene in enumerate(['S0','S2']):
        for i,metric in enumerate(['gain_eta_vs_SMR','harm_vs_F02']):
            ax=axes[i,j];q=summary[summary.scope.eq(scene)&summary.metric.eq(metric)].set_index('method')
            for k,m in enumerate(methods):
                r=q.loc[m]
                ax.errorbar(k,r['mean'],yerr=[[r['mean']-r.lo],[r.hi-r['mean']]],fmt=markers[k],color=colors[k],markersize=4,capsize=2)
            ax.set_xticks(range(4),names);ax.set_xlim(-.5,3.5)
            if i==0:ax.set_ylabel('Gain over SMR, Δη');ax.axhline(0,color='#888888',lw=.8);ax.set_title(scene,pad=12)
            else:ax.set_ylabel('Harm rate relative to F02')
    axes[1,0].set_ylim(bottom=-.01)
    labels(axes);save(fig,'fig_C_gain_harm')
    captions={
        'fig_C_paired_eta':'All 14 scene × SNR cells from 2,800 new phase-52 records, 200 paired records per cell. Points show mean pure-target efficiency differences; error bars are 95% paired record bootstrap intervals (2,000 replicates). Upper panels compare frozen ADA with F02; lower panels compare it with UNB. Grey solid line: zero. Red dashed line: −0.005, the S1 deterioration boundary in upper panels and the P2 noninferiority boundary in lower panels. P1/P2 decisions use pooled seed-cluster intervals, reported in the endpoint table, rather than requiring each cell to pass. ADA denotes the unchanged ADA_local_c04_t30_A (10-s spacing, local 0.04-Hz cap, 30-s trigger, full three-stage rerun).',
        'fig_C_gain_harm':'All confirmation records retained. Within each scene, the seven SNR-cell means receive equal weight. Upper panels: paired efficiency gain relative to the same-record SMR start. Lower panels: fraction with η_method < η_F02 − 0.01. Points and error bars show means and 95% scene-stratified seed-cluster bootstrap intervals (2,000 replicates, 200 seeds per scene carried across all seven SNRs). Method order is fixed; F04 is the preregistered fixed comparator. No observed spectral metric or η was used to choose optimizer candidates. Colors are redundant with the labeled method positions and marker shapes.'
    }
    (OUT/'FIGURE_CAPTIONS.md').write_text('\n\n'.join(k+'\n\n'+v for k,v in captions.items())+'\n',encoding='utf8')

if __name__=='__main__':plots()
