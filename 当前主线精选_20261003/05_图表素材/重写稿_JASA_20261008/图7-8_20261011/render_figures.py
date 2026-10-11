"""Render the real-background and natural-tonal results from verified source data."""
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from audit_panel_alignment import require_matplotlib_panel_alignment

HERE = Path(__file__).parent
GRAY = "#737373"
ORANGE = "#d77832"
BLUE = "#477aab"
GREEN = "#499a7b"
COLORS = dict(strong=BLUE, shallow=GREEN, weak=ORANGE)
matplotlib.rcParams.update({
    "font.family":"sans-serif", "font.sans-serif":["Arial","Microsoft YaHei","DejaVu Sans"],
    "font.size":8, "axes.labelsize":8, "axes.titlesize":8.5,
    "axes.spines.top":False,"axes.spines.right":False,"axes.linewidth":.7,
    "xtick.labelsize":7.5,"ytick.labelsize":7.5,"legend.fontsize":7.5,
    "pdf.fonttype":42,"svg.fonttype":"none","legend.frameon":False,
    "lines.linewidth":1.2,"savefig.dpi":600,
})


def label(ax, text):
    ax.text(0,1.12,text,transform=ax.transAxes,fontweight="bold",fontsize=9,
            ha="left",va="bottom")


def save(fig, name, **alignment_options):
    base=HERE/name
    require_matplotlib_panel_alignment(fig,json_out=str(base)+".alignment.json",
        tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True,**alignment_options)
    fig.savefig(str(base)+".pdf")
    fig.savefig(str(base)+".svg")
    fig.savefig(str(base)+".png",dpi=600)
    # TIFF is a lossless raster export; SVG/PDF remain the editable originals.
    fig.savefig(str(base)+".tiff",dpi=600,pil_kwargs={"compression":"tiff_lzw"})
    plt.close(fig)


def fig7(zh):
    source=pd.read_csv(HERE/"source_data/FIG7_SOURCE.csv")
    fig,axes=plt.subplots(2,2,figsize=(183/25.4,139/25.4))
    fig.subplots_adjust(left=.095,right=.975,bottom=.105,top=.80,wspace=.31,hspace=.55)
    names={"GEO":"几何目标" if zh else "Geometric target",
           "GPS":"GPS 目标" if zh else "GPS target"}
    for col,scene in enumerate(["GEO","GPS"]):
        d=source[source.scene==scene].sort_values("snr_db")
        x=d.snr_db.to_numpy()
        for metric,color,marker,text in [("eta_in",GRAY,"o","LPS"),("eta_out",ORANGE,"s","CDTR")]:
            a=axes[0,col]
            a.fill_between(x,d[metric+"_lo"].to_numpy(),d[metric+"_hi"].to_numpy(),color=color,alpha=.16,lw=0)
            a.plot(x,d[metric].to_numpy(),color=color,marker=marker,ms=3.5,label=text,
                   markerfacecolor="white" if metric=="eta_in" else color)
        a.set(xlim=(-20.35,-13.65),ylim=(0,1.02),ylabel="相干效率 η" if zh else "Coherent efficiency η")
        a.set_xticks(x);a.set_yticks(np.linspace(0,1,6))
        a.set_title(names[scene],pad=8)
        a.set_xlabel("信噪比 (dB)" if zh else "SNR (dB)")
        a=axes[1,col]
        y=100*d.harm.to_numpy();lo=100*d.harm_lo.to_numpy();hi=100*d.harm_hi.to_numpy()
        a.fill_between(x,lo,hi,color=ORANGE,alpha=.16,lw=0)
        a.plot(x,y,color=ORANGE,marker="s",ms=3.5)
        a.set(xlim=(-20.35,-13.65),ylim=(-.35,40),ylabel="变差记录比例 (%)" if zh else "Degraded records (%)",
              xlabel="信噪比 (dB)" if zh else "SNR (dB)")
        a.set_xticks(x);a.set_yticks([0,10,20,30,40])
        a.set_title(names[scene],pad=8)
    label(axes[0,0],"(a)");label(axes[1,0],"(b)")
    handles=[Line2D([],[],color=GRAY,marker="o",ms=4,mfc="white",label="LPS"),
             Line2D([],[],color=ORANGE,marker="s",ms=4,label="CDTR")]
    fig.legend(handles=handles,loc="upper center",bbox_to_anchor=(.52,.99),ncol=2,columnspacing=3)
    fig.text(.52,.914,"每类目标、每个信噪比 360 条记录；18 个背景窗" if zh else
             "360 records per target and SNR; 18 background windows",ha="center",fontsize=7.5)
    save(fig,"fig07_真实背景注入_中文" if zh else "fig07_real_background_injection")


