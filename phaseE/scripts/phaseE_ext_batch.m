function phaseE_ext_batch(stage,first,last)
root='D:\论文集';addpath(fullfile(root,'phaseD','code'));addpath(fullfile(root,'phaseD','codeX'));
lock=jsondecode(fileread(fullfile(root,'phaseE','PREREGISTRATION_PhaseE_20261007.sha256.json')));
assert(strcmp(phaseD_hash(fullfile(root,'phaseE',lock.file),'SHA-256',true),lock.sha256));
if strcmp(stage,'C'),dirname='E3_duration_ext';else,dirname='E2_frontend_ext';end
dest=fullfile(root,'phaseE',dirname);jobs=readtable(fullfile(dest,[stage '_jobs.csv']),'TextType','string');
for j=first:last
 if isfile(fullfile(root,'phaseE','STOP_REQUESTED')),error('PhaseE:StopRequested','Run stop requested.');end
 r=jobs(j,:);tag=char(r.tag);target=fullfile(dest,'records',[tag '.csv']);
 if isfile(target)
  info=dir(target);
  if info.bytes>0,fprintf('ALREADY SAVED %s\n',tag);continue;end
 end
 fprintf('%s JOB %d/%d: %s\n',stage,j,height(jobs),tag);
 matpath=fullfile(dest,'records',[tag '.mat']);
 if isfile(matpath)
  q=load(matpath,'S');S=q.S;
  assert(strcmp(S.scene,char(r.scene)) && S.snr_db==r.snr_db && S.record_id==r.record_id && S.duration_s==r.duration_s,'PhaseE:CheckpointMismatch','Saved MAT does not match job.');
  fprintf('RESTORE CSV FROM SAVED MAT %s\n',tag);
 else
  S=phaseE_ext_one(stage,char(r.scene),r.snr_db,r.record_id,r.duration_s);
  mattemp=fullfile(dest,'records',[tag '.pending.mat']);save(mattemp,'S','-v7');
  [ok,msg]=movefile(mattemp,matpath);assert(ok,'PhaseE:SaveFailed','%s',msg);
 end
 expected=3;if strcmp(stage,'B_reg') || strcmp(stage,'C'),expected=2;end
 assert(numel(S.rows)==expected && all(isfinite([S.rows.eta_in])) && all(isfinite([S.rows.eta_out])),'PhaseE:CheckpointMismatch','Saved rows are incomplete.');
 csvtemp=fullfile(dest,'records',[tag '.pending.csv']);writetable(struct2table(S.rows),csvtemp);
 [ok,msg]=movefile(csvtemp,target,'f');assert(ok,'PhaseE:SaveFailed','%s',msg);
 if strcmp(stage,'B_reg')
  regtemp=fullfile(dest,'regression',[tag '.pending.csv']);writetable(struct2table([S.regcheck{:}]),regtemp);
  [ok,msg]=movefile(regtemp,fullfile(dest,'regression',[tag '.csv']),'f');assert(ok,'PhaseE:SaveFailed','%s',msg);
 end
 clear S;
end
end
