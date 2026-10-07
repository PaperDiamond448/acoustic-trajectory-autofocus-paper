"""Display-only export wrapper: original frozen plotting source and data unchanged."""
from pathlib import Path
import json,hashlib
import plot_phaseX as plots
import matplotlib.patheffects as path_effects
plots.plt.rcParams['savefig.dpi']=600
original_save=plots.save
def final_save(fig,O,name):
 if name=='fig_X3_trajectory_duration':
  ax=fig.axes[0];legend=ax.get_legend();legend.set_bbox_to_anchor((.5,1.16),transform=ax.transAxes)
  for text in legend.get_texts():
   text.set_text({'GPS_Hz':'GPS reference','VS_FM':'ADA'}.get(text.get_text(),text.get_text()))
  stroke=[path_effects.withStroke(linewidth=1.7,foreground='#666666')]
  for line in ax.lines:
   if line.get_color()=='#F8F8F8':line.set_path_effects(stroke)
  for line in legend.legend_handles:
   if line.get_color()=='#F8F8F8':line.set_path_effects(stroke)
 original_save(fig,O,name)
plots.save=final_save
for fn in [plots.x1,plots.x2,plots.x3]:fn()
R=Path('D:/论文集/phaseD')
(R/'Y_compute/FIGURE_EXPORT_WRAPPER.json').write_text(json.dumps({'status':'EXPORTED','wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'change':'Set savefig.dpi=600 for PDF/SVG raster layers; move trajectory legend below title, use GPS reference/ADA display labels, outline white SMR overlay for legend contrast. All plotted data, cases, axes and intervals unchanged. PNG already600dpi.','plot_source_unchanged':True},indent=2),encoding='utf-8')
