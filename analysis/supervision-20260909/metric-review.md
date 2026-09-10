# 统计量与置乱检验理论审查（2026-09-09）

## 结论

按题述定义，\(M_i\) 对 \(X\) 固定且 \(M_i\ne0\)，候选统计量

\[
 R_i=\left|\operatorname{mean}_{X}
 \left(\frac{L_X}{|L_X|}\,\overline{\frac{M_i}{|M_i|}}\right)\right|
\]

**应否决为模型比较统计量**。它不依赖模型 \(i\)，随机化模型的整体相位也不能改变它，因此不能支持“模型选窗优于随机高度”的结论。若某个 \(L_X=0\) 或 \(M_i=0\)，相位归一化未定义；实现必须显式排除或预先规定处理规则。

## 代数证明与相位随机化

令
\[
 u_X=L_X/|L_X|,\qquad m_i=M_i/|M_i|,
\]
其中 \(m_i\) 与 \(X\) 无关。则
\[
 R_i=\left|\operatorname{mean}_X(u_X\overline{m_i})\right|
 =\left|\overline{m_i}\,\operatorname{mean}_X u_X\right|
 =|\overline{m_i}|\,\left|\operatorname{mean}_X u_X\right|
 =\left|\operatorname{mean}_X u_X\right|.
\]
最后一步使用 \(|m_i|=1\)。所以对任意两个非零模型 \(M_i,M_j\)，均有 \(R_i=R_j\)。若随机化 \(M_i\mapsto e^{\mathrm i\theta}M_i\)，归一化相位变成 \(e^{\mathrm i\theta}m_i\)，从而
\[
 R_i' = |e^{-\mathrm i\theta}|R_i=R_i.
\]
这覆盖任意全局随机相位。只有给每个 \(X\) 使用不同的随机相位（即把 \(M_i\) 改成真正的 \(M_i(X)\)）才可能改变数值；那已经是另一个统计量和另一个置乱方案，不能作为当前公式的性质。

**小数值反例。** 取
\[
 L=(1,1,\mathrm i,-\mathrm i),\quad
 M\in\{1,\mathrm i,-1,e^{0.731\mathrm i}\}.
\]
则 \(u=(1,1,\mathrm i,-\mathrm i)\)，
\(\operatorname{mean}(u)=1/2\)，故四个模型都给 \(R=0.5\)。将第一个模型乘以 \(e^{0.13\mathrm i},e^{1.7\mathrm i},e^{4.2\mathrm i}\) 后，数值仍为 0.5（浮点误差小于 \(10^{-12}\)）。可复现实验见 [`metric_check.py`](./metric_check.py)，输出见 [`metric_check.json`](./metric_check.json)。

## 累计截止 \(X\) 的 Lambda sums 不是独立尺度

若尺度量是累计和
\[
 \Lambda_X=\sum_{n\le X}a_n,
\]
则不同截止点共享全部较小索引的项。即使 \(a_n\) 是均值为零、方差有限且相互独立的随机增量，\(X\le Y\) 时也有
\[
 \operatorname{Cov}(\Lambda_X,\Lambda_Y)=\operatorname{Var}(\Lambda_X),\qquad
 \operatorname{Corr}(\Lambda_X,\Lambda_Y)
 =\sqrt{\operatorname{Var}(\Lambda_X)/\operatorname{Var}(\Lambda_Y)}.
\]
通常该相关性很高；若 \(a_n\) 是确定的算术序列，则“独立”更无概率意义。把重叠累计值当作独立观测会夸大有效样本量、使标准误和 p 值过小。需要使用不重叠增量、预先定义的块，或在置乱/重抽样中按整条相关向量（或块）交换并以簇数估计不确定性。

## 精确全枚举 p 与 Monte Carlo +1

