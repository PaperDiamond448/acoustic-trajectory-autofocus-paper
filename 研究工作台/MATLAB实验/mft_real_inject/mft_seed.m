function s = mft_seed(cfg, phase, scene, record_id)
%MFT_SEED  seed = master_seed + 1e6*phase_id + 1e4*scene_code + record_id
%   phase : 'budget' | 'h0_calibration' | 'h0_validation' | 'h1_test' | 'bootstrap'
%   scene : scene NAME ('S0','S1','S2','H0_0','H0_I') or its numeric code
%   The SNR is deliberately NOT part of the seed: within one scene, one
%   record_id shares geometry, phase and noise across all six SNR levels, so
%   the levels are paired and only the target amplitude changes.
if ischar(scene) || isstring(scene)
    code = cfg.scene_code.(char(scene));
else
    code = scene;
end
s = cfg.master_seed + 1000000*cfg.phase_id.(phase) + 10000*code + record_id;
end
