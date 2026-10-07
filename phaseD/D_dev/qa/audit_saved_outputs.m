function audit_saved_outputs()
% Read-only audit of saved numerical outputs. No simulation or optimisation.
root='D:\论文集\phaseD'; out=fullfile(root,'D_dev');
stages={'D1','fixed','rerunA','rerunB','grid'};
report=struct('status','PASS','scope','All existing completed development chunks; saved-output consistency only; no objective recomputation or optimisation','stages',struct());
for si=1:numel(stages)
    stage=stages{si}; folder=fullfile(out,[stage '_chunks']);
    if ~exist(folder,'dir'),continue;end
    files=dir(fullfile(folder,'*.mat')); files=files(~endsWith({files.name},'.partial.mat'));
    assert(numel(files)==84,'Stage incomplete.'); nr=0;nc=0;na=0;nh=0;
    for fi=1:numel(files)
        C=load(fullfile(folder,files(fi).name),'results');
        for ri=1:numel(C.results)
            S=C.results(ri);nr=nr+1;
            for di=1:numel(S.details)
                d=S.details{di};r=S.rows(di);nc=nc+1;
                assert(strcmp(S.input_hash,r.input_hash));
                assert(r.seed==20260915+51e6+(1+2*strcmp(S.scene,'S2'))*1e4+S.record_id);
                assert(r.eta>=0 && r.eta<=1 && isfinite(r.eta));
                assert(r.P==300/r.Delta_s+1);
                if isfield(d,'ada')
                    a=d.ada; o=a.out; m=a.m;na=na+1;
                    assert(numel(a.logs)==a.rounds+1 && a.rounds<=2);
                    assert(a.triggered==(a.rounds>0));
                    match=regexp(d.method,'_c(\d+)_t(\d+)_','tokens','once');
                    if isempty(match),cap=4;tau=20;else,cap=str2double(match{1})/2;tau=str2double(match{2});end
                    assert(all(m<=cap) && all(ismember(m,[1 2 4])));
                    for k=1:numel(a.logs)
                        L=a.logs{k}; check_out(L.out,L.m,r.P);
                        globalmode=startsWith(d.method,'ADA_global') || startsWith(d.method,'ADA_AB');
                        if globalmode,assert(all(L.m==L.m(1)));end
                        if k>1
                            prev=a.logs{k-1};
                            assert(prev.dwell_s>=tau);
                            assert(isequal(L.out.u_init,prev.out.u));
                            assert(isequal(L.out.cands{1},prev.out.u));
                            assert(L.J>=prev.J-1e-12);
                            assert(all(L.m>=prev.m) && all(L.m<=2*prev.m));
                            if globalmode,assert(all(L.m==2*prev.m));end
                        end
                    end
                    assert(isequal(o.u,a.logs{end}.out.u));
                else
                    o=d.out;
                    if strcmp(d.method,'UNB'),m=Inf(r.P,1);
                    else,rad=sscanf(d.method,'F%d');m=rad/2*ones(r.P,1);end
                    check_out(o,m,r.P);
                end
                assert(r.J==o.J_best && r.hard_fail==o.hard_fail);
                nh=nh+double(o.hard_fail);
            end
        end
    end
    assert(nr==840);
    report.stages.(stage)=struct('chunks',numel(files),'records',nr,'configuration_rows',nc,'ada_variants_checked',na,'hard_fail_count',nh);
end
fid=fopen(fullfile(out,'qa','saved_outputs_audit.json'),'w');
assert(fid>=0);fprintf(fid,'%s',jsonencode(report,'PrettyPrint',true));fclose(fid);
fprintf('Saved-output audit PASS.\n');
end

function check_out(o,m,P)
assert(all(isfinite(o.u)) && numel(o.u)==P);
assert(all(abs(o.u)<=m+1e-8));
assert(all(isfinite(o.g)) && max(abs(o.g))<=2+1e-6);
assert(isfinite(o.J_best) && o.J_best==max(o.J));
i=find(strcmp(o.J_labels,o.selected));assert(isscalar(i));
assert(isequal(o.u,o.cands{i}) && o.J(i)==o.J_best);
assert(all(o.max_iter==round(240*max(1,P/21))));
assert(all(o.max_fevals==round(1000*max(1,P/21))));
assert(all(isnan(o.iters) | o.iters<=o.max_iter));
end
