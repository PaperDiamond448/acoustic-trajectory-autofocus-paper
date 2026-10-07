function S = cluster_draws(ids, NB, seed)
%CLUSTER_DRAWS  Resampling plan for statistics that POOL the three SNR levels.
%
%   mft_seed does not include the SNR: one record_id shares geometry, initial
%   phase and noise across -18 / -17 / -16 dB, and only the target amplitude
%   changes.  The 300 versions of one branch are therefore 100 independent
%   realisations, not 300.  Anything that pools the levels resamples the
%   record_id and carries all of its SNR versions together.
%
%   Per-SNR cells hold one row per record_id and are already independent, so
%   they keep their own within-cell bootstrap and their Wilson intervals.
%
%   S is NB x numel(ids).  ONE draw per replicate is shared by every branch
%   and every metric, so branch-to-branch comparisons stay paired inside a
%   replicate.
ids = ids(:);
rs  = RandStream('mt19937ar','Seed',seed);
n   = numel(ids);
S   = ids(randi(rs, n, NB, n));
end
