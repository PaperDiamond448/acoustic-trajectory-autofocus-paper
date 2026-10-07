from pathlib import Path
import shutil,json,hashlib
R=Path('D:/论文集/phaseD');O=R/'X3_real';A=O/'qa/initial_independent_window_screen';A.mkdir(parents=True,exist_ok=True)
assert not (O/'chunks').exists(),'Never change a testset after modules start'
names=['X3_visibility.csv','X3_FROZEN_TESTSET.csv','X3_FROZEN_DURATION_TESTSET.csv','X3_A3_comparison.csv','X3_TESTSET_FREEZE.json','X3_FREEZE_MANIFEST.csv','SCREEN_COMPLETE.json']
for name in names:shutil.copy2(O/name,A/name)
note={'status':'PRE_MODULE_INTERFACE_CORRECTION','reason':'Use exact original A3 continuous LOFAR frame support. Preliminary per-window frames omitted boundary frames. No module output existed. All raw inputs, thresholds and methods unchanged.','archived_files':{name:hashlib.sha256((A/name).read_bytes()).hexdigest() for name in names}}
(A/'CORRECTION_RECORD.json').write_text(json.dumps(note,ensure_ascii=False,indent=2),encoding='utf-8');print('Preliminary screen archived before any real-data module')
