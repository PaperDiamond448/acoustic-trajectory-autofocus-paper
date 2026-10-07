function D2 = second_difference_matrix(P)
%SECOND_DIFFERENCE_MATRIX  (P-2) x P second-difference operator [1 -2 1].
D2 = zeros(P-2, P);
for i = 1:P-2
    D2(i, i:i+2) = [1 -2 1];
end
end
