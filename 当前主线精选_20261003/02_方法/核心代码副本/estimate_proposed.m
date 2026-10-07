function out = estimate_proposed(y, fe, fam, u0, evalIdx, mcfg)
%ESTIMATE_PROPOSED  Coherent-output driven refinement inside the SAME family as B2.
%   Starts at u0 = u_B2, optimises -J_h over the stage schedule in sequence, then
%   selects among {u_B2, stage endpoints} by the final 290 s objective J.
%   Ground truth is never used: only y, the shared family and the eval interval.
%
%   Algorithm unchanged from week 1.  Two implementation changes only:
%     * mcfg.max_iter / mcfg.max_fevals may be PER-STAGE vectors (a scalar is
%       expanded), so the budget diagnostic can run P180 without touching P60;
%     * every stage endpoint is logged (exit flag, iterations, function count,
%       first-order optimality, exit message, J290 at the stage end, seconds).
%       Week 1 only stored the LAST stage's exit flag, which made the reported
%       "99.2% hit MaxIterations" ambiguous.

P = fam.P;
ctx.y     = y(evalIdx);
ctx.phiA  = fam.phiA(evalIdx);
ctx.H     = fam.H(evalIdx,:);
ctx.P     = P;
ctx.DtD   = fam.D2.'*fam.D2;
ctx.lambda= mcfg.lambda_C;
ctx.E     = sum(abs(ctx.y).^2) + eps;

Ne = numel(evalIdx);
nst = numel(mcfg.h_stages_s);
blkOf = cell(nst,1);
for s = 1:nst
    blkOf{s} = make_blocks(Ne, round(mcfg.h_stages_s(s)*fe.fs));
end
maxit = expand(mcfg.max_iter,   nst);
maxfe = expand(mcfg.max_fevals, nst);

cands = {u0(:)};  labels = {'B2'};
exitflags = nan(nst,1); iters = nan(nst,1); fevals = nan(nst,1);
foopt = nan(nst,1); stage_J290 = nan(nst,1); stage_s = nan(nst,1);
messages = repmat({''}, nst, 1);
uc = u0(:);  fallback = false;  errmsg = '';
ctxF = ctx; ctxF.blk = blkOf{end};          % final-stage context, for J290 logging
for s = 1:nst
    ctx.blk = blkOf{s};
    opts = optimoptions('fmincon','Algorithm','sqp','SpecifyObjectiveGradient',true, ...
        'MaxIterations',maxit(s),'MaxFunctionEvaluations',maxfe(s), ...
        'StepTolerance',mcfg.tol_x,'OptimalityTolerance',mcfg.tol_opt,'Display','off');
    t0 = tic;
    try
        [us, ~, ef, info] = fmincon(@(uu) coherence_objective(uu, ctx), uc, ...
            fam.Aineq, fam.bineq, [], [], fam.lb, fam.ub, [], opts);
        stage_s(s) = toc(t0);
        exitflags(s) = ef; iters(s) = info.iterations; fevals(s) = info.funcCount;
        if isfield(info,'firstorderopt'), foopt(s) = info.firstorderopt; end
        if isfield(info,'message'), messages{s} = first_line(info.message); end
        if all(isfinite(us)) && is_feasible(us, fam)
            uc = us(:);
            cands{end+1} = uc; labels{end+1} = sprintf('stage%d', s); %#ok<AGROW>
            stage_J290(s) = -coherence_objective(uc, ctxF);
        end
    catch ME
        stage_s(s) = toc(t0);
        fallback = true; errmsg = ME.message;
        exitflags(s) = -99; messages{s} = first_line(ME.message);
        break
    end
end

% --- unified candidate selection on the final 290 s objective (no truth used) ---
J = nan(numel(cands),1);
for i = 1:numel(cands)
    J(i) = -coherence_objective(cands{i}, ctxF);
end
[Jbest, ib] = max(J);
out.u_init = u0(:);
out.u = cands{ib};
out.selected = labels{ib};
out.J = J; out.J_labels = labels; out.J_best = Jbest;
out.J_B2 = J(1);
out.fallback = fallback || (ib == 1);
out.hard_fail = fallback;
out.errmsg = errmsg;
out.exitflags = exitflags; out.iters = iters; out.fevals = fevals;
out.firstorderopt = foopt; out.stage_J290 = stage_J290;
out.stage_seconds = stage_s; out.messages = messages;
out.max_iter = maxit; out.max_fevals = maxfe;
out.all_stages_capped = all(iters(:) >= maxit(:) - 1e-9) && ~fallback;
out.cands = cands;
out.g = fam.gA + fam.r*(fam.Bt*out.u);
end

function v = expand(x, n)
if isscalar(x), v = repmat(x, n, 1); else, v = x(:); end
end

function s = first_line(m)
m = char(m);
k = find(m == newline, 1, 'first');
if isempty(k), s = strtrim(m); else, s = strtrim(m(1:k-1)); end
if numel(s) > 120, s = s(1:120); end
end

function ok = is_feasible(u, fam)
tol = 1e-8;
ok = all(u >= fam.lb - tol) && all(u <= fam.ub + tol) && ...
     all(fam.Aineq*u <= fam.bineq + 1e-6);
end
