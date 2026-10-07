"""Post-hoc attribution of the maximum observed spectral peak in the 15 weak-line
SWellEx-96 cases (rules fixed beforehand in 归属检查规则.md).

Read-only: uses the saved 20 Hz baseband inputs (exported from the v7.3 MAT files
to raw binary by export_bb.m), the saved compensation tracks, spectra and peak
frequencies. No front end, correction or screening is rerun.

Run:  python -X utf8 peak_attribution.py [baseband_dir]

baseband_dir holds f{tone}_s{start}.bin files written by export_bb.m (float64
little-endian, interleaved real/imag, 6000 samples per 300 s segment). It defaults
to the environment variable PEAK_ATTR_BASEBAND, then to ./baseband next to this
script. Dependencies: numpy, pandas, matplotlib. Inputs also read: phaseD/X3_real
X3_FROZEN_TESTSET.csv, X3_cases.csv, X3_duration.csv, tracks/ and spectra/.
Expected outputs: 实测峰归属_15例.csv, 积累时长窗口归属.csv, 图/*.png; the script
prints the reproduction checks against the screening table and the case table.
"""
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

X3 = Path(__file__).resolve().parents[4] / 'phaseD/X3_real'
OUT = Path(__file__).resolve().parent
BB = Path(sys.argv[1] if len(sys.argv) > 1 and __name__ == '__main__'
          else os.environ.get('PEAK_ATTR_BASEBAND', OUT / 'baseband'))
FS, L, D, NFFT = 20, 200, 20, 8192
ACCEPT, REJECT, WIN, WIN2 = 0.05, 0.10, 0.10, 0.05
METHODS = {'SMR': 'LPS', 'VS_FM': '完整方法', 'F02': '固定±0.02 Hz',
           'MFT': 'MFT', 'MFT_FM': 'MFT+修正', 'SUV': '相位连续TBD', 'SUV_FM': '相位连续TBD+修正'}

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_tone(tone):
    parts = []
    for s in range(0, 3000, 300):
        a = np.fromfile(BB / f'f{tone}_s{s}.bin', dtype='<f8').reshape(-1, 2)
        parts.append(a[:, 0] + 1j * a[:, 1])
    return np.concatenate(parts)


