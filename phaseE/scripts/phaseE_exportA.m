function phaseE_exportA(stage,T)
% Export archived trajectories. No frontend or optimizer is rerun here.
root='D:\论文集'; out=fullfile(root,'phaseE','E1_trajexport');
addpath(fullfile(root,'phaseD','code'),'-begin');
addpath(fullfile(root,'phaseD','codeX'),'-begin');
pre=jsondecode(fileread(fullfile(root,'phaseE','E0_preflight','preflight_status.json')));
assert(pre.passed && pre.checked_frontend_rows==12);
% The replay process exited during shutdown after saving. Read its saved S
% structures back and verify against the complete 12-row CSV before export.
pr=readtable(fullfile(root,'phaseE','E0_preflight','preflight_records.csv'),'TextType','string');
pf=dir(fullfile(root,'phaseE','E0_preflight','rerun_*.mat')); assert(numel(pf)==3);
checked=0;
for j=1:numel(pf)
    Q=load(fullfile(pf(j).folder,pf(j).name),'S');
    for k=1:numel(Q.S.rows)
        r=Q.S.rows(k);
        rr=pr(pr.scene==r.scene&pr.snr_db==r.snr_db&pr.record_id==r.record_id&pr.frontend==r.frontend,:);
        assert(height(rr)==1 && strcmp(char(r.input_hash),char(rr.input_hash_replayed)));
        assert(abs(r.eta_in-rr.eta_in_replayed)<1e-14 && abs(r.eta_out-rr.eta_out_replayed)<1e-14);
        checked=checked+1;
    end
end
assert(checked==12);
fprintf('Saved preflight MAT/CSV readback: all 12 rows match.\n');
phaseX_verify_sources();
[~,cfg,B]=phaseX_settings(T,false);
assert(B.fs==20 && B.fft_pad==8 && isequal(B.band,[-2 2]));
if strcmp(stage,'X2')
    phase=54; source=fullfile(root,'phaseD','X2_frontend');
    tab=readtable(fullfile(source,'X2_records.csv'),'TextType','string');
    names={'VS','MFT','SUV','V0'}; stem=sprintf('traj_export_X2');
    ntruth=1400;
else
    assert(strcmp(stage,'X1')); phase=53; source=fullfile(root,'phaseD','X1_duration');
    tab=readtable(fullfile(source,'X1_records.csv'),'TextType','string');
    tab=tab(tab.duration_s==T,:); names={'VS'};
    stem=sprintf('traj_export_X1_T%d',T); ntruth=600;
end
N=T*B.fs; nrows=ntruth*numel(names); path=fullfile(out,[stem '.h5']);
assert(~exist(path,'file'),'PhaseE:AlreadyExists','Export already exists; do not overwrite.');
h5create(path,'/truth',[N ntruth],'Datatype','double','ChunkSize',[N 1],'Deflate',4);
h5create(path,'/input',[N nrows],'Datatype','double','ChunkSize',[N 1],'Deflate',4);
h5create(path,'/output',[N nrows],'Datatype','double','ChunkSize',[N 1],'Deflate',4);
h5writeatt(path,'/','fs_hz',B.fs); h5writeatt(path,'/','duration_s',T);
h5writeatt(path,'/','evaluation_interval_s',[5 T-5]);
h5writeatt(path,'/','frequency_units','Hz baseband');
h5writeatt(path,'/','time_grid','t=n/20, n=0,...,N-1');
h5writeatt(path,'/','index_origin',0);
files=dir(fullfile(source,'chunks',sprintf('T%d_*.mat',T)));
assert(numel(files)==ntruth/10);
config=struct('task','A','stage',stage,'duration_s',T,'phase_id',phase, ...
    'truth_records',ntruth,'trajectory_rows',nrows,'samples_per_row',N, ...
    'fs_hz',B.fs,'evaluation_interval_s',[5 T-5],'source_directory',source, ...
    'seed_rule',sprintf('master_seed+%de6+1e4*scene_code+record_id',phase), ...
    'frontends',{names},'h5_local_path',path,'matlab_version',version, ...
    'no_new_estimation',true,'chunk_count',numel(files));
