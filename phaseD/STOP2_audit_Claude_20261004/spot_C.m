T=readtable('D:\论文集\phaseD\C_confirm\C_records.csv','TextType','string');
files={'S0_-17dB_chunk_007.mat','S2_-20dB_chunk_013.mat'}; mx=0; n=0;
for i=1:2
  C=load(fullfile('D:\论文集\phaseD\C_confirm\chunks',files{i}));
  fn=fieldnames(C); R=C.(fn{find(strcmp(fn,'results'),1)});
  for r=1:numel(R)
    rows=R(r).rows;
    for j=1:numel(rows)
      q=T(T.scene==rows(j).scene & T.snr_db==rows(j).snr_db & T.record_id==rows(j).record_id & T.method==rows(j).method,:);
      assert(height(q)==1); mx=max([mx,abs(q.eta-rows(j).eta),abs(q.J-rows(j).J)]); n=n+1;
    end
  end
end
fprintf('rows compared %d, max|diff| %.3g\n',n,mx);
