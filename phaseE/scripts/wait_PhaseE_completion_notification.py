"""One-time local notification after B/C/D verification and GitHub upload."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
PHASE=ROOT/'phaseE'
OUT=PHASE/'_completion_notification'
REPO=ROOT/'GitHub整理_20261007/acoustic-trajectory-autofocus-paper'
OUT.mkdir(exist_ok=True)
STATUS=OUT/'status.json'
TZ=timezone(timedelta(hours=8))

def write_status(**items):
    value={'updated_local':datetime.now(TZ).isoformat(),**items}
    STATUS.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def notify(title,body,**details):
    message={'title':title,'body':body}
    (OUT/'message.json').write_text(json.dumps(message,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    script=PHASE/'scripts/submit_completion_notification.ps1'
    result=subprocess.run([r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
        '-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(script)],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    (OUT/'delivery.stdout.log').write_bytes(result.stdout)
    (OUT/'delivery.stderr.log').write_bytes(result.stderr)
    write_status(notification_submitted=result.returncode==0,notification_exit_code=result.returncode,**details)

def main():
    write_status(state='waiting',notify_when='B/C/D complete, validated and uploaded; or actual run stops',poll_seconds=60)
    while True:
        try:
            state=json.loads((PHASE/'REMAINING_RUN_STATUS.json').read_text(encoding='utf-8-sig'))
        except (FileNotFoundError,json.JSONDecodeError):
            time.sleep(60)
            continue
        if state.get('state')=='stopped':
            notify('论文扩展实验已暂停',f'任务 {state.get("stage","")} 停止。原因及已保存结果见 phaseE 对应 README。',
                   state='run_stopped',run_state=state)
            return
        if state.get('stage')=='B/C/D' and state.get('state')=='complete' and state.get('uploaded'):
            files={'E2_frontend_ext':(1400,4200),'E3_duration_ext':(2400,4800),'E5_inject':(5040,30240)}
            finals={}
            for folder,(inputs,rows) in files.items():
                result=json.loads((PHASE/folder/'FINAL_STATUS.json').read_text(encoding='utf-8'))
                assert result['complete'] and result['eta_recomputation_passed'] and result['protected_files_unchanged']==154
                assert result['input_records']==inputs and result['method_rows']==rows
                finals[folder]=result
            def ref(name):
                return subprocess.check_output([r'D:\Git\cmd\git.exe','rev-parse',name],cwd=REPO).decode().strip()
            head=ref('HEAD');uploaded=ref('refs/remotes/origin/main')
            assert head==uploaded,'Local and uploaded commit references differ.'
            notify('论文扩展实验已完成','B、C、D 全部完成核验并推送至 GitHub。完整报告已列入仓库 phaseE 入口。',
                   state='complete',verified_commit=head,task_status=finals)
            return
        time.sleep(60)

if __name__=='__main__':
    try:
        main()
    except Exception as error:
        write_status(state='notification_error',error=str(error))
        raise
