function phaseE_preflight()
% Read-only replay of three archived X2 records; output only to phaseE.
root='D:\论文集'; out=fullfile(root,'phaseE','E0_preflight');
addpath(fullfile(root,'phaseD','code'),'-begin');
addpath(fullfile(root,'phaseD','codeX'),'-begin');
assert(strcmp(version('-release'),'2023a'));
old=readtable(fullfile(root,'phaseD','X2_frontend','X2_records.csv'),'TextType','string');
cases={'S0',-16,1;'S2',-20,7;'S0',-8,50};
config=struct('task','0.1','matlab_version',version,'matlab_release',version('-release'), ...
    'eta_tolerance',1e-9,'driver','phaseX2_one','output_root',out, ...
    'cases',struct('scene',cases(:,1),'snr_db',cases(:,2),'record_id',cases(:,3)));
writejson(fullfile(out,'run_config.json'),config);
rows={}; clock0=tic; pass=true;
for i=1:size(cases,1)
    scene=cases{i,1}; snr=cases{i,2}; rid=cases{i,3};
    fprintf('PRECHECK %d/3: %s SNR=%g id=%d\n',i,scene,snr,rid);
    S=phaseX2_one(scene,snr,rid);
    save(fullfile(out,sprintf('rerun_%s_snr%g_id%d.mat',scene,snr,rid)),'S','-v7.3');
    for k=1:numel(S.rows)
        r=S.rows(k);
        expected=old(old.scene==string(scene)&old.snr_db==snr&old.record_id==rid&old.frontend==r.frontend,:);
        assert(height(expected)==1);
        di=abs(r.eta_in-expected.eta_in); do=abs(r.eta_out-expected.eta_out);
        hash_match=strcmp(char(r.input_hash),char(expected.input_hash));
        ok=hash_match && di<1e-9 && do<1e-9;
        rows{end+1}=struct('scene',string(scene),'snr_db',snr,'record_id',rid, ...
            'seed',r.seed,'frontend',r.frontend,'input_hash_saved',expected.input_hash, ...
            'input_hash_replayed',r.input_hash,'input_hash_match',hash_match, ...
            'eta_in_saved',expected.eta_in,'eta_in_replayed',r.eta_in,'eta_in_abs_diff',di, ...
            'eta_out_saved',expected.eta_out,'eta_out_replayed',r.eta_out,'eta_out_abs_diff',do,'passed',ok); %#ok<AGROW>
        fprintf('  %s hash=%d eta_in_diff=%.3g eta_out_diff=%.3g pass=%d\n',r.frontend,hash_match,di,do,ok);
        pass=pass && ok;
    end
    writetable(struct2table([rows{:}]),fullfile(out,'preflight_records.csv'));
    if ~pass, break; end
end
R=struct2table([rows{:}]);
status=struct('passed',pass,'checked_records',i,'checked_frontend_rows',height(R), ...
    'max_eta_in_abs_diff',max(R.eta_in_abs_diff),'max_eta_out_abs_diff',max(R.eta_out_abs_diff), ...
    'input_hashes_match',all(R.input_hash_match),'elapsed_seconds',toc(clock0));
writejson(fullfile(out,'preflight_status.json'),status);
disp(status);
assert(pass,'PhaseE:PreflightMismatch','Preflight differs from frozen X2 outputs; stop Phase E.');
end

function writejson(path,value)
f=fopen(path,'w','n','UTF-8'); assert(f~=-1); c=onCleanup(@()fclose(f));
fprintf(f,'%s\n',jsonencode(value,'PrettyPrint',true));
end
