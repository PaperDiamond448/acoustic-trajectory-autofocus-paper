function [F,cfg,B,M]=phaseX_settings(T,isreal)
[cfg,B,M]=phaseD_setup();
root='D:\论文集\phaseD';F=jsondecode(fileread(fullfile(root,'D_dev','FROZEN_METHOD.json')));
assert(strcmp(phaseD_hash(fullfile(root,'D_dev','FROZEN_METHOD.json'),'SHA-256',true),'ff63f32c38fc17e99620faa074025c337df247bf823be4fa4b40e74860c0a89f'));
assert(strcmp(F.method,'ADA_local_c04_t30_A') && F.Delta_s==10 && F.ADA.tau_s==30 && F.ADA.cap_hz==.04 && strcmp(F.ADA.rerun,'A'));
[lc,lf,P]=phaseD_regularization(F.Delta_s,T,true);
B.T=T;B.N=round(T*B.fs);B.eval_s=[5 T-5];
if isreal,B.band=[-1.5 1.5];end
M.B2.band=B.band;M.B2.lambda_F=lf;M.P.lambda_C=lc;
M.P.h_stages_s=[20 60 T-10];
M.P.max_iter=repmat(round(240*max(1,P/21)),1,3);
M.P.max_fevals=repmat(round(1000*max(1,P/21)),1,3);
assert(M.P.tol_x==1e-6 && M.P.tol_opt==1e-6);
end
