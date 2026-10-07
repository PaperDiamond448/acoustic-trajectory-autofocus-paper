"""Chinese colour redraw of the manuscript figures (Claude, 2026-10-04).

Colours and line styles follow the original figure set (render_manuscript_figures.py);
only the flowchart (make_fig03_zh_bw.py) is black and white. Reads saved results
only; no experiment is rerun. Outputs: figNN_*_中文.{pdf,svg,png}.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zh_bw_style import CM, SCENE, panel_letter, save  # noqa: E402  (fonts and save only)

OUT = Path(__file__).resolve().parents[1]
SD = OUT / 'source_data'
CUR = OUT.parents[1]
SPEC = CUR.parent / 'phaseD/X3_real/spectra'
WEAK = CUR / '10_论证骨架/实验设计复核_20261004/weak15_peak_correspondence.csv'
FM = 'ADA_local_c04_t30_A'
W2 = 16.5

# palette and styles of the original figure set
COL = {'SMR': '#747A80', 'F01': '#4477AA', 'F02': '#4477AA', 'F04': '#669977', 'F08': '#4477AA',
       'UNB': '#9977AA', 'ADA': '#C5653F'}
LS = {'SMR': (0, (1.2, 1.2)), 'F02': '-', 'F04': (0, (5, 1.5, 1, 1.5)), 'UNB': (0, (4, 1.5)), 'ADA': '-'}
MK = {'SMR': 's', 'F02': 'o', 'F04': 'v', 'UNB': '^', 'ADA': 'D'}
NAME = {'SMR': '局部峰值平滑轨迹', 'F02': '固定 ±0.02 Hz', 'F04': '固定 ±0.04 Hz', 'UNB': '不设修正幅度界', 'ADA': '自适应扩张（本文）'}
KEY = {'SMR': 'SMR', 'F02': 'F02', 'F04': 'F04', 'UNB': 'UNB', FM: 'ADA', 'F01': 'F01', 'F08': 'F08'}
BLACK = '#222222'


def out(name):
    return OUT / f'{name}_中文'


def mline(k, **kw):
    d = dict(color=COL[k], ls=LS.get(k, '-'), marker=MK.get(k, 'o'), mfc=COL[k], mec=COL[k], lw=1.1, ms=4)
    d.update(kw)
    return d


def scene_mark(sc, color):
    return dict(marker='o' if sc == 'S0' else 's', mfc='white' if sc == 'S0' else color, mec=color, color=color)


def errbar(ax, x, m, lo, hi, **kw):
    ax.errorbar(x, m, yerr=[np.asarray(m) - np.asarray(lo), np.asarray(hi) - np.asarray(m)],
                capsize=2, elinewidth=0.8, capthick=0.8, lw=0, ms=4.5, **kw)


def zero(ax):
    ax.axhline(0, color='0.65', lw=0.6, zorder=0)


def scene_legend(ax, loc, color=BLACK):
    h = [Line2D([], [], lw=0, ms=4.5, **scene_mark(s, color), label=SCENE[s]) for s in ('S0', 'S2')]
    ax.legend(handles=h, loc=loc, handletextpad=0.3)


# ---------------------------------------------------------------- fig01
def fig01():
    g = pd.read_csv(SD / 'geometry_curve.csv')
    fig, (a, b) = plt.subplots(1, 2, figsize=(W2 * CM, 6.0 * CM), gridspec_kw=dict(wspace=0.35))
    a.plot([-900, 750], [1000, 1000], color='0.6', lw=1.2)
    a.plot([-560, 0], [1000, 0], color='#4477AA', lw=1.0)
    a.plot([0, 0], [1000, 0], color='0.5', lw=0.8, ls=(0, (1, 1.5)))
    a.annotate('', xy=(-250, 1000), xytext=(-540, 1000),
               arrowprops=dict(arrowstyle='-|>', color=BLACK, lw=1.0, mutation_scale=8))
    a.plot(-560, 1000, 'o', color='#C5653F', ms=6)
    a.plot(0, 1000, 'o', mfc='white', mec='0.4', ms=5)
    a.plot(0, 0, '^', color=BLACK, ms=7)
    a.text(-720, 1130, '运动声源', ha='center', color='#C5653F')
    a.text(-300, 1130, 'v = 5 m/s', ha='center')
    a.text(30, 1080, '最近通过点', ha='left')
    a.text(40, 500, 'd = 1000 m', ha='left')
    a.text(-330, 450, 'R(τ)', ha='right', style='italic', color='#4477AA')
    a.text(60, -40, '水听器', ha='left', va='center')
    a.set_xlim(-950, 800)
    a.set_ylim(-150, 1250)
    a.set_xlabel('沿航迹位置/m')
    a.set_ylabel('与航迹的垂直距离/m')
    panel_letter(a, 'a')
    b.plot(g.time_s, g.received_frequency_hz, color='#C5653F', lw=1.3)
    b.axvline(150, color='0.5', lw=0.6, ls=(0, (1, 1.5)))
    b.axhline(100, color='0.5', lw=0.6, ls=(0, (4, 2)))
    b.text(55, 100.07, '接近', ha='center')
    b.text(245, 99.93, '远离', ha='center')
    b.text(152, 100.17, '最近通过', ha='left', fontsize=7.5)
    b.set_xlim(0, 300)
    b.set_xlabel('接收时间/s')
    b.set_ylabel('接收频率/Hz')
    panel_letter(b, 'b')
    save(fig, out('fig01_geometry'))


# ---------------------------------------------------------------- fig02
def fig02():
    c = pd.read_csv(SD / 'expA_curves.csv')
    s = pd.read_csv(SD / 'mechanism_spectra.csv')
    t21 = pd.read_csv(SD / 'T21_expA_mechanism.csv')
    rA, rB = t21.rmse_hz.iloc[0] * 1e3, t21.rmse_hz.iloc[1] * 1e3
    eA, eB = t21.eta_max.iloc[0], t21.eta_max.iloc[1]
    kA = dict(color='#4477AA', lw=1.3)
    kB = dict(color='#C5653F', lw=0.9)
    fig, axs = plt.subplots(1, 3, figsize=(W2 * CM, 5.4 * CM), gridspec_kw=dict(wspace=0.45))
    axs[0].plot(c.t_s, c.e_A_hz * 1e3, **kA)
    axs[0].plot(c.t_s, c.e_B_hz * 1e3, **kB)
    axs[0].set_ylabel('频率误差/mHz')
    axs[1].plot(c.t_s, c.phi_A_rad / (2 * np.pi), **kA)
    axs[1].plot(c.t_s, c.phi_B_rad / (2 * np.pi), **kB)
    axs[1].set_ylabel('残余相位/周')
    for ax in axs[:2]:
        ax.set_xlim(0, 300)
        ax.set_xlabel('时间/s')
        zero(ax)
    sel = s.frequency_hz.abs() <= 0.03
    axs[2].plot(s.frequency_hz[sel], s.A[sel], **kA)
    axs[2].plot(s.frequency_hz[sel], s.B[sel], **kB)
    axs[2].set_xlabel('残余频率/Hz')
    axs[2].set_ylabel('归一化功率')
    axs[2].set_ylim(0, 1.05)
    for ax, l in zip(axs, 'abc'):
        panel_letter(ax, l, dx=-0.2)
    h = [Line2D([], [], **kA, label=f'误差 A（缓变）：RMSE {rA:.2f} mHz，η = {eA:.3f}'),
         Line2D([], [], **kB, label=f'误差 B（快速交替）：RMSE {rB:.2f} mHz，η = {eB:.3f}')]
    fig.legend(handles=h, loc='upper center', ncol=2, bbox_to_anchor=(0.5, 1.07))
    save(fig, out('fig02_error_structure'))


# ---------------------------------------------------------------- fig04 / figS01
def fig04(metric='eta', name='fig04_knot_spacing', ylab='相干效率 η'):
    d = pd.read_csv(SD / 'D1_summary.csv')
    P = sorted(d.P.unique())
    ctrl = dict(color='0.55', ls=(0, (1, 1.2)), marker='x', ms=4, lw=1.0, mec='0.55')
    fig, axs = plt.subplots(1, 3, figsize=(W2 * CM, 5.8 * CM), gridspec_kw=dict(wspace=0.42))
    for ax, sc, l in zip(axs[:2], ('S0', 'S2'), 'ab'):
        for meth, dx in (('F02', -1.1), ('UNB', 1.1)):
            q = d[(d.scene == sc) & (d.arm == 'scaled') & (d.method == meth)].sort_values('P')
            ax.plot(q.P + dx, q[metric], **mline(meth, lw=0.9))
            errbar(ax, q.P + dx, q[metric], q[metric + '_lo'], q[metric + '_hi'], color=COL[meth], marker='')
        q = d[(d.scene == sc) & (d.method == 'F02') & ((d.arm == 'unscaled') | (d.P == 21))]
        q = q.drop_duplicates('P').sort_values('P')
        ax.plot(q.P, q[metric], **ctrl)
        ax.axvline(31, color='#C5653F', lw=0.7, ls=(0, (3, 2)))
        ax.set_title(SCENE[sc])
        ax.set_ylabel(ylab)
        ax.set_xticks(P)
        ax.set_xlabel('节点数 P')
        panel_letter(ax, l, dx=-0.22)
    q = d[d.scene == 'pooled']
    for arm, meth, st, dx in (('scaled', 'F02', mline('F02', lw=0.9), -1.1), ('scaled', 'UNB', mline('UNB', lw=0.9), 1.1),
                              ('unscaled', 'F02', ctrl, 0)):
        r = q[(q.arm == arm) & (q.method == meth)]
        if arm == 'unscaled':
            r = pd.concat([r, q[(q.arm == 'scaled') & (q.method == 'F02') & (q.P == 21)]])
        axs[2].plot(r.sort_values('P').P + dx, r.sort_values('P').runtime_median_s, **st)
    axs[2].axvline(31, color='#C5653F', lw=0.7, ls=(0, (3, 2)))
    axs[2].set_ylabel('单次求解耗时中位数/s')
    axs[2].set_title('计算量')
    axs[2].set_xticks(P)
    axs[2].set_xlabel('节点数 P')
    panel_letter(axs[2], 'c', dx=-0.22)
    h = [Line2D([], [], **mline('F02'), label='固定 ±0.02 Hz'), Line2D([], [], **mline('UNB'), label='不设修正幅度界'),
         Line2D([], [], **ctrl, label='固定 ±0.02 Hz，正则不随节点缩放'),
         Line2D([], [], color='#C5653F', lw=0.7, ls=(0, (3, 2)), label='选定：P = 31（节点间隔 10 s）')]
    fig.legend(handles=h, loc='upper center', ncol=4, bbox_to_anchor=(0.5, 1.1))
    save(fig, out(name))


# ---------------------------------------------------------------- fig05
def fig05():
    d = pd.read_csv(SD / 'D2_summary.csv')
    keys = ['F01', 'F02', 'F04', 'F08', 'UNB', FM]
    labs = ['±0.01', '±0.02', '±0.04', '±0.08', '不设修正\n幅度界', '自适应\n扩张']
    fig, axs = plt.subplots(1, 2, figsize=(W2 * CM, 5.6 * CM), gridspec_kw=dict(wspace=0.32))
    for ax, (m, sc_, ylab), l in zip(axs, [('gain_eta_vs_F02', 1, '相对固定 ±0.02 Hz 的 Δη'),
                                           ('harm_vs_F02', 100, '实质退化比例/%')], 'ab'):
        for sc, dx in (('S0', -0.14), ('S2', 0.14)):
            q = d[(d.scene == sc) & (d.method.isin(keys))].set_index('method').loc[keys]
            for i, k in enumerate(keys):
                c = COL[KEY[k]]
                errbar(ax, [i + dx], [q[m][k] * sc_], [q[m + '_lo'][k] * sc_], [q[m + '_hi'][k] * sc_], **scene_mark(sc, c))
        zero(ax)
        ax.axvline(4.5, color='0.7', lw=0.6, ls=(0, (3, 2)))
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels(labs, fontsize=7)
        ax.set_xlim(-0.6, 5.6)
        ax.set_xlabel('修正范围/Hz')
        ax.set_ylabel(ylab)
        panel_letter(ax, l, dx=-0.16)
    scene_legend(axs[1], 'upper center')
    save(fig, out('fig05_radius_development'))


# ---------------------------------------------------------------- fig06
def fig06():
    c = pd.read_csv(SD / 'C_cell_statistics.csv')
    c = c[c.method == FM]
    fig, axs = plt.subplots(1, 2, figsize=(W2 * CM, 5.4 * CM), gridspec_kw=dict(wspace=0.3))
    for ax, (m, ylab), l in zip(axs, [('gain_eta_vs_SMR', '相对 LPS 的 Δη'),
                                      ('gain_peak_vs_SMR_db', '相对 LPS 的谱峰增量/dB')], 'ab'):
        for sc, dx in (('S0', -0.13), ('S2', 0.13)):
            q = c[(c.scene == sc) & (c.metric == m)].sort_values('snr_db')
            errbar(ax, q.snr_db + dx, q['mean'], q.lo, q.hi, **scene_mark(sc, COL['ADA']))
        zero(ax)
        ax.set_xticks(range(-20, -13))
        ax.set_xlabel('基带信噪比/dB')
        ax.set_ylabel(ylab)
        panel_letter(ax, l, dx=-0.15)
    scene_legend(axs[0], 'upper right', COL['ADA'])
    save(fig, out('fig06_confirmation_gain'))


# ---------------------------------------------------------------- fig07
def fig07():
    s = pd.read_csv(SD / 'C_summary.csv')
    keys = ['F04', 'UNB', FM]
    labs = ['固定 ±0.04 Hz', '不设修正\n幅度界', '自适应扩张']
    fig, axs = plt.subplots(1, 2, figsize=(W2 * CM, 5.4 * CM), gridspec_kw=dict(wspace=0.32))
    for ax, (m, sc_, ylab), l in zip(axs, [('gain_eta_vs_F02', 1, '相对固定 ±0.02 Hz 的 Δη'),
                                           ('harm_vs_F02', 100, '实质退化比例/%')], 'ab'):
        for sc, dx in (('S0', -0.13), ('S2', 0.13)):
            q = s[(s.scope == sc) & (s.metric == m)].set_index('method').loc[keys]
            for i, k in enumerate(keys):
                c = COL[KEY[k]]
                v = q['mean'][k] * sc_
                errbar(ax, [i + dx], [v], [q.lo[k] * sc_], [q.hi[k] * sc_], **scene_mark(sc, c))
                if m == 'harm_vs_F02':
                    if sc == 'S0':
                        ax.text(i + dx - 0.08, v + 1.5, f'{v:.1f}', fontsize=7, va='bottom', ha='right')
                    else:
                        ax.text(i + dx + 0.08, v, f'{v:.1f}', fontsize=7, va='center', ha='left')
        zero(ax)
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels(labs)
        ax.set_xlim(-0.5, 2.6)
        ax.set_ylabel(ylab)
        panel_letter(ax, l, dx=-0.16)
    scene_legend(axs[0], 'lower left')
    save(fig, out('fig07_confirmation_tradeoff'))


# ---------------------------------------------------------------- fig08
def fig08():
    x = pd.read_csv(SD / 'X1_summary.csv')
    T = [150, 300, 450, 600]
    meths = (('SMR', 'SMR', -36), ('F02', 'F02', -12), ('UNB', 'UNB', 12), ('ADA', FM, 36))
    fig, axs = plt.subplots(1, 3, figsize=(W2 * CM, 5.6 * CM), gridspec_kw=dict(wspace=0.4))
    for ax, sc, l in zip(axs[:2], ('S0', 'S2'), 'ab'):
        for k, meth, dx in meths:
            q = x[(x.scope == sc) & (x.method == meth) & (x.metric == 'eta')].sort_values('duration_s')
            ax.plot(q.duration_s + dx, q['mean'], **mline(k, lw=0.8))
            errbar(ax, q.duration_s + dx, q['mean'], q.lo, q.hi, color=COL[k], marker='')
        ax.set_xlim(90, 660)
        ax.set_title(SCENE[sc])
        ax.set_ylabel('相干效率 η')
        ax.set_xticks(T)
        ax.set_xlabel('积累时长/s')
        panel_letter(ax, l, dx=-0.22)
    for k, meth in (('F02', 'F02'), ('ADA', FM)):
        q = x[(x.scope == 'pooled') & (x.method == meth) & (x.metric == 'runtime_s')].sort_values('duration_s')
        axs[2].plot(q.duration_s, q['median'], **mline(k))
        axs[2].plot(q.duration_s, q['p90'], color=COL[k], lw=0.8, ls=(0, (1, 1.2)), marker=MK[k], mfc='white', mec=COL[k], ms=3)
    axs[2].set_xticks(T)
    axs[2].set_xlabel('积累时长/s')
    axs[2].set_ylabel('单次求解耗时/s')
    axs[2].set_title('计算量')
    axs[2].legend(handles=[Line2D([], [], color=BLACK, lw=1.1, label='中位数'),
                           Line2D([], [], color=BLACK, lw=0.8, ls=(0, (1, 1.2)), label='90% 分位')], loc='upper left', fontsize=7)
    panel_letter(axs[2], 'c', dx=-0.22)
    h = [Line2D([], [], **mline(k), label=NAME[k]) for k in ('SMR', 'F02', 'UNB', 'ADA')]
    fig.legend(handles=h, loc='upper center', ncol=4, bbox_to_anchor=(0.5, 1.08))
    save(fig, out('fig08_duration_gain_cost'))


# ---------------------------------------------------------------- fig09
FE = {'VS': ('VIT–LPS（主链路）', dict(color='#4477AA', ls='-', marker='o', mfc='#4477AA', mec='#4477AA'), -0.015),
      'V0': ('VIT', dict(color='#6B7B8C', ls=(0, (1, 1.2)), marker='D', mfc='#6B7B8C', mec='#6B7B8C'), -0.005),
      'MFT': ('MFT', dict(color='#669977', ls=(0, (4, 1.5)), marker='s', mfc='#669977', mec='#669977'), 0.005),
      'SUV': ('相位连续 TBD', dict(color='#C5653F', ls=(0, (5, 1.5, 1, 1.5)), marker='^', mfc='#C5653F', mec='#C5653F'), 0.015)}


def fig09():
    b = pd.read_csv(SD / 'X2_eta_bins.csv')
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
        lab, st, _ = FE[k]
        ax.plot(curve[k].bin_center, curve[k].gain_eta, lw=1.2, ms=3.8, zorder=3, **st)
        zero(ax)
        ax.set_title(lab, fontsize=7.5, color=st['color'], pad=3)
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.03, 0.35)
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
        st = dict(FE[k][1])
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


# ---------------------------------------------------------------- fig10
GROUP_COL = {'weak': '#C5653F', 'strong': '#4477AA', 'shallow': '#669977'}


def fig10():
    inc = pd.read_csv(SD / 'X3_increments.csv')
    inc = inc[inc.pair == 'VS_FM-SMR']
    wk = pd.read_csv(WEAK)
    near = {(r.tone_hz, r.start_s): r.SMR_track_fraction_outside_nominal_half_hz <= 0.5 for r in wk.itertuples()}
    w = inc[inc.group == 'weak'].sort_values('gain_peak_db').reset_index(drop=True)
    fig, axs = plt.subplots(1, 2, figsize=(W2 * CM, 7.0 * CM), gridspec_kw=dict(wspace=0.55, width_ratios=[1.15, 1]))
    a = axs[0]
    c = GROUP_COL['weak']
    for i, r in w.iterrows():
        on = near[(r.tone_hz, r.segment_start_s)]
        a.plot(r.gain_peak_db, i, 'o', ms=5, mec=c, mfc=c if on else 'white', mew=1.1)
    a.set_yticks(range(len(w)))
    a.set_yticklabels([f'{int(r.tone_hz)} Hz，{int(r.segment_start_s)} s 起' for r in w.itertuples()], fontsize=7)
    med = w.gain_peak_db.median()
    a.axvline(0, color='0.65', lw=0.6)
    a.axvline(med, color=c, lw=0.8, ls=(0, (3, 2)))
    a.text(med + 0.08, len(w) - 0.6, f'中位数 +{med:.2f} dB', fontsize=7, color=c)
    a.set_xlabel('相对 LPS 的最大谱峰增量/dB')
    a.set_title(f'弱线组（{len(w)} 例）')
    a.set_xlim(-0.3, 4.6)
    h = [Line2D([], [], lw=0, marker='o', ms=5, mec=c, mfc=c, label='LPS 轨迹在名义频点 ±0.5 Hz 内'),
         Line2D([], [], lw=0, marker='o', ms=5, mec=c, mfc='white', mew=1.1, label='LPS 轨迹偏离名义频点')]
    a.legend(handles=h, loc='lower right', fontsize=6.5)
    panel_letter(a, 'a', dx=-0.42)
    b = axs[1]
    rng = np.random.default_rng(0)
    groups = [('shallow', '浅源组'), ('strong', '强线组'), ('weak', '弱线组')]
    for j, (g, lab) in enumerate(groups):
        v = inc[inc.group == g].gain_peak_db.to_numpy()
        yj = j + rng.uniform(-0.18, 0.18, len(v))
        b.plot(v, yj, 'o', ms=3.2, mfc=GROUP_COL[g], mec='white', mew=0.4, alpha=0.9)
        m = np.median(v)
        b.plot([m, m], [j - 0.3, j + 0.3], color=BLACK, lw=1.4)
        b.text(4.55, j + 0.42, f'n = {len(v)}，中位 +{m:.2f} dB，{(v > 0).sum()} 例为正', fontsize=6.5,
               va='center', ha='right', color=GROUP_COL[g])
    b.axvline(0, color='0.65', lw=0.6)
    b.set_yticks(range(3))
    b.set_yticklabels([g[1] for g in groups])
    b.set_ylim(-0.5, 2.75)
    b.set_xlim(-0.3, 4.6)
    b.set_xlabel('相对 LPS 的最大谱峰增量/dB')
    b.set_title('全部 105 例（黑竖线为中位数）')
    panel_letter(b, 'b', dx=-0.25)
    save(fig, out('fig10_real_all_cases'))


# ---------------------------------------------------------------- fig11
def spec_db(path, tone):
    d = pd.read_csv(path)
    x = d.frequency_Hz.to_numpy() - tone
    band = np.abs(x) <= 1.5
    ref = d.Periodogram[band].max()
    return x, {m: 10 * np.log10(d[m].to_numpy() / ref) for m in ('Periodogram', 'SMR', 'VS_FM')}, band


def fig11():
    matplotlib.rcParams.update({
        'font.family': ['Times New Roman', 'SimSun', 'Arial'],
        'pdf.fonttype': 42, 'svg.fonttype': 'none',
    })
    cases = [('f100_s900_T300.csv', 100, '100 Hz，900–1200 s\n（两种方法的最大峰均在零频）'),
             ('f133_s1200_T300.csv', 133, '133 Hz，1200–1500 s\n（全带最大峰位置变化）'),
             ('f49_s1200_T300.csv', 49, '49 Hz，1200–1500 s\n（强线）')]
    fig = plt.figure(figsize=(W2 * CM, 12.5 * CM))
    gs = fig.add_gridspec(4, 3, height_ratios=[1, 1, 0.28, 1.7], hspace=0.12, wspace=0.35)
    for j, (fn, tone, title) in enumerate(cases):
        x, P, band = spec_db(SPEC / fn, tone)
        strips = [('SMR', 'LPS', COL['SMR']), ('VS_FM', '自适应', COL['ADA'])]
        top = None
        for r, (m, lab, c) in enumerate(strips):
            ax = fig.add_subplot(gs[r, j], sharex=top) if top else fig.add_subplot(gs[r, j])
            top = top or ax
            ax.plot(x[band], P[m][band], color=c, lw=0.35)
            i = np.argmax(np.where(band, P[m], -np.inf))
            ax.plot(x[i], P[m][i] + 4, 'v', ms=5, mec=c, mfc=c, clip_on=False)
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-40, 16)
            ax.set_yticks([-30, -15, 0, 15])
            if j == 0:
                ax.set_ylabel(f'{lab}/dB', labelpad=4, color=c)
            if r == 0:
                ax.set_title(title, fontsize=7.5)
                ax.tick_params(labelbottom=False)
                panel_letter(ax, 'abc'[j], dx=-0.25, dy=1.0)
            else:
                ax.set_xlabel('残余频率/Hz（全搜索带）')
        z = np.abs(x) <= 0.05
        bot = fig.add_subplot(gs[3, j])
        bot.fill_between(x[z], -40, P['SMR'][z], color=COL['SMR'], alpha=0.3, lw=0, zorder=1)
        bot.plot(x[z], P['SMR'][z], color=COL['SMR'], lw=0.6, zorder=2)
        bot.plot(x[z], P['VS_FM'][z], color=COL['ADA'], lw=1.2, zorder=3)
        bot.axvline(0, ymax=0.68, color='0.6', lw=0.5, ls=(0, (2, 2)), zorder=0)
        n0 = np.abs(x) <= 0.005
        s0, a0 = P['SMR'][n0].max(), P['VS_FM'][n0].max()
        txt = f'±0.005 Hz 内的峰值：\nLPS {s0:+.2f} dB\n自适应 {a0:+.2f} dB'.replace('-', '−')
        bot.text(0.03, 0.97, txt, transform=bot.transAxes, fontsize=6.5, va='top')
        if j == 2:
            bot.text(0.97, 0.55, '两者几乎重合', transform=bot.transAxes, fontsize=6.5, ha='right', color='0.35')
        bot.set_xlim(-0.05, 0.05)
        bot.set_ylim(-25, 22)
        bot.set_xlabel('残余频率/Hz（零频附近）')
        if j == 0:
            bot.set_ylabel('相对未补偿谱峰/dB')
        panel_letter(bot, 'def'[j], dx=-0.25)
    h = [Patch(fc=COL['SMR'], alpha=0.45, ec=COL['SMR'], lw=0.6, label='局部峰值平滑轨迹（LPS）'),
         Line2D([], [], color=COL['ADA'], lw=1.2, label='自适应扩张（本文）'),
         Line2D([], [], lw=0, marker='v', mec=BLACK, mfc=BLACK, ms=5, label='该方法在全搜索带内的最大峰')]
    fig.legend(handles=h, loc='upper center', ncol=3, bbox_to_anchor=(0.5, 1.0), fontsize=7)
    audit_scripts = Path.home() / '.codex' / 'skills' / 'nature-figure' / 'scripts'
    sys.path.insert(0, str(audit_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment
    qa_dir = OUT / '_检查记录_20261005'
    qa_dir.mkdir(exist_ok=True)
    require_matplotlib_panel_alignment(
        fig, json_out=qa_dir / 'fig11.alignment.json', strict=True,
        exemptions=[{
            'panels': ['c', 'f', 'i'], 'checks': ['vertical-gutter'],
            'reason': 'The zero-frequency zoom row is separated from the full-band pair by space for their x-axis labels.',
        }],
    )
    out_stem = out('fig11_real_spectra')
    export_options = dict(facecolor='white', bbox_inches='tight', pad_inches=0.03)
    fig.savefig(f'{out_stem}.pdf', **export_options)
    fig.savefig(f'{out_stem}.svg', **export_options)
    fig.savefig(f'{out_stem}.png', dpi=600, **export_options)
    plt.close(fig)
    print('saved', out_stem.name)


# ---------------------------------------------------------------- fig12
def fig12():
    d = np.loadtxt(SD / 'baseband_f100_600_2100.csv', delimiter=',')
    y = d[:, 0] + 1j * d[:, 1]
    fs, Lw, hop, nfft = 20, 60, 5, 8192
    L, H = Lw * fs, hop * fs
    w = np.hanning(L)
    st = np.arange(0, len(y) - L + 1, H)
    Pm = np.array([np.abs(np.fft.fftshift(np.fft.fft(y[s:s + L] * w, nfft))) ** 2 for s in st]).T
    f = np.fft.fftshift(np.fft.fftfreq(nfft, 1 / fs))
    sel = (f >= -0.25) & (f <= 0.35)
    db = 10 * np.log10(Pm[sel])
    db -= np.median(db)
    t = 600 + (st + L / 2) / fs
    fig = plt.figure(figsize=(W2 * CM, 16.0 * CM))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.1, 1.6, 1.0], hspace=0.42)
    gbc = gs[1].subgridspec(2, 1, height_ratios=[1.0, 0.5], hspace=0.1)
    a = fig.add_subplot(gs[0])
    im = a.imshow(db, origin='lower', aspect='auto', cmap='magma', extent=[t[0], t[-1], f[sel][0], f[sel][-1]],
                  vmin=np.percentile(db, 40), vmax=np.percentile(db, 99.7), interpolation='nearest')
    a.set_xlim(600, 2100)
    a.set_ylabel('频偏/Hz')
    a.set_xlabel('记录时间/s')
    a.set_title('100 Hz 线谱的 LOFAR（显示用 60 s Hann 窗、5 s 步长）', fontsize=7.5)
    cb = fig.colorbar(im, ax=a, pad=0.015, fraction=0.03)
    cb.set_label('相对中位数/dB', fontsize=7)
    cb.ax.tick_params(labelsize=6.5)
    panel_letter(a, 'a', dx=-0.1)
    b = fig.add_subplot(gbc[0])
    dd = fig.add_subplot(gbc[1], sharex=b)
    for k, s0 in enumerate(range(600, 2100, 300)):
        tr = pd.read_csv(SD / f'f100_s{s0}_T300.csv')
        b.plot(tr.time_s, tr.GPS_Hz - 100, color='0.45', lw=0.8, ls=(0, (1, 1.2)), label='GPS 推算（仅作参考）' if k == 0 else None)
        b.plot(tr.time_s, tr.SMR - 100, color=COL['SMR'], lw=3.0, alpha=0.4, solid_capstyle='butt', label='局部峰值平滑轨迹（LPS）' if k == 0 else None)
        b.plot(tr.time_s, tr.VS_FM - 100, color=COL['ADA'], lw=0.9, label='自适应扩张（本文）' if k == 0 else None)
        dd.plot(tr.time_s, (tr.VS_FM - tr.SMR) * 1e3, color=COL['ADA'], lw=0.9)
        for ax in (b, dd):
            if s0 > 600:
                ax.axvline(s0, color='0.85', lw=0.5)
    b.set_ylim(-0.25, 0.35)
    b.set_ylabel('频偏/Hz')
    b.tick_params(labelbottom=False)
    b.legend(loc='upper right', ncol=3, fontsize=7)
    panel_letter(b, 'b', dx=-0.1)
    zero(dd)
    dd.set_ylim(-35, 35)
    dd.set_ylabel('差值/mHz')
    dd.text(0.006, 0.93, '自适应 − LPS', transform=dd.transAxes, fontsize=7, va='top', color=COL['ADA'])
    dd.set_xlabel('记录时间/s（每 300 s 段独立处理）')
    dd.set_xlim(600, 2100)
    panel_letter(dd, 'c', dx=-0.1, dy=0.98)
    for ax in (b, dd):
        pa, pb = a.get_position(), ax.get_position()
        ax.set_position([pa.x0, pb.y0, pa.width, pb.height])
    c = fig.add_subplot(gs[2])
    du = pd.read_csv(SD / 'X3_duration.csv')
    p = du.pivot_table(index=['tone_hz', 'segment_start_s', 'duration_s'], columns='method',
                       values='peak_relative_periodogram_db').reset_index()
    p['gain'] = p.VS_FM - p.SMR
    styles = [((52, 600), '52 Hz，600 s 起', '#4477AA', 'o', -9), ((100, 600), '100 Hz，600 s 起', '#669977', 's', -3),
              ((100, 900), '100 Hz，900 s 起', '#C5653F', '^', 3), ((103, 900), '103 Hz，900 s 起（附近有竞争脊）', '#9977AA', 'D', 9)]
    for (tone, s0), lab, col, mk, dx in styles:
        q = p[(p.tone_hz == tone) & (p.segment_start_s == s0)].sort_values('duration_s')
        c.plot(q.duration_s + dx, q.gain, color=col, marker=mk, mfc=col, mec=col, lw=1.1, ms=4.5, label=lab)
    zero(c)
    c.set_xticks([150, 300, 450, 600])
    c.set_xlabel('积累时长/s（同一起点的嵌套窗口）')
    c.set_ylabel('最大谱峰增量/dB')
    c.legend(loc='upper left', ncol=2, fontsize=7)
    c.set_ylim(-1.0, 5.3)
    panel_letter(c, 'd', dx=-0.1)
    pa, pc = a.get_position(), c.get_position()
    c.set_position([pa.x0, pc.y0, pa.width, pc.height])
    save(fig, out('fig12_real_trajectory_duration'))


# ---------------------------------------------------------------- figS02
def figS02():
    c = pd.read_csv(SD / 'C_cell_statistics.csv')
    c = c[c.method == FM]
    fig, axs = plt.subplots(1, 2, figsize=(W2 * CM, 5.4 * CM), gridspec_kw=dict(wspace=0.3))
    for ax, (m, ylab), l in zip(axs, [('gain_eta_vs_F02', '自适应 − 固定 ±0.02 Hz 的 Δη'),
                                      ('gain_eta_vs_UNB', '自适应 − 不设修正幅度界\n的 Δη')], 'ab'):
        for sc, dx in (('S0', -0.13), ('S2', 0.13)):
            q = c[(c.scene == sc) & (c.metric == m)].sort_values('snr_db')
            errbar(ax, q.snr_db + dx, q['mean'], q.lo, q.hi, **scene_mark(sc, COL['ADA']))
        zero(ax)
        ax.axhline(-0.005, color='#B23A3A', lw=0.7, ls=(0, (3, 2)))
        ax.set_xticks(range(-20, -13))
        ax.set_xlabel('基带信噪比/dB')
        ax.set_ylabel(ylab)
        panel_letter(ax, l, dx=-0.17)
    scene_legend(axs[0], 'upper right', COL['ADA'])
    save(fig, out('figS02_confirmation_paired'))


# ---------------------------------------------------------------- figS03
def figS03():
    e = pd.read_csv(SD / 'E0_phase_corrected_perrecord.csv')
    fig, axs = plt.subplots(1, 2, figsize=(W2 * CM, 5.6 * CM), gridspec_kw=dict(wspace=0.3), sharey=True)
    sty = {('MFT', 'S0'): dict(marker='o', color='#4477AA'), ('MFT', 'S2'): dict(marker='^', color='#4477AA'),
           ('VIT', 'S0'): dict(marker='o', color='#C5653F'), ('VIT', 'S2'): dict(marker='^', color='#C5653F')}
    for ax, (col, xl), l in zip(axs, [('rmse_eval_hz', '频率 RMSE/Hz'), ('rms_slow_eval_T60', '慢误差 RMS（60 s 尺度）/Hz')], 'ab'):
        for (est, sc), st in sty.items():
            q = e[(e.estimator == est) & (e.scene == sc)]
            ax.plot(q[col], q.eta_full, lw=0, ms=3, mew=0, alpha=0.6, label=f'{est}，{SCENE[sc]}', **st)
        ax.set_xscale('log')
        ax.set_xlabel(xl)
        panel_letter(ax, l, dx=-0.15)
        ax.text(0.86 if l == 'b' else 0.9, 0.24, 'MFT 两种场景\n重叠于此', transform=ax.transAxes, fontsize=6.5,
                color='#4477AA', ha='center', va='bottom')
    axs[0].set_ylabel('相干效率 η')
    axs[0].legend(loc='upper right', fontsize=6.5)
    save(fig, out('figS03_frontend_diagnostic'))


if __name__ == '__main__':
    todo = sys.argv[1:] or ['fig01', 'fig02', 'fig04', 'figS01', 'fig05', 'fig06', 'fig07', 'fig08',
                            'fig09', 'fig10', 'fig11', 'fig12', 'figS02', 'figS03']
    for name in todo:
        if name == 'figS01':
            fig04('peak_db', 'figS01_knot_spectral_peak', '观测谱峰/dB')
        else:
            globals()[name]()
