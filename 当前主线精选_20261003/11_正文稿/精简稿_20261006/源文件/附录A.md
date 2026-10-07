# 附录 A 理论推导

## A.1 运动声源的发射时刻与接收频率关系

声源沿直线匀速运动，速度为 $v$，在发射时刻 $\tau_c$ 距水听器最近，最近距离为 $d_c$。发射时刻 $\tau$ 的源–水听器距离为

$$
R(\tau)=\sqrt{d_c^2+v^2(\tau-\tau_c)^2}.
\tag{A1}
$$

在 $\tau$ 时刻发出的信号于 $t=\tau+R(\tau)/c$ 时刻到达。由 $c(t-\tau)=R(\tau)\ge0$ 可知 $\tau\le t$。两边平方，得到关于 $\tau$ 的二次方程

$$
(c^2-v^2)\,\tau^2-2\,(c^2t-v^2\tau_c)\,\tau+\big(c^2t^2-v^2\tau_c^2-d_c^2\big)=0 .
\tag{A2}
$$

其判别式化简为 $4\big[c^2v^2(t-\tau_c)^2+(c^2-v^2)d_c^2\big]$，两个根为

$$
\tau_\pm(t)=\frac{c^2t-v^2\tau_c\pm\sqrt{c^2v^2(t-\tau_c)^2+(c^2-v^2)\,d_c^2}}{c^2-v^2}.
\tag{A3}
$$

对 $\tau_-$，有

$$
t-\tau_-=\frac{-v^2(t-\tau_c)+\sqrt{c^2v^2(t-\tau_c)^2+(c^2-v^2)\,d_c^2}}{c^2-v^2}.
$$

由于 $c>v$，根号项不小于 $cv\,|t-\tau_c|\ge v^2|t-\tau_c|$，所以 $t-\tau_-\ge0$，满足因果条件。$\tau_+$ 则给出 $t-\tau_+<0$。因此发射时刻取

$$
\tau(t)=\frac{c^2t-v^2\tau_c-\sqrt{c^2v^2(t-\tau_c)^2+(c^2-v^2)\,d_c^2}}{c^2-v^2}.
\tag{A4}
$$

最近通过位置处发出的信号在 $t_c=\tau_c+d_c/c$ 时刻到达水听器，本文以 $t_c$ 表示接收时间轴上的最近通过时刻；仿真先抽取 $t_c$，再换算出 $\tau_c$。目标的基带相位为 $\phi_g(t)$，下变频前的接收频率为 $f_{\rm rec}(t)=f_0\,d\tau/dt$，对应的基带频率为 $g(t)=f_{\rm rec}(t)-f_{\rm ref}$：

$$
\phi_g(t)=2\pi f_0\,\tau(t)-2\pi f_{\rm ref}\,t+\phi_0,\qquad
f_{\rm rec}(t)=\frac{f_0}{c^2-v^2}\left[c^2-\frac{c^2v^2(t-\tau_c)}{\sqrt{c^2v^2(t-\tau_c)^2+(c^2-v^2)\,d_c^2}}\right].
\tag{A5}
$$

$d\tau/dt$ 随 $t$ 单调减小。令 $d\tau/dt=1$，可解得 $t-\tau_c=d_c/c$，即 $t=t_c$。因此接收频率在接收端最近通过时刻恰好等于 $f_0$，此前高于 $f_0$，此后低于 $f_0$。

## A.2 分块相干目标的最小二乘形式

相位补偿不改变样点的模，$|z_{\mathbf u}[n]|=|y[n]|$，因此对任意 $\mathbf u$ 都有 $\sum_{n\in\mathcal I}|z_{\mathbf u}[n]|^2=E$。

对第 $b$ 块，令 $c_b$ 为待定的常数复幅度。残差

$$
\sum_{n\in\mathcal I_b}\big|z_{\mathbf u}[n]-c_b\big|^2
=\sum_{n\in\mathcal I_b}|z_{\mathbf u}[n]|^2-2\,{\rm Re}\{c_b^*R_b\}+N_b|c_b|^2
\tag{A6}
$$

是 $c_b$ 的二次函数，在 $c_b=R_b/N_b$ 时取最小，最小值为 $\sum_{n\in\mathcal I_b}|z_{\mathbf u}[n]|^2-|R_b|^2/N_b$。对所有块求和，得到

$$
\min_{\{c_b\}}\sum_b\sum_{n\in\mathcal I_b}\big|z_{\mathbf u}[n]-c_b\big|^2
=E-\sum_b\frac{|R_b|^2}{N_b}=E\,\big[1-Q_h(\mathbf u)\big],
\tag{A7}
$$

即式 (11)。由 Cauchy–Schwarz 不等式，$|R_b|^2\le N_b\sum_{n\in\mathcal I_b}|z_{\mathbf u}[n]|^2$，所以 $0\le Q_h\le1$。

若每块的补偿后记录由一个未知常数复幅度和方差为 $\sigma^2$ 的白色圆对称复高斯噪声组成，即 $z_{\mathbf u}[n]=c_b+w[n]$，$n\in\mathcal I_b$，则对数似然为

$$
\ell(\mathbf u,\{c_b\},\sigma^2)=-|\mathcal I|\ln(\pi\sigma^2)-\frac1{\sigma^2}\sum_b\sum_{n\in\mathcal I_b}\big|z_{\mathbf u}[n]-c_b\big|^2 .
\tag{A8}
$$

代入 $c_b=R_b/N_b$，得到 $-|\mathcal I|\ln(\pi\sigma^2)-E\,[1-Q_h(\mathbf u)]/\sigma^2$。再代入 $\sigma^2$ 的最优值 $E\,[1-Q_h(\mathbf u)]/|\mathcal I|$，集中对数似然为 $-|\mathcal I|\ln\{\pi E\,[1-Q_h(\mathbf u)]/|\mathcal I|\}-|\mathcal I|$。$E$ 与 $\mathbf u$ 无关，所以无论 $\sigma^2$ 已知还是未知，集中对数似然都随 $Q_h$ 单调增加，最大化 $Q_h$ 就是这一模型下关于 $\mathbf u$ 的最大似然估计。

## A.3 相干优化目标的梯度推导

由式 (9)，$\phi_{\mathbf u}(t)$ 对 $u_p$ 的导数为 $h_p(t)$，于是 $\partial z_{\mathbf u}[n]/\partial u_p=-j\,h_p(t_n)\,z_{\mathbf u}[n]$，且

$$
\frac{\partial R_b}{\partial u_p}=\sum_{n\in\mathcal I_b}\big(-j\,h_p(t_n)\big)\,z_{\mathbf u}[n],\qquad
\frac{\partial|R_b|^2}{\partial u_p}=2\,{\rm Re}\Big\{R_b^*\,\frac{\partial R_b}{\partial u_p}\Big\}.
\tag{A9}
$$

代入式 (10) 即得式 (13) 中的 $\partial Q_h/\partial u_p$。平滑罚 $\lambda\|D_2\mathbf u\|^2/(P-2)$ 的梯度为 $2\lambda D_2^{\mathsf T}D_2\mathbf u/(P-2)$。每次计算需要对 $|\mathcal I|$ 个样点和 $P$ 个系数求和，运算量为 $O(|\mathcal I|P)$。
