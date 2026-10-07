function blk = make_blocks(Ne, hs)
%MAKE_BLOCKS  Non-overlapping blocks of hs samples over 1..Ne; a short final
%   block is KEPT and its actual length is used.
b = 1:hs:Ne;
e = min(b + hs - 1, Ne);
blk = arrayfun(@(a,z) (a:z)', b, e, 'UniformOutput', false);
end
