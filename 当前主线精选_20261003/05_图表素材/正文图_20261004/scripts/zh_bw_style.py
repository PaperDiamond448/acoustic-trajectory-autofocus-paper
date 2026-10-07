"""Shared Chinese black-and-white figure style (Claude, 2026-10-04).

Chinese text uses SimSun, Latin text, numbers and formulas use Times New Roman.
Matplotlib's mathtext does not fall back to SimSun, so strings that mix Chinese
and $...$ formulas are laid out segment by segment with `rich()`.
Plain strings (no $) may mix Chinese and Latin freely; Greek letters such as
η or Δ should be typed as Unicode characters there.
"""
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

FONT_DIR = Path('C:/Windows/Fonts')
for _f in ['times.ttf', 'timesbd.ttf', 'timesi.ttf', 'timesbi.ttf', 'simsun.ttc', 'simhei.ttf']:
    fm.fontManager.addfont(str(FONT_DIR / _f))

mpl.rcParams.update({
    'font.family': ['Times New Roman', 'SimSun'],
    'font.size': 8,
    'axes.labelsize': 8,
    'axes.titlesize': 8.5,
    'xtick.labelsize': 7.5,
    'ytick.labelsize': 7.5,
    'legend.fontsize': 7.5,
    'mathtext.fontset': 'custom',
    'mathtext.rm': 'Times New Roman',
    'mathtext.it': 'Times New Roman:italic',
    'mathtext.bf': 'Times New Roman:bold',
    'pdf.fonttype': 42,
    'svg.fonttype': 'path',
    'axes.unicode_minus': True,
    'axes.linewidth': 0.6,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
    'xtick.major.size': 2.5,
    'ytick.major.size': 2.5,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'lines.linewidth': 1.0,
    'lines.markersize': 4,
    'legend.frameon': False,
    'savefig.dpi': 600,
})

CM = 1 / 2.54
PT_CM = 2.54 / 72
BOLD = ['Times New Roman', 'SimHei']

# grayscale encodings: (color, linestyle, marker, marker face)
GRAY = {
    'SMR': ('0.55', (0, (1.2, 1.2)), 's', 'white'),
    'F02': ('0.0', '-', 'o', 'white'),
    'F04': ('0.35', (0, (5, 1.5, 1, 1.5)), 'v', 'white'),
    'UNB': ('0.35', (0, (4, 1.5)), '^', '0.35'),
    'ADA': ('0.0', '-', 'D', '0.0'),
}
NAME = {'SMR': 'SMR（起点）', 'F02': '固定 ±0.02 Hz', 'F04': '固定 ±0.04 Hz',
        'UNB': '去盒界', 'ADA': '自适应扩张（本文）'}
SCENE = {'S0': '无干扰', 'S2': '局部邻频干扰'}


def rich(ax, x, y, text, fontsize=8, ha='center', linespacing=1.45, zorder=3, **kw):
    """Draw multi-line text that mixes Chinese and $math$; x,y in data units (cm)."""
    fig = ax.figure
    renderer = fig.canvas.get_renderer()
    lines = text.split('\n')
    lh = fontsize * linespacing * PT_CM
    n = len(lines)
    for k, line in enumerate(lines):
        base = y + (n - 1) / 2 * lh - k * lh - 0.32 * fontsize * PT_CM
        parts = line.split('$')
        objs, widths = [], []
        for i, seg in enumerate(parts):
            if not seg:
                continue
            s = f'${seg}$' if i % 2 else seg
            t = ax.text(0, base, s, fontsize=fontsize, ha='left', va='baseline', zorder=zorder, **kw)
            w = t.get_window_extent(renderer).width / fig.dpi * 2.54
            objs.append(t)
            widths.append(w)
        total = sum(widths)
        x0 = {'center': x - total / 2, 'left': x, 'right': x - total}[ha]
        for t, w in zip(objs, widths):
            t.set_x(x0)
            x0 += w


def panel_letter(ax, letter, dx=-0.12, dy=1.04):
    ax.text(dx, dy, f'({letter})', transform=ax.transAxes, fontsize=8.5,
            va='bottom', ha='left')


def save(fig, out_stem):
    out_stem = Path(out_stem)
    kw = dict(facecolor='white', bbox_inches='tight', pad_inches=0.03)
    for ext in ('pdf', 'svg'):
        fig.savefig(f'{out_stem}.{ext}', **kw)
    fig.savefig(f'{out_stem}.png', dpi=600, **kw)
    plt.close(fig)
    print('saved', out_stem.name)
