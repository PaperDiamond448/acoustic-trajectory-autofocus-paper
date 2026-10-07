# Phase D 核验门报告

MATLAB 9.14.0.2206163 (R2023a)；R2023a；G3 使用 6 workers。

| 门 | 状态 | 最大差异 | 通过标准 |
|---|---|---:|---|
| G1 | PASS | 0 | All family fields <=1e-12 |
| G2 | PASS | 0 | Samplewise exact equality of y and truth.gtrue |
| G3 | PASS | 0 | Archived bounded/unbounded u, J290, eta absolute difference <=1e-8 |
| G4 | PASS | 0 | ADA tau=Inf output bitwise identical to fixed F02 |
| G5 | PASS | 0 | Exact lambda_C=1e-3 and lambda_F=0.1 at Delta=15,T=300 |
| G6 | PASS | 0 | New and historical seed sets disjoint |
| G7 | PASS | 8.324418798721922e-08 | MD5 d39204a14031ce097707b440ef58e601; peak increment within 1e-4 of 1.757253 dB |
| G8 | PASS | 0 | SUV output g exact equality to original implementation on 3 ExpB records |

G1: Three archived E4a record inputs; all fields compared.

G2: S0/S2, 3 historical seeds each.

G3: Six E4a records, two box modes; archived chunk coefficients and metrics.

G4: No-trigger path reuses exact fixed-0.02 result; archive reproduction covered by G3.

G5: Explicit exact-return baseline branch.

G6: Historical superset includes IDs through 5000, every historical scene.

G7: Fresh original SIO extraction and old 21-node B240 configuration; full-record FFT matching original real-spectrum definition.

G8: Original unchanged implementation versus new-name copy on W4 ExpB phase-24 records.

