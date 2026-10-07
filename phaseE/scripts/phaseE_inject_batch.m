function phaseE_inject_batch(first,last)
root='D:\论文集';addpath(fullfile(root,'phaseD','code'));addpath(fullfile(root,'phaseD','codeX'));
lock=jsondecode(fileread(fullfile(root,'phaseE','PREREGISTRATION_PhaseE_20261007.sha256.json')));
assert(strcmp(phaseD_hash(fullfile(root,'phaseE',lock.file),'SHA-256',true),lock.sha256));
dest=fullfile(root,'phaseE','E5_inject');cal=fullfile(dest,'screen_revision_20261007');
screen=jsondecode(fileread(fullfile(cal,'BACKGROUND_SCREEN_REVISED_FREEZE.json')));
assert(screen.screen_complete && strcmp(phaseD_hash(fullfile(cal,'BACKGROUND_SCREEN_REVISED.csv'),'SHA-256',true),screen.screen_csv_sha256));
jobs=readtable(fullfile(dest,'D_jobs.csv'),'TextType','string');
for j=first:last
 if isfile(fullfile(root,'phaseE','STOP_REQUESTED')),error('PhaseE:StopRequested','Run stop requested.');end
 r=jobs(j,:);tag=char(r.tag);target=fullfile(dest,'records',[tag '.csv']);
 if isfile(target)
  info=dir(target);
  if info.bytes>0,fprintf('ALREADY SAVED %s\n',tag);continue;end
 end
 fprintf('D JOB %d/%d: %s\n',j,height(jobs),tag);
 matpath=fullfile(dest,'records',[tag '.mat']);
 if isfile(matpath)
  q=load(matpath,'S');S=q.S;
  assert(S.band_id==r.band_id && S.window_id==r.window_id && S.target_kind==r.target_kind && S.snr_db==r.snr_db && S.record_id==r.record_id,'PhaseE:CheckpointMismatch','Saved MAT does not match injection job.');
  fprintf('RESTORE CSV FROM SAVED MAT %s\n',tag);
 else
  S=phaseE_inject_one(r.band_id,r.window_id,r.target_kind,r.snr_db,r.record_id);
  mattemp=fullfile(dest,'records',[tag '.pending.mat']);save(mattemp,'S','-v7');
  [ok,msg]=movefile(mattemp,matpath);assert(ok,'PhaseE:SaveFailed','%s',msg);
 end
 assert(numel(S.rows)==6 && all(isfinite([S.rows.eta_in])) && all(isfinite([S.rows.eta_out])),'PhaseE:CheckpointMismatch','Saved rows are incomplete.');
 csvtemp=fullfile(dest,'records',[tag '.pending.csv']);writetable(struct2table(S.rows),csvtemp);
 [ok,msg]=movefile(csvtemp,target,'f');assert(ok,'PhaseE:SaveFailed','%s',msg);clear S;
end
end
