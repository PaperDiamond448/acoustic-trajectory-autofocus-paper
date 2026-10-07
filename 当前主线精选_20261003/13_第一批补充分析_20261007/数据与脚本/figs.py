import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
plt.rcParams['font.sans-serif']=['Noto Sans CJK JP','DejaVu Sans']; plt.rcParams['axes.unicode_minus']=False
from theory import kernel
fig,ax=plt.subplots(1,3,figsize=(13,3.8))
# (a) kernel
f=np.logspace(np.log10(0.5/290),np.log10(0.5),60); K=kernel(f,nphi=8)
ax[0].loglog(f,K,'k-'); ax[0].loglog(f[f>3/290],1/f[f>3/290]**2,'--',color='gray',label='1/f²')
for fx,lab in [(1/290,'周期=T'),(0.05,'1/(2Δ), Δ=10 s')]:
    ax[0].axvline(fx,color='C1' if fx<0.01 else 'C0',ls=':'); ax[0].text(fx*1.1,K.max()*0.4,lab,fontsize=8)
ax[0].set_xlabel('频率误差分量的频率 f / Hz'); ax[0].set_ylabel('权重 K(f) / (rad²/Hz²)'); ax[0].set_title('(a) 相位误差权重（T=300 s）'); ax[0].legend(fontsize=8)
# (b) MC
d=pd.read_csv('mc_results.csv')
ax[1].scatter(d.pred,d.eta,s=6,c=np.log10(d.spacing),cmap='viridis'); ax[1].plot([0,1],[0,1],'k--',lw=0.8)
ax[1].set_xlabel('预测 exp(−σ²)'); ax[1].set_ylabel('实际 η'); ax[1].set_title('(b) 随机缓变误差：预测与实际')
ax[1].text(0.03,0.70,'σ²<0.5: MAE 0.003\nSpearman(η, −σ²)=0.993\nSpearman(η, −RMSE)=0.910',fontsize=8,transform=ax[1].transAxes)
# (c) real corrections
r=pd.read_csv('real_correction_spectra.csv')
for i,g in enumerate(['weak','strong','shallow']):
    s=r[r.group==g]; ax[2].scatter(s.phase_change_s2+1e-4,s.gain,s=12,label={'weak':'弱线组','strong':'强线组','shallow':'浅源组'}[g])
ax[2].set_xscale('log'); ax[2].set_xlabel('修正量引起的去趋势相位变化 σ² / rad²'); ax[2].set_ylabel('谱峰增量 / dB'); ax[2].set_title('(c) SWellEx-96：修正量与增益'); ax[2].legend(fontsize=8)
plt.tight_layout(); plt.savefig('/home/claude/out/图1_理论初步验证.png',dpi=150)
print('ok')