def fig8(zh):
    data=pd.read_csv(HERE/"source_data/FIG8_ALL_CASES.csv")
    track=pd.read_csv(HERE/"source_data/FIG8_EXAMPLE_TRACKS.csv")
    spec=pd.read_csv(HERE/"source_data/FIG8_EXAMPLE_SPECTRA.csv")
    with np.load(HERE/"source_data/FIG8_EXAMPLE_LOFAR.npz") as z:
        times=z["time_s"];frequency=z["frequency_Hz"];power=z["power_dB"]
    fig,axes=plt.subplots(2,2,figsize=(183/25.4,151/25.4))
    fig.subplots_adjust(left=.105,right=.89,bottom=.11,top=.86,wspace=.40,hspace=.60)
    a=axes[0,0];a.axhline(0,color="#cccccc",lw=.6,zorder=0)
    for i,group in enumerate(["strong","shallow","weak"]):
        d=data[data.group==group].sort_values(["tone_hz","segment_start_s"])
        values=d.gain_peak_vs_SMR_db.to_numpy()
        # Horizontal offsets prevent coincident marks; no observations are excluded.
        offsets=.21*np.sin(np.arange(len(d))*2.399963229728653)
        a.scatter(i+offsets,values,s=13,color=COLORS[group],alpha=.73,edgecolor="white",linewidth=.25,zorder=2)
        q=np.quantile(values,[.25,.5,.75]);a.plot([i+.31,i+.31],[q[0],q[2]],color="#323232",lw=1.2,zorder=3)
        a.plot([i+.25,i+.37],[q[1],q[1]],color="#323232",lw=1.8,zorder=3)
    a.set(xlim=(-.45,2.6),ylim=(-.45,5.25),ylabel="观测谱峰增量 (dB)" if zh else "Observed peak gain (dB)")
    a.set_xticks([0,1,2],["强线组\n(n=60)","浅源组\n(n=30)","弱线组\n(n=15)"] if zh else
                 ["Strong\n(n=60)","Shallow\n(n=30)","Weak\n(n=15)"])
    a.set_yticks([0,1,2,3,4,5]);label(a,"(a)")
    a=axes[0,1]
    m=(frequency>=135.94)&(frequency<=136.34)
    image=a.pcolormesh(times,frequency[m],power[m],cmap="cividis",vmin=-5,vmax=20,
                       shading="nearest",rasterized=True)
    a.plot(track.time_s,track.LPS_Hz,color="#dedede",lw=2.4,alpha=.95,zorder=3)
    a.plot(track.time_s,track.CDTR_Hz,color=ORANGE,lw=1.05,zorder=4)
    a.plot(track.time_s,track.guide_Hz,color="#82c8e8",lw=1.0,ls="--",zorder=5)
    a.set(xlim=(900,1200),ylim=(135.94,136.34),xlabel="时间 (s)" if zh else "Time (s)",
          ylabel="接收频率 (Hz)" if zh else "Received frequency (Hz)")
    a.set_xticks([900,1000,1100,1200]);a.set_yticks([136.0,136.1,136.2,136.3]);a.ticklabel_format(axis="y",useOffset=False)
    label(a,"(b)")
    # Colorbar sits outside the quantitative grid and does not resize the plot areas.
    bb=a.get_position();cbax=fig.add_axes([.915,bb.y0,.016,bb.height]);cb=fig.colorbar(image,cax=cbax)
    cb.set_label("超出背景 (dB)" if zh else "Above background (dB)",fontsize=7.5);cb.ax.tick_params(labelsize=7)
    a=axes[1,0];view=(abs(spec.residual_frequency_Hz)<=.025)
    for field,color,width in [("LPS",GRAY,1.4),("CDTR",ORANGE,1.2)]:
        d=spec[view];p=np.ma.masked_outside(d[field+"_dB"],-22,12)
        a.plot(d.residual_frequency_Hz,p,color=color,lw=width,label=field)
    a.set(xlim=(-.025,.025),ylim=(-22,12),xlabel="残余频率 (Hz)" if zh else "Residual frequency (Hz)",
          ylabel="相对功率 (dB)" if zh else "Relative power (dB)")
    a.set_xticks([-.02,-.01,0,.01,.02]);a.set_yticks([-20,-10,0,10])
    a.legend(loc="lower left",bbox_to_anchor=(0,1.01),ncol=2,handlelength=1.6,columnspacing=1.6)
    a.text(.96,.985,"峰值增量 3.09 dB" if zh else "Peak gain: 3.09 dB",transform=a.transAxes,
           fontsize=7.5,ha="right",va="top")
    label(a,"(c)")
    a=axes[1,1]
    a.axhline(0,color="#cccccc",lw=.6,zorder=0)
    opt=(track.time_s>=905)&(track.time_s<1195)
    a.plot(track.time_s[opt],track.correction_mHz[opt],color=ORANGE,lw=1.15)
    a.set(xlim=(900,1200),ylim=(-35,35),xlabel="时间 (s)" if zh else "Time (s)",
          ylabel="CDTR − LPS (mHz)")
    a.set_xticks([900,1000,1100,1200]);a.set_yticks([-30,-15,0,15,30]);label(a,"(d)")
    handles=[Line2D([],[],color=GRAY,lw=2,label="LPS"),
             Line2D([],[],color=ORANGE,lw=1.2,label="CDTR"),
             Line2D([],[],color=BLUE,lw=1.1,ls="--",label="强线多普勒参照" if zh else "Strong-tonal Doppler reference")]
    fig.legend(handles=handles,loc="upper center",bbox_to_anchor=(.52,.99),ncol=3,columnspacing=1.8)
    fig.text(.52,.925,"136 Hz，900–1200 s（面板 b–d）" if zh else "136 Hz, 900–1200 s (panels b–d)",
             ha="center",fontsize=7.5)
    save(fig,"fig08_自然线谱_中文" if zh else "fig08_natural_tonals",exclude_axes=[cbax])


if __name__=="__main__":
    for zh in [True,False]:
        matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei"] if zh else ["Arial","DejaVu Sans"]
        fig7(zh);fig8(zh)
