function run_all_w4(nworkers)
%RUN_ALL_W4  Reproduce the whole of protocol MFT-W4-MODULE-20260918.
%
%   Experiment A is deterministic and takes seconds.
%   Experiment B regenerates 300 records x 2 branches (about 4 min on 10
%   workers) and then runs the pre-registered analysis, the two post-hoc
%   descriptions and all four figures.
%
%   Every record is regenerated from its seed, so the batch does not depend
%   on the order parfor happens to use.
if nargin < 1 || isempty(nworkers), nworkers = 8; end
t0 = tic;

fprintf('\n================ experiment A: mechanism counterexample ================\n');
run_expA_mechanism;
make_figure_expA;

fprintf('\n================ experiment B: cross-front-end refinement =============\n');
run_expB_crossfrontend([], nworkers);
analyze_expB;
analyze_expB_matched;
analyze_expB_rmse_vs_eta;
make_figure_expB;

fprintf('\n================ supporting figures ===================================\n');
make_figure_geometry;
make_figure_module;

fprintf('\nMFT-W4-MODULE-20260918 complete in %.1f s\n', toc(t0));
end
