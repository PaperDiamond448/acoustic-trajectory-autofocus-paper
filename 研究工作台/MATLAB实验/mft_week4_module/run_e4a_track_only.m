function run_e4a_track_only(outdir, nworkers)
%RUN_E4A_TRACK_ONLY  Track-only feasibility pilot; deliberately no BTA call.
% Frozen grid: S0/S2 x -20:-14 dB x record_id 1:200 (2,800 inputs).
% Uses the week-4 generator and eval geometry; records are paired across SNR.
% The only estimators called are the existing VIT (B1) and SMR (B2).

if nargin < 1 || isempty(outdir)
    outdir = fullfile(pwd, '..', '..', '..', 'phaseC', ...
        'E4a_track_only_pilot_20260925');
end
if nargin < 2 || isempty(nworkers), nworkers = 6; end
if ~exist(outdir,'dir'), mkdir(outdir); end
cfg = mft_config(); B = cfg.B; M = cfg.M;
cfg.phase_id.track_only = 33; % new, unused phase; frozen in pilot manifest
scenes = {'S0','S2'}; snrs = -20:-14; ids = 1:200;
jobs = make_jobs(cfg,'track_only',scenes,snrs,ids);
assert(numel(jobs) == 2800);
assert(numel(unique([jobs.seed])) == 400, 'Expected paired seed reuse across SNR.');

if ~exist(fullfile(outdir,'cells'),'dir'), mkdir(fullfile(outdir,'cells')); end
fcfg = struct('fs',B.fs,'L',B.L,'D',B.D,'df_fine',B.df_fine, ...
    'band',B.band,'coarse_dec',B.coarse_dec,'noise_bands',B.noise_bands);
