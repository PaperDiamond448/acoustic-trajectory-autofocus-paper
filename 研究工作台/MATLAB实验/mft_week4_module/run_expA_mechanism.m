function run_expA_mechanism(outdir)
%RUN_EXPA_MECHANISM  Deterministic counterexample: a smaller frequency RMSE
%   does not imply a higher coherent efficiency.
%
%   Protocol MFT-W4-MODULE-20260918, section 1 of PREREGISTRATION_W4.md.
%   No noise, no interference, no estimator is run.  Two frequency-error
%   trajectories are CONSTRUCTED on the same 21 knots the refinement module
%   uses, and both are scored with the discrete coherence efficiency of
%   evaluate_record.m.
if nargin < 1, outdir = fullfile(pwd,'results','expA'); end
if ~exist(outdir,'dir'), mkdir(outdir); end
cfg = mft_config();  B = cfg.B;  mP = cfg.M.B2;      % knot_ds / radius / band

fs = B.fs;  N = B.N;  t = (0:N-1)'/fs;
knots = (0:mP.knot_ds:300)';  P = numel(knots);
r = mP.radius;
evalIdx = find(t >= B.eval_s(1) & t < B.eval_s(2));
Ne = numel(evalIdx);
nfft = 2^nextpow2(B.fft_pad*Ne);
nu = (0:nfft-1)'*fs/nfft;  nu(nu >= fs/2) = nu(nu >= fs/2) - fs;
sel = find(abs(nu) <= B.band(2));

U = struct( ...
    'tag',   {'A','B'}, ...
    'name',  {'small, slowly varying','larger, alternating'}, ...
    'formula',{'0.3*sin(2*pi*t_p/300)','0.5*(-1)^p'}, ...
    'u',     {0.3*sin(2*pi*knots/300), 0.5*(-1).^(0:P-1)'});

rows = cell(numel(U),1);
curves = table(t, 'VariableNames', {'t_s'});
for k = 1:numel(U)
    e   = interp_const(knots, r*U(k).u, t);          % Hz, frequency error
    phi = 2*pi*cumtrapz(t, e);                       % rad, residual phase
    z   = exp(1j*phi(evalIdx));                      % unit-amplitude target
    Z   = abs(fft(z, nfft)).^2;
    [pk, i0] = max(Z(sel));
    eta = pk/Ne^2;                                   % (sum|s|)^2 = Ne^2 here
    nup = nu(sel(i0));
    ee  = e(evalIdx);
    rows{k} = {U(k).tag, U(k).name, U(k).formula, ...
        sqrt(mean(ee.^2)), sqrt(mean((ee-mean(ee)).^2)), mean(ee), max(abs(ee)), ...
        eta, -10*log10(max(eta,1e-12)), nup, Ne, nfft};
    curves.(['e_' U(k).tag '_hz'])       = e;
    curves.(['phi_' U(k).tag '_rad'])    = phi;
    % residual phase after removing the best constant frequency offset (the
    % part the final residual-frequency search can absorb); nu_peak is logged
    % with it so the figure can state what was subtracted.
    curves.(['phi_' U(k).tag '_detr_rad']) = phi - 2*pi*nup*(t - t(evalIdx(1)));
end
T = cell2table(vertcat(rows{:}), 'VariableNames', {'case_tag','description','knot_formula', ...
    'rmse_hz','rmse_demeaned_hz','mean_error_hz','max_abs_error_hz', ...
    'eta_max','loss_db','nu_peak_hz','Ne','nfft'});
writetable(T, fullfile(outdir,'expA_mechanism.csv'));
writetable(curves, fullfile(outdir,'expA_curves.csv'));

% ---- comparison with the values frozen in PREREGISTRATION_W4.md ----
expect = struct('rmse',[0.0042793125 0.0057291551], ...
                'rmse_dm',[0.0042793125 0.0057245411], ...
                'eta',[0.3627360352 0.9703425052]);
d = struct();
d.rmse_absdiff    = abs(T.rmse_hz(:).'          - expect.rmse);
d.rmse_dm_absdiff = abs(T.rmse_demeaned_hz(:).' - expect.rmse_dm);
d.eta_absdiff     = abs(T.eta_max(:).'          - expect.eta);
d.max_absdiff     = max([d.rmse_absdiff d.rmse_dm_absdiff d.eta_absdiff]);
d.tolerance       = 1e-9;
d.reproduces_preregistered_values = d.max_absdiff <= d.tolerance;
d.counterexample_holds = (T.rmse_hz(1) < T.rmse_hz(2)) && (T.eta_max(1) < T.eta_max(2));
d.counterexample_holds_after_demeaning = ...
    (T.rmse_demeaned_hz(1) < T.rmse_demeaned_hz(2)) && (T.eta_max(1) < T.eta_max(2));
d.B_error_not_pointwise_larger = any(abs(curves.e_B_hz(evalIdx)) < abs(curves.e_A_hz(evalIdx)));
d.frac_samples_absB_lt_absA = mean(abs(curves.e_B_hz(evalIdx)) < abs(curves.e_A_hz(evalIdx)));
d.protocol = 'MFT-W4-MODULE-20260918';
d.eta_definition = 'evaluate_record.m discrete: max_{|nu|<=2Hz} |FFT(z,nfft)|^2 / (sum|s|)^2';
fid = fopen(fullfile(outdir,'expA_check.json'),'w');
fprintf(fid,'%s', jsonencode(d,'PrettyPrint',true)); fclose(fid);

disp(T(:,{'case_tag','rmse_hz','rmse_demeaned_hz','max_abs_error_hz','eta_max','nu_peak_hz'}));
fprintf('max |MATLAB - preregistered| = %.3e (tol %.0e) -> reproduces = %d\n', ...
    d.max_absdiff, d.tolerance, d.reproduces_preregistered_values);
fprintf('counterexample holds = %d ; after demeaning = %d\n', ...
    d.counterexample_holds, d.counterexample_holds_after_demeaning);
fprintf('fraction of eval samples with |e_B| < |e_A| = %.3f\n', d.frac_samples_absB_lt_absA);
end
