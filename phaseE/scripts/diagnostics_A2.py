#!/usr/bin/env python3
"""
diagnostics_A2.py -- follow-up to task A (run locally on the H5 exports; no MATLAB needed).

For every (record, frontend) row it computes
  1) eta_clean_m1 / eta_clean_m2 : coherence the correction family can reach on the NOISE-FREE target
     (same anchor, hat basis Delta=10 s, r=0.02 Hz, bounds |u|<=m, 2nd-difference penalty with lambda from Eq. 15,
     staged blocks 20/60/(T-10) s, start = the frontend's start: LPS coefficients for VS, 0 otherwise).
     This is an idealised ceiling (no noise, global bounds instead of the local expansion rule, L-BFGS-B
     instead of SQP, no frequency-band constraint). It separates "what the family/bounds allow" from
     "what noise lets the solver find":  gain = (eta_clean - eta_in) - (eta_clean - eta_out).
  2) burst diagnostics on e = g_true - g_hat over the evaluation window (after removing the median):
     frac_gt20mHz, frac_gt50mHz, longest run above 50 mHz (s), and n_slip_runs = number of runs where
     |e| > 1/(2*tau) = 0.0625 Hz lasting 4-12 s (tau = 8 s PC-TBD block; a mis-resolved integer in the
     phase-difference readout gives a ~1/tau = 0.125 Hz error over ~tau, i.e. a ~2*pi phase step).
  3) wrapped-phase check: eta of the target after removing a least-squares linear phase, computed with the
     phase wrapped (identical to eta up to the nu grid) versus exp(-sigma2) from the unwrapped phase.
Usage:  python diagnostics_A2.py <export_name> [n_workers]
Inputs: <export_name>.h5 and <export_name>_index.csv as written in task A.
Anchor rule: VS -> anchor = V0 input of the same record (VIT); V0, MFT, SUV -> their own input.
If no V0 row exists (X1 exports), VS uses its own input as anchor with start 0 (flag anchor_is_input=1).
Output: <export_name>_diagA2.csv
"""
import sys, numpy as np, pandas as pd, h5py
from multiprocessing import Pool
from scipy.optimize import minimize, lsq_linear
from scipy.integrate import cumulative_trapezoid
FS = 20.0; R = 0.02; DELTA = 10.0

def lam_eq15(P, T, lam0=1e-3, P0=21, D0=15.0, T0=300.0):
    return lam0*(P-2)/(P0-2)*(T0/T)*(D0/DELTA)**3

def eta_from_phase(d, idx, numax=2.0):
    z = np.exp(1j*d[idx]); N = len(z); nfft = 1
    while nfft < 8*N: nfft *= 2
    S = np.abs(np.fft.fft(z, nfft))**2/N**2
    nu = np.fft.fftfreq(nfft, 1/FS); return S[np.abs(nu) <= numax].max()

def runs(mask):
    out = []; n = 0
    for v in mask:
        if v: n += 1
        elif n: out.append(n); n = 0
    if n: out.append(n)
    return np.array(out)/FS

def clean_ceiling(gt, ga, u0, T, m):
    N = len(gt); t = np.arange(N)/FS; idx = (t >= 5) & (t < T-5)
    nodes = np.arange(0, T+DELTA/2, DELTA); P = len(nodes)
    B = np.maximum(0, 1-np.abs(t[:, None]-nodes[None, :])/DELTA)
    H = 2*np.pi*R*cumulative_trapezoid(B, t, axis=0, initial=0.0)
    d0 = 2*np.pi*cumulative_trapezoid(gt-ga, t, initial=0.0)
    zi = np.exp(1j*d0[idx]); Hi = H[idx]; ti = t[idx]; E = float(len(zi))
    D2 = np.diff(np.eye(P), 2, axis=0); lam = lam_eq15(P, T)
    def make(h):
        blk = np.floor((ti-ti[0])/h).astype(int); nb = blk.max()+1; Nb = np.bincount(blk, minlength=nb)
        def f(u):
            zu = zi*np.exp(-1j*(Hi@u))
            Rb = np.bincount(blk, weights=zu.real, minlength=nb)+1j*np.bincount(blk, weights=zu.imag, minlength=nb)
            Q = np.sum(np.abs(Rb)**2/Nb)/E
            w = (np.conj(Rb)/Nb)[blk]*zu*(-1j)
            gQ = 2/E*np.real(Hi.T@w)
            Du = D2@u; pen = lam/(P-2)*Du@Du; gp = 2*lam/(P-2)*(D2.T@Du)
            return -(Q-pen), -(gQ-gp)
        return f
    u = np.clip(u0, -m, m); cands = [u.copy()]
    for h in (20.0, 60.0, T-10):
        res = minimize(make(h), u, jac=True, method='L-BFGS-B', bounds=[(-m, m)]*P, options=dict(maxiter=500))
        u = res.x; cands.append(u.copy())
    fT = make(T-10); best = min(cands, key=lambda v: fT(v)[0])
    return eta_from_phase(d0 - H@best, idx)