def lofar(y):
    w = np.hanning(L)                      # symmetric Hann, as MATLAB hann(L,'symmetric')
    K = (len(y) - L) // D + 1
    idx = np.arange(L)[:, None] + D * np.arange(K)[None, :]
    S = np.fft.fftshift(np.fft.fft(y[idx] * w[:, None], NFFT, axis=0), axes=0)
    P = 10 * np.log10(np.maximum(np.abs(S) ** 2 / np.sum(w ** 2), np.finfo(float).tiny))
    tc = (np.arange(K) * D + (L - 1) / 2) / FS
    freq = (np.arange(NFFT) - NFFT // 2) * FS / NFFT
    return tc, freq, P


def main():
    test = pd.read_csv(X3 / 'X3_FROZEN_TESTSET.csv')
    weak = test[test.group == 'weak'].sort_values(['tone_hz', 'segment_start_s'])
    cases = pd.read_csv(X3 / 'X3_cases.csv')
    rows, cache = [], {}
    for _, c in weak.iterrows():
        tone, s = int(c.tone_hz), int(c.segment_start_s)
        if tone not in cache:
            cache[tone] = lofar(load_tone(tone))
        tc, freq, P = cache[tone]
        core = np.abs(freq) <= 0.5
        ann = (np.abs(freq) >= 1) & (np.abs(freq) <= 2)
        sel = (tc >= s) & (tc < s + 300)
        pc = P[core][:, sel]
        ridge = freq[core][np.argmax(pc, axis=0)]
        # reproduce the two screening statistics as a check on the LOFAR
        excess = pc.max() - np.median(P[ann][:, sel])
        cont = np.mean(np.abs(ridge - np.median(ridge)) <= 0.2)
        # reference ridge: cubic LS fit on frames counted as continuous
        t = tc[sel]
        keep = np.abs(ridge - np.median(ridge)) <= 0.2
        tn = (t - t.mean()) / 150.0
        coef = np.polyfit(tn[keep], ridge[keep], 3)
        fref = tone + np.polyval(coef, tn)
        fit_rms = np.sqrt(np.mean((tone + ridge[keep] - fref[keep]) ** 2))

        tr = pd.read_csv(X3 / 'tracks' / f'f{tone}_s{s}_T300.csv')
        sp = pd.read_csv(X3 / 'spectra' / f'f{tone}_s{s}_T300.csv')
        cs = cases[(cases.tone_hz == tone) & (cases.segment_start_s == s)].set_index('method')
        gps = np.interp(t, tr.time_s, tr.GPS_Hz)
        row = dict(tone_hz=tone, start_s=s, screen_excess_db=c.peak_excess_dB,
                   screen_excess_repro_db=excess, screen_cont=c.ridge_continuity,
                   screen_cont_repro=cont, ridge_fit_rms_hz=fit_rms,
                   ridge_minus_gps_mean_hz=np.mean(fref - gps),
                   ridge_minus_gps_rms_hz=np.std(fref - gps))
        mapped = {}
        for m in METHODS:
            ftrack = np.interp(t, tr.time_s, tr[m])
            nu = cs.loc[m, 'peak_frequency_hz'] - tone
            mt = ftrack + nu
            mapped[m] = mt
            dev = np.median(np.abs(mt - fref))
            row[f'{m}_peak_resid_hz'] = nu
            row[f'{m}_track_minus_nominal_median_hz'] = np.median(ftrack - tone)
            row[f'{m}_median_dev_hz'] = dev
            row[f'{m}_class'] = ('对应' if dev <= ACCEPT else '不对应' if dev > REJECT else '不确定')
            nubar = np.mean(fref - ftrack)
            r = sp.frequency_Hz.values - tone
            row[f'{m}_ridge_resid_hz'] = nubar
            # NaN when the reference ridge maps outside the saved +-1.5 Hz spectrum
            v1, v2 = sp[m].values[np.abs(r - nubar) <= WIN], sp[m].values[np.abs(r - nubar) <= WIN2]
            row[f'{m}_ridge_peak'] = v1.max() if v1.size else np.nan
            row[f'{m}_ridge_peak_w05'] = v2.max() if v2.size else np.nan
            row[f'{m}_max_peak'] = sp[m].values.max()
        row['gain_max_peak_db'] = 10 * np.log10(row['VS_FM_max_peak'] / row['SMR_max_peak'])
        row['gain_ridge_peak_db'] = 10 * np.log10(row['VS_FM_ridge_peak'] / row['SMR_ridge_peak'])
        row['gain_ridge_peak_w05_db'] = 10 * np.log10(row['VS_FM_ridge_peak_w05'] / row['SMR_ridge_peak_w05'])
        row['gain_case_table_db'] = cs.loc['VS_FM', 'gain_peak_vs_SMR_db']
        row['gain_mft_max_peak_db'] = 10 * np.log10(row['MFT_FM_max_peak'] / row['MFT_max_peak'])
        row['gain_suv_max_peak_db'] = 10 * np.log10(row['SUV_FM_max_peak'] / row['SUV_max_peak'])
        d = np.interp(t, tr.time_s, tr['VS_FM']) - np.interp(t, tr.time_s, tr['SMR'])
        row['corr_minus_lps_mean_mhz'] = 1e3 * d.mean()
        row['corr_minus_lps_maxabs_mhz'] = 1e3 * np.abs(d).max()
        rows.append(row)

        # diagnostic figure
        band = np.abs(freq) <= 1.5
        fig, ax = plt.subplots(figsize=(7.2, 4.0))
        ext = [s, s + 300, tone + freq[band][0], tone + freq[band][-1]]
        Pd = P[band][:, sel]
        ax.imshow(Pd, origin='lower', aspect='auto', extent=ext, cmap='gray_r',
                  vmin=np.percentile(Pd, 50), vmax=np.percentile(Pd, 99.7))
        ax.plot(t, fref, color='tab:green', lw=1.6, label='参照脊线（筛选峰值拟合）')
        ax.plot(t, mapped['SMR'], color='tab:blue', lw=1.2, ls='--',
                label=f"LPS 最大峰映射（{row['SMR_class']}）")
        ax.plot(t, mapped['VS_FM'], color='tab:red', lw=1.2,
                label=f"完整方法最大峰映射（{row['VS_FM_class']}）")
        ax.plot(t, gps, color='tab:purple', lw=1.0, ls=':', label='GPS 推算（参考）')
        ax.plot(t, np.interp(t, tr.time_s, tr['VS_FM']), color='k', lw=0.8, ls='-.',
                label='完整方法补偿轨迹（残余频率 0）')
        ax.axhline(tone - 0.5, color='tab:orange', lw=0.6, ls=':')
        ax.axhline(tone + 0.5, color='tab:orange', lw=0.6, ls=':')
        ax.set_xlabel('时间 / s')
        ax.set_ylabel('频率 / Hz')
        ax.set_title(f'{tone} Hz，{s}–{s + 300} s；最大峰增量 {row["gain_max_peak_db"]:.2f} dB，'
                     f'参照脊线峰值增量 {row["gain_ridge_peak_db"]:.2f} dB', fontsize=9)
        ax.legend(fontsize=7, loc='upper right', framealpha=0.85)
        fig.tight_layout()
        fig.savefig(OUT / '图' / f'f{tone}_s{s}.png', dpi=150)
        plt.close(fig)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / '实测峰归属_15例.csv', index=False, encoding='utf-8-sig')
    cols = ['tone_hz', 'start_s', 'SMR_class', 'VS_FM_class', 'SMR_median_dev_hz',
            'VS_FM_median_dev_hz', 'SMR_peak_resid_hz', 'VS_FM_peak_resid_hz',
            'gain_max_peak_db', 'gain_ridge_peak_db', 'gain_ridge_peak_w05_db',
            'ridge_minus_gps_mean_hz', 'corr_minus_lps_mean_mhz', 'corr_minus_lps_maxabs_mhz']
    pd.set_option('display.width', 250)
    print(df[cols].round(3).to_string(index=False))
    print('\nscreening reproduction max |diff|: excess %.2e dB, continuity %.2e' % (
        np.max(np.abs(df.screen_excess_db - df.screen_excess_repro_db)),
        np.max(np.abs(df.screen_cont - df.screen_cont_repro))))
    print('case-table gain reproduction max |diff|: %.2e dB' % np.max(
        np.abs(df.gain_max_peak_db - df.gain_case_table_db)))
    print('ridge fit rms (Hz): median %.4f, max %.4f' % (df.ridge_fit_rms_hz.median(), df.ridge_fit_rms_hz.max()))


