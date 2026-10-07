from pathlib import Path
import csv,hashlib,json
R=Path('D:/论文集/phaseD');names=['analyze_phaseX.py','plot_phaseX.py','audit_phaseX.py','audit_phaseX_figures.py','audit_real_metrics.py','audit_phaseX_saved.m','audit_phaseX3_saved.m','export_phaseX3_lofar.m','write_phaseX_report.py','package_phaseX.py','FIGURE_CONTRACT.md']
with (R/'codeX/POSTPROCESS_MANIFEST_sha256.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['source_file','sha256']);w.writerows((str(R/'codeX'/name),hashlib.sha256((R/'codeX'/name).read_bytes()).hexdigest()) for name in names)
print('Preanalysis postprocessing manifest registered:',len(names))
