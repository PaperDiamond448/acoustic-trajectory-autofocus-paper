import numpy as np, pandas as pd
from scipy.integrate import cumulative_trapezoid
FS=20.0
def eval_idx(T):
    t=np.arange(int(T*FS))/FS; return t,(t>=5)&(t<T-5)
def eta_actual(e,t,idx,numax=2.0):
    d=2*np.pi*cumulative_trapezoid(e,t,initial=0.0)
    z=np.exp(1j*d[idx]); N=len(z); nfft=1
    while nfft<8*N: nfft*=2
    S=np.abs(np.fft.fft(z,nfft))**2/N**2
    nu=np.fft.fftfreq(nfft,1/FS); return S[np.abs(nu)<=numax].max()
def sigma2(e,t,idx):
    d=2*np.pi*cumulative_trapezoid(e,t,initial=0.0)[idx]; tt=t[idx]
    A=np.vstack([np.ones_like(tt),tt]).T
    r=d-A@np.linalg.lstsq(A,d,rcond=None)[0]; return np.mean(r**2)
def kernel(f,T=300,nphi=16):
    t,idx=eval_idx(T); out=[]
    for ff in np.atleast_1d(f):
        v=[sigma2(np.cos(2*np.pi*ff*t+p),t,idx) for p in np.linspace(0,np.pi,nphi,endpoint=False)]
        out.append(np.mean(v)/0.5)   # per unit error variance (Hz^2)
    return np.array(out)
if __name__=='__main__':
    T=300; t,idx=eval_idx(T)
    # 1) kernel shape
    fgrid=np.array([0.5,1,1.5,2,3,5,10,20,40])/290
    K=kernel(fgrid)
    print('kernel K(f) [rad^2 per Hz^2 of error variance]:')
    for f,k in zip(fgrid,K): print(f'  f={f*1e3:7.2f} mHz (period {1/f:6.1f} s): K={k:10.1f}')
    for f in [0.02,0.05,0.1]: print(f'  f={f} Hz: K={kernel([f])[0]:.1f}   (1/(2pi f)^2*... ref 1/f^2={1/f**2:.1f})')
    # 2) Fig.2 constructed errors
    ex=pd.read_csv('/home/claude/repo/当前主线精选_20261003/05_图表素材/正文图_20261004/source_data/expA_curves.csv')
    eA=np.interp(t,ex.t_s,ex.e_A_hz); eB=np.interp(t,ex.t_s,ex.e_B_hz)
    for nm,e in [('A',eA),('B',eB)]:
        s2=sigma2(e,t,idx); print(f'Fig2 error {nm}: rms={1e3*np.sqrt(np.mean(e[idx]**2)):.2f} mHz  sigma2={s2:.3f}  eta_pred=exp(-s2)={np.exp(-s2):.3f}  eta_actual={eta_actual(e,t,idx):.3f}')