def duration_windows():
    """Same rule for the nested duration windows (150-600 s) of the four groups."""
    dur = pd.read_csv(X3 / 'X3_duration.csv')
    rows, cache = [], {}
    for (tone, s, T), g in dur.groupby(['tone_hz', 'segment_start_s', 'duration_s']):
        if tone not in cache:
            cache[tone] = lofar(load_tone(tone))
        tc, freq, P = cache[tone]
        core = np.abs(freq) <= 0.5
        sel = (tc >= s) & (tc < s + T)
        ridge = freq[core][np.argmax(P[core][:, sel], axis=0)]
        t = tc[sel]
        keep = np.abs(ridge - np.median(ridge)) <= 0.2
        tn = (t - t.mean()) / (T / 2)
        fref = tone + np.polyval(np.polyfit(tn[keep], ridge[keep], 3), tn)
        tr = pd.read_csv(X3 / 'tracks' / f'f{tone}_s{s}_T{T}_duration.csv')
        cs = g.set_index('method')
        row = dict(tone_hz=tone, start_s=s, duration_s=T,
                   gain_max_peak_db=cs.loc['VS_FM', 'gain_peak_vs_SMR_db'])
        for m in ('SMR', 'VS_FM'):
            mt = np.interp(t, tr.time_s, tr[m]) + cs.loc[m, 'peak_frequency_hz'] - tone
            dev = np.median(np.abs(mt - fref))
            row[f'{m}_median_dev_hz'] = dev
            row[f'{m}_class'] = ('对应' if dev <= ACCEPT else '不对应' if dev > REJECT else '不确定')
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / '积累时长窗口归属.csv', index=False, encoding='utf-8-sig')
    print(df.round(3).to_string(index=False))


if __name__ == '__main__':
    main()
    duration_windows()
