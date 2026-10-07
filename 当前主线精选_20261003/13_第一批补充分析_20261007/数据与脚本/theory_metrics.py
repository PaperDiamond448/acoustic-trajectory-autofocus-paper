#!/usr/bin/env python3
"""
theory_metrics.py  --  frequency-error spectrum vs. coherence loss, per trajectory.

Input (produced by the MATLAB export in Codex task A):
  <name>_index.csv : one row per (record, frontend); columns at least
      row, truth_row, scene, snr_db, record_id, seed, frontend, eta_in, eta_out, input_usable
  <name>.h5        : datasets (float64, Hz, baseband, 20 Hz grid, t = n/20)
      /truth  [n_records x N]   true baseband frequency g_true(t)
      /input  [n_rows    x N]   frontend trajectory (module input)
      /output [n_rows    x N]   module output trajectory
Output:
  <name>_theory_metrics.csv : per-row metrics (see column list in the code)
  <name>_theory_summary.csv : per-frontend summary
Definitions follow the manuscript: evaluation set I = [5, T-5) s, eta = max_|nu|<=2 Hz of the
normalised zero-padded FFT of exp(j*delta), delta = 2*pi*cumtrapz(g_true - g_hat) (a(t)=1).
sigma2 = mean over I of the residual of delta after a least-squares constant+linear fit.
Small-error prediction: eta ~= exp(-sigma2). Band contributions use FFT masks on the
demeaned error over I; each band is integrated/detrended separately (cross terms ignored).
"""
import sys, numpy as np, pandas as pd, h5py
from scipy.integrate import cumulative_trapezoid
FS = 20.0
BANDS = [(0.0, 1/60), (1/60, 1/20), (1/20, 0.1), (0.1, FS/2)]
BNAMES = ['p_gt60s', 'p_20to60s', 'p_10to20s', 'p_lt10s']

def eta_of(e, t, idx, numax=2.0):
    d = 2*np.pi*cumulative_trapezoid(e, t, initial=0.0)
    z = np.exp(1j*d[idx]); N = len(z); nfft = 1
    while nfft < 8*N: nfft *= 2
    S = np.abs(np.fft.fft(z, nfft))**2 / N**2
    nu = np.fft.fftfreq(nfft, 1/FS)
    return S[np.abs(nu) <= numax].max()

def sigma2_of(e_eval, t_eval):
    d = 2*np.pi*cumulative_trapezoid(e_eval, t_eval, initial=0.0)
    A = np.vstack([np.ones_like(t_eval), t_eval]).T
    r = d - A @ np.linalg.lstsq(A, d, rcond=None)[0]
    return float(np.mean(r**2))

def band_sigma2(e_eval, t_eval):
    x = e_eval - e_eval.mean()
    X = np.fft.rfft(x); F = np.fft.rfftfreq(len(x), 1/FS)
    out = []
    for lo, hi in BANDS:
        m = (F >= lo) & (F < hi) if hi < FS/2 else (F >= lo)
        xb = np.fft.irfft(X*m, n=len(x))
        out.append(sigma2_of(xb, t_eval))
    return out

def metrics(e, t, idx):
    te, ee = t[idx], e[idx]
    s2 = sigma2_of(ee, te); bs = band_sigma2(ee, te)
    hi = bs[2] + bs[3]                      # components faster than 2*Delta (Delta = 10 s)
    return dict(rmse_hz=float(np.sqrt(np.mean(ee**2))), rmse_demeaned_hz=float(np.std(ee)),
                sigma2=s2, eta_pred=float(np.exp(-s2)),
                **{f'{n}': b for n, b in zip(BNAMES, bs)},
                low_share=float((bs[0]+bs[1])/max(sum(bs), 1e-12)),
                eta_ceiling_nodes10s=float(np.exp(-hi)))

def main(name):
    idxdf = pd.read_csv(f'{name}_index.csv')
    h = h5py.File(f'{name}.h5', 'r')
    N = h['truth'].shape[1]; t = np.arange(N)/FS; T = N/FS
    idx = (t >= 5) & (t < T-5)
    rows = []
    for r in idxdf.itertuples(index=False):
        gt = h['truth'][r.truth_row]; gi = h['input'][r.row]; go = h['output'][r.row]
        ei, eo = gt-gi, gt-go
        mi, mo = metrics(ei, t, idx), metrics(eo, t, idx)
        row = r._asdict()
        row['eta_in_check'] = eta_of(ei, t, idx); row['eta_out_check'] = eta_of(eo, t, idx)
        row.update({f'in_{k}': v for k, v in mi.items()}); row.update({f'out_{k}': v for k, v in mo.items()})
        rows.append(row)
    d = pd.DataFrame(rows)
    d['check_dev_in'] = (d.eta_in_check - d.eta_in).abs(); d['check_dev_out'] = (d.eta_out_check - d.eta_out).abs()
    d['pred_recoverable'] = d.in_eta_ceiling_nodes10s - d.eta_in     # loss attributable to components the 10-s nodes can represent
    d['gain'] = d.eta_out - d.eta_in
    d.to_csv(f'{name}_theory_metrics.csv', index=False)
    g = d.groupby('frontend')
    s = g.agg(n=('gain', 'size'), eta_in=('eta_in', 'mean'), eta_out=('eta_out', 'mean'), gain=('gain', 'mean'),
              in_sigma2_median=('in_sigma2', 'median'), in_low_share_median=('in_low_share', 'median'),
              in_rmse_median_hz=('in_rmse_hz', 'median'), ceiling_mean=('in_eta_ceiling_nodes10s', 'mean'),
              pred_recoverable_mean=('pred_recoverable', 'mean'),
              max_check_dev=('check_dev_in', 'max'))
    s['corr_pred_vs_gain'] = g.apply(lambda x: x.pred_recoverable.corr(x.gain, method='spearman'))
    s.to_csv(f'{name}_theory_summary.csv'); print(s.round(4).to_string())
    print('max |eta recomputed - eta saved| (in/out):', d.check_dev_in.max(), d.check_dev_out.max(),
          ' -> must be < 1e-6; otherwise the export or evaluation window does not match the frozen code.')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'traj_export_X2')