writejson(fullfile(out,[stem '_run_config.json']),config);
rows={}; hashes={}; truthrow=0; row=0; timer=tic;
sig=phaseD_hash(fullfile(root,'phaseD','codeX','SOURCE_MANIFEST_X_sha256.csv'),'SHA-256',true);
for j=1:numel(files)
    file=fullfile(files(j).folder,files(j).name);
    before=phaseD_hash(file,'SHA-256',true);
    C=load(file,'results','signature','phase_id');
    assert(C.phase_id==phase && strcmp(C.signature,sig));
    assert(numel(C.results)==10);
    for k=1:numel(C.results)
        S=C.results(k); scene=char(S.scene); snr=S.snr_db; rid=S.record_id;
        seed=cfg.master_seed+phase*1e6+1e4*cfg.scene_code.(scene)+rid;
        rec=simulate_baseband_T(cfg,scene,snr,seed,'eval',T);
        hash=phaseD_hash(rec.y,'MD5');
        assert(strcmp(hash,char(S.input_hash)),'PhaseE:InputMismatch','Input hash differs from archived chunk.');
        assert(numel(rec.t)==N && isequal(rec.t,(0:N-1)'/20));
        h5write(path,'/truth',rec.truth.gtrue(:),[1 truthrow+1],[N 1]);
        idx=find(rec.t>=5&rec.t<T-5);
        for f=1:numel(names)
            if strcmp(stage,'X2')
                d=S.details{f}; assert(strcmp(d.frontend,names{f}));
                gi=d.input_g; go=d.ada.out.g; methodmask=tab.frontend==string(names{f});
            else
                gi=S.smr.g; go=S.ada.out.g;
                methodmask=tab.method=="ADA_local_c04_t30_A";
            end
            expected=tab(tab.scene==string(scene)&tab.snr_db==snr&tab.record_id==rid&methodmask,:);
            assert(height(expected)==1 && expected.seed==seed && strcmp(hash,char(expected.input_hash)));
            mi=phaseD_measure(rec,gi,idx,B); mo=phaseD_measure(rec,go,idx,B);
            if strcmp(stage,'X2')
                ei=expected.eta_in; eo=expected.eta_out; usable=expected.input_usable;
            else
                ei=expected.eta_SMR; eo=expected.eta;
                e=gi(idx)-rec.truth.gtrue(idx); usable=mean(abs(e-mean(e))<=.1)>=.9;
            end
            assert(abs(mi.eta-ei)<1e-9 && abs(mo.eta-eo)<1e-9, ...
                'PhaseE:SavedEtaMismatch','Exported trajectory does not reproduce the archived eta.');
            assert(numel(gi)==N&&numel(go)==N&&all(isfinite(gi(:)))&&all(isfinite(go(:))));
            h5write(path,'/input',gi(:),[1 row+1],[N 1]);
            h5write(path,'/output',go(:),[1 row+1],[N 1]);
            rows{end+1}=struct('row',row,'truth_row',truthrow,'scene',string(scene),'snr_db',snr, ...
                'record_id',rid,'seed',seed,'frontend',string(names{f}),'eta_in',ei,'eta_out',eo, ...
                'input_usable',usable,'input_hash',string(hash),'duration_s',T, ...
                'eta_in_matlab_check',mi.eta,'eta_out_matlab_check',mo.eta, ...
                'eta_in_matlab_abs_diff',abs(mi.eta-ei),'eta_out_matlab_abs_diff',abs(mo.eta-eo)); %#ok<AGROW>
            row=row+1;
        end
        truthrow=truthrow+1;
    end
    after=phaseD_hash(file,'SHA-256',true); assert(strcmp(before,after));
    hashes{end+1}=struct('path',string(file),'bytes',files(j).bytes,'sha256_before',string(before), ...
        'sha256_after',string(after),'unchanged',true); %#ok<AGROW>
    fprintf('%s T%d export chunk %d/%d: truth=%d rows=%d elapsed=%.1fs\n',stage,T,j,numel(files),truthrow,row,toc(timer));
    if mod(j,10)==0
        writetable(struct2table([rows{:}]),fullfile(out,[stem '_index.partial.csv']));
    end
end
assert(row==nrows && truthrow==ntruth);
R=struct2table([rows{:}]);
writetable(R,fullfile(out,[stem '_index.csv']));
writetable(struct2table([hashes{:}]),fullfile(out,[stem '_source_chunks_sha256.csv']));
status=struct('export_complete',true,'trajectory_rows',row,'truth_records',truthrow, ...
    'all_input_hashes_match',true,'all_source_chunks_unchanged',true, ...
    'max_eta_in_matlab_abs_diff',max(R.eta_in_matlab_abs_diff), ...
    'max_eta_out_matlab_abs_diff',max(R.eta_out_matlab_abs_diff),'elapsed_seconds',toc(timer), ...
    'h5_sha256',phaseD_hash(path,'SHA-256',true));
writejson(fullfile(out,[stem '_export_status.json']),status);
disp(status);
end

function writejson(path,value)
f=fopen(path,'w','n','UTF-8'); assert(f~=-1); c=onCleanup(@()fclose(f));
fprintf(f,'%s\n',jsonencode(value,'PrettyPrint',true));
end
