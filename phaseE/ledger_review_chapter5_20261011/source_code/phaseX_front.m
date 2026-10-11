function [fe,v,idx,times]=phaseX_front(y,t,B,M)
fc=struct('fs',B.fs,'L',B.L,'D',B.D,'df_fine',B.df_fine,'band',B.band,'coarse_dec',B.coarse_dec,'noise_bands',B.noise_bands);
timer=tic;fe=common_frontend(y,t,fc);times.frontend=toc(timer);
timer=tic;v=estimate_b1(fe,M.B1);times.vit=toc(timer);
idx=find(t>=5&t<B.T-5);
end
