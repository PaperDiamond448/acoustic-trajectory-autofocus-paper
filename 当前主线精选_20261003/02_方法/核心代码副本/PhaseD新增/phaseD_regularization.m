function [lambdaC,lambdaF,P]=phaseD_regularization(Delta,T,scaled)
if nargin<3, scaled=true; end
P=T/Delta+1; assert(abs(P-round(P))<1e-10 && P>=3);
if Delta==15 && T==300, scale=1;
elseif scaled, scale=(P-2)/19*(300/T)*(15/Delta)^3;
else, scale=1; end
lambdaC=1e-3*scale; lambdaF=0.1*scale;
end