设有 \(P\) 个**唯一**允许置乱，包含观测排列（通常记为恒等排列）\(\pi_0\)，统计量为 \(T(\pi)\)，检验方向为“大值更极端”。在置乱可交换的零假设下，精确离散 p 值是
\[
 p_{\mathrm{exact}}=\frac{1}{P}\sum_{\pi\in\Pi}{\bf1}\{T(\pi)\ge T(\pi_0)\}.
\]
计数包含 observed 本身，因此 p 至少为 \(1/P\)。使用“\(>\)”而不是“\(\ge\)”会得到另一种（可能反保守的）并列处理；若需随机化并列或 mid-p，必须预先声明，不能与上述 exact 定义混用。对全枚举不应再套一个“+1”而写成 \((k+1)/(P+1)\)，那不是该枚举空间的精确 p。

若只抽取 \(B\) 次 Monte Carlo 置乱，并把 observed 作为额外的一次，则常用保守估计为
\[
 \hat p_{+1}=\frac{1+\sum_{b=1}^{B}{\bf1}\{T_b\ge T_{\rm obs}\}}{B+1}.
\]
这里的“+1”对应分子中的 observed，分母是总的 \(B+1\) 次评估；它适用于随机抽样而非已完成的 \(P\) 项全枚举。若恰好枚举其余 \(P-1\) 个排列（即 \(B=P-1\)），该公式才退化为上面的 exact 计数。抽样是否允许重复、是否从包含 observed 的全集抽样，都必须在方案中固定并在解释时说明。

## 一个可用但条件更严格的修订量

要测“模型选窗比匹配随机高度有更强跨尺度结构”，必须让模型在尺度上有相对相位信息。对窗口/高度 \(h_i\) 和预先固定的 \(S\ge2\) 个尺度 \(X_s\)，定义
\[
 q_{i,s}=\frac{L(X_s,h_i)}{|L(X_s,h_i)|}\,
       \overline{\frac{M_i(X_s)}{|M_i(X_s)|}},
\]
并定义模型校正后的跨尺度相干
\[
 C_i=\frac{2}{S(S-1)}\sum_{s<t}\Re\!\left(q_{i,s}\overline{q_{i,t}}\right).
\]
它等价于
\[
 C_i=\frac{|\sum_s q_{i,s}|^2-S}{S(S-1)},
\]
取值范围为 \([-1/(S-1),1]\)。全局旋转 \(M_i(X_s)\mapsto e^{\mathrm i\theta}M_i(X_s)\) 会同时旋转所有 \(q_{i,s}\)，故 \(C_i\) 不变；但模型在不同尺度间的**相对**相位会改变 \(C_i\)，这正是当前 \(R_i\) 缺失的模型信息。

令 \(A\) 为模型选出的窗口集合，令 \(B\) 为按同一锚点、层/区域、窗口数和可用尺度匹配抽取的随机高度集合，使用一个差值统计量
\[
 \Delta=|A|^{-1}\sum_{i\in A}C_i-|B|^{-1}\sum_{j\in B}C_j.
\]
在零假设下，仅当以下可交换性限制成立时，才可对“选窗组标签”做置乱并计算 p 值：

1. \(A\) 与 \(B\) 的高度在匹配分层内可交换，且随机高度抽样机制在检验前固定；重叠累计尺度必须按整组/块交换，不能逐尺度假定独立。
2. 选窗若由同一批 \(L\) 数据挑选，会产生选择后偏差。应使用独立的留出尺度/数据来计算 \(C_i\)，或在每次置乱中完整重跑“选窗”步骤（包括阈值和排名），以保持选择机制对称。
3. 模型相位 \(M_i(X_s)\) 必须在检验数据之前预先确定，不能用同一观测 \(L\) 调参后再声称可交换；零值相位的排除规则也须预注册。

即使这些条件满足，\(\Delta\) 的显著性也只支持“该模型校正的跨尺度相干高于匹配随机高度”这一有限统计命题，不构成关于黎曼假设或 ζ 零点的结论。
