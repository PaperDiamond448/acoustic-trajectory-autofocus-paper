from pathlib import Path
import sys
sys.path.insert(0,str(Path('D:/论文集/phaseE/_local_pydeps')))
sys.path.insert(0,str(Path('C:/Users/Lenovo/.codex/skills/nature-figure/scripts')))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from audit_panel_alignment import require_matplotlib_panel_alignment
O=Path(__file__).parent
matplotlib.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':8,'axes.spines.right':False,'axes.spines.top':False,'axes.linewidth':.7,'pdf.fonttype':42,'svg.fonttype':'none','legend.frameon':False})
t=pd.read_csv(O/'FIG3_example_trajectories.csv');s=pd.read_csv(O/'FIG3_example_spectra.csv')
fig,axes=plt.subplots(1,2,figsize=(7.1,2.8));fig.subplots_adjust(left=.083,right=.985,bottom=.21,top=.78,wspace=.30)
ax=axes[0];z=t[(t.time_s>=5)&(t.time_s<295)]
ax.axhline(0,color='#d5d5d5',lw=.6,zorder=0)
ax.plot(z.time_s,1000*(z.true_g_Hz-z.LPS_g_Hz),color='#737373',lw=1.15,label='LPS')
ax.plot(z.time_s,1000*(z.true_g_Hz-z.CDTR_g_Hz),color='#d77832',lw=1.2,label='CDTR')
ax.set(xlabel='Time (s)',ylabel='Frequency error (mHz)',xlim=(5,295),ylim=(-23,23));ax.legend(loc='lower left',bbox_to_anchor=(0,1.015),fontsize=7,ncol=2)
ax=axes[1]
for label,color,style in [('LPS','#737373','-'),('CDTR','#d77832','-'),('ideal','#477aab','--')]:
 visible=s[(s.residual_frequency_Hz>=-.02)&(s.residual_frequency_Hz<=.02)]
 ax.plot(visible.residual_frequency_Hz,np.ma.masked_outside(visible[label+'_power_dB'],-32,2),color=color,ls=style,lw=1.2,label='Ideal' if label=='ideal' else label)
ax.set(xlabel='Residual frequency (Hz)',ylabel='Target power (dB)',xlim=(-.02,.02),ylim=(-32,2));ax.set_xticks([-.02,-.01,0,.01,.02]);ax.legend(loc='lower left',bbox_to_anchor=(0,1.015),fontsize=7,ncol=3,handlelength=1.5,columnspacing=1)
for ax,label in zip(axes,['(a)','(b)']):ax.text(0,1.20,label,transform=ax.transAxes,fontweight='bold',va='bottom')
base=O/'FIG3_example_panels'
require_matplotlib_panel_alignment(fig,json_out=str(base)+'.alignment.json',tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
fig.savefig(str(base)+'.pdf')
fig.savefig(str(base)+'.svg')
fig.savefig(str(base)+'.png',dpi=600)
plt.close(fig)
