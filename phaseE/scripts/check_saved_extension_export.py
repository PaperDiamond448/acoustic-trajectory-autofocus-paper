"""Check the new extension exporter on saved B records without rerunning MATLAB."""
from pathlib import Path
import json
import shutil
import pandas as pd
import finalize_extension as finalize

root=Path(__file__).resolve().parents[2]
source=root/'phaseE/E2_frontend_ext'
out=root/'phaseE/E0_preflight/extension_export_check'
(out/'records').mkdir(parents=True,exist_ok=True)
jobs=pd.read_csv(source/'B_jobs.csv').iloc[:3].copy()
for row in jobs.itertuples(index=False):
    for suffix in ('.csv','.mat'):
        src=source/'records'/f'{row.tag}{suffix}'
        assert src.exists(),str(src)
        shutil.copy2(src,out/'records'/src.name)
status=finalize.export(out,'B',jobs,300)
status['scope']='Exporter check on three saved inputs, nine method outputs; task B remains incomplete.'
(out/'CHECK_STATUS.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
print(json.dumps(status),flush=True)
