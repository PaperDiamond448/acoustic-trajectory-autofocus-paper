#!/usr/bin/env python3
"""
Computation entries for ledger items R1, R2, R4 (SWellEx-96, frozen X3 outputs; read-only).
Run from this folder:  python ledger_supplement_R.py <repo_root>
Common definitions
  y            : saved 20 Hz complex baseband, phaseD/X3_real/screen_inputs/f{f}_s{s}.mat (300 s, 6000 samples)
  tracks       : phaseD/X3_real/tracks/f{f}_s{s}_T300.csv (absolute Hz); VS_FM = frozen module output after VIT-LPS
  strong set   : 49 64 79 94 112 130 Hz (deep source set 1)
  guided track : f_target * median_k [ VS_FM_k(t) / f_k ] over strong lines k (k != target when target is strong)
  spectrum     : compensate y with 2*pi*cumtrapz(g - fref), rectangular window over all 6000 samples,
                 zero-padded FFT length = smallest power of 2 >= 8N, |FFT|^2/N; dB relative to the max of the
                 uncompensated periodogram within |nu| <= 1.5 Hz (same normalisation as X3).
  background   : median dB over 0.05 < |nu| < 0.5 Hz of the same compensated spectrum
  excess(c,w)  : max dB within |nu - c| <= w, minus background
Outputs: R1_noise_positions.csv, R1_strong94.csv, R2_100Hz.csv, R4_interline.csv, R1_cross_guidance_nu.csv, summary printed.
"""
import sys, numpy as np, pandas as pd
import realtools as rt
root = sys.argv[1] if len(sys.argv) > 1 else '.'
rt.BASE = f'{root}/phaseD/X3_real'
STRONG = [49, 64, 79, 94, 112, 130]
SEG100 = [600, 900, 1200, 1500, 1800]

def comp_spec_db(y, fref, g_abs):
    nu0, S0 = rt.spectrum(y)
    nu, S = rt.spectrum(y*np.exp(-1j*rt.comp_phase(g_abs, fref)))
    Sdb = 10*np.log10(S/S0.max()); bg = np.median(Sdb[(np.abs(nu) > 0.05) & (np.abs(nu) < 0.5)])
    return nu, Sdb, bg

def guided(target, s, exclude_self=True):
    D = [rt.load_tracks(k, s)['VS_FM'].values/k for k in STRONG if not (exclude_self and k == target)]
    return target*np.median(np.array(D), axis=0)

# R1a: noise-only positions around the 100 Hz guided spectrum
rows = []
noise_pos = np.round(np.concatenate([np.arange(-0.45, -0.149, 0.03), np.arange(0.15, 0.451, 0.03)]), 2)
for s in SEG100:
    y, fref = rt.load_y(100, s); nu, Sdb, bg = comp_spec_db(y, fref, guided(100, s))
    for c in noise_pos:
        rows.append(dict(tone_hz=100, start_s=s, position_hz=c, window_hz=0.01, excess_db=Sdb[np.abs(nu-c) <= 0.01].max()-bg))
r1 = pd.DataFrame(rows); r1.to_csv('R1_noise_positions.csv', index=False)
# R1b: 94 Hz at its position predicted from the other five strong lines
rows = []
for s in SEG100:
    y, fref = rt.load_y(94, s); nu, Sdb, bg = comp_spec_db(y, fref, guided(94, s))
    rows.append(dict(tone_hz=94, start_s=s, excess_at_predicted_db=Sdb[np.abs(nu) <= 0.01].max()-bg))
r1b = pd.DataFrame(rows); r1b.to_csv('R1_strong94.csv', index=False)
# R2: 100 Hz predicted position vs observed ridge (ridge position = median offset of the VS_FM track from the guided track)
rows = []
for s in SEG100:
    y, fref = rt.load_y(100, s); g = guided(100, s); tr = rt.load_tracks(100, s)
    t = tr.time_s.values - s; ev = (t >= 5) & (t < 295)
    nu, Sdb, bg = comp_spec_db(y, fref, g)
    off_vs = np.median(tr.VS_FM.values - g); off_suv = np.median(tr.SUV.values - g)
    rows.append(dict(tone_hz=100, start_s=s, excess_at_predicted_db=Sdb[np.abs(nu) <= 0.01].max()-bg,
                     ridge_offset_hz=off_vs, excess_at_ridge_db=Sdb[np.abs(nu-off_vs) <= 0.01].max()-bg,
                     suv_offset_hz=off_suv,
                     vsfm_minus_gps_mean_eval_hz=np.mean((tr.VS_FM.values-tr.GPS_Hz.values)[ev]),
                     vsfm_minus_gps_median_all_hz=np.median(tr.VS_FM.values-tr.GPS_Hz.values)))
y, fref = rt.load_y(136, 900); tr = rt.load_tracks(136, 900)
rows.append(dict(tone_hz=136, start_s=900, ridge_offset_hz=np.median(tr.VS_FM.values-guided(136, 900))))
r2 = pd.DataFrame(rows); r2.to_csv('R2_100Hz.csv', index=False)
# R4: inter-line deviation of each strong line from the scaled median of the other five
rows = []
for f in STRONG:
    for s in range(0, 3000, 300):
        tr = rt.load_tracks(f, s); t = tr.time_s.values - s; ev = (t >= 5) & (t < 295)
        d = tr.VS_FM.values - guided(f, s)
        rows.append(dict(tone_hz=f, start_s=s,
                         rms_median_demeaned_full_mHz=1e3*np.sqrt(np.mean((d-np.median(d))**2)),
                         rms_mean_demeaned_eval_mHz=1e3*np.std(d[ev]),
                         rms_not_demeaned_eval_mHz=1e3*np.sqrt(np.mean(d[ev]**2)),
                         max_abs_median_demeaned_full_mHz=1e3*np.max(np.abs(d-np.median(d)))))
r4 = pd.DataFrame(rows); r4.to_csv('R4_interline.csv', index=False)
# R1c: residual-frequency position of the cross-guided strong-line peak (from first-batch strong_cross.csv)
sc = pd.read_csv(f'{root}/当前主线精选_20261003/13_第一批补充分析_20261007/数据与脚本/strong_cross.csv')
sc[['s', 'target', 'guide', 'nu']].to_csv('R1_cross_guidance_nu.csv', index=False)

print('R1a noise positions: n=%d, median %.2f, p90 %.2f, max %.2f dB' % (len(r1), r1.excess_db.median(), r1.excess_db.quantile(.9), r1.excess_db.max()))
print('R1b 94 Hz at predicted:', r1b.excess_at_predicted_db.round(1).tolist())
print('R1c cross-guided strong-line peak |nu| (Hz): median %.4f, p90 %.4f, p99 %.4f, max %.4f (n=%d pairs)' % tuple(list(np.percentile(np.abs(sc.nu), [50, 90, 99, 100])) + [len(sc)]))
print(r2.round(4).to_string(index=False))
g = r4.groupby('tone_hz').median(numeric_only=True).drop(columns='start_s')
print('R4 per-line median over 10 segments (mHz):'); print(g.round(2).to_string())
