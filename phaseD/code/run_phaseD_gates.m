function run_phaseD_gates()
root='D:\论文集'; outdir=fullfile(root,'phaseD','G_gates'); if ~exist(outdir,'dir'),mkdir(outdir);end
[cfg,B,M,wk,snap]=phaseD_setup();
diary(fullfile(outdir,'matlab_gates.log')); diary on;
gates=repmat(struct('gate','','status','NOT_RUN','maximum_difference',NaN,'criterion','','detail',''),8,1);
for k=1:8,gates(k).gate=sprintf('G%d',k);end
gates(1).criterion='All family fields <=1e-12';
gates(2).criterion='Samplewise exact equality of y and truth.gtrue';
gates(3).criterion='Archived bounded/unbounded u, J290, eta absolute difference <=1e-8';
gates(4).criterion='ADA tau=Inf output bitwise identical to fixed F02';
gates(5).criterion='Exact lambda_C=1e-3 and lambda_F=0.1 at Delta=15,T=300';
gates(6).criterion='New and historical seed sets disjoint';
gates(7).criterion='MD5 d39204a14031ce097707b440ef58e601; peak increment within 1e-4 of 1.757253 dB';
gates(8).criterion='SUV output g exact equality to original implementation on 3 ExpB records';
try
    maxdiff=0; familyRows=[];
    scenes={'S0','S2','S0'};snrs=[-20 -17 -14];
    for i=1:3
        seed=cfg.master_seed+33e6+1e4*cfg.scene_code.(scenes{i})+1;
        rec=simulate_baseband(cfg,scenes{i},snrs(i),seed,'eval');fe=frontend(rec,B);v=estimate_b1(fe,M.B1);
        old=build_family(rec.t,fe.tc,v.g,M.B2);new=build_family_T(rec.t,fe.tc,v.g,M.B2,15,300,1);
        fields=fieldnames(old);assert(isequal(fields,fieldnames(new)));
        for q=1:numel(fields)
            assert(isequal(size(old.(fields{q})),size(new.(fields{q}))));
            dd=max(abs(old.(fields{q})(:)-new.(fields{q})(:)));if isempty(dd),dd=0;end
            maxdiff=max(maxdiff,dd);
            familyRows=[familyRows;{scenes{i},snrs(i),1,fields{q},dd}]; %#ok<AGROW>
        end
    end
    writetable(cell2table(familyRows,'VariableNames',{'scene','snr_db','record_id','field','max_abs_diff'}),fullfile(outdir,'gate_G1.csv'));
    gates(1).maximum_difference=maxdiff;check(1,maxdiff<=1e-12,'Three archived E4a record inputs; all fields compared.');

    rows=[];equal=true;
    for sc={'S0','S2'}
        for rid=1:3
            seed=cfg.master_seed+33e6+1e4*cfg.scene_code.(sc{1})+rid;
            old=simulate_baseband(cfg,sc{1},-17,seed,'eval');new=simulate_baseband_T(cfg,sc{1},-17,seed,'eval',300);
            ok=isequal(old.y,new.y)&&isequal(old.truth.gtrue,new.truth.gtrue);equal=equal&&ok;
            rows=[rows;{sc{1},rid,seed,ok,phaseD_hash(new.y,'MD5')}]; %#ok<AGROW>
        end
    end
    writetable(cell2table(rows,'VariableNames',{'scene','record_id','seed','exact_equal','input_md5'}),fullfile(outdir,'gate_G2.csv'));
    gates(2).maximum_difference=double(~equal);check(2,equal,'S0/S2, 3 historical seeds each.');

    pool=gcp('nocreate');if isempty(pool),pool=parpool('Processes',6);end;assert(pool.NumWorkers==6);
    rows=cell(6,1); states=cell(6,1); qsc={'S0','S0','S0','S2','S2','S2'};qsnr=[-20 -17 -14 -20 -17 -14];
    parfor i=1:6
        [rows{i},states{i}]=gate_e4a_one(cfg,B,M,qsc{i},qsnr(i),root);
    end
    G3=struct2table([rows{:}]);writetable(G3,fullfile(outdir,'gate_G3.csv'));
    maxdiff=max([G3.u_bounded_diff;G3.u_unbounded_diff;G3.J_bounded_diff;G3.J_unbounded_diff;G3.eta_bounded_diff;G3.eta_unbounded_diff]);
    save(fullfile(outdir,'gate_G3_states.mat'),'states','G3','-v7.3');
    gates(3).maximum_difference=maxdiff;check(3,maxdiff<=1e-8,'Six E4a records, two box modes; archived chunk coefficients and metrics.');

    ok=true;G4=cell(6,1);
    for i=1:6
        s=states{i};base=struct('out',s.bounded,'seconds',s.seconds);
        a=phaseD_ada(s.rec.y,s.fe,s.fam,s.smr.u,s.idx,M.P,s.rec.t,Inf,0.08,'global','A',base);
        bit=isequal(a.out.u,s.bounded.u)&&isequal(a.out.g,s.bounded.g)&&isequal(a.out.J_best,s.bounded.J_best)&&a.rounds==0;
        ok=ok&&bit;G4{i}={qsc{i},qsnr(i),1,bit,a.rounds};
    end
    writetable(cell2table(vertcat(G4{:}),'VariableNames',{'scene','snr_db','record_id','bitwise_equal','expansion_rounds'}),fullfile(outdir,'gate_G4.csv'));
    gates(4).maximum_difference=double(~ok);check(4,ok,'No-trigger path reuses exact fixed-0.02 result; archive reproduction covered by G3.');

    [lc,lf,p]=phaseD_regularization(15,300,true);ok=isequal(lc,1e-3)&&isequal(lf,0.1)&&p==21;
    writetable(table(15,300,p,lc,lf,ok,'VariableNames',{'Delta_s','T_s','P','lambda_C','lambda_F','exact'}),fullfile(outdir,'gate_G5.csv'));
    gates(5).maximum_difference=max(abs([lc-1e-3 lf-0.1]));check(5,ok,'Explicit exact-return baseline branch.');

    newseeds=[];oldseeds=[];
    counts=[60 200 100 100];
    for phase=51:54,for scene=[1 3],newseeds=[newseeds cfg.master_seed+1e6*phase+1e4*scene+(1:counts(phase-50))];end;end
    % Conservative superset: all historical scenes, phases, record IDs 1:5000.
    for phase=[21:28 31 33],for scene=[1 2 3 11 12],oldseeds=[oldseeds cfg.master_seed+1e6*phase+1e4*scene+(1:5000)];end;end
    common=intersect(newseeds,oldseeds);
    writetable(table(numel(unique(newseeds)),numel(unique(oldseeds)),numel(common),'VariableNames',{'new_unique_seeds','historical_superset_seeds','overlap'}),fullfile(outdir,'gate_G6.csv'));
    gates(6).maximum_difference=numel(common);check(6,isempty(common),'Historical superset includes IDs through 5000, every historical scene.');

    R=real_config();[y,extract]=phaseA_load_baseband(R.file,9,100,20,10,R.fs_raw,R.n_raw,900,300,10,10);
    md5=phaseD_hash(y,'MD5');t=(0:numel(y)-1)'/20;
    Br=B;Br.band=[-1.5 1.5];Mr=M;Mr.B2.band=Br.band;recR=struct('y',y,'t',t);
    fe=frontend(recR,Br);v=estimate_b1(fe,Mr.B1);fam=build_family_T(t,fe.tc,v.g,Mr.B2,15,300,1);smr=estimate_b2(fe,fam,Mr.B2);idx=find(t>=5&t<295);
    bta=estimate_proposed_T(y,fe,fam,smr.u,idx,Mr.P);
    nfft=2^nextpow2(8*numel(y));f=(-nfft/2:nfft/2-1)'*20/nfft;use=abs(f)<=1.5;
    ps=fftshift(abs(fft(y.*exp(-1j*2*pi*cumtrapz(t,smr.g)),nfft)).^2);
    pb=fftshift(abs(fft(y.*exp(-1j*2*pi*cumtrapz(t,bta.g)),nfft)).^2);
    delta=10*log10(max(pb(use))/max(ps(use)));diffpeak=abs(delta-1.757253);
    writetable(table(string(md5),delta,diffpeak,'VariableNames',{'baseband_md5','SMR_to_BTA_peak_increment_db','absolute_difference_db'}),fullfile(outdir,'gate_G7.csv'));
    save(fullfile(outdir,'gate_G7_states.mat'),'y','extract','smr','bta','fam','-v7.3');
    gates(7).maximum_difference=diffpeak;check(7,strcmp(md5,'d39204a14031ce097707b440ef58e601')&&diffpeak<=1e-4,'Fresh original SIO extraction and old 21-node B240 configuration; full-record FFT matching original real-spectrum definition.');

    rows=[];ok=true; s=suvorova_config();
    for snr=[-18 -17 -16]
        seed=cfg.master_seed+24e6+3e4+1;rec=simulate_baseband_T(cfg,'S2',snr,seed,'eval',300);fe=frontend(rec,B);idx=find(rec.t>=5&rec.t<295);
        old=estimate_suvorova(rec.y,rec.t,fe.noise_hat,s,idx);new=estimate_suvorova_D(rec.y,rec.t,fe.noise_hat,s,idx);
        bit=isequal(old.g,new.g);ok=ok&&bit;rows=[rows;{'S2',snr,1,seed,bit,max(abs(old.g-new.g))}];
    end
    writetable(cell2table(rows,'VariableNames',{'scene','snr_db','record_id','seed','exact_equal','max_abs_diff'}),fullfile(outdir,'gate_G8.csv'));
    gates(8).maximum_difference=double(~ok);check(8,ok,'Original unchanged implementation versus new-name copy on W4 ExpB phase-24 records.');
