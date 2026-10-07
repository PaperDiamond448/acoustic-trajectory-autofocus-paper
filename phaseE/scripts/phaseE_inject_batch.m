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
 r=jobs(j,:);target=fullfile(dest,'records',[char(r.tag) '.csv']);
 if isfile(target),fprintf('ALREADY SAVED %s\n',char(r.tag));continue;end
 fprintf('D JOB %d/%d: %s\n',j,height(jobs),char(r.tag));
 S=phaseE_inject_one(r.band_id,r.window_id,r.target_kind,r.snr_db,r.record_id);
 save(fullfile(dest,'records',[char(r.tag) '.mat']),'S','-v7');writetable(struct2table(S.rows),target);clear S;
end
end