evalIdx = find((0:B.N-1)'/B.fs >= B.eval_s(1) & ...
               (0:B.N-1)'/B.fs < B.eval_s(2));
assert(numel(evalIdx) == 5800 && B.eval_s(1) == 5 && B.eval_s(2) == 295);
t=(0:B.N-1)'/B.fs;

% Reproducible code/config snapshot, separate from inherited algorithm files.
meta = struct('pilot','E4a track-only feasibility pilot', ...
    'protocol','MFT-W4-MODULE-20260918 with track-only extension', ...
    'generated_utc',datestr(datetime('now','TimeZone','UTC'), ...
        'yyyy-mm-ddTHH:MM:SSZ'), ...
    'geometry_mode','eval (same as run_main_w2/run_expB_crossfrontend)', ...
    'snr_semantics','20 Hz synthetic complex-baseband sample SNR', ...
    'scenes',{scenes},'snr_db',snrs,'record_ids',[ids(1),ids(end)], ...
    'n_records',numel(jobs),'unique_seed_count',numel(unique([jobs.seed])), ...
    'seed_formula','20260915 + 1e6*33 + 1e4*scene_code + record_id; SNR excluded', ...
    'phase_id',33,'scene_code',cfg.scene_code,'B',B,'M_B1',M.B1,'M_B2',M.B2, ...
    'eval_interval_s',B.eval_s,'out_threshold_hz',0.02, ...
    'projection','min ||d_req - radius*Bt*u||_2 subject to original band inequalities; bounded [-1,1] or unbounded; no BTA/objective call', ...
    'methods_called',{{'simulate_baseband','common_frontend','estimate_b1','build_family','estimate_b2'}}, ...
    'methods_not_called',{{'estimate_proposed','estimate_refine','BTA'}});
fid=fopen(fullfile(outdir,'pilot_config.json'),'w');
fprintf(fid,'%s',jsonencode(meta,'PrettyPrint',true)); fclose(fid);

poolReady=false;
cellsComputedThisInvocation=0;
fprintf('E4a track-only: %d records, %d cells, %d workers\n',numel(jobs), ...
    numel(scenes)*numel(snrs),nworkers);
totalTimer = tic;
for si=1:numel(scenes)
    for qi=1:numel(snrs)
        scene=scenes{si}; snr=snrs(qi);
        cellfile=fullfile(outdir,'cells',sprintf('%s_%+03ddB.mat',scene,snr));
        cellJobs=jobs(strcmp({jobs.scene},scene) & [jobs.snr_db]==snr);
        expectedSeeds=[cellJobs.seed]';
        if exist(cellfile,'file')
            C=load(cellfile,'rows','gtrue','gvit','gsmr','uSMR','t','cell_seeds');
            if numel(C.cell_seeds)==200 && isequal(C.cell_seeds(:),expectedSeeds) && ...
                    isequal(size(C.uSMR),[21 200])
                fprintf('resume verified: %s %d dB\n',scene,snr);
                continue
            end
            warning('Discarding mismatched cell checkpoint %s',cellfile);
        end
        ticCell=tic; n=numel(cellJobs);
        if ~poolReady
            pool=gcp('nocreate');
            if isempty(pool), pool=parpool('Processes',nworkers); end %#ok<NASGU>
            poolReady=true;
        end
        rows=cell(n,1); gtrue=zeros(B.N,n,'single');
        uSMR=zeros(round(B.T/M.B2.knot_ds)+1,n,'single');
        gvit=zeros(B.N,n,'single'); gsmr=zeros(B.N,n,'single');
        parfor ri=1:n
            j=cellJobs(ri);
            rec=simulate_baseband(cfg,j.scene,j.snr_db,j.seed,'eval');
            fe=common_frontend(rec.y,rec.t,fcfg);
            o1=estimate_b1(fe,M.B1);
            fam=build_family(rec.t,fe.tc,o1.g,M.B2);
            o2=estimate_b2(fe,fam,M.B2);
            [mV,runV,longV,nrunV]=track_metrics(rec.truth.gtrue-o1.g,evalIdx,B.fs,0.02);
            [mS,runS,longS,nrunS]=track_metrics(rec.truth.gtrue-o2.g,evalIdx,B.fs,0.02);
            dreq=rec.truth.gtrue(evalIdx)-o1.g(evalIdx);
            [ub,mb]=oracle_projection(dreq,fam,evalIdx,M.B2,true);
            [uu,mu]=oracle_projection(dreq,fam,evalIdx,M.B2,false);
            h=input_hash(rec.y);
            rows{ri}=table(j.record_id,string(j.scene),j.snr_db,j.seed, ...
                rec.truth.geo.f0,rec.truth.geo.v,rec.truth.geo.t_cpa_rx, ...
                fe.noise_hat,string(h), ...
                mV.rmse,mV.maxabs,mV.p95,mV.pout,runV,longV,nrunV, ...
                mS.rmse,mS.maxabs,mS.p95,mS.pout,runS,longS,nrunS, ...
                max(abs(o2.u)), ...
                mb.rmse,mb.p95,mb.maxabs,max(abs(ub)),mb.band_violation, ...
                mu.rmse,mu.p95,mu.maxabs,max(abs(uu)),mu.band_violation, ...
                mb.rmse-mu.rmse, ...
                'VariableNames',{'record_id','scene','snr_db','seed', ...
                'geo_f0_hz','geo_v_mps','geo_t_cpa_rx_s','noise_hat','input_hash', ...
                'vit_rmse_hz','vit_maxabs_hz','vit_p95_hz','vit_pout','vit_out_total_s','vit_out_longest_s','vit_out_runs', ...
                'smr_rmse_hz','smr_maxabs_hz','smr_p95_hz','smr_pout','smr_out_total_s','smr_out_longest_s','smr_out_runs', ...
                'u_smr_maxabs','proj_bounded_rmse_hz','proj_bounded_p95_hz','proj_bounded_maxabs_hz','proj_bounded_umax','proj_bounded_band_violation_hz', ...
                'proj_unbounded_rmse_hz','proj_unbounded_p95_hz','proj_unbounded_maxabs_hz','proj_unbounded_umax','proj_unbounded_band_violation_hz','delta_proj_rmse_hz'});
            gtrue(:,ri)=single(rec.truth.gtrue);
            gvit(:,ri)=single(o1.g);
            gsmr(:,ri)=single(o2.g);
            uSMR(:,ri)=single(o2.u);
        end
        rows=vertcat(rows{:}); cell_seeds=expectedSeeds; %#ok<NASGU>
        save(cellfile,'rows','gtrue','gvit','gsmr','uSMR','t','cell_seeds','-v7.3');
        cellsComputedThisInvocation=cellsComputedThisInvocation+1;
        writetable(rows,fullfile(outdir,'cells',sprintf('%s_%+03ddB.csv',scene,snr)));
        fprintf('saved %s %d dB: %d records in %.1f min\n',scene,snr,n,toc(ticCell)/60);
    end
end

% Assemble only after validating all 14 cells; keep the per-cell checkpoints.
allRows=table(); cellNames={};
for si=1:numel(scenes)
    for qi=1:numel(snrs)
        scene=scenes{si}; snr=snrs(qi);
        f=fullfile(outdir,'cells',sprintf('%s_%+03ddB.mat',scene,snr));
        assert(exist(f,'file')==2,'Missing cell output %s',f);
        C=load(f,'rows','gtrue','gvit','gsmr','t');
        assert(height(C.rows)==200,'Cell has wrong row count: %s',f);
        allRows=[allRows;C.rows]; %#ok<AGROW>
        cellNames{end+1}=f; %#ok<AGROW>
    end
end
assert(height(allRows)==2800 && numel(unique(allRows.seed))==400);
for si=1:numel(scenes)
    for qi=1:numel(snrs)
        assert(sum(allRows.scene==scenes{si} & allRows.snr_db==snrs(qi))==200);
    end
end
writetable(allRows,fullfile(outdir,'track_only_metrics.csv'));
save(fullfile(outdir,'track_only_tracks.mat'),'cellNames','t','-v7.3');
write_summary(allRows,outdir);
make_pilot_figures(allRows,outdir);
meta.finalization_seconds=toc(totalTimer);
meta.cells_computed_this_invocation=cellsComputedThisInvocation;
if cellsComputedThisInvocation==14
    meta.compute_seconds=meta.finalization_seconds;
else
    meta.compute_seconds=[];
    meta.compute_seconds_note='Not measured for the full grid in this invocation; one or more cells were resumed from checkpoints.';
end
meta.rows=height(allRows); meta.cells=14;
fid=fopen(fullfile(outdir,'pilot_run.json'),'w');
fprintf(fid,'%s',jsonencode(meta,'PrettyPrint',true)); fclose(fid);
fprintf('Pilot complete: 2,800 rows; elapsed %.2f h\n',meta.seconds/3600);
end

function [m,total_s,longest_s,nruns]=track_metrics(e,idx,fs,thr)
e=e(idx); a=abs(e); mask=a>thr; dif=diff([false;mask(:);false]);
st=find(dif==1); en=find(dif==-1)-1; lens=en-st+1;
m.rmse=sqrt(mean(e.^2)); m.maxabs=max(a); m.p95=percentile_local(a,95);
m.pout=mean(mask); total_s=sum(mask)/fs;
if isempty(lens), longest_s=0; nruns=0; else, longest_s=max(lens)/fs; nruns=numel(lens); end
end

function [u,m]=oracle_projection(d,fam,evalIdx,mcfg,bounded)
X=mcfg.radius*fam.Bt(evalIdx,:); A=fam.Aineq; b=fam.bineq;
if bounded, lb=fam.lb; ub=fam.ub; else, lb=-inf(fam.P,1); ub=inf(fam.P,1); end
opts=optimoptions('lsqlin','Display','off','Algorithm','interior-point');
[u,~,~,flag]=lsqlin(X,d,A,b,[],[],lb,ub,zeros(fam.P,1),opts);
assert(flag>0 && all(isfinite(u)),'Oracle projection failed (bounded=%d, flag=%d)',bounded,flag);
res=d-X*u; m.rmse=sqrt(mean(res.^2)); m.p95=percentile_local(abs(res),95); m.maxabs=max(abs(res));
gchk=fam.gAchk+fam.r*fam.Bchk*u;
m.band_violation=max([0;gchk-mcfg.band(2);mcfg.band(1)-gchk]);
end

function q=percentile_local(x,p)
x=sort(x(:)); k=max(1,min(numel(x),ceil((p/100)*numel(x)))); q=x(k);
end

function h=input_hash(y)
b=typecast([real(y(:));imag(y(:))],'uint8');
md=java.security.MessageDigest.getInstance('MD5'); md.update(b);
h=lower(reshape(dec2hex(typecast(md.digest(),'uint8')).',1,[]));
end

function write_summary(T,outdir)
vars={'vit_rmse_hz','vit_pout','vit_out_longest_s','smr_rmse_hz','smr_pout', ...
    'smr_out_longest_s','proj_bounded_rmse_hz','proj_unbounded_rmse_hz','delta_proj_rmse_hz'};
% Use explicit per-cell medians/means to avoid version-specific groupsummary formats.
scene=string.empty(0,1); snr_db=[]; n=[];
for si=unique(T.scene,'stable')'
    for q=unique(T.snr_db)'
        z=T(T.scene==si & T.snr_db==q,:); scene(end+1,1)=si; %#ok<AGROW>
        snr_db(end+1,1)=q; n(end+1,1)=height(z); %#ok<AGROW>
    end
end
S=table(scene,snr_db,n);
for v=1:numel(vars)
    vv=vars{v}; means=zeros(height(S),1); medians=means; p95s=means;
    for k=1:height(S)
        z=T(T.scene==S.scene(k) & T.snr_db==S.snr_db(k),:).(vv);
        means(k)=mean(z); medians(k)=median(z); p95s(k)=percentile_local(z,95);
    end
    S.([vv '_mean'])=means; S.([vv '_median'])=medians; S.([vv '_p95'])=p95s;
end
writetable(S,fullfile(outdir,'track_only_summary.csv'));
end

function make_pilot_figures(T,outdir)
scenes=unique(T.scene,'stable'); snrs=unique(T.snr_db);
for si=1:numel(scenes)
    fig=figure('Visible','off','Color','w','Position',[100 100 1200 820]);
    for v=1:4
        subplot(2,2,v); hold on; grid on;
        names={'vit_pout','vit_out_longest_s','proj_bounded_rmse_hz','delta_proj_rmse_hz'};
        labels={'VIT P_{out} (|d|>0.02 Hz)','VIT longest out-of-bound run (s)', ...
            'Bounded oracle projection RMSE (Hz)','Bounded - unbounded projection RMSE (Hz)'};
        if v==1
            center=zeros(size(snrs)); lo=center; hi=center;
        else
            center=zeros(size(snrs)); lo=center; hi=center;
        end
        for k=1:numel(snrs)
            z=T(T.scene==scenes(si) & T.snr_db==snrs(k),:).(names{v});
            if v==1, center(k)=mean(z); else, center(k)=median(z); end
            lo(k)=percentile_local(z,10); hi(k)=percentile_local(z,90);
        end
        errorbar(snrs,center,center-lo,hi-center,'-o','LineWidth',1.2,'MarkerSize',5);
        xlabel('Sample SNR (dB)'); ylabel(labels{v});
        title(labels{v},'Interpreter','tex');
    end
    sgtitle(sprintf('%s: track-only feasibility diagnostics',scenes(si)));
    exportgraphics(fig,fullfile(outdir,sprintf('fig_track_feasibility_%s.png',scenes(si))),'Resolution',180);
    close(fig);
end

fig=figure('Visible','off','Color','w','Position',[100 100 1100 740]);
for si=1:numel(scenes)
    subplot(2,1,si); hold on; grid on;
    for v=1:2
        name={'vit_rmse_hz','smr_rmse_hz'}; lab={'VIT','SMR'};
        med=zeros(size(snrs)); lo=med; hi=med;
        for k=1:numel(snrs)
            z=T(T.scene==scenes(si) & T.snr_db==snrs(k),:).(name{v});
            med(k)=median(z); lo(k)=percentile_local(z,10); hi(k)=percentile_local(z,90);
        end
        errorbar(snrs,med,med-lo,hi-med,'-o','LineWidth',1.2,'MarkerSize',5,'DisplayName',lab{v});
    end
    if scenes(si)=="S0"
        set(gca,'YScale','log');
    end
    xlabel('Sample SNR (dB)'); ylabel('Median RMSE (Hz; bars: 10th-90th percentile)');
    title(sprintf('%s: VIT and SMR track RMSE',scenes(si))); legend('Location','best');
end
exportgraphics(fig,fullfile(outdir,'fig_vit_smr_rmse.png'),'Resolution',180); close(fig);
end
