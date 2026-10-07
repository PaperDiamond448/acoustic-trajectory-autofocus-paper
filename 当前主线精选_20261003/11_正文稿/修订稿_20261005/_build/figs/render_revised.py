"""Revised figures for the 2026-10-05 revision (Claude).

Reuses the style and helpers of 05_图表素材/正文图_20261004/scripts/render_zh.py and
reads saved results only; no experiment is rerun. Outputs go to this folder, the
original figure files are not touched.

- fig09 (manuscript Fig. 7 after reordering): per-bin 95% intervals from a
  seed-cluster bootstrap (seeds resampled within scene), and n per bin printed to
  fig09_bin_counts.csv for the appendix table.
- fig10: weak-case markers by post-hoc peak attribution (补充分析_实测峰归属).
- fig11: 133 Hz column relabelled; mapped frequencies of the two maxima annotated.
- fig12: duration windows whose maximum peak is not on the screened ridge drawn hollow.
- manuscript Fig. 11 (figS04) and the top row of Fig. 12 (fig11): 10 s LOFAR with the screened ridge and the mapped maxima
  (the time-frequency data are cached in source_data/ on first run).

Run:  python -X utf8 render_revised.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ORIG = Path(r'D:/论文集/当前主线精选_20261003/05_图表素材/正文图_20261004/scripts')
sys.path.insert(0, str(ORIG))
import render_zh as R  # noqa: E402  (fonts, palette, helpers)
from render_zh import plt, Line2D, Patch, CM, W2, COL, BLACK, SD, SPEC, panel_letter, save, zero, errbar  # noqa: E402

HERE = Path(__file__).resolve().parent
ATTR = HERE.parents[1] / '补充分析_实测峰归属'
X2REC = Path(r'D:/论文集/phaseD/X2_frontend/X2_records.csv')


def out(name):
    return HERE / f'{name}_中文_修订'


def bin_ci(reps=2000, seed=20261005):
    x = pd.read_csv(X2REC)
    edges = np.round(np.arange(0, 1.01, 0.1), 10)
    x['bin'] = np.clip(np.digitize(x.eta_in, edges) - 1, 0, 9)
    rng = np.random.default_rng(seed)
    rows = []
    for fe, g in x.groupby('frontend'):
        seeds = {sc: gg.seed.unique() for sc, gg in g.groupby('scene')}
        by_seed = {s: gg for s, gg in g.groupby('seed')}
        boot = np.full((reps, 10), np.nan)
        for r in range(reps):
            pick = np.concatenate([rng.choice(v, len(v), replace=True) for v in seeds.values()])
            d = pd.concat([by_seed[s] for s in pick])
            m = d.groupby('bin').gain_eta.mean()
            boot[r, m.index.to_numpy()] = m.to_numpy()
        for b in range(10):
            gb = g[g.bin == b]
            if len(gb) == 0:
                continue
            lo, hi = np.nanpercentile(boot[:, b], [2.5, 97.5])
            rows.append(dict(frontend=fe, bin_left=edges[b], bin_center=edges[b] + 0.05, n=len(gb),
                             gain_eta=gb.gain_eta.mean(), lo=lo, hi=hi))
    df = pd.DataFrame(rows)
    df.to_csv(HERE / 'fig09_bin_counts.csv', index=False, encoding='utf-8-sig')
    return df


def fig09():
    b = bin_ci()
    ref = pd.read_csv(SD / 'X2_eta_bins.csv')
    chk = b.merge(ref, on=['frontend', 'bin_center'], suffixes=('', '_ref'))
    assert (chk.n == chk.n_ref).all() and np.allclose(chk.gain_eta, chk.gain_eta_ref), 'binning differs'
    p = pd.read_csv(SD / 'X2_pooled.csv')
    keys = ['VS', 'V0', 'MFT', 'SUV']
    curve = {k: b[(b.frontend == k) & (b.n >= 20)].sort_values('bin_center') for k in keys}
    fig = plt.figure(figsize=(W2 * CM, 8.4 * CM))
    outer = fig.add_gridspec(1, 2, width_ratios=[1.75, 1], wspace=0.32)
    inner = outer[0].subgridspec(2, 2, hspace=0.42, wspace=0.16)
    first = None
    for n, k in enumerate(keys):
        ax = fig.add_subplot(inner[n // 2, n % 2], sharex=first, sharey=first)
        first = first or ax
        for o in keys:
            if o != k:
                ax.plot(curve[o].bin_center, curve[o].gain_eta, color='0.8', lw=0.8, zorder=1)
        lab, st, _ = R.FE[k]
        c = curve[k]
        ax.fill_between(c.bin_center, c.lo, c.hi, color=st['color'], alpha=0.18, lw=0, zorder=2)
        ax.plot(c.bin_center, c.gain_eta, lw=1.2, ms=3.8, zorder=3, **st)
        zero(ax)
        ax.set_title(lab, fontsize=7.5, color=st['color'], pad=3)
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.03, 0.38)
        ax.set_xticks([0, 0.5, 1])
        ax.set_xticklabels(['0', '0.5', '1'])
        if n % 2:
            ax.tick_params(labelleft=False)
        else:
            ax.set_ylabel('模块带来的 Δη')
        if n // 2:
            ax.set_xlabel('修正前的相干效率 η')
        else:
            ax.tick_params(labelbottom=False)
        panel_letter(ax, 'abcd'[n], dx=-0.05 if n % 2 else -0.3, dy=1.02)
    ax = fig.add_subplot(outer[1])
    q = p[p.group == 'all'].set_index('frontend').loc[keys]
    for i, k in enumerate(keys):
        st = dict(R.FE[k][1])
        st.pop('ls')
        errbar(ax, [i], [q.equal_cell_mean[k]], [q.lo[k]], [q.hi[k]], **st)
        ax.text(i + 0.14, q.equal_cell_mean[k], f'{q.equal_cell_mean[k]:.3f}', fontsize=7, va='center')
    zero(ax)
    ax.set_xticks(range(4))
    ax.set_xticklabels(['VIT–LPS', 'VIT', 'MFT', '相位连续\nTBD'])
    ax.set_xlim(-0.5, 3.75)
    ax.set_ylabel('全部记录的平均 Δη')
    ax.set_title('全部 1400 条记录', fontsize=7.5, pad=3)
    panel_letter(ax, 'e', dx=-0.25, dy=1.02)
    save(fig, out('fig09_frontend_generality'))


ATTR_STYLE = {'对应': dict(mfc='fill', label='与筛选脊线一致（8 例）'),
              '不确定': dict(mfc='half', label='不确定，中位偏差 0.05–0.10 Hz（1 例）'),
              '不对应': dict(mfc='white', label='与筛选脊线不一致（6 例）')}


def fig10():
    inc = pd.read_csv(SD / 'X3_increments.csv')
    inc = inc[inc.pair == 'VS_FM-SMR']
    at = pd.read_csv(ATTR / '实测峰归属_15例.csv')
    cls = {(r.tone_hz, r.start_s): r.VS_FM_class for r in at.itertuples()}
    w = inc[inc.group == 'weak'].sort_values('gain_peak_db').reset_index(drop=True)
    fig, axs = plt.subplots(1, 2, figsize=(W2 * CM, 7.0 * CM), gridspec_kw=dict(wspace=0.55, width_ratios=[1.15, 1]))
    a = axs[0]
    c = R.GROUP_COL['weak']
    for i, r in w.iterrows():
        k = cls[(r.tone_hz, r.segment_start_s)]
        if k == '不确定':
            a.plot(r.gain_peak_db, i, 'o', ms=5, mec=c, mfc=c, mew=1.1, fillstyle='left', markerfacecoloralt='white')
        else:
            a.plot(r.gain_peak_db, i, 'o', ms=5, mec=c, mfc=c if k == '对应' else 'white', mew=1.1)
    a.set_yticks(range(len(w)))
    a.set_yticklabels([f'{int(r.tone_hz)} Hz，{int(r.segment_start_s)} s 起' for r in w.itertuples()], fontsize=7)
    on = [r.gain_peak_db for r in w.itertuples() if cls[(r.tone_hz, r.segment_start_s)] == '对应']
    med_all, med_on = w.gain_peak_db.median(), float(np.median(on))
    a.axvline(0, color='0.65', lw=0.6)
    a.axvline(med_on, color=c, lw=0.8, ls=(0, (3, 2)))
    a.text(med_on + 0.1, 5.5, f'实心 8 例中位 +{med_on:.2f} dB\n全部 15 例中位 +{med_all:.2f} dB',
           fontsize=6.5, color=c, va='center')
    a.set_xlabel('相对 LPS 的最大谱峰增量/dB')
    a.set_title(f'弱线组（{len(w)} 例）')
    a.set_xlim(-0.3, 4.6)
    h = [Line2D([], [], lw=0, marker='o', ms=5, mec=c, mfc=c, label=ATTR_STYLE['对应']['label']),
         Line2D([], [], lw=0, marker='o', ms=5, mec=c, mfc=c, fillstyle='left', markerfacecoloralt='white',
                label=ATTR_STYLE['不确定']['label']),
         Line2D([], [], lw=0, marker='o', ms=5, mec=c, mfc='white', mew=1.1, label=ATTR_STYLE['不对应']['label'])]
    a.legend(handles=h, loc='lower right', fontsize=6.3)
    panel_letter(a, 'a', dx=-0.42)
    b = axs[1]
    rng = np.random.default_rng(0)
    groups = [('shallow', '浅源组'), ('strong', '强线组'), ('weak', '弱线组')]
    for j, (g, lab) in enumerate(groups):
        v = inc[inc.group == g].gain_peak_db.to_numpy()
        yj = j + rng.uniform(-0.18, 0.18, len(v))
        b.plot(v, yj, 'o', ms=3.2, mfc=R.GROUP_COL[g], mec='white', mew=0.4, alpha=0.9)
        m = np.median(v)
        b.plot([m, m], [j - 0.3, j + 0.3], color=BLACK, lw=1.4)
        b.text(4.55, j + 0.42, f'n = {len(v)}，中位 +{m:.2f} dB，{(v > 0).sum()} 例为正', fontsize=6.5,
               va='center', ha='right', color=R.GROUP_COL[g])
    b.axvline(0, color='0.65', lw=0.6)
    b.set_yticks(range(3))
    b.set_yticklabels([g[1] for g in groups])
    b.set_ylim(-0.5, 2.75)
    b.set_xlim(-0.3, 4.6)
    b.set_xlabel('相对 LPS 的最大谱峰增量/dB')
    b.set_title('全部 105 例（黑竖线为中位数）')
    panel_letter(b, 'b', dx=-0.25)
    save(fig, out('fig10_real_all_cases'))


# ---------------------------------------------------------------- time-frequency mapping
X3 = Path(r'D:/论文集/phaseD/X3_real')
SRCD = HERE / 'source_data'
TF = dict(ridge='#669977', lps='#4F555B', ada=COL['ADA'], edge='0.35', gps='#9977AA')
CLASS = {'对应': '一致', '不确定': '不确定', '不对应': '不一致'}


def case_tf(tone, s):
    """LOFAR (screening settings) around one case, screened ridge and mapped maxima.

    Cached in source_data/ as float32 with every 4th frequency bin (0.0098 Hz,
    well inside the 0.2 Hz Hann mainlobe), so the figure rebuilds without MATLAB.
    """
    SRCD.mkdir(exist_ok=True)
    f = SRCD / f'tf_f{tone}_s{s}.npz'
    if f.exists():
        return dict(np.load(f))
    import matplotlib
    keep_rc = matplotlib.rcParams.copy()
    sys.path.insert(0, str(ATTR))
    import peak_attribution as PA  # sets its own font and minus-sign options
    matplotlib.rcParams.update(keep_rc)
    tc, freq, P = PA.lofar(PA.load_tone(tone))
    sel = (tc >= s) & (tc < s + 300)
    t = tc[sel]
    core = np.abs(freq) <= 0.5
    ridge = freq[core][np.argmax(P[core][:, sel], axis=0)]
    keep = np.abs(ridge - np.median(ridge)) <= 0.2
    tn = (t - t.mean()) / 150.0
    fsc = tone + np.polyval(np.polyfit(tn[keep], ridge[keep], 3), tn)
    band = np.where(np.abs(freq) <= 3.5)[0][::4]
    tr = pd.read_csv(X3 / 'tracks' / f'f{tone}_s{s}_T300.csv')
    cs = pd.read_csv(X3 / 'X3_cases.csv')
    cs = cs[(cs.tone_hz == tone) & (cs.segment_start_s == s)].set_index('method')
    tl, ta = np.interp(t, tr.time_s, tr.SMR), np.interp(t, tr.time_s, tr.VS_FM)
    d = dict(t=t, f=tone + freq[band], P=P[band][:, sel].astype(np.float32), fsc=fsc,
             map_lps=tl + cs.loc['SMR', 'peak_frequency_hz'] - tone,
             map_ada=ta + cs.loc['VS_FM', 'peak_frequency_hz'] - tone,
             trk_ada=ta, gps=np.interp(t, tr.time_s, tr.GPS_Hz), tone=np.array(tone), start=np.array(s))
    np.savez_compressed(f, **d)
    return d


def tf_panel(ax, d, ylim, gps=False, lw=1.0):
    m = (d['f'] >= ylim[0]) & (d['f'] <= ylim[1])
    Pd = d['P'][m] - np.median(d['P'][m])
    ax.imshow(Pd, origin='lower', aspect='auto', cmap='gray_r', interpolation='nearest',
              extent=[d['t'][0], d['t'][-1], d['f'][m][0], d['f'][m][-1]],
              vmin=np.percentile(Pd, 55), vmax=np.percentile(Pd, 99.7))
    tone = float(d['tone'])
    for e in (tone - 1.5, tone + 1.5):
        ax.axhline(e, color=TF['edge'], lw=0.5, ls=(0, (1, 1.5)))
    if gps:
        ax.plot(d['t'], d['gps'], color=TF['gps'], lw=0.7, ls=(0, (1, 1)))
    ax.plot(d['t'], d['fsc'], color=TF['ridge'], lw=1.5 * lw)
    ax.plot(d['t'], d['trk_ada'], color=TF['ada'], lw=0.7 * lw, ls=(0, (1, 1.2)))
    ax.plot(d['t'], d['map_lps'], color=TF['lps'], lw=1.1 * lw, ls=(0, (4, 2)))
    ax.plot(d['t'], d['map_ada'], color=TF['ada'], lw=1.0 * lw)
    ax.set_ylim(*ylim)
    ax.set_xlim(d['t'][0] - 5, d['t'][0] + 300)


def tf_handles(gps=False):
    h = [Line2D([], [], color=TF['ridge'], lw=1.5, label='筛选脊线'),
         Line2D([], [], color=TF['lps'], lw=1.1, ls=(0, (4, 2)), label='LPS 最大峰的映射'),
         Line2D([], [], color=TF['ada'], lw=1.0, label='自适应最大峰的映射'),
         Line2D([], [], color=TF['ada'], lw=0.7, ls=(0, (1, 1.2)), label='自适应补偿轨迹（残余频率 0）'),
         Line2D([], [], color=TF['edge'], lw=0.5, ls=(0, (1, 1.5)), label='±1.5 Hz 搜索带边缘')]
    if gps:
        h.append(Line2D([], [], color=TF['gps'], lw=0.7, ls=(0, (1, 1)), label='GPS 推算（参考）'))
    return h


def figS04():
    at = pd.read_csv(ATTR / '实测峰归属_15例.csv').sort_values(['tone_hz', 'start_s'])
    fig, axs = plt.subplots(5, 3, figsize=(W2 * CM, 22.5 * CM), gridspec_kw=dict(hspace=0.55, wspace=0.32))
    for ax, r in zip(axs.flat, at.itertuples()):
        d = case_tf(int(r.tone_hz), int(r.start_s))
        tone = float(d['tone'])
        lines = np.concatenate([d['fsc'], d['map_lps'], d['map_ada'], d['trk_ada']])
        lo = max(tone - 3.45, min(tone - 1.5, lines.min()) - 0.2)
        hi = min(tone + 3.45, max(tone + 1.5, lines.max()) + 0.2)
        tf_panel(ax, d, (lo, hi), gps=True, lw=0.85)
        ax.set_title(f'{int(r.tone_hz)} Hz，{int(r.start_s)}–{int(r.start_s) + 300} s（{CLASS[r.VS_FM_class]}）',
                     fontsize=7, pad=2.5)
        ax.tick_params(labelsize=6.5)
    for ax in axs[-1]:
        ax.set_xlabel('记录时间/s', fontsize=7)
    for ax in axs[:, 0]:
        ax.set_ylabel('频率/Hz', fontsize=7)
    fig.legend(handles=tf_handles(gps=True), loc='upper center', ncol=3, bbox_to_anchor=(0.5, 0.935), fontsize=6.8)
    save(fig, out('fig11_real_peak_mapping'))


def fig11():
    import matplotlib
    matplotlib.rcParams.update({'font.family': ['Times New Roman', 'SimSun', 'Arial'],
                                'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    cases = [('f100_s900_T300.csv', 100, '100 Hz，900–1200 s\n（两种方法的最大峰均在零频）'),
             ('f133_s1200_T300.csv', 133, '133 Hz，1200–1500 s\n（前端轨迹沿搜索带下沿）'),
             ('f49_s1200_T300.csv', 49, '49 Hz，1200–1500 s\n（强线）')]
    notes = {(1, 'SMR'): '映射至 133 Hz 筛选脊线', (1, 'VS_FM'): '映射至约 130.0 Hz'}
    starts = {100: 900, 133: 1200, 49: 1200}
    ylims = {100: (98.4, 101.6), 133: (129.6, 134.6), 49: (47.4, 50.6)}
    fig = plt.figure(figsize=(W2 * CM, 18.0 * CM))
    gs = fig.add_gridspec(6, 3, height_ratios=[1.45, 0.42, 1, 1, 0.28, 1.7], hspace=0.12, wspace=0.35)
    for j, (fn, tone, title) in enumerate(cases):
        d = case_tf(tone, starts[tone])
        tfa = fig.add_subplot(gs[0, j])
        tf_panel(tfa, d, ylims[tone])
        tfa.set_title(title, fontsize=7.5)
        tfa.set_xlabel('记录时间/s')
        tfa.set_xticks([starts[tone], starts[tone] + 150, starts[tone] + 300])
        if j == 0:
            tfa.set_ylabel('频率/Hz')
        if tone == 133:
            for y, txt in ((130.0, '130 Hz 强线'), (131.5, '补偿轨迹'), (133.25, '筛选脊线')):
                tfa.text(starts[tone] + 295, y + 0.12, txt, fontsize=6, ha='right', va='bottom', color='0.15')
        panel_letter(tfa, 'abc'[j], dx=-0.25, dy=1.0)
        x, P, band = R.spec_db(SPEC / fn, tone)
        strips = [('SMR', 'LPS', COL['SMR']), ('VS_FM', '自适应', COL['ADA'])]
        top = None
        for r, (m, lab, c) in enumerate(strips):
            ax = fig.add_subplot(gs[r + 2, j], sharex=top) if top else fig.add_subplot(gs[r + 2, j])
            top = top or ax
            ax.plot(x[band], P[m][band], color=c, lw=0.35)
            i = np.argmax(np.where(band, P[m], -np.inf))
            ax.plot(x[i], P[m][i] + 4, 'v', ms=5, mec=c, mfc=c, clip_on=False)
            if (j, m) in notes:
                ha = 'right' if x[i] > 0 else 'left'
                ax.text(x[i] + (-0.08 if x[i] > 0 else 0.08), 11.5, notes[(j, m)], fontsize=6.3, ha=ha,
                        va='center', color=c)
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-40, 16)
            ax.set_yticks([-30, -15, 0, 15])
            if j == 0:
                ax.set_ylabel(f'{lab}/dB', labelpad=4, color=c)
            if r == 0:
                ax.tick_params(labelbottom=False)
                panel_letter(ax, 'def'[j], dx=-0.25, dy=1.0)
            else:
                ax.set_xlabel('残余频率/Hz（全搜索带）')
        z = np.abs(x) <= 0.05
        bot = fig.add_subplot(gs[5, j])
        bot.fill_between(x[z], -40, P['SMR'][z], color=COL['SMR'], alpha=0.3, lw=0, zorder=1)
        bot.plot(x[z], P['SMR'][z], color=COL['SMR'], lw=0.6, zorder=2)
        bot.plot(x[z], P['VS_FM'][z], color=COL['ADA'], lw=1.2, zorder=3)
        bot.axvline(0, ymax=0.68, color='0.6', lw=0.5, ls=(0, (2, 2)), zorder=0)
        n0 = np.abs(x) <= 0.005
        s0, a0 = P['SMR'][n0].max(), P['VS_FM'][n0].max()
        txt = f'±0.005 Hz 内的峰值：\nLPS {s0:+.2f} dB\n自适应 {a0:+.2f} dB'.replace('-', '−')
        bot.text(0.03, 0.97, txt, transform=bot.transAxes, fontsize=6.5, va='top')
        if j == 1:
            bot.text(0.97, 0.70, '零频对应补偿轨迹\n（约 131.5 Hz）', transform=bot.transAxes, fontsize=6.3,
                     ha='right', va='center', color='0.35')
        if j == 2:
            bot.text(0.97, 0.55, '两者几乎重合', transform=bot.transAxes, fontsize=6.5, ha='right', color='0.35')
        bot.set_xlim(-0.05, 0.05)
        bot.set_ylim(-25, 22)
        bot.set_xlabel('残余频率/Hz（零频附近）')
        if j == 0:
            bot.set_ylabel('相对未补偿谱峰/dB')
        panel_letter(bot, 'ghi'[j], dx=-0.25)
    h = [Patch(fc=COL['SMR'], alpha=0.45, ec=COL['SMR'], lw=0.6, label='局部峰值平滑轨迹（LPS）'),
         Line2D([], [], color=COL['ADA'], lw=1.2, label='自适应扩张（本文）'),
         Line2D([], [], lw=0, marker='v', mec=BLACK, mfc=BLACK, ms=5, label='该方法在全搜索带内的最大峰')]
    fig.legend(handles=h, loc='upper center', ncol=3, bbox_to_anchor=(0.5, 1.022), fontsize=7)
    fig.legend(handles=tf_handles(), loc='upper center', ncol=3, bbox_to_anchor=(0.5, 0.996), fontsize=6.8)
    stem = out('fig12_real_spectra')
    opts = dict(facecolor='white', bbox_inches='tight', pad_inches=0.03)
    fig.savefig(f'{stem}.pdf', **opts)
    fig.savefig(f'{stem}.png', dpi=600, **opts)
    plt.close(fig)


def fig12():
    # panels (a)-(c) unchanged: draw with the original function, then redo (d)
    du_attr = pd.read_csv(ATTR / '积累时长窗口归属.csv')
    cls = {(r.tone_hz, r.start_s, r.duration_s): r.VS_FM_class for r in du_attr.itertuples()}
    orig_save = R.save
    captured = {}

    def grab(fig, path):
        captured['fig'] = fig
    R.save = grab
    try:
        R.fig12()
    finally:
        R.save = orig_save
    fig = captured['fig']
    c = [a for a in fig.axes if a.get_xlabel().startswith('积累时长')][0]
    for ln in list(c.lines):
        ln.remove()
    if c.get_legend():
        c.get_legend().remove()
    du = pd.read_csv(SD / 'X3_duration.csv')
    p = du.pivot_table(index=['tone_hz', 'segment_start_s', 'duration_s'], columns='method',
                       values='peak_relative_periodogram_db').reset_index()
    p['gain'] = p.VS_FM - p.SMR
    styles = [((52, 600), '52 Hz，600 s 起', '#4477AA', 'o', -9),
              ((100, 600), '100 Hz，600 s 起', '#669977', 's', -3),
              ((100, 900), '100 Hz，900 s 起（与上组重叠）', '#C5653F', '^', 3),
              ((103, 900), '103 Hz，900 s 起（附近有竞争脊）', '#9977AA', 'D', 9)]
    handles = []
    for (tone, s0), lab, col, mk, dx in styles:
        q = p[(p.tone_hz == tone) & (p.segment_start_s == s0)].sort_values('duration_s')
        c.plot(q.duration_s + dx, q.gain, color=col, lw=1.0, zorder=2)
        for r in q.itertuples():
            k = cls[(tone, s0, r.duration_s)]
            style = dict(mfc=col) if k == '对应' else dict(mfc='white') if k == '不对应' else \
                dict(mfc=col, fillstyle='left', markerfacecoloralt='white')
            c.plot(r.duration_s + dx, r.gain, marker=mk, ms=4.8, mec=col, mew=1.0, lw=0, zorder=3, **style)
        handles.append(Line2D([], [], color=col, marker=mk, mfc=col, mec=col, lw=1.0, ms=4.5, label=lab))
    handles.append(Line2D([], [], lw=0, marker='o', ms=4.5, mec='0.3', mfc='0.3', fillstyle='left',
                          markerfacecoloralt='white', mew=1.0, label='半实心：与筛选脊线的对应不确定'))
    handles.append(Line2D([], [], lw=0, marker='o', ms=4.5, mec='0.3', mfc='white', mew=1.0,
                          label='空心：与筛选脊线不一致'))
    zero(c)
    c.legend(handles=handles, loc='upper left', ncol=2, fontsize=6.6)
    c.set_ylim(-1.0, 7.0)
    save(fig, out('fig13_real_trajectory_duration'))


if __name__ == '__main__':
    for name in sys.argv[1:] or ['fig09', 'fig10', 'fig11', 'fig12', 'figS04']:
        globals()[name]()
        print('done', name)
