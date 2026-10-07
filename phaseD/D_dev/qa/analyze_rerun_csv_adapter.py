"""Read binary CSV flags as Boolean; keep original analysis and data intact."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(r'D:\论文集\phaseD');OUT=ROOT/'D_dev'
proof=json.loads((OUT/'qa/csv_trigger_representation_check.json').read_text(encoding='utf8'))
assert proof['status']=='PASS' and proof['triggered_records']==323
for name,want in proof['csv_sha256'].items():
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==want
sys.path.insert(0,str(ROOT/'code'))
import analyze_phaseD_dev as original
original_read=original.read
def read_binary_flags(name):
    table=original_read(name)
    if 'triggered' in table:
        assert table.triggered.notna().all() and table.triggered.isin([0,1]).all()
        table['triggered']=table.triggered.eq(1)
    return table
original.read=read_binary_flags
original.rerun()
for name,want in proof['csv_sha256'].items():
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==want
print('CSV binary-flag adaptation complete; original inputs unchanged.')
