function audit_phaseC_saved()
% Independent read-only reconstruction: no optimisation and no budget changes.
maxNumCompThreads(1); % Match process-worker arithmetic for the read-only reconstruction.
root='D:\论文集\phaseD';phaseD_setup();addpath(fullfile(root,'codeC'),'-begin');
[cfg,B,~]=phaseD_setup();files=dir(fullfile(root,'C_confirm','chunks','*.mat'));
files=files(~endsWith({files.name},'.partial.mat'));assert(numel(files)==280);
nr=0;nc=0;triggered=0;hardfail=0;budgetcap=0;roundrows={};stagerows={};metricdiff=0;trackdiff=0;
sig=phaseD_hash(fullfile(root,'codeC','SOURCE_MANIFEST_C_sha256.csv'),'SHA-256',true);
for fi=1:numel(files)
    C=load(fullfile(files(fi).folder,files(fi).name));assert(C.phase_id==52 && strcmp(C.signature,sig));
    for ri=1:numel(C.results)
        S=C.results(ri);nr=nr+1;fam=S.family;assert(numel(S.rows)==5 && fam.P==31);
        seed=cfg.master_seed+52e6+1e4*cfg.scene_code.(S.scene)+S.record_id;
        rec=simulate_baseband_T(cfg,S.scene,S.snr_db,seed,'eval',300);idx=find(rec.t>=5&rec.t<295);
        assert(strcmp(S.input_hash,phaseD_hash(rec.y,'MD5')));
        base=S.details{2}.out;smr=S.details{1}.smr;
        assert(isequal(base.u_init,smr.u));
        for di=1:5
            r=S.rows(di);d=S.details{di};nc=nc+1;
            assert(r.seed==seed && strcmp(r.input_hash,S.input_hash));
            assert(r.Delta_s==10 && r.P==31);
            if di==1
                o=smr;m=ones(31,1);assert(r.hard_fail==smr.fit_failed);
            elseif di<5
                o=d.out;if di==2,m=ones(31,1);elseif di==3,m=2*ones(31,1);else,m=Inf(31,1);end
                assert(isequal(o.u_init,smr.u));check_out(o,m,fam,rec,idx);
            else
                a=d.ada;o=a.out;m=a.m;assert(a.rounds<=1 && numel(a.logs)==a.rounds+1);
                assert(a.triggered==(a.rounds>0));triggered=triggered+a.triggered;
                assert(isequal(a.logs{1}.out,base));
                for k=1:numel(a.logs)
                    L=a.logs{k};check_out(L.out,L.m,fam,rec,idx);
                    [dw,runs]=phaseD_dwell(L.out.u,L.m,fam,rec.t,idx,B.fs);
                    assert(L.dwell_s==dw && L.J==L.out.J_best);
                    roundrows{end+1}=struct('scene',string(S.scene),'snr_db',S.snr_db,'record_id',S.record_id,'round',k-1,'runtime_s',L.seconds,'dwell_s',dw,'J',L.J);
                    if k<numel(a.logs)
                        rs=runs(runs.length_s>=30,:);assert(~isempty(rs));hit=false(31,1);
                        for p=1:31,lo=fam.knots(max(1,p-1));hi=fam.knots(min(31,p+1));hit(p)=any(hi>rs.start_s & lo<rs.end_s);end
                        hit=hit | [false;hit(1:end-1)] | [hit(2:end);false];expected=ones(31,1);expected(hit)=2;
                        next=a.logs{k+1};assert(isequal(next.m,expected));
                        assert(isequal(next.out.u_init,L.out.u) && isequal(next.out.cands{1},L.out.u));
                        assert(next.J>=L.J-1e-12);
                    end
                end
                assert(a.seconds==sum(cellfun(@(x)x.seconds,a.logs)));
                assert(isequal(a.out,a.logs{end}.out));
                if ~a.triggered,assert(isequal(o,base));end
                assert(o.J_best>=base.J_best-1e-12);
            end
            assert(all(abs(o.u)<=m+1e-8) && all(fam.Aineq*o.u<=fam.bineq+1e-6));
            gd=max(abs(o.g-(fam.gA+fam.r*(fam.Bt*o.u))));assert(gd<=1e-12);trackdiff=max(trackdiff,gd);
            met=phaseD_measure(rec,o.g,idx,B);
            saved=[r.eta r.peak_db r.prominence_db r.width_3db_hz r.track_rmse_hz r.max_error_hz r.longest_out_0p02_s];
            recomputed=[met.eta met.peak_db met.prom_db met.width met.rmse met.maxabs met.longest];
            assert(isequal(isnan(saved),isnan(recomputed)));md=max(abs(saved(~isnan(saved))-recomputed(~isnan(recomputed))));assert(md<=1e-12);metricdiff=max(metricdiff,md);
            if di>1
                assert(r.J==o.J_best && r.J_start==o.J_B2 && r.hard_fail==o.hard_fail);
                hardfail=hardfail+o.hard_fail;budgetcap=budgetcap+r.budget_cap;
                for st=1:numel(o.iters)
                    stagerows{end+1}=struct('scene',string(S.scene),'snr_db',S.snr_db,'record_id',S.record_id,'method',string(d.method),'stage',st,'iterations',o.iters(st),'fevals',o.fevals(st),'exitflag',o.exitflags(st),'runtime_s',o.stage_seconds(st));
                end
            end
        end
        if mod(nr,200)==0,fprintf('Read-only C audit %d/2800\n',nr);end
    end
end
assert(nr==2800 && nc==14000);
writetable(struct2table([roundrows{:}]),fullfile(root,'C_confirm','C_ADA_rounds.csv'));
writetable(struct2table([stagerows{:}]),fullfile(root,'C_confirm','C_final_solver_stages.csv'));
phaseD_json(fullfile(root,'C_confirm','SAVED_OUTPUTS_AUDIT.json'),struct('status','PASS','records',nr,'rows',nc,'triggered',triggered,'hard_fail_solver_outputs',hardfail,'budget_cap_final_outputs',budgetcap,'recomputation_tolerance',1e-12,'metric_max_abs_difference',metricdiff,'track_max_abs_difference',trackdiff,'scope','All records regenerated at phase 52; all five methods metrics reconstructed within 1e-12; full objective candidate selection, constraints, budgets, local expansion supports and saved nontrigger bitwise identity verified without optimisation'));
end

function check_out(o,m,fam,rec,idx)
assert(all(isfinite(o.u)) && numel(o.u)==31 && all(abs(o.u)<=m+1e-8));
assert(all(isfinite(o.g)) && max(abs(o.g))<=2+1e-6);
assert(isfinite(o.J_best) && o.J_best==max(o.J));
ib=find(strcmp(o.J_labels,o.selected));assert(isscalar(ib));
assert(isequal(o.u,o.cands{ib}) && o.J(ib)==o.J_best);
assert(all(o.max_iter==354) && all(o.max_fevals==1476));
assert(all(isnan(o.iters) | o.iters<=354));
ctx=struct('y',rec.y(idx),'phiA',fam.phiA(idx),'H',fam.H(idx,:),'P',31,...
    'DtD',fam.D2.'*fam.D2,'lambda',0.005151315789473684,'E',sum(abs(rec.y(idx)).^2)+eps);
ctx.blk=make_blocks(numel(idx),290*20);
for k=1:numel(o.cands)
    u=o.cands{k};ok=all(abs(u)<=m+1e-8)&&all(fam.Aineq*u<=fam.bineq+1e-6);
    if ok,assert(abs(o.J(k)+coherence_objective(u,ctx))<=1e-12);else,assert(o.J(k)==-Inf);end
end
end
