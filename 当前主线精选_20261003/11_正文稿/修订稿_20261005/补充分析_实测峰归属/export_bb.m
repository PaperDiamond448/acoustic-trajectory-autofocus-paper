% Read-only export of saved 20 Hz baseband screening inputs to raw binary.
root = 'D:\论文集\phaseD\X3_real\screen_inputs';
% Output folder: ./baseband next to this script (pass another folder by editing this line).
out  = fullfile(fileparts(mfilename('fullpath')), 'baseband');
if ~exist(out, 'dir'), mkdir(out); end
tones = [49 52 61 100 103 118 121 133 136];
for tone = tones
  for s = 0:300:2700
    Q = load(fullfile(root, sprintf('f%d_s%d.mat', tone, s)), 'y');
    y = Q.y(:);
    fid = fopen(fullfile(out, sprintf('f%d_s%d.bin', tone, s)), 'w');
    fwrite(fid, [real(y) imag(y)].', 'double'); fclose(fid);
  end
end
disp('done');
