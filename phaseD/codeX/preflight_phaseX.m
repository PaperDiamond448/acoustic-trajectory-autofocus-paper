function preflight_phaseX()
phaseD_setup();addpath('D:\论文集\phaseD\codeX','-begin');phaseX_verify_sources();
for T=[150 300 450 600]
 [F,cfg,B,M]=phaseX_settings(T,false);P=T/10+1;
 assert(B.N==20*T && isequal(M.P.h_stages_s,[20 60 T-10]));
 assert(all(M.P.max_iter==round(240*max(1,P/21))) && all(M.P.max_fevals==round(1000*max(1,P/21))));
 [lc,lf,Q]=phaseD_regularization(10,T,true);assert(Q==P && M.P.lambda_C==lc && M.B2.lambda_F==lf);
 if T==300,assert(lc==F.regularization.lambda_C && lf==F.regularization.lambda_F);end
 seed=cfg.master_seed+53e6+1e4*cfg.scene_code.S0+1;r=simulate_baseband_T(cfg,'S0',-17,seed,'eval',T);
 assert(numel(r.y)==B.N && all(isfinite(r.y)) && r.truth.seed==seed);
end
names={'phaseX_settings','phaseX_front','phaseX1_one','phaseX2_one','run_phaseX_sim','run_phaseX3_screen'};
for k=1:numel(names),a=checkcode(which(names{k}),'-id');fprintf('%s: %d diagnostics\n',names{k},numel(a));for j=1:numel(a),fprintf('%s\n',a(j).message);end,end
phaseD_json('D:\论文集\phaseD\Y_compute\PREFLIGHT.json',struct('status','PASS','scope','Frozen parameter scaling, fresh phase53 input dimensions and driver static checks; no output-dependent tuning','matlab',version));
end
