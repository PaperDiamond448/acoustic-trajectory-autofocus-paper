"""Fig. 3 processing flow, Chinese, black and white (Claude, 2026-10-04).

Redraw of fig03_adaptive_method. Content follows the frozen Phase D method
(ADA_local_c04_t30_A). Outputs: fig03_流程图_中文黑白.{pdf,svg,png}.
"""
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, Polygon, FancyArrowPatch, Rectangle

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from zh_bw_style import rich

CM = 1 / 2.54
W, H = 16.5, 13.4
FS = 8.5
LW = 0.8
fig = plt.figure(figsize=(W * CM, H * CM), dpi=300)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis('off')


def box(x, y, w, h, text, fs=FS):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle='round,pad=0,rounding_size=0.08',
                                fc='white', ec='black', lw=LW, zorder=2))
    rich(ax, x, y, text, fontsize=fs)


def diamond(x, y, hw, hh, text):
    ax.add_patch(Polygon([(x, y + hh), (x + hw, y), (x, y - hh), (x - hw, y)],
                         closed=True, fc='white', ec='black', lw=LW, zorder=2))
    rich(ax, x, y, text, fontsize=FS)


def arrow(p0, p1):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>', mutation_scale=8,
                                 lw=LW, color='black', shrinkA=0, shrinkB=0,
                                 zorder=1))


def line(*pts):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color='black', lw=LW, solid_capstyle='butt', zorder=1)


def label(x, y, text, ha='center'):
    rich(ax, x, y, text, fontsize=FS, ha=ha)


XC, WC = 8.25, 6.6          # module column
XR, WR = 13.85, 4.0         # right column
XL, WL = 2.4, 3.8           # input box

# input row
box(XL, 12.75, WL, 0.8, '复基带记录 $y[n]$')
box(XC, 12.75, WC, 1.0, '轨迹前端（VIT、MFT 或相位连续 TBD）\n'
    r'给出锚轨迹 $g_A(t)$ 与起点 $\mathbf{u}_{\mathrm{s}}$')
arrow((XL + WL / 2, 12.75), (XC - WC / 2, 12.75))

# module frame
ax.add_patch(Rectangle((4.65, 3.8), 16.15 - 4.65, 11.85 - 3.8, fc='none',
                       ec='black', lw=LW, ls=(0, (4, 2.5)), zorder=0))
ax.text(XR, 11.3, '相干驱动频率轨迹自聚焦', ha='center', va='center',
        fontsize=9, fontfamily=['Times New Roman', 'SimHei'])

box(XC, 11.05, WC, 1.0,
    r'① 频率修正：$g_{\mathbf{u}}(t)=g_A(t)+r\,\mathbf{B}(t)\,\mathbf{u}$' '\n'
    r'节点间隔 10 s，初始范围 $|u_p|\leq 1$（±0.02 Hz）')
box(XC, 9.85, WC, 0.75,
    r'② 相位积分：$\phi_{\mathbf{u}}(t)=\phi_A(t)+\mathbf{h}(t)^{\mathrm{T}}\mathbf{u}$（关于 $\mathbf{u}$ 仿射）')
box(XC, 8.40, WC, 1.35,
    '③ 目标：分块相干能量 − 平滑罚，解析梯度\n'
    r'分阶段 SQP，块长 20、60、$T-10$ s' '\n'
    r'按全长目标 $J$ 选出 $\mathbf{u}^{(0)}$')
diamond(XC, 6.65, 2.2, 0.75, '④ 最长边界驻留\n≥ 30 s？')
box(XR, 6.65, WR, 1.75,
    '⑤ 局部放宽\n驻留段内节点及相邻节点\n'
    r'放宽到 $|u_p|\leq 2$（±0.04 Hz）' '\n'
    r'从 $\mathbf{u}^{(0)}$ 出发重解一次')
box(XC, 4.75, WC, 1.35,
    r'⑥ 确定修正系数 $\mathbf{u}^{\star}$' '\n'
    r'未放宽：$\mathbf{u}^{\star}=\mathbf{u}^{(0)}$' '\n'
    r'放宽：候选含 $\mathbf{u}^{(0)}$，按全长目标 $J$ 选优')

arrow((XC, 12.25), (XC, 11.55))
arrow((XC, 10.55), (XC, 10.225))
arrow((XC, 9.475), (XC, 9.075))
arrow((XC, 7.725), (XC, 7.40))
arrow((XC + 2.2, 6.65), (XR - WR / 2, 6.65))
label((XC + 2.2 + XR - WR / 2) / 2, 6.88, '是')
arrow((XC, 5.90), (XC, 5.425))
label(XC + 0.3, 5.66, '否', ha='left')
line((XR, 6.65 - 1.75 / 2), (XR, 4.75))
arrow((XR, 4.75), (XC + WC / 2, 4.75))

# output row
box(XC, 2.75, WC, 0.75, '相位补偿与全长 FFT')
box(XR, 2.75, 3.4, 0.75, '补偿谱')
arrow((XC, 4.075), (XC, 3.125))
label(XC + 0.25, 3.6, r'修正轨迹 $g_{\mathbf{u}^{\star}}(t)$', ha='left')
arrow((XC + WC / 2, 2.75), (XR - 1.7, 2.75))

# the record also enters the objective and the final compensation
line((XL, 12.35), (XL, 2.75))
arrow((XL, 8.40), (XC - WC / 2, 8.40))
arrow((XL, 2.75), (XC - WC / 2, 2.75))
label(3.62, 8.62, '$y[n]$')
label(3.62, 2.97, '$y[n]$')

rich(ax, 0.5, 1.45,
     r'注：边界驻留指修正量 $|r\,\mathbf{B}(t)\,\mathbf{u}|$ 连续保持在当前边界 0.95 倍以上的时间。' '\n'
     '候选只按求解目标 $J$ 选择；相干效率、谱峰等评价指标不参与选择。',
     fontsize=8, ha='left', linespacing=1.7)

out = Path(__file__).resolve().parents[1]
stem = out / 'fig03_流程图_中文黑白'
fig.savefig(f'{stem}.pdf', bbox_inches='tight', pad_inches=0.03)
fig.savefig(f'{stem}.svg', bbox_inches='tight', pad_inches=0.03)
fig.savefig(f'{stem}.png', dpi=600, bbox_inches='tight', pad_inches=0.03)
print('saved', stem)