catch ME
    write_report();diary off;rethrow(ME);
end
write_report();diary off;

    function check(k,ok,detail)
        gates(k).detail=detail;
        if ok,gates(k).status='PASS';else,gates(k).status='FAIL';end
        write_report();fprintf('%s %s; maximum difference %.17g\n',gates(k).gate,gates(k).status,gates(k).maximum_difference);
        assert(ok,'PhaseD:GateFailed','%s failed; stop without tuning or retry.',gates(k).gate);
    end
    function write_report()
        phaseD_json(fullfile(outdir,'gates.json'),struct('gates',gates,'all_pass',all(strcmp({gates.status},'PASS'))));
        fid=fopen(fullfile(outdir,'GATES_REPORT.md'),'w','n','UTF-8');c=onCleanup(@()fclose(fid));
        fprintf(fid,'# Phase D 核验门报告\n\nMATLAB %s；R2023a；G3 使用 6 workers。\n\n',version);
        fprintf(fid,'| 门 | 状态 | 最大差异 | 通过标准 |\n|---|---|---:|---|\n');
        for q=1:8,fprintf(fid,'| %s | %s | %.17g | %s |\n',gates(q).gate,gates(q).status,gates(q).maximum_difference,gates(q).criterion);end
        fprintf(fid,'\n');for q=1:8,if ~isempty(gates(q).detail),fprintf(fid,'%s: %s\n\n',gates(q).gate,gates(q).detail);end;end
        if any(strcmp({gates.status},'FAIL')),fprintf(fid,'任一门失败即停止。D1/D2 未启动；未调参数、未追加预算、未重试。\n');end
    end
