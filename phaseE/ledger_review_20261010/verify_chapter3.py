"""Read frozen CSVs and independently check numbers used in Chapter 3."""
from pathlib import Path
import hashlib
import importlib.util
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
METHOD = "ADA_local_c04_t30_A"
sources = {}


def source(rel):
    p = ROOT / rel
    sources[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p


def csv(rel):
    return pd.read_csv(source(rel))


d1 = csv("phaseD/D_dev/D1_records.csv")
s1 = csv("phaseD/D_dev/D1_summary.csv")
d2 = csv("phaseD/D_dev/D2_records.csv")
s2 = csv("phaseD/D_dev/D2_summary.csv")
confirm = csv("phaseD/C_confirm/C_records.csv")
timing = csv("phaseD/C_confirm/C_runtime.csv")
frozen = json.loads(source("phaseD/D_dev/FROZEN_METHOD.json").read_text(encoding="utf-8-sig"))
decision = json.loads(source("phaseD/D_dev/D1_DECISION.json").read_text(encoding="utf-8-sig"))
checks = []


def check(label, actual, stored, note="", atol=2e-13):
    actual, stored = float(actual), float(stored)
    ok = abs(actual - stored) <= atol
    checks.append(dict(label=label, recomputed=actual, stored=stored,
                       abs_difference=abs(actual-stored), passed=ok, note=note))
    if not ok:
        raise AssertionError((label, actual, stored))


base = d1[(d1.arm == "scaled") & (d1.method == "F02") & (d1.Delta_s == 10)]
population = dict(records=len(base), seeds=int(base.seed.nunique()),
                  scene_counts=base.groupby("scene").size().to_dict(),
                  snr_db=sorted(base.snr_db.unique().tolist()),
                  spacings_s=sorted(d1.Delta_s.unique().tolist(), reverse=True))
assert population["records"] == 840 and population["seeds"] == 120
assert set(population["scene_counts"].values()) == {420}

for scene in ["S0", "S2"]:
    for delta in [20, 10, 6]:
        raw = d1[(d1.arm == "scaled") & (d1.method == "F02") &
                 (d1.scene == scene) & (d1.Delta_s == delta)]
        stored = s1[(s1.arm == "scaled") & (s1.method == "F02") &
                    (s1.scene == scene) & (s1.Delta_s == delta)].iloc[0]
        check(f"D1 {scene} Delta={delta} eta", raw.groupby("snr_db").eta.mean().mean(), stored.eta)

for delta in [20, 10, 6]:
    raw = d1[(d1.arm == "scaled") & (d1.method == "F02") & (d1.Delta_s == delta)]
    stored = s1[(s1.arm == "scaled") & (s1.method == "F02") &
                (s1.scene == "pooled") & (s1.Delta_s == delta)].iloc[0]
    check(f"D1 pooled Delta={delta} runtime median", raw.runtime_s.median(), stored.runtime_median_s)

gain_rows = []
for (scene, method, delta), raw in d1[d1.arm == "scaled"].groupby(["scene", "method", "Delta_s"]):
    gain_rows.append(dict(scene=scene, method=method, Delta_s=delta,
                         gain=float((raw.eta-raw.eta_VIT).groupby(raw.snr_db).mean().mean())))
gain = pd.DataFrame(gain_rows)
gain["max_gain"] = gain.groupby(["scene", "method"]).gain.transform("max")
gain["ratio"] = gain.gain/gain.max_gain
gain["passes_95pct"] = gain.gain >= .95*gain.max_gain
eligible = sorted(gain.groupby("Delta_s").passes_95pct.all().loc[lambda x:x].index.tolist(), reverse=True)
assert eligible == decision["eligible_intersection"] == [10, 7.5, 6]
gain.to_csv(OUT / "D1_gain_rule_recomputed.csv", index=False, encoding="utf-8-sig")

for method in ["F04", METHOD, "ADA_local_c04_t10_A", "ADA_local_c04_t45_A"]:
    raw = d2[(d2.method == method) & (d2.scene == "S2")]
    stored = s2[(s2.method == method) & (s2.scene == "S2")].iloc[0]
    paired = raw.eta-raw.eta_F02
    harm = paired < -.01
    check(f"D2 S2 {method} harm", harm.groupby(raw.snr_db).mean().mean(), stored.harm_vs_F02)
    check(f"D2 S2 {method} gain", paired.groupby(raw.snr_db).mean().mean(), stored.gain_eta_vs_F02)

for method in [METHOD, "F02", "SMR"]:
    raw = confirm[confirm.method == method]
    stored = timing[(timing.scope == "ALL") & (timing.method == method) &
                    (timing.component == "runtime_s")].iloc[0]
    check(f"C {method} runtime median", raw.runtime_s.median(), stored["median"])
    check(f"C {method} runtime p90", raw.runtime_s.quantile(.9), stored.p90)

path = source("当前主线精选_20261003/13_第一批补充分析_20261007/数据与脚本/theory.py")
spec = importlib.util.spec_from_file_location("chapter3_supplied_theory", path)
theory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theory)
k20, k310 = theory.kernel(np.array([1/20, 1/310]), T=300)
TI = 290.0


def analytic_kernel(f):
    x = f*TI
    sinc = np.sinc(x)
    return (1-sinc*sinc-3*((np.cos(np.pi*x)-sinc)/(np.pi*x))**2)/f**2


kernel = dict(record_duration_s=300, evaluation_duration_s=290,
              supplied_discrete_K20=float(k20), supplied_discrete_K310=float(k310),
              ratio=float(k20/k310), continuous_K20=float(analytic_kernel(1/20)),
              continuous_K310=float(analytic_kernel(1/310)),
              initial_phase_average=True, unit="rad^2/Hz^2")
assert k20/k310 < .01

P, delta, T = 31, 10, 300
scale = (P-2)/19*(300/T)*(15/delta)**3
check("lambda", .001*scale, frozen["regularization"]["lambda_C"])
check("lambda_F", .1*scale, frozen["regularization"]["lambda_F"])
assert int(np.floor(240*max(1,P/21)+.5)) == frozen["budget_formula"]["selected_iterations"] == 354
assert int(np.floor(1000*max(1,P/21)+.5)) == frozen["budget_formula"]["selected_fevals"] == 1476

report = dict(population=population, node_rule=dict(eligible=eligible, chosen=max(eligible),
              reference="same-record Viterbi eta", combinations="S0/S2 x F02/UNB"),
              kernel=kernel, checks=checks, all_passed=all(x["passed"] for x in checks),
              corrections=["S2 F02 Delta=6 eta rounds to 0.587, rather than 0.588",
                           "95% gain rule uses gain over Viterbi under both F02 and UNB",
                           "runtime_s is solver call time, excluding shared preprocessing and dwell evaluation"],
              source_sha256=sources)
(OUT / "CHAPTER3_NUMERIC_CHECK.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
pd.DataFrame(checks).to_csv(OUT / "CHAPTER3_NUMERIC_CHECK.csv", index=False, encoding="utf-8-sig")
print(json.dumps(dict(all_passed=report["all_passed"], checked_values=len(checks),
                     population=population, node_rule=report["node_rule"], kernel=kernel,
                     corrections=report["corrections"]), ensure_ascii=False, indent=2))
