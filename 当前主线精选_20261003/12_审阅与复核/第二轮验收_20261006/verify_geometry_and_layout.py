"""Read-only acceptance checks; all generated files stay in this directory."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
REV = Path(r'D:/论文集/当前主线精选_20261003/11_正文稿/修订稿_20261005')
ATTR = REV / '补充分析_实测峰归属'

def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def compare_frames(a, b):
    assert list(a.columns) == list(b.columns) and a.shape == b.shape
    max_diff = 0.0
    for c in a.columns:
        if pd.api.types.is_numeric_dtype(a[c]):
            np.testing.assert_allclose(a[c], b[c], rtol=0, atol=1e-10, equal_nan=True)
            d = np.abs(a[c].to_numpy() - b[c].to_numpy())
            if np.isfinite(d).any():
                max_diff = max(max_diff, float(np.nanmax(d)))
        else:
            assert a[c].fillna('').equals(b[c].fillna(''))
    return max_diff

spec = importlib.util.spec_from_file_location('attribution_readonly', ATTR / 'peak_attribution.py')
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)
assert pa.BB.resolve() == (ATTR / 'baseband').resolve()
pa.OUT = OUT / '归属检查复现'
(pa.OUT / '图').mkdir(parents=True, exist_ok=True)
with (OUT / '归属检查运行日志.txt').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log):
    pa.main()
    pa.duration_windows()
checks = {}
for name in ('实测峰归属_15例.csv', '积累时长窗口归属.csv'):
    checks[name] = compare_frames(pd.read_csv(pa.OUT / name), pd.read_csv(ATTR / name))
print('ATTRIBUTION_SCRIPT_PASS', flush=True)

# Independently derive the new per-frame statistics from the same fixed
# LOFAR ridge and saved compensation trajectory, without rescreening.
original = pd.read_csv(ATTR / '逐帧偏差统计_15例.csv')
attribution = pd.read_csv(pa.OUT / '实测峰归属_15例.csv')
new_rows = []
for tone, group in original.groupby('tone', sort=True):
    tc, freq, power = pa.lofar(pa.load_tone(int(tone)))
    core = np.abs(freq) <= .5
    for _, row in group.iterrows():
        start = int(row.start)
        sel = (tc >= start) & (tc < start + 300)
        t = tc[sel]
        ridge = freq[core][np.argmax(power[core][:, sel], axis=0)]
        keep = np.abs(ridge - np.median(ridge)) <= .2
        tn = (t - t.mean()) / 150
        ref = tone + np.polyval(np.polyfit(tn[keep], ridge[keep], 3), tn)
        tr = pd.read_csv(pa.X3 / 'tracks' / f'f{int(tone)}_s{start}_T300.csv')
        attr = attribution[(attribution.tone_hz == tone) & (attribution.start_s == start)].iloc[0]
        mapped = np.interp(t, tr.time_s, tr.VS_FM) + attr.VS_FM_peak_resid_hz
        dev = np.abs(mapped - ref)
        median = float(np.median(dev))
        new_rows.append(dict(tone=int(tone), start=start, median=median,
            p90=float(np.quantile(dev, .9)), frac05=float(np.mean(dev <= .05)),
            cls='对应' if median <= .05 else '不对应' if median > .1 else '不确定',
            gain=attr.gain_max_peak_db, w10=attr.gain_ridge_peak_db,
            w05=attr.gain_ridge_peak_w05_db))
    del power
new = pd.DataFrame(new_rows).sort_values(['tone', 'start']).reset_index(drop=True)
old = original.sort_values(['tone', 'start']).reset_index(drop=True)
checks['逐帧偏差统计_15例.csv'] = compare_frames(new, old)
new.to_csv(pa.OUT / '逐帧偏差统计_15例.csv', index=False, encoding='utf-8-sig')
hundred = new[new.tone == 100]
thresholds = []
for threshold in (.025, .04, .05, .075):
    selected = new[new['median'] <= threshold]
    thresholds.append(dict(threshold_hz=threshold, cases=len(selected),
        median_gain_db=float(selected.gain.median())))
same = attribution[attribution.tone_hz == 100]
assert len(same) == 5
assert all((same[c] == '对应').all() for c in ('SMR_class', 'VS_FM_class', 'SUV_class', 'SUV_FM_class'))
result = dict(status='PASS', original_script_run=True, original_outputs_preserved=True,
    max_numeric_difference_by_table=checks, cases=15, duration_windows=len(pd.read_csv(pa.OUT / '积累时长窗口归属.csv')),
    threshold_sensitivity=thresholds,
    hundred_hz=dict(cases=5, gain_min_db=float(hundred.gain.min()), gain_max_db=float(hundred.gain.max()),
        gain_median_db=float(hundred.gain.median()), frac05_min=float(hundred.frac05.min()),
        frac05_max=float(hundred.frac05.max()), p90_min_hz=float(hundred.p90.min()), p90_max_hz=float(hundred.p90.max()),
        paired_LPS_median_gain_db=float(same.gain_max_peak_db.median()),
        paired_TBD_median_gain_db=float(same.gain_suv_max_peak_db.median())),
    sixty_one_hz=new[new.tone == 61].to_dict('records'))
dump('归属与敏感性独立核查.json', result)
print('FRAME_STATISTICS_PASS', flush=True)

# Verify paragraph anchors against the current Word XML, including equations.
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with zipfile.ZipFile(REV / '论文修订稿_中文_20261005.docx') as z:
    doc = ET.fromstring(z.read('word/document.xml'))
    paragraphs = []
    for p in doc.find('w:body', ns).findall('w:p', ns):
        value = ''.join(node.text or '' for node in p.iter() if node.tag in
            (f"{{{ns['w']}}}t", f"{{{ns['m']}}}t")).strip()
        if value:
            paragraphs.append((value, p))
    txt = (REV / '回复审稿' / '修订稿Word正文段落.txt').read_text(encoding='utf-8-sig')
    numbered_pairs = re.findall(r'^\[(P\d{4})\] (.*)$', txt, flags=re.M)
    numbered = [value for _, value in numbered_pairs]
    assert numbered == [p[0] for p in paragraphs]
    media_hashes = {name: hashlib.sha256(z.read(name)).hexdigest() for name in z.namelist() if name.startswith('word/media/')}
    fig13 = REV / '_build' / 'figs' / 'fig13_real_trajectory_duration_中文_修订.png'
    fig_hash = hashlib.sha256(fig13.read_bytes()).hexdigest()
    embedded = [name for name, h in media_hashes.items() if h == fig_hash]
    assert embedded
    paragraph291 = paragraphs[[key for key, _ in numbered_pairs].index('P0291')][1]
    assert paragraph291.findall('.//m:rad', ns), 'Check sqrt(2) formula in actual Word XML'

sys.path.insert(0, r'D:/论文集/phaseD/runtime')
import fitz
pdf = fitz.open(REV / '_build' / '排版检查' / '修订稿.pdf')
assert len(pdf) == 52
pages = [30, 31]
figure13_page = None
for i, page in enumerate(pdf):
    if '图13' in page.get_text().replace(' ', '') and page.get_images():
        figure13_page = i + 1
        pages.append(i + 1)
        break
for page_number in sorted(set(pages)):
    pdf[page_number-1].get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(OUT / f'排版核查_第{page_number:02d}页.png')
dump('段落与版面核查.json', dict(status='PASS', paragraph_count=len(paragraphs),
    docx_matches_paragraph_snapshot=True, pdf_pages=len(pdf), fig13_embedded_media=embedded,
    sqrt2_confirmed_in_Word_XML=True, rendered_pages=sorted(set(pages)), figure13_page=figure13_page))
print('PARAGRAPHS_AND_LAYOUT_PASS', flush=True)