end
function fe=frontend(rec,B)
fcfg=struct('fs',B.fs,'L',B.L,'D',B.D,'df_fine',B.df_fine,'band',B.band,'coarse_dec',B.coarse_dec,'noise_bands',B.noise_bands);
fe=common_frontend(rec.y,rec.t,fcfg);
end
function [row,state]=gate_e4a_one(cfg,B,M,scene,snr,root)
seed=cfg.master_seed+33e6+1e4*cfg.scene_code.(scene)+1;
rec=simulate_baseband_T(cfg,scene,snr,seed,'eval',300);fe=frontend(rec,B);v=estimate_b1(fe,M.B1);
fam=build_family_T(rec.t,fe.tc,v.g,M.B2,15,300,1);smr=estimate_b2(fe,fam,M.B2);idx=find(rec.t>=5&rec.t<295);
timer=tic;b=estimate_proposed_T(rec.y,fe,fam,smr.u,idx,M.P);secs=toc(timer);fu=fam;fu.lb=-Inf(fam.P,1);fu.ub=Inf(fam.P,1);
u=estimate_proposed_T(rec.y,fe,fu,smr.u,idx,M.P);mb=phaseD_measure(rec,b.g,idx,B);mu=phaseD_measure(rec,u.g,idx,B);
file=fullfile(root,'phaseC','E4a_formal_paired_20260925','chunks',sprintf('%s_%+03ddB_chunk_001.mat',scene,snr));
C=load(file,'records','coeffB','coeffU');ix=find([C.records.record_id]==1);assert(isscalar(ix));r=C.records(ix);
assert(strcmp(char(r.input_hash),phaseD_hash(rec.y,'MD5')));
row=struct('scene',string(scene),'snr_db',snr,'record_id',1,'seed',seed,...
    'u_bounded_diff',max(abs(b.u-C.coeffB(:,ix))),'u_unbounded_diff',max(abs(u.u-C.coeffU(:,ix))),...
    'J_bounded_diff',abs(b.J_best-r.J290_bounded),'J_unbounded_diff',abs(u.J_best-r.J290_unbounded),...
    'eta_bounded_diff',abs(mb.eta-r.eta_bounded),'eta_unbounded_diff',abs(mu.eta-r.eta_unbounded));
state=struct('rec',rec,'fe',struct('fs',fe.fs),'fam',fam,'smr',smr,'idx',idx,'bounded',b,'seconds',secs);
end
