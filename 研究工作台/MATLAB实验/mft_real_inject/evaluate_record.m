function m = evaluate_record(y, t, ghat, evalIdx, noise_hat, truth, B)
%EVALUATE_RECORD  Detection statistic, residual peak, trajectory metrics and
%   ground-truth coherence efficiency for one trajectory on one record.
%   Everything is computed on the SAME evaluation interval.

fs = B.fs;
phi = 2*pi*cumtrapz(t, ghat);
z   = y .* exp(-1j*phi);
ze  = z(evalIdx);
Ne  = numel(ze);
nfft= 2^nextpow2(B.fft_pad*Ne);
nu  = (0:nfft-1)'*fs/nfft;  nu(nu >= fs/2) = nu(nu >= fs/2) - fs;
sel = find(abs(nu) <= B.band(2));
Zs  = abs(fft(ze, nfft)).^2;
[pk, i0] = max(Zs(sel));
m.nu_peak = nu(sel(i0));
m.Z = pk/(Ne*noise_hat);
m.Z_db = 10*log10(max(m.Z, realmin));
m.nfft = nfft;

geff = ghat + m.nu_peak;
m.phi = phi;

if truth.has_target
    st  = truth.s_target(evalIdx).*exp(-1j*phi(evalIdx));
    den = (sum(abs(truth.s_target(evalIdx))))^2;
    Es  = abs(fft(st, nfft)).^2;
    m.eta_max = max(Es(sel))/den;
    m.eta_at_selected_peak = Es(sel(i0))/den;
    m.loss_db = -10*log10(max(m.eta_max, 1e-12));
    m.loss_at_peak_db = -10*log10(max(m.eta_at_selected_peak, 1e-12));

    gt  = truth.gtrue(evalIdx);
    m.rmse_raw = sqrt(mean((ghat(evalIdx)-gt).^2));
    m.rmse_eff = sqrt(mean((geff(evalIdx)-gt).^2));
    ok  = abs(geff(evalIdx)-gt) <= B.track_tol;
    a   = truth.amp(evalIdx);
    te  = t(evalIdx);
    act = a >= B.active_amp;
    m.coverage_active = mean(ok(act));
    if any(~act), m.coverage_weak = mean(ok(~act)); else, m.coverage_weak = NaN; end
    ev  = te >= 140 & te <= 160;
    m.coverage_event = mean(ok(ev));
    m.track_success = m.coverage_active >= B.track_min_cov;
    m.max_bad_s = max_run(~ok)/fs;
    m.recovery_s = recovery_time(te, ok, 160, 5);
else
    m.eta_max = NaN; m.eta_at_selected_peak = NaN;
    m.loss_db = NaN; m.loss_at_peak_db = NaN;
    m.rmse_raw = NaN; m.rmse_eff = NaN;
    m.coverage_active = NaN; m.coverage_weak = NaN; m.coverage_event = NaN;
    m.track_success = false; m.max_bad_s = NaN; m.recovery_s = NaN;
end
end

function L = max_run(b)
L = 0; c = 0;
for i = 1:numel(b)
    if b(i), c = c + 1; if c > L, L = c; end, else, c = 0; end
end
end

function r = recovery_time(te, ok, t_end, hold_s)
i0 = find(te >= t_end, 1, 'first');
if isempty(i0), r = NaN; return; end
fs = 1/median(diff(te));
need = round(hold_s*fs);
n = numel(ok);
run = 0; start = NaN;
for i = i0:n
    if ok(i)
        if run == 0, start = i; end
        run = run + 1;
        if run >= need, r = te(start) - t_end; return; end
    else
        run = 0;
    end
end
if run > 0 && (n - start + 1) == run && run >= min(need, n-i0+1)
    r = te(start) - t_end; return;
end
r = NaN;
end
