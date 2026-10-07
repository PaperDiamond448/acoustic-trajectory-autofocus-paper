import numpy as np, pandas as pd, h5py
from scipy.integrate import cumulative_trapezoid
BASE='/home/claude/repo/phaseD/X3_real'
FS=20.0
def load_y(f,s):
    h=h5py.File(f'{BASE}/screen_inputs/f{f}_s{s}.mat','r')
    y=h['y'][0]; y=y['real']+1j*y['imag']
    fref=float(h['extract/fref'][0,0]); return y,fref
def load_tracks(f,s,T=300):
    return pd.read_csv(f'{BASE}/tracks/f{f}_s{s}_T{T}.csv')
def comp_phase(g_abs,fref):
    t=np.arange(len(g_abs))/FS
    return 2*np.pi*cumulative_trapezoid(g_abs-fref,t,initial=0.0)
def spectrum(z,numax=1.5):
    N=len(z); nfft=1
    while nfft<8*N: nfft*=2
    S=np.abs(np.fft.fft(z,nfft))**2/N
    nu=np.fft.fftfreq(nfft,1/FS)
    m=np.abs(nu)<=numax
    return nu[m],S[m]
def peak_rel_db(y,fref,g_abs):
    nu0,S0=spectrum(y)
    z=y*np.exp(-1j*comp_phase(g_abs,fref))
    nu,S=spectrum(z)
    k=np.argmax(S)
    return 10*np.log10(S[k]/S0.max()), nu[k]
