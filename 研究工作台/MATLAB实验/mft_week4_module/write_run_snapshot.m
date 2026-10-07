function h = write_run_snapshot(outdir)
%WRITE_RUN_SNAPSHOT  Separate SHA-256 hashes for receiver code, configuration
%   and analysis code of the CORRECTED neighbour run, so that a later re-plot
%   or re-summary cannot be confused with a change to the receiver.
if nargin < 1, outdir = fullfile(pwd,'results'); end
if ~exist(outdir,'dir'), mkdir(outdir); end
here = fileparts(mfilename('fullpath'));

algo = {'geometry_tau.m','envelope_h.m','interp_const.m','second_difference_matrix.m', ...
        'czt_match.m','common_frontend.m','noise_scale.m','detect_stat.m', ...
        'build_family.m','estimate_b0.m','estimate_b1.m','estimate_b2.m', ...
        'estimate_proposed.m','coherence_objective.m','dp_viterbi.m','band_logT.m', ...
        'make_blocks.m','evaluate_record.m','simulate_baseband.m','mft_seed.m', ...
        'make_jobs.m','suvorova_transition.m','estimate_suvorova.m'};
conf = {'mft_config.m','suvorova_config.m','neighbour_plan.m'};
anal = {'run_neighbour_dev.m','run_neighbour_compare.m','analyze_neighbour.m', ...
        'run_checks_w3fix.m','run_timing_same_basis.m','make_figures_w3.m', ...
        'pctl.m','wilson_interval.m','ensure_pool.m'};

h.receiver = hash_set(here, algo);
h.config   = hash_set(here, conf);
h.analysis = hash_set(here, anal);
h.combined = hash_set(here, [algo conf anal]);
h.revision = 'fix-ABC-20260917';
h.timestamp= datestr(now,'yyyy-mm-dd HH:MM:SS'); %#ok<TNOW1,DATST>

rows = {};
for f = [algo conf anal]
    p = fullfile(here, f{1});
    if ~exist(p,'file'), continue; end
    d = dir(p);
    grp = 'analysis';
    if any(strcmp(f{1}, algo)), grp = 'receiver'; end
    if any(strcmp(f{1}, conf)), grp = 'config';   end
    rows(end+1,:) = {grp, f{1}, d.bytes, hash_set(here, f)}; %#ok<AGROW>
end
T = cell2table(rows,'VariableNames',{'group','file','bytes','sha256'});
writetable(T, fullfile(outdir,'source_manifest.csv'));
fid = fopen(fullfile(outdir,'source_hashes.json'),'w');
fprintf(fid,'%s',jsonencode(h,'PrettyPrint',true)); fclose(fid);
fprintf('receiver %s\nconfig   %s\nanalysis %s\n', h.receiver, h.config, h.analysis);
end

function out = hash_set(here, files)
if ischar(files), files = {files}; end
md = java.security.MessageDigest.getInstance('SHA-256');
for i = 1:numel(files)
    p = fullfile(here, files{i});
    if ~exist(p,'file'), continue; end
    fid = fopen(p,'r'); b = fread(fid, Inf, '*uint8'); fclose(fid);
    md.update(uint8(files{i}));
    md.update(b);
end
out = lower(reshape(dec2hex(typecast(md.digest(),'uint8')).', 1, []));
end
