function res = run_record(rec, cfg, methods, pvariants)
%RUN_RECORD  Run {B0,B1,B2,P60} on one record.  Receiver code is unchanged from
%   week 1; only the method label P -> P60 and the per-stage logging are new.
%
%   pvariants (optional) : cell array of P configurations, each a struct with
%   fields label / h_stages_s / max_iter / max_fevals.  Used by the budget
%   diagnostic to run several P variants from the SAME B2 start on the SAME
%   front end.  When omitted, the single frozen P60 configuration is used.
if nargin < 3 || isempty(methods), methods = {'B0','B1','B2','P60'}; end
B = cfg.B; M = cfg.M;
if nargin < 4 || isempty(pvariants)
    pv = {M.P};                      % the frozen P60 configuration
else
    pv = pvariants;                  % budget diagnostic: several variants
end
y = rec.y; t = rec.t;
evalIdx = find(t >= B.eval_s(1) & t < B.eval_s(2));

fcfg = struct('fs',B.fs,'L',B.L,'D',B.D,'df_fine',B.df_fine,'band',B.band, ...
              'coarse_dec',B.coarse_dec,'noise_bands',B.noise_bands);
tic; fe = common_frontend(y, t, fcfg); t_fe = toc;

res = [];
pv_run = pv(cellfun(@(v) any(strcmp(methods, v.label)), pv));
wantP   = ~isempty(pv_run);
need_b1 = any(ismember({'B1','B2'}, methods)) || wantP;
need_b2 = any(strcmp(methods,'B2')) || wantP;

if any(strcmp(methods,'B0'))
    tic; o0 = estimate_b0(fe, M.B0); tt = toc;
    res = [res, pack('B0', o0.g, t, y, evalIdx, fe, rec.truth, B, tt, t_fe+tt, ...
        struct('zero_frames',o0.zero_frames))];
end
if need_b1
    tic; o1 = estimate_b1(fe, M.B1); t1 = toc;
    if any(strcmp(methods,'B1'))
        res = [res, pack('B1', o1.g, t, y, evalIdx, fe, rec.truth, B, t1, t_fe+t1, struct())];
    end
end
if need_b2
    tic; fam = build_family(t, fe.tc, o1.g, M.B2); t_fam = toc;
    tic; o2 = estimate_b2(fe, fam, M.B2); t2 = toc;
    t2 = t2 + t_fam;
    fam_sig = [numel(fam.knots); fam.r; sum(fam.Bt(:)); sum(fam.Aineq(:)); sum(fam.bineq)];
    if any(strcmp(methods,'B2'))
        res = [res, pack('B2', o2.g, t, y, evalIdx, fe, rec.truth, B, t2, ...
            t_fe+t1+t2, struct('u',o2.u,'fit_failed',o2.fit_failed,'fam_sig',fam_sig))];
    end
end
if wantP
    for k = 1:numel(pv_run)
        vc = pv_run{k};
        tic; oP = estimate_proposed(y, fe, fam, o2.u, evalIdx, vc); tP = toc;
        res = [res, pack(vc.label, oP.g, t, y, evalIdx, fe, rec.truth, B, tP, ...
            t_fe+t1+t2+tP, ...
            struct('u',oP.u,'u_init',oP.u_init,'selected',oP.selected, ...
                   'fallback',oP.fallback,'hard_fail',oP.hard_fail, ...
                   'exitflags',oP.exitflags,'iters',oP.iters,'fevals',oP.fevals, ...
                   'firstorderopt',oP.firstorderopt,'stage_J290',oP.stage_J290, ...
                   'stage_seconds',oP.stage_seconds,'messages',{oP.messages}, ...
                   'all_stages_capped',oP.all_stages_capped, ...
                   'max_iter',oP.max_iter,'max_fevals',oP.max_fevals, ...
                   'J',oP.J,'J_B2',oP.J_B2,'J_best',oP.J_best,'fam_sig',fam_sig))];
    end
end

ih = input_hash(y);
for i = 1:numel(res)
    res(i).t_frontend = t_fe;
    res(i).noise_hat  = fe.noise_hat;
    res(i).input_hash = ih;
end
end

function s = pack(name, g, t, y, evalIdx, fe, truth, B, tm, tc, extra)
mm = evaluate_record(y, t, g, evalIdx, fe.noise_hat, truth, B);
mm = rmfield(mm, 'phi');
s = struct('method',name,'g',{g},'metrics',mm,'t_method',tm,'t_chain',tc, ...
           'extra',extra,'t_frontend',NaN,'noise_hat',NaN,'input_hash','');
end

function h = input_hash(y)
try
    b = typecast([real(y(:)); imag(y(:))], 'uint8');
    md = java.security.MessageDigest.getInstance('MD5');
    md.update(b);
    h = lower(reshape(dec2hex(typecast(md.digest(),'uint8')).', 1, []));
catch
    h = sprintf('%.17g_%.17g_%d', sum(real(y)), sum(abs(y).^2), numel(y));
end
end
