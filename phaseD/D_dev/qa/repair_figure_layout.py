"""Output-only layout correction; numerical sources/manifests stay frozen."""
from pathlib import Path
import sys,json
ROOT=Path(r'D:\论文集\phaseD');sys.path.insert(0,str(ROOT/'code'))
import plot_phaseD_dev as plot
import pandas as pd
original_save=plot.save
def checked_save(fig,name):
    if name=='fig_D1_observed_peak':
        fig.subplots_adjust(top=.76)
    if name.startswith('fig_D1_'):
        identities={plot.colors['F02']:('o','-'),plot.colors['UNB']:('^','--'),plot.colors['Control']:('s',':')}
        for line in [line for ax in fig.axes for line in ax.lines]+[line for legend in fig.legends for line in legend.get_lines()]:
            if line.get_color() in identities:
                marker,style=identities[line.get_color()];line.set_marker(marker);line.set_linestyle(style)
    original_save(fig,name)
plot.save=checked_save
if len(sys.argv)>1 and sys.argv[1]=='peak':
    plot.d1_plot(pd.read_csv(plot.OUT/'D1_summary.csv'),'peak_db','fig_D1_observed_peak')
else:
    plot.plot_all()
(plot.OUT/'qa/figure_layout_correction.json').write_text(json.dumps({'scope':'display only','original_source_unchanged':True,'decision_inputs_affected':False,'figure':'fig_D1_observed_peak','change':'top subplot boundary 0.84 -> 0.76 to separate panel b from shared legend','method_identity':'D1 F02 solid circle; UNB dashed triangle; unscaled Control dotted square; legend updated consistently','reason':'Rendered PDF collision audit found a text-box overlap; subsequent exports must use this wrapper.'},indent=2),encoding='utf8')
