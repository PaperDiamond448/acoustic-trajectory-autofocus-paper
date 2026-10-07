function M = cluster_map(rec_ids, ids)
%CLUSTER_MAP  M(i,:) lists the rows whose record_id equals ids(i).
%   Every record_id must appear the same number of times (one row per SNR
%   level), which is what makes the carry-all-versions resample well defined.
ids = ids(:);
M = [];
for i = 1:numel(ids)
    r = find(rec_ids == ids(i));
    if i == 1
        M = zeros(numel(ids), numel(r));
    elseif numel(r) ~= size(M,2)
        error('cluster_map:ragged', ...
            'record_id %d has %d rows, expected %d', ids(i), numel(r), size(M,2));
    end
    M(i,:) = r(:).';                                                  %#ok<AGROW>
end
end
