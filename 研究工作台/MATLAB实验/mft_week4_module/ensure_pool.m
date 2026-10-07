function p = ensure_pool(n)
%ENSURE_POOL  Start (or reuse) a process pool with n workers.
p = gcp('nocreate');
if isempty(p)
    p = parpool('Processes', n);
elseif p.NumWorkers ~= n
    delete(p); p = parpool('Processes', n);
end
end
