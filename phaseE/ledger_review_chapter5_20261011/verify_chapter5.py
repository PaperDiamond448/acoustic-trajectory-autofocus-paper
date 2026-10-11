"""Read-only verification of Chapter 5 and source data for Figures 7 and 8."""
from pathlib import Path
import hashlib
import json
import re
import sys

import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid
from scipy.signal import spectrogram
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
SELECTED = ROOT / "当前主线精选_20261003"
FIRST = SELECTED / "13_第一批补充分析_20261007/数据与脚本"
REAL = ROOT / "phaseD/X3_real"
INJECT = ROOT / "phaseE/E5_inject"
FS = 20.0
sources = {}
checks = []


def read_csv(path, **kw):
    path = Path(path)
    sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path, **kw)


def check(key, value, expected=None, tolerance=0.00051, definition=""):
    value = float(value)
    checks.append(dict(key=key, value=value, expected=expected, tolerance=tolerance,
                       passed=None if expected is None else abs(value-expected) <= tolerance,
                       definition=definition))


def phase_variance(e, t, idx):
    phase = 2*np.pi*cumulative_trapezoid(e, t, initial=0)[idx]
    tt = t[idx]
    a = np.c_[np.ones(len(tt)), tt-tt.mean()]
    residual = phase-a @ np.linalg.lstsq(a, phase, rcond=None)[0]
    return float(np.mean(residual**2))


def spectrum(y):
    nfft = 2**int(np.ceil(np.log2(8*len(y))))
    frequency = np.fft.fftshift(np.fft.fftfreq(nfft, 1/FS))
    power = np.fft.fftshift(np.abs(np.fft.fft(y, nfft))**2/len(y))
    return frequency, power


def same_sign_duration(e):
    edges = np.r_[0, np.flatnonzero(np.diff(np.sign(e)) != 0)+1, len(e)]
    return np.diff(edges).max()/FS


