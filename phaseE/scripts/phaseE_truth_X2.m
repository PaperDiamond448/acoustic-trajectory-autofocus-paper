function phaseE_truth_X2()
% Recreate only truth and input fingerprints. No frontend/solver/chunks load.
root='D:\论文集'; out=fullfile(root,'phaseE','E1_trajexport');
addpath(fullfile(root,'phaseD','code'),'-begin'); addpath(fullfile(root,'phaseD','codeX'),'-begin');
phaseX_verify_sources(); [~,cfg,B]=phaseX_settings(300,false);
old=readtable(fullfile(root,'phaseD','X2_frontend','X2_records.csv'),'TextType','string');
old=old(old.frontend=="VS",:); assert(height(old)==1400);
truth=zeros(6000,1400); rows={}; timer=tic;
for i=1:height(old)
    r=old(i,:); scene=char(r.scene);
    seed=cfg.master_seed+54e6+1e4*cfg.scene_code.(scene)+r.record_id;
    assert(seed==r.seed);
    rec=simulate_baseband_T(cfg,scene,r.snr_db,seed,'eval',300);
    hash=phaseD_hash(rec.y,'MD5'); assert(strcmp(hash,char(r.input_hash)));
    truth(:,i)=rec.truth.gtrue(:);
    rows{end+1}=struct('truth_row',i-1,'scene',r.scene,'snr_db',r.snr_db, ...
        'record_id',r.record_id,'seed',seed,'input_hash',string(hash),'input_hash_match',true); %#ok<AGROW>
    if mod(i,100)==0,fprintf('X2 truth/hash recreation %d/1400: %.1fs\n',i,toc(timer));end
end
path=fullfile(out,'truth_X2_checked.h5'); assert(~exist(path,'file'));
h5create(path,'/truth',[6000 1400],'Datatype','double','ChunkSize',[6000 1],'Deflate',4);
h5write(path,'/truth',truth);
h5writeatt(path,'/','fs_hz',B.fs);
writetable(struct2table([rows{:}]),fullfile(out,'truth_X2_checked_index.csv'));
status=struct('complete',true,'records',1400,'all_input_hashes_match',true,'elapsed_seconds',toc(timer), ...
    'sha256',phaseD_hash(path,'SHA-256',true),'generator','simulate_baseband_T','no_frontend_or_solver',true);
f=fopen(fullfile(out,'truth_X2_checked_status.json'),'w','n','UTF-8');assert(f~=-1);
fprintf(f,'%s\n',jsonencode(status,'PrettyPrint',true));fclose(f);disp(status);
end