def start_coeffs(gin, ga, T):
    N = len(gin); t = np.arange(N)/FS; nodes = np.arange(0, T+DELTA/2, DELTA)
    B = np.maximum(0, 1-np.abs(t[:, None]-nodes[None, :])/DELTA)
    sol = lsq_linear(R*B, gin-ga, bounds=(-1, 1)); return sol.x, float(np.sqrt(np.mean((R*B@sol.x-(gin-ga))**2)))

def work(args):
    name, r, arow, use_start = args
    with h5py.File(f'{name}.h5', 'r') as h:
        gt = h['truth'][r['truth_row']]; gi = h['input'][r['row']]
        ga = h['input'][arow] if arow is not None else gi
    N = len(gt); T = N/FS; t = np.arange(N)/FS; idx = (t >= 5) & (t < T-5)
    if use_start: u0, fit_rms = start_coeffs(gi, ga, T)
    else: u0, fit_rms = np.zeros(int(T/DELTA)+1), 0.0
    out = dict(row=r['row'], anchor_is_input=int(arow is None), start_fit_rms_hz=fit_rms)
    for m in (1.0, 2.0): out[f'eta_clean_m{int(m)}'] = clean_ceiling(gt, ga, u0, T, m)
    e = (gt-gi)[idx]; e = e-np.median(e)
    out['frac_gt20mHz'] = float(np.mean(np.abs(e) > 0.02)); out['frac_gt50mHz'] = float(np.mean(np.abs(e) > 0.05))
    rr = runs(np.abs(e) > 0.05); out['longest_run_gt50mHz_s'] = float(rr.max()) if len(rr) else 0.0
    rs = runs(np.abs(e) > 0.0625); out['n_slip_runs'] = int(np.sum((rs >= 4) & (rs <= 12)))
    d = 2*np.pi*cumulative_trapezoid(gt-gi, t, initial=0.0)
    out['eta_in_recomputed'] = eta_from_phase(d, idx)
    return out

def main(name, nw=4):
    ix = pd.read_csv(f'{name}_index.csv')
    v0 = ix[ix.frontend == 'V0'].set_index('truth_row')['row'].to_dict()
    jobs = []
    for r in ix.to_dict('records'):
        if r['frontend'] == 'VS':
            arow = v0.get(r['truth_row']); jobs.append((name, r, arow, arow is not None))
        else:
            jobs.append((name, r, r['row'], False))
    with Pool(nw) as p: res = p.map(work, jobs, chunksize=8)
    d = ix.merge(pd.DataFrame(res), on='row')
    d['gain'] = d.eta_out-d.eta_in
    d['ceiling_gain_m1'] = d.eta_clean_m1-d.eta_in; d['noise_loss_m1'] = d.eta_clean_m1-d.eta_out
    d.to_csv(f'{name}_diagA2.csv', index=False)
    g = d.groupby('frontend')
    s = g.agg(n=('gain', 'size'), eta_in=('eta_in', 'mean'), eta_out=('eta_out', 'mean'),
              eta_clean_m1=('eta_clean_m1', 'mean'), eta_clean_m2=('eta_clean_m2', 'mean'),
              slip_runs_mean=('n_slip_runs', 'mean'), frac_gt50_mean=('frac_gt50mHz', 'mean'))
    s['rho_ceiling_gain_vs_gain'] = g.apply(lambda x: x.ceiling_gain_m1.corr(x.gain, method='spearman'))
    print(s.round(4).to_string()); s.to_csv(f'{name}_diagA2_summary.csv')
    print('max |eta_in recomputed - saved| =', (d.eta_in_recomputed-d.eta_in).abs().max())

if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4)