def main():
    # Equal-window estimates, stratified by background band; original draws are reused.
    records = read_csv(INJECT / "E5_records.csv")
    metrics = read_csv(INJECT / "traj_export_E5_theory_metrics.csv")
    pairkeys = ["band_id", "window_id", "scene", "snr_db", "record_id", "frontend"]
    assert not records.duplicated(pairkeys).any() and len(records) == 30240
    merged = records.merge(metrics[pairkeys+["in_sigma2", "out_sigma2"]], on=pairkeys, validate="one_to_one")
    summary = records.groupby("frontend")[["eta_in", "eta_out", "gain_eta"]].mean()
    summary.to_csv(OUT / "INJECTION_FRONTEND_MEANS.csv")
    for fe, row in summary.iterrows():
        for metric, value in row.items():
            expected = {("VS", "eta_in"):.517, ("VS", "eta_out"):.668,
                        ("DHMM", "eta_out"):.744, ("DHMM", "gain_eta"):.394,
                        ("SUV", "eta_in"):.736, ("SUV", "gain_eta"):.007,
                        ("SUV_GRID", "gain_eta"):.371}.get((fe, metric))
            check(f"D_{fe}_{metric}", value, expected)
    p = records.pivot(index=pairkeys[:-1], columns="frontend", values=["eta_in", "eta_out"])
    q = metrics.pivot(index=pairkeys[:-1], columns="frontend", values="in_sigma2")
    paired = []
    for scene, nn, dd in [("GEO",1295,.0219),("GPS",1349,.0109)]:
        mask = (q.index.get_level_values("scene")==scene) & (q.VS<5) & (q.SUV<5)
        diff = (p.eta_out.VS-p.eta_in.SUV)[mask]
        check(f"paired_{scene}_n", len(diff), nn, 0)
        check(f"paired_{scene}_difference", diff.mean(), dd, .000051)
        paired.append(dict(scene=scene, n=len(diff), mean_difference=diff.mean()))
    pd.DataFrame(paired).to_csv(OUT / "PAIRED_SMALL_PHASE_MEANS.csv", index=False)
    vs = merged[merged.frontend=="VS"].copy()
    geo = vs[(vs.scene=="GEO") & (vs.in_sigma2>=.5) & (vs.in_sigma2<5)]
    check("GEO_medium_phase_n",len(geo),614,0)
    check("GEO_medium_phase_eta_in",geo.eta_in.mean(),.509)
    check("GEO_medium_phase_eta_out",geo.eta_out.mean(),.878)
    vs["harm"] = vs.gain_eta<-.01
    stats = vs.groupby(["scene","snr_db"])[["eta_in","eta_out","gain_eta","harm","input_usable"]].mean()
    stats.to_csv(OUT / "INJECTION_VS_CELLS.csv")
    for (scene,snr), row in stats.iterrows():
        check(f"D_{scene}_{snr}_harm",row.harm,
              {("GPS",-20):.217,("GPS",-19):.122}.get((scene,snr)),.00051)
    for scene, expected in [("GEO",.247),("GPS",.231)]:
        check(f"D_{scene}_minus17_gain",stats.loc[(scene,-17),"gain_eta"],expected)
        check(f"D_{scene}_peak_gain_snr",stats.xs(scene).gain_eta.idxmax(),-17,0)
    for snr, expected in [(-20,-.182),(-19,-.171)]:
        a=vs[(vs.scene=="GPS") & (vs.snr_db==snr) & vs.harm]
        check(f"D_GPS_{snr}_harmed_mean_gain",a.gain_eta.mean(),expected)
    check("D_GPS_minus20_input_usable",stats.loc[("GPS",-20),"input_usable"],.95,.00001)
    check("D_GPS_minus20_eta_in",stats.loc[("GPS",-20),"eta_in"],.224)
    check("D_GEO_max_harm",stats.xs("GEO").harm.max(),.014,.00051)
    check("D_GPS_minus18on_max_harm",stats.xs("GPS").loc[-18:].harm.max(),.036,.00051)
    draws_path=INJECT/"BOOTSTRAP_DRAWS.npz"
    sources[draws_path.relative_to(ROOT).as_posix()] = hashlib.sha256(draws_path.read_bytes()).hexdigest()
    figure_rows=[]
    with np.load(draws_path) as draws:
        for scene in ["GEO","GPS"]:
            for snr in range(-20,-13):
                x=vs[(vs.scene==scene)&(vs.snr_db==snr)]
                point_bands=[]; boot_bands=[]
                for band in [1,2]:
                    z=x[x.band_id==band]
                    means=z.groupby("window_id")[["eta_in","eta_out","gain_eta","harm"]].mean().sort_index()
                    assert len(means)==9 and (z.groupby("window_id").size()==20).all()
                    point_bands.append(means.to_numpy().mean(axis=0))
                    boot_bands.append(means.to_numpy()[draws[f"T300_{band}"]].mean(axis=1))
                point=np.mean(point_bands,axis=0);boot=np.mean(boot_bands,axis=0)
                row=dict(scene=scene,snr_db=snr,n=360,background_windows=18)
                for j,key in enumerate(["eta_in","eta_out","gain_eta","harm"]):
                    lo,hi=np.quantile(boot[:,j],[.025,.975])
                    row.update({key:point[j],key+"_lo":lo,key+"_hi":hi})
                figure_rows.append(row)
    pd.DataFrame(figure_rows).to_csv(OUT/"FIG7_SOURCE.csv",index=False)
    cal_path=INJECT/"screen_revision_20261007/CALIBRATION_FREEZE.json"
    cal=json.loads(cal_path.read_text("utf-8-sig"))
    sources[cal_path.relative_to(ROOT).as_posix()]=hashlib.sha256(cal_path.read_bytes()).hexdigest()
    check("background_calibration_q99",cal["null_q99_db"],1.857,.00051)
    check("background_calibration_threshold",cal["threshold_db"],1.9,1e-12)
    screen=read_csv(INJECT/"screen_revision_20261007/BACKGROUND_SCREEN_REVISED.csv")
    check("background_retained",screen.retained.sum(),18,0)
    screen[~screen.retained].to_csv(OUT/"BACKGROUND_EXCLUSIONS.csv",index=False)
    gps=read_csv(SELECTED/"04_实测数据/表/A4_groundtruth.csv")
    ranges=[]
    for s in range(0,3000,300):
        y=gps[(gps.t_s>=s)&(gps.t_s<s+300)].f_gps_100
        ranges.append(dict(start_s=s,end_s=s+300,range_hz=y.max()-y.min()))
    pd.DataFrame(ranges).to_csv(OUT/"GPS_WINDOW_RANGES.csv",index=False)

    frozen=read_csv(REAL/"X3_FROZEN_TESTSET.csv")
    cases=read_csv(REAL/"X3_cases.csv")
    ada=cases[(cases.method=="VS_FM")&(cases.duration_s==300)].merge(
        frozen[["tone_hz","segment_start_s","group","peak_excess_dB"]],
        on=["tone_hz","segment_start_s"],validate="one_to_one")
    assert len(ada)==105
    ada[["tone_hz","segment_start_s","group","gain_peak_vs_SMR_db","peak_excess_dB"]].to_csv(OUT/"FIG8_ALL_CASES.csv",index=False)
    group_summary=[]
    for group,n,positive,median in [("strong",60,58,.177),("shallow",30,30,.069),("weak",15,15,1.744)]:
        a=ada[ada.group==group];gain=a.gain_peak_vs_SMR_db
        check("natural_"+group+"_n",len(a),n,0)
        check("natural_"+group+"_positive",(gain>0).sum(),positive,0)
        check("natural_"+group+"_gain_median",gain.median(),median)
        check("natural_"+group+"_peak_excess_median",a.peak_excess_dB.median(),
              {"strong":24.0,"shallow":25.8,"weak":15.4}[group],.051)
        group_summary.append(dict(group=group,n=n,positive=positive,median=gain.median(),
                                  q25=gain.quantile(.25),q75=gain.quantile(.75)))
    pd.DataFrame(group_summary).to_csv(OUT/"NATURAL_GROUP_SUMMARY.csv",index=False)
    guides=[49,64,79,94,112,130]
    saved_position=read_csv(FIRST/"guided_position_check.csv")
    position_rows=[];cache={}
    for r in ada[ada.group=="weak"].itertuples():
        tone=int(r.tone_hz);start=int(r.segment_start_s)
        track=read_csv(REAL/f"tracks/f{tone}_s{start}_T300.csv")
        guide=np.median([read_csv(REAL/f"tracks/f{f}_s{start}_T300.csv").VS_FM.to_numpy()/f for f in guides],axis=0)*tone
        cache[(tone,start)]=(track,guide)
        key=f"{tone} Hz, {start}-{start+300} s"
        offset=float(np.median(track.VS_FM.to_numpy()-guide))
        old=saved_position[saved_position.case==key].iloc[0]
        rel=track.SMR.to_numpy()-tone;idx=(track.time_s>=start+5)&(track.time_s<start+295)
        outrel=track.VS_FM.to_numpy()-tone
        position_rows.append(dict(tone_hz=tone,segment_start_s=start,
            median_module_minus_guide_hz=offset,previous_value=old.module_track_minus_guided_hz,
            abs_difference=abs(offset-old.module_track_minus_guided_hz),
            median_LPS_offset_hz=float(np.median(rel[idx])),median_CDTR_offset_hz=float(np.median(outrel[idx])),
            LPS_fraction_abs_offset_ge1p3=float(np.mean(abs(rel[idx])>=1.3)),
            CDTR_fraction_abs_offset_ge1p3=float(np.mean(abs(outrel[idx])>=1.3)),
            max_LPS_abs_offset_hz=float(abs(rel[idx]).max()),
            max_CDTR_abs_offset_hz=float(abs(outrel[idx]).max())))
    pos=pd.DataFrame(position_rows);pos.to_csv(OUT/"WEAK_GUIDED_POSITIONS_RECOMPUTED.csv",index=False)
    check("weak_position_readback_max_diff",pos.abs_difference.max(),0,1e-11)
    check("weak_within_10mHz_of_guide",(abs(pos.median_module_minus_guide_hz)<=.01).sum(),1,0)
    check("weak_within_20mHz_of_guide",(abs(pos.median_module_minus_guide_hz)<=.02).sum(),1,0)
    other=pos[pos.tone_hz!=136]
    check("weak_other_min_abs_offset",abs(other.median_module_minus_guide_hz).min(),.067,.00051)
    check("weak_other_max_abs_offset",abs(other.median_module_minus_guide_hz).max(),1.415,.00051)
    check("weak_136_offset",pos[pos.tone_hz==136].median_module_minus_guide_hz.iloc[0],-.009)
    # Independent spectral/time-scale calculation from all 105 saved trajectory pairs.
    saved_correction=read_csv(FIRST/"real_correction_spectra.csv")
    correction_rows=[]
    t=np.arange(6000)/FS;idx=(t>=5)&(t<295)
    for r in ada.itertuples():
        tone=int(r.tone_hz);start=int(r.segment_start_s)
        track=cache[(tone,start)][0] if (tone,start) in cache else read_csv(REAL/f"tracks/f{tone}_s{start}_T300.csv")
        dg=track.VS_FM.to_numpy()-track.SMR.to_numpy();seg=dg[idx]-dg[idx].mean()
        f=np.fft.rfftfreq(len(seg),1/FS);power=abs(np.fft.rfft(seg))**2;power[0]=0
        correction_rows.append(dict(tone=tone,seg=start,group=r.group,gain=r.gain_peak_vs_SMR_db,
            rms_mHz=1000*np.sqrt(np.mean(seg**2)),max_mHz=1000*abs(dg[idx]).max(),
            frac_var_period_gt60=(power[(f>0)&(f<1/60)].sum()/power.sum() if power.sum()>0 else np.nan),
            phase_change_s2=phase_variance(dg,t,idx)))
    corr=pd.DataFrame(correction_rows);corr.to_csv(OUT/"REAL_CORRECTION_RECOMPUTED.csv",index=False)
    old=corr.merge(saved_correction,on=["tone","seg"],suffixes=("","_saved"),validate="one_to_one")
    for field in ["rms_mHz","max_mHz","frac_var_period_gt60","phase_change_s2"]:
        check("correction_readback_max_diff_"+field,abs(old[field]-old[field+"_saved"]).max(),0,1e-8)
    for group,slow,rms in [("weak",.88,7.35),("strong",.42,None),("shallow",.21,None)]:
        c=corr[corr.group==group]
        check("correction_"+group+"_slow_median",c.frac_var_period_gt60.median(),slow,.0051)
        check("correction_"+group+"_rms_median",c.rms_mHz.median(),rms,.0051)
    rho=spearmanr(corr.phase_change_s2,corr.gain).statistic
    check("natural_phase_change_gain_rho",rho,.932)
    c=corr[(corr.tone==136)&(corr.seg==900)].iloc[0]
    check("natural_136_gain",c.gain,3.0854,.000051)
    check("natural_136_max_mHz",c.max_mHz,28.311,.00051)
    check("natural_136_slow_share",c.frac_var_period_gt60,.951,.00051)
    cross=read_csv(ROOT/"phaseE/ledger_review_20261008/supplement_R/rerun/R1_cross_guidance_nu.csv")
    check("strong_cross_pairs",len(cross),300,0)
    check("strong_cross_abs_nu_median_mHz",1000*abs(cross.nu).median(),2.136,.00051)
    check("strong_cross_abs_nu_q90_mHz",1000*abs(cross.nu).quantile(.9),5.829,.00051)

    # Figure 8 example: saved input and tracks, with no estimator rerun.
    inp=REAL/"screen_inputs/f136_s900.mat"
    raw_csv=read_csv(REAL/"audit_raw/f136_s900_T300.csv",header=None)
    raw_copy=raw_csv.iloc[:,1].to_numpy()+1j*raw_csv.iloc[:,2].to_numpy()
    y=raw_copy;reference=136.0
    if inp.exists():
        local_deps=ROOT/"phaseE/_local_pydeps"
        if local_deps.exists():sys.path.insert(0,str(local_deps))
        shared_deps=ROOT.parents[1]/"phaseE/_local_pydeps"
        if shared_deps.exists():sys.path.insert(0,str(shared_deps))
        try:
            import h5py
        except ModuleNotFoundError:
            h5py=None
        if h5py is not None:
            sources[inp.relative_to(ROOT).as_posix()]=hashlib.sha256(inp.read_bytes()).hexdigest()
            with h5py.File(inp) as h:
                raw=h["y"][0];y=raw["real"]+1j*raw["imag"];reference=float(h["extract/fref"][0,0])
            check("136_raw_csv_mat_max_diff",abs(raw_copy-y).max(),0,1e-11)
    track,guide=cache[(136,900)]
    figure_track=pd.DataFrame(dict(time_s=track.time_s,LPS_Hz=track.SMR,CDTR_Hz=track.VS_FM,
                                  guide_Hz=guide,correction_mHz=1000*(track.VS_FM-track.SMR)))
    figure_track.to_csv(OUT/"FIG8_EXAMPLE_TRACKS.csv",index=False)
    guide_error=figure_track.CDTR_Hz.to_numpy()[idx]-figure_track.guide_Hz.to_numpy()[idx]
    guide_check=dict(interval_s=[905,1195],median_offset_hz=float(np.median(guide_error)),
        max_abs_offset_hz=float(abs(guide_error).max()),p90_abs_offset_hz=float(np.quantile(abs(guide_error),.9)),
        fraction_abs_offset_gt_005_hz=float(np.mean(abs(guide_error)>.05)),
        fraction_abs_offset_le_001_hz=float(np.mean(abs(guide_error)<=.01)),
        fraction_abs_offset_le_002_hz=float(np.mean(abs(guide_error)<=.02)),
        max_correction_full300_mHz=float(abs(figure_track.correction_mHz).max()),
        max_correction_opt290_mHz=float(abs(figure_track.correction_mHz.to_numpy()[idx]).max()),
        interpretation="The segment median is close; the full trajectory has large local departures from the strong-tonal reference.")
    (OUT/"136HZ_REFERENCE_COMPARISON.json").write_text(json.dumps(guide_check,ensure_ascii=False,indent=2),encoding="utf-8")
    nu,per=spectrum(y);band=abs(nu)<=1.5;den=per[band].max()
    spec={"residual_frequency_Hz":nu[band],"Periodogram_dB":10*np.log10(np.maximum(per[band]/den,1e-15))}
    stored=read_csv(REAL/"spectra/f136_s900_T300.csv")
    stored_index=np.argsort(stored.frequency_Hz.to_numpy())
    for name,g,column in [("LPS",track.SMR.to_numpy(),"SMR"),("CDTR",track.VS_FM.to_numpy(),"VS_FM")]:
        phase=2*np.pi*cumulative_trapezoid(g-reference,t,initial=0)
        ff,power=spectrum(y*np.exp(-1j*phase));assert np.array_equal(ff,nu)
        spec[name+"_dB"]=10*np.log10(np.maximum(power[band]/den,1e-15))
        check("136_spectrum_saved_max_diff_"+name,
              abs(power[band]-stored[column].to_numpy()[stored_index]).max(),0,1e-6)
    pd.DataFrame(spec).to_csv(OUT/"FIG8_EXAMPLE_SPECTRA.csv",index=False)
    gain=max(spec["CDTR_dB"])-max(spec["LPS_dB"])
    check("136_full300_peak_gain",gain,3.0854,.000051)
    # Exact same 10 s symmetric Hann and 1 s hop; each frame uses its annular background.
    ff,tt,pow=spectrogram(y,fs=FS,window=np.hanning(200),nperseg=200,noverlap=180,
                        nfft=2048,detrend=False,return_onesided=False,scaling="spectrum",mode="psd")
    order=np.argsort(ff);ff=ff[order];pow=pow[order]
    keep=abs(ff)<=.4;power=pow[keep];level=10*np.log10(np.maximum(power,np.finfo(float).tiny))
    annulus=(abs(ff)>=1)&(abs(ff)<=2)
    baseline=np.median(10*np.log10(np.maximum(pow[annulus],np.finfo(float).tiny)),axis=0)
    level-=baseline[None,:]
    np.savez_compressed(OUT/"FIG8_EXAMPLE_LOFAR.npz",frequency_Hz=136+ff[keep],time_s=900+tt,power_dB=level)
    # Demonstrate all candidate bands from the actual call chain, not stale run status.
    config_paths=["phaseE/scripts/phaseE_inject_one.m","phaseD/codeX/phaseX_settings.m",
                  "phaseD/codeX/phaseX_front.m","phaseD/code/phaseD_measure.m",
                  "研究工作台/MATLAB实验/mft_week4_module/mft_config.m"]
    for rel in config_paths:
        path=ROOT/rel
        if not path.exists():path=OUT/"source_code"/Path(rel).name
        sources[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    config=dict(frontend_candidate_band_Hz=[-2,2],residual_search_band_Hz=[-2,2],
                evidence="phaseE_inject_one calls phaseX_settings(300,false); mft_config sets B.band=[-2 2]; phaseX_front passes B.band; phaseD_measure searches B.band.",
                evaluation_interval_s=[5,295],natural_accumulation_interval_s=[0,300],
                preprocessing_guard_s={"interior":[10,10],"first":[0,20],"last":[20,0]})
    (OUT/"PROCESSING_SETTINGS.json").write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding="utf-8")
    # Same-sign lengths are sign-invariant; Figure 3 now uses truth minus estimate.
    example=read_csv(ROOT/"phaseE/ledger_review_20261011/FIG3_example_trajectories.csv")
    m=(example.time_s>=5)&(example.time_s<295)
    for name,expected in [("LPS",46.35),("CDTR",24.05)]:
        e=example.true_g_Hz-example[name+"_g_Hz"]
        check("FIG3_"+name+"_longest_same_sign_s",same_sign_duration(e[m].to_numpy()),expected,.051)
    pd.DataFrame(dict(time_s=example.time_s,LPS_error_mHz=1000*(example.true_g_Hz-example.LPS_g_Hz),
                      CDTR_error_mHz=1000*(example.true_g_Hz-example.CDTR_g_Hz))).to_csv(OUT/"FIG3_ERRORS_TRUTH_MINUS_ESTIMATE.csv",index=False)
    result=pd.DataFrame(checks);result.to_csv(OUT/"CHAPTER5_NUMERIC_CHECK.csv",index=False)
    failed=result[result.passed==False].fillna("").to_dict("records")
    report=dict(entries=len(checks),checked_expectations=int(result.expected.notna().sum()),failed=failed,
                source_sha256=sources,original_inputs_unchanged=True)
    assert all(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha for rel,sha in sources.items())
    (OUT/"CHAPTER5_NUMERIC_CHECK.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(dict(entries=len(checks),failed=failed),ensure_ascii=False,indent=2))
    print("weak positions\n",pos.to_string(index=False))
    print("GPS ranges\n",pd.DataFrame(ranges).to_string(index=False))


if __name__=="__main__":main()
