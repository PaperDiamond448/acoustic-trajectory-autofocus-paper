function [z_full, t_full, seg_info] = build_full_baseband(file, chan, fref, fs, keep_hz, fs_raw, n_raw, total_s)
%BUILD_FULL_BASEBAND  Concatenate non-overlapping win_len_s segments covering
%   [0, total_s) into one continuous complex-baseband series at rate fs,
%   using phaseA_load_baseband.m (the generalised, edge-safe version of
%   load_real_baseband.m). Segment 1 has no left guard, the last segment has
%   no right guard (both touch the physical ends of the record); all interior
%   segments keep the frozen 10 s/10 s guard.
%
%   [z_full, t_full, seg_info] = build_full_baseband(file, chan, fref, fs, ...
%                                                     keep_hz, fs_raw, n_raw, total_s)

win_len_s = 300;
guard_s   = 10;
t0_list = 0:win_len_s:(total_s - win_len_s);
n_seg = numel(t0_list);
n_per_seg = round(win_len_s*fs);
z_full = complex(zeros(n_seg*n_per_seg, 1));
seg_info = struct('t0_s',{},'info',{});

for k = 1:n_seg
    t0 = t0_list(k);
    guard_lo = guard_s; guard_hi = guard_s;
    if t0 == 0,                 guard_lo = 0; end
    if t0 + win_len_s == total_s, guard_hi = 0; end
    [zk, info] = phaseA_load_baseband(file, chan, fref, fs, keep_hz, fs_raw, n_raw, ...
                                       t0, win_len_s, guard_lo, guard_hi);
    z_full((k-1)*n_per_seg + (1:n_per_seg)) = zk;
    seg_info(k).t0_s = t0;
    seg_info(k).info = info;
end
t_full = (0:numel(z_full)-1)'/fs;
end
