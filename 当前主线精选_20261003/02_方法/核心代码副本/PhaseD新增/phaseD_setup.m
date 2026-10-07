function [cfg,B,M,wk,snap]=phaseD_setup()
root='D:\论文集';
wk=fullfile(root,'研究工作台','MATLAB实验','mft_week4_module');
snap=fullfile(root,'phaseC','E4a_track_only_pilot_20260925','source_snapshot');
addpath(fullfile(root,'phaseA','code'),'-begin');
addpath(fullfile(root,'研究工作台','MATLAB实验','mft_real_inject'),'-begin');
addpath(wk,'-begin'); addpath(snap,'-begin');
addpath(fullfile(root,'phaseD','code'),'-begin');
assert(strcmp(version('-release'),'2023a'),'MATLAB R2023a required.');
cfg=mft_config(); B=cfg.B; M=cfg.M;
M.P.max_iter=[240 240 240]; M.P.max_fevals=[1000 1000 1000];
end
