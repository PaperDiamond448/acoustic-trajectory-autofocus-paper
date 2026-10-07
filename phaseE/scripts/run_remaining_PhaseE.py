"""Resume B regression, then B/C/D; validate and push once each task completes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,os,subprocess,sys,time,traceback,threading
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];PHASE=ROOT/'phaseE';SCRIPTS=Path(__file__).parent
REPO=ROOT/'GitHub整理_20261007/acoustic-trajectory-autofocus-paper'
MATLAB=Path(r'C:\Program Files\MATLAB\R2023a\bin\matlab.exe')
DIRS={'B_reg':'E2_frontend_ext','B':'E2_frontend_ext','C':'E3_duration_ext','D':'E5_inject'}
STATE=PHASE/'REMAINING_RUN_STATUS.json'
STOP=threading.Event()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
LOCK=json.loads((PHASE/'PREREGISTRATION_PhaseE_20261007.sha256.json').read_text())
EXPECTED_PLAN=LOCK['sha256']
CORE_HASHES={p:sha(SCRIPTS/p) for p in ('estimate_dhmm.m','phaseE_ext_one.m','phaseE_ext_batch.m','phaseE_inject_one.m','phaseE_inject_batch.m','finalize_extension.py')}
def guard():
    assert not (PHASE/'STOP_REQUESTED').exists(),'Run stop requested.'
    assert sha(PHASE/LOCK['file'])==EXPECTED_PLAN,'Phase E plan changed during the run.'
    for n,v in CORE_HASHES.items():assert sha(SCRIPTS/n)==v,f'New experiment implementation changed during run: {n}'
def status(stage,**kw):
    v={'stage':stage,'updated_local':time.strftime('%Y-%m-%d %H:%M:%S'),'preregistration_sha256':EXPECTED_PLAN,**kw}
    STATE.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(v,ensure_ascii=False),flush=True)
def valid_record(out,tag,n):
    p=out/'records'/f'{tag}.csv';m=p.with_suffix('.mat')
    if not p.exists():return False
    assert m.exists(),f'Saved CSV without MAT: {p}'
    d=pd.read_csv(p)
    assert len(d)==n and d.frontend.nunique()==n and d[['eta_in','eta_out']].notna().all().all(),f'Incomplete saved record: {p}'
    return True
def run_batch(stage,a,b,jobs):
    if STOP.is_set():return
    guard();out=PHASE/DIRS[stage];n={'B_reg':2,'B':3,'C':2,'D':6}[stage]
    log=out/f'run_{stage}_{a:05d}_{b:05d}.log'
    call=f"phaseE_inject_batch({a},{b})" if stage=='D' else f"phaseE_ext_batch('{stage}',{a},{b})"
    cmd=[str(MATLAB),'-batch',f"addpath('{SCRIPTS}'); {call}",'-logfile',str(log)]
    for attempt in range(3):
        if STOP.is_set():return
        guard()
        if all(valid_record(out,jobs.iloc[j-1].tag,n) for j in range(a,b+1)):return
        p=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        complete=all(valid_record(out,jobs.iloc[j-1].tag,n) for j in range(a,b+1))
        if complete:return
        if p.returncode not in (-1073740940,3221226356):
            raise RuntimeError(f'{stage} batch {a}:{b} failed (exit {p.returncode}); see {log}')
        print('Saved rows preserved; retry incomplete heap-crash batch',stage,a,b,attempt+1,flush=True)
    raise RuntimeError(f'Repeated MATLAB heap crash in {stage} batch {a}:{b}; stopped.')
def git(*args):return subprocess.run([r'D:\Git\cmd\git.exe',*args],cwd=REPO,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
def commit_and_push(stage):
    guard();git('add','--',f'phaseE/{DIRS[stage]}','phaseE/scripts','phaseE/README.md')
    diff=subprocess.run([r'D:\Git\cmd\git.exe','diff','--cached','--quiet'],cwd=REPO)
    if diff.returncode==1:git('commit','-m',f'Phase E task {stage}: complete and independently verify all planned records')
    elif diff.returncode!=0:raise RuntimeError('Cannot inspect staged changes')
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/'GitHub整理_20261007/push_git_api.py')],check=True)
def main():
    guard()
    runtime={'workers_matlab':2,'batch_records':25,'preregistration_sha256':EXPECTED_PLAN,'new_implementation_sha256':CORE_HASHES,
        'order':['B_reg','B','C','D'],'heap_crash_retry_limit':3,'other_errors':'stop and report','upload':'once task complete after eta/hash verification'}
    (PHASE/'REMAINING_RUN_CONFIG.json').write_text(json.dumps(runtime,indent=2)+'\n',encoding='utf-8')
    for stage in ['B_reg','B','C','D']:
        out=PHASE/DIRS[stage];jobs=pd.read_csv(out/f'{stage}_jobs.csv');n={'B_reg':2,'B':3,'C':2,'D':6}[stage]
        if stage!='B_reg' and (out/'FINAL_STATUS.json').exists():
            assert json.loads((out/'FINAL_STATUS.json').read_text())['complete'];continue
        chunks=[]
        for a in range(1,len(jobs)+1,25):
            b=min(a+24,len(jobs))
            if not all(valid_record(out,jobs.iloc[j-1].tag,n) for j in range(a,b+1)):chunks.append((a,b))
        status(stage,state='running',input_records=len(jobs),pending_batches=len(chunks))
        with ThreadPoolExecutor(max_workers=2) as pool:
            future={pool.submit(run_batch,stage,a,b,jobs):(a,b) for a,b in chunks}
            for done in as_completed(future):
                try:done.result()
                except Exception:
                    STOP.set()
                    for f in future:f.cancel()
                    raise
                count=sum(valid_record(out,r.tag,n) for r in jobs.itertuples(index=False))
                status(stage,state='running',input_records=len(jobs),completed_inputs=count)
        if stage=='B_reg':
            reg=pd.concat([pd.read_csv(p) for p in (out/'regression').glob('B_reg*.csv')],ignore_index=True)
            assert len(reg)==140 and reg.passed.all() and max(reg.eta_in_abs_diff.max(),reg.eta_out_abs_diff.max())<1e-9
            reg.to_csv(out/'REGRESSION_CHECKS.csv',index=False)
            status(stage,state='complete',checked_method_rows=140);continue
        subprocess.run([sys.executable,'-X','utf8',str(SCRIPTS/'finalize_extension.py'),stage],check=True)
        text=(PHASE/'README.md').read_text(encoding='utf-8')
        line=f'\n任务 {stage}：完整结果已生成并核对，见 [{DIRS[stage]}]({DIRS[stage]}/README.md)。\n'
        (PHASE/'README.md').write_text(text+line,encoding='utf-8')
        (REPO/'phaseE/README.md').write_text(text+line,encoding='utf-8')
        commit_and_push(stage);status(stage,state='complete',input_records=len(jobs),method_rows=len(jobs)*n,uploaded=True)
    status('B/C/D',state='complete',uploaded=True)
if __name__=='__main__':
    try:main()
    except Exception as e:
        stage=json.loads(STATE.read_text()).get('stage','B') if STATE.exists() else 'B'
        out=PHASE/DIRS.get(stage,'E2_frontend_ext');msg='运行停止：'+str(e)+'\n\n冻结原代码和已保存结果未改动；未完成任务保持未完成，不根据结果改参数。详细日志留本机。\n'
        (out/'README_STOPPED.md').write_text(msg,encoding='utf-8');dest=REPO/out.relative_to(ROOT);dest.mkdir(parents=True,exist_ok=True)
        (dest/'README_STOPPED.md').write_text(msg,encoding='utf-8');status(stage,state='stopped',reason=str(e));traceback.print_exc()
        try:
            git('add','--',str((out/'README_STOPPED.md').relative_to(ROOT)).replace('\\','/'))
            git('commit','-m',f'Phase E task {stage}: report stopped run without changing frozen methods')
            subprocess.run([sys.executable,'-X','utf8',str(ROOT/'GitHub整理_20261007/push_git_api.py')],check=True)
        except Exception:traceback.print_exc()
        sys.exit(1)
