# Python PREVIEW of the coherence-driven correction (NOT the frozen MATLAB code):
# hat basis, Delta=10 s, r=0.02 Hz, bounds |u|<=1, staged blocks 20/60/290 s, 2nd-diff penalty, L-BFGS-B.
import numpy as np
from scipy.optimize import minimize
from scipy.integrate import cumulative_trapezoid
from realtools import *
FS=20.0
def hat_basis(t,T=300,D=10):
    nodes=np.arange(0,T+D/2,D); B=np.maximum(0,1-np.abs(t[:,None]-nodes[None,:])/D); return B,nodes
def refine(y,fref,g_abs,lam=0.005151,r=0.02):
    N=len(y); t=np.arange(N)/FS; idx=(t>=5)&(t<295)
    B,nodes=hat_basis(t); P=B.shape[1]
    H=2*np.pi*r*cumulative_trapezoid(B,t,axis=0,initial=0.0)
    z0=y*np.exp(-1j*comp_phase(g_abs,fref))
    zi=z0[idx]; Hi=H[idx]; ti=t[idx]; E=np.sum(np.abs(zi)**2)
    D2=np.diff(np.eye(P),2,axis=0)
    def make(h):
        blk=np.floor((ti-ti[0])/h).astype(int); nb=blk.max()+1; Nb=np.bincount(blk,minlength=nb)
        def f(u):
            zu=zi*np.exp(-1j*(Hi@u))
            R=np.bincount(blk,weights=zu.real,minlength=nb)+1j*np.bincount(blk,weights=zu.imag,minlength=nb)
            Q=np.sum(np.abs(R)**2/Nb)/E
            # grad: dQ/du_p = 2/E sum_b 1/Nb Re{conj(R_b) sum_n (-j h_p) z_n}
            w=(np.conj(R)/Nb)[blk]*zu*(-1j)
            gQ=2/E*np.real(Hi.T@w)
            pen=lam/(P-2)*np.sum((D2@u)**2); gpen=2*lam/(P-2)*(D2.T@(D2@u))
            return -(Q-pen),-(gQ-gpen)
        return f
    u=np.zeros(P); cands=[u.copy()]
    for h in [20,60,290]:
        res=minimize(make(h),u,jac=True,method='L-BFGS-B',bounds=[(-1,1)]*P,options=dict(maxiter=400))
        u=res.x; cands.append(u.copy())
    fT=make(290); best=min(cands,key=lambda v: fT(v)[0])
    return g_abs+r*(B@best)
def peaks(y,fref,g_abs):
    nu0,S0=spectrum(y); nu,S=spectrum(y*np.exp(-1j*comp_phase(g_abs,fref))); Sdb=10*np.log10(S/S0.max())
    return Sdb.max(), nu[np.argmax(Sdb)], Sdb[np.abs(nu)<=0.01].max()
if __name__=='__main__':
    strong=[49,64,79,94,112,130]
    cases=[(136,900),(133,1200),(118,1500),(52,600),(52,900),(52,2400),(61,2100),(100,900)]
    print('case | VS_FM(max,nu) | SUV(max,nu) | guided(max,nu,zero) | guided+refine(max,nu,zero) | check: LPS+refine vs saved VS_FM')
    for f,s in cases:
        y,fref=load_y(f,s); tr=load_tracks(f,s)
        D=np.median([load_tracks(fk,s)['VS_FM'].values/fk for fk in strong],axis=0); gG=f*D
        gR=refine(y,fref,gG)
        out=[peaks(y,fref,tr.VS_FM.values),peaks(y,fref,tr.SUV.values),peaks(y,fref,gG),peaks(y,fref,gR)]
        chk=peaks(y,fref,refine(y,fref,tr.SMR.values))[0]
        print(f'{f} Hz {s}:',' | '.join(f'{a:6.2f} @{b:+.3f} (zero {c:6.2f})' for a,b,c in out), f'| LPS+refine {chk:5.2f} vs VS_FM {out[0][0]:5.2f}')
