function phaseE_ext_batch(stage,first,last)
root='D:\论文集';addpath(fullfile(root,'phaseD','code'));addpath(fullfile(root,'phaseD','codeX'));
lock=jsondecode(fileread(fullfile(root,'phaseE','PREREGISTRATION_PhaseE_20261007.sha256.json')));
assert(strcmp(phaseD_hash(fullfile(root,'phaseE',lock.file),'SHA-256',true),lock.sha256));
if strcmp(stage,'C'),dirname='E3_duration_ext';else,dirname='E2_frontend_ext';end
dest=fullfile(root,'phaseE',dirname);jobs=readtable(fullfile(dest,[stage '_jobs.csv']),'TextType','string');
for j=first:last
 if isfile(fullfile(root,'phaseE','STOP_REQUESTED')),error('PhaseE:StopRequested','Run stop requested.');end
 r=jobs(j,:);tag=char(r.tag);target=fullfile(dest,'records',[tag '.csv']);
 if isfile(target),fprintf('ALREADY SAVED %s\n',tag);continue;end
 fprintf('%s JOB %d/%d: %s\n',stage,j,height(jobs),tag);
 S=phaseE_ext_one(stage,char(r.scene),r.snr_db,r.record_id,r.duration_s);
 save(fullfile(dest,'records',[tag '.mat']),'S','-v7');writetable(struct2table(S.rows),target);
 if strcmp(stage,'B_reg'),writetable(struct2table([S.regcheck{:}]),fullfile(dest,'regression',[tag '.csv']));end
 clear S;
end
end
