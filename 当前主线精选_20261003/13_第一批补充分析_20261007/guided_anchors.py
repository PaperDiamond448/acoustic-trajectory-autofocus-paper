#!/usr/bin/env python3
"""Build strong-line-guided anchor trajectories for the 15 weak-line cases (Codex task E).
Guided absolute frequency for weak tone f_w in segment s:
    g_med(t)  = f_w * median_k [ VS_FM_k(t) / f_k ],  k in strong set {49,64,79,94,112,130} Hz, same segment
    g_94(t)   = f_w * VS_FM_94(t) / 94
VS_FM_k = saved module output track of strong tone k (phaseD/X3_real/tracks/f{k}_s{s}_T300.csv).
Writes one CSV per case: time_s, guided_med_abs_hz, guided94_abs_hz (20 Hz grid, 6000 rows).
Run from the repository root:  python guided_anchors.py  -> writes to phaseG_guided/anchors/ (new folder).
"""
import os, numpy as np, pandas as pd
BASE = 'phaseD/X3_real/tracks'
OUT = 'phaseG_guided/anchors'
WEAK = [(52,600),(52,900),(52,2400),(61,2100),(100,600),(100,900),(100,1200),(100,1500),(100,1800),
        (103,900),(103,1200),(118,1500),(121,0),(133,1200),(136,900)]
STRONG = [49, 64, 79, 94, 112, 130]
os.makedirs(OUT, exist_ok=True)
for fw, s in WEAK:
    D = []; t = None
    for fk in STRONG:
        tr = pd.read_csv(f'{BASE}/f{fk}_s{s}_T300.csv'); t = tr.time_s.values
        D.append(tr.VS_FM.values / fk)
        if fk == 94: g94 = fw * tr.VS_FM.values / 94
    gmed = fw * np.median(np.array(D), axis=0)
    pd.DataFrame({'time_s': t, 'guided_med_abs_hz': gmed, 'guided94_abs_hz': g94}).to_csv(
        f'{OUT}/f{fw}_s{s}_guided.csv', index=False, float_format='%.9f')
print('wrote', len(WEAK), 'files to', OUT)
