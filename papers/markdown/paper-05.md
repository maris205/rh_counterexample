# An Area-Preserving Hénon-Map Model for the Riemann Zeros: A Deterministic-Dynamics Approach with Quantum and Dissipative Solvers

[论文目录](../README.md)

- 原始文件：`5-An Area-Preserving Henon-Map Model.pdf`。
- [原始 PDF](../pdf/paper-05.pdf)，共 17 个物理页。
- PDF SHA-256：`23dad812162728316f633081e1a1995d4c00614a70d0f5877d425c68d0c726b9`。

> 本文为 PDF 的按页文本提取版，供搜索、引用定位和程序读取。
> 正文使用等宽文本块保留提取顺序与空格；未将公式人工重排成 LaTeX。
> 上下标、特殊符号、双栏顺序及图形可能无法由文本准确表达，请以所附 PDF 为准。
> 原稿表述按原文保留；归档不表示其中的数学结论已经通过验证。

## 页码导航

[1](#pdf-page-1) · [2](#pdf-page-2) · [3](#pdf-page-3) · [4](#pdf-page-4) · [5](#pdf-page-5) · [6](#pdf-page-6) · [7](#pdf-page-7) · [8](#pdf-page-8) · [9](#pdf-page-9) · [10](#pdf-page-10) · [11](#pdf-page-11) · [12](#pdf-page-12) · [13](#pdf-page-13) · [14](#pdf-page-14) · [15](#pdf-page-15) · [16](#pdf-page-16) · [17](#pdf-page-17)

## PDF page 1

[核对 PDF 原页](../pdf/paper-05.pdf#page=1)

```text
 1


     An Area-Preserving Hénon-Map Model for the
     Riemann Zeros: A Deterministic-Dynamics
     Approach with Quantum and Dissipative
     Solvers
     Liang Wang 1,∗
     1 School of Artificial Intelligence and Automation, Huazhong University of Science

     and Technology, Wuhan, P.R. China
     Correspondence*:
     Liang Wang
     wangliang.f@gmail.com




 2   ABSTRACT


 3     The Hilbert–Pólya conjecture proposes that the imaginary parts of the nontrivial Riemann
 4   zeros are the eigenvalues of a self-adjoint operator. Random matrix theory describes their local
 5   statistics: after unfolding, the pair correlation matches the Gaussian Unitary Ensemble (GUE),
 6   with subleading arithmetic corrections from the Hardy–Littlewood conjectures. Building on our
 7   finding that the symbolic dynamics of the Logistic map at its band-merging point is isomorphic to
 8   the prime sieve [Wang, Research in Mathematics 13(1), 2026], we ask a constructive question:
 9   can a single low-dimensional deterministic system reproduce both the global counting function of
10   the zeros and their local repulsion? The one-dimensional Logistic map is dissipative (det J → 0)
11   and cannot host a unitary spectrum, so we lift it to the two-dimensional area-preserving Hénon
12   map (det J = 1) and analyze its spectrum near the edge of chaos. From the map’s continuum
13   limit we build a quartic-regularized Hamiltonian and two independent eigensolvers — a unitary
14   Fourier (quantum) solver and a Markovian Fokker–Planck (dissipative) solver — and compare
15   to the first 100 zeros. With single-point anchoring, the quantum solver reaches a best mean
16   absolute percentage error of 2.3% (a sharp optimum) and a robust ≈ 10–20% across grids and
17   regularizations; the dissipative solver reaches 6.5%. A globally fitted GUE surrogate shows
18   systematic deviation in the same comparison. The quantum solver’s Floquet eigenphases show
19   GUE-type level repulsion, though such statistics are generic to chaotic systems; the distinctive
20   result is the agreement with the actual zero values. We present these as numerical observations
21   and heuristic arguments rather than proofs, and state explicitly which claims are conjectural,
22   numerical, or established.


23 Keywords: Riemann zeros, Hénon map, area-preserving dynamics, quantum chaos, Hilbert–Pólya conjecture, Fokker–Planck dynamics,
24 spectral statistics



                                                                                                                                 1
```

## PDF page 2

[核对 PDF 原页](../pdf/paper-05.pdf#page=2)

```text
     Wang                                                             A Hénon-Map Model for Riemann Zeros


     1     INTRODUCTION
25   1.1    The Hilbert–Pólya conjecture and the dynamical viewpoint
26     Since Riemann’s 1859 memoir (Riemann, 1859) connected the distribution of primes to the nontrivial
27   zeros of the ζ function, the Riemann Hypothesis — that all nontrivial zeros ρ = 1/2 + iγn lie on the critical
28   line — has remained central to both mathematics and mathematical physics (Titchmarsh and Heath-Brown,
29   1986; Sarnak, 2000). The Hilbert–Pólya conjecture offers a physical route to this statement: if the ordinates
30   γn are the eigenvalues of a self-adjoint operator, their reality follows automatically (Schumayer and
31   Hutchinson, 2011). This idea has motivated a long line of candidate operators and quantization schemes,
32   from the Berry–Keating H = xp proposal (Berry and Keating, 1999) and its Bender–Brody–Müller variant
33   (Bender et al., 2017), to the modified-commutator generalizations explored by Bishop et al. (2019), as well
34   as approaches based on noncommutative geometry (Connes, 1999) and Landau levels (Sierra and Townsend,
35   2008). We emphasize at the outset that the present work does not claim to identify the Hilbert–Pólya
36   operator or to prove any statement about the zeros; it explores a specific deterministic dynamical system as
37   a numerical model whose spectrum is compared to the zeros.

38   1.2    Random matrix theory: what it does and does not assert
39     A foundational result in this area is the agreement between the local statistics of the Riemann zeros
40   and those of the GUE. Montgomery’s pair-correlation conjecture (Montgomery, 1973), together with
41   Dyson’s identification of the corresponding random-matrix form (Dyson, 1962) and Odlyzko’s high-
42   precision numerical confirmation (Odlyzko, 1987), established this connection, which sits within the
43   Bohigas–Giannoni–Schmit framework relating quantum chaos to RMT (Bohigas et al., 1984; Gutzwiller,
44   1990).
45     It is important to state the RMT position accurately, as our earlier draft did not. The GUE correspondence
46   concerns the unfolded local spectral statistics: one first removes the smooth, slowly varying mean density
47   N̄ (E) ∼ (E/2π) log(E/2π) (Weyl, 1911) — which is dictated by the prime number theorem (Hadamard,
48   1896) — so that the rescaled spacings have unit mean, and only then compares correlation functions.
49   RMT does not assert that a finite Wigner semicircle reproduces the global counting function of the zeros;
50   the unfolding step removes exactly that global information. Moreover, the deviations of the zeros from
51   pure GUE behavior are not failures of RMT but carry arithmetic content: the subleading, non-universal
52   corrections to the pair correlation are equivalent to the Hardy–Littlewood twin-prime conjecture, as shown
53   by Keating and Smith (2019). We thank the reviewers for pressing this point.
54     Given this, our motivation is not to claim that RMT “fails.” Rather, we ask a constructive and
55   complementary question: can a single, low-dimensional deterministic dynamical system generate, within
56   one model and without a manual unfolding step, both the global mean density and the local repulsion of
57   the zeros? A positive numerical answer would not contradict RMT; it would offer a concrete dynamical
58   object whose spectrum exhibits both scales simultaneously, in the spirit of the Hilbert–Pólya program.

59   1.3    From a published prime–chaos isomorphism to a 2D area-preserving map
60     The starting point of this paper is a result we have recently published. In Wang (2026) we showed that
61   the symbolic dynamics of the one-dimensional Logistic map at its band-merging point (uc ≈ 1.5437) is
62   isomorphic to the symbolic structure of the prime sieve, and that the Hardy–Littlewood twin-prime constant
63   (C2 ≈ 0.6602) emerges as a fixed point of that dynamical system to a numerical precision better than 10−4
64   without parameter tuning. That work concerns the primes themselves; the present work asks the natural

     Frontiers                                                                                                   2
```

## PDF page 3

[核对 PDF 原页](../pdf/paper-05.pdf#page=3)

```text
      Wang                                                           A Hénon-Map Model for Riemann Zeros


 65 follow-up question dictated by the Hilbert–Pólya viewpoint: if a deterministic map encodes the arithmetic
 66 of the sieve, what is the spectrum associated with it, and how does that spectrum compare to the Riemann
 67 zeros?

 68     The Logistic map is, however, strongly dissipative: its Jacobian determinant collapses (det J → 0),
 69   phase-space volume is not conserved, and the dynamics are not time-reversible. Such a system cannot
 70   support the unitary, time-reversal-respecting structure required for a real, Hermitian-like spectrum in the
 71   Hilbert–Pólya sense; a spectrum extracted directly from it would generically drift into the complex plane.
 72   This is a structural obstruction, not a numerical one. We therefore lift the dynamics to the two-dimensional
 73   area-preserving Hénon map (Hénon, 1969), in which the area-preserving constraint (det J = 1) restores
 74   volume conservation and time-reversal symmetry. The remainder of the paper performs a spectral analysis
 75   of this 2D map near the edge of chaos and compares the resulting eigenvalues with the Riemann zeros,
 76   using two numerically independent solvers as a cross-check.

 77   1.4    Scope and claims
 78     Because the subject touches the Riemann Hypothesis, we are explicit about the epistemic status of our
 79   statements. This paper reports (i) a structural argument for moving from a 1D dissipative map to a 2D
 80   area-preserving map; (ii) a numerical determination of a critical parameter associated with a homoclinic
 81   tangency; (iii) numerical comparisons between the spectra of two independent solvers and the first 100
 82   Riemann zeros; and (iv) a qualitative comparison with published quantum-hardware decoherence data.
 83   None of these constitutes a proof that the spectrum of our operator coincides with the zeros, and we do
 84   not claim otherwise. Table 1 summarizes the status of each claim. We have correspondingly removed the
 85   proof-level and promotional language of the previous version.

      2     MATERIALS AND METHODS
 86   2.1    From the 1D dissipative map to the 2D area-preserving map
 87     A semiclassical heuristic for level repulsion is that the underlying classical dynamics should occupy a
 88   mixed phase space in which regular and chaotic regions coexist. As noted above, the 1D Logistic map
 89   xn+1 = 1 − u x2n that we used in Wang (2026) to model the prime sieve is dissipative: det J → 0, the
 90   maximal Lyapunov exponent at the band-merging point is large (λ ≈ 0.34), and time-reversal symmetry is
 91   absent. We regard the 1D map as a reduced (dissipative) description of the arithmetic and not as a candidate
 92   spectral host.
 93   To restore the structure required by Hilbert–Pólya, we use the area-preserving Hénon family with b = −1
 94 (det J = 1):
                                             xn+1 = 1 − a x2n − xn−1 .                                       (1)
 95 In this conservative setting, phase-space volume is preserved and the dynamics are time-reversible.
 96 Numerically, the maximal Lyapunov exponent in the regime of interest drops to a weakly chaotic value
 97 (λ ≈ 0.11), which is the kind of weak chaos associated with level repulsion while still allowing long-lived
 98 (near-)regular structures.

 99   2.2    Phase-space scan and the parity statistic at a ≈ 1.02
100   In a conservative system the control parameter a governs the breakup of Kolmogorov–Arnold–Moser
101 (KAM) tori. We performed a Monte Carlo scan over a, sampling orbits and recording (i) the orbit survival


      Frontiers                                                                                                 3
```

## PDF page 4

[核对 PDF 原页](../pdf/paper-05.pdf#page=4)

```text
      Wang                                                          A Hénon-Map Model for Riemann Zeros


102 rate (fraction of initial conditions remaining bounded) and (ii) a symbolic “LL” statistic that counts
103 consecutive same-side excursions, the dynamical analogue of the consecutive-odd-cluster prohibition
104 identified in Wang (2026).




      Figure 1. Phase portraits of the area-preserving Hénon map (1) as the control parameter a increases. (a)
      a = 0.50: predominantly regular, with unbroken KAM tori. (b) a = 0.9: onset of nonlinear resonance. (c)
      a ≈ 1.0: near the onset of homoclinic tangency. (d) a = 1.05: global KAM breakup, leaving a chaotic
      saddle. Panels are generated by 1-henon attractor.ipynb.

105   As shown in Figures 1 and 2, increasing a toward ≈ 1.0 drives the progressive breakup of KAM tori. The
106 LL statistic on surviving orbits decreases and reaches zero, within our sampling resolution, near a ≈ 1.02.
107 We stress that this is a numerically observed transition at finite sampling, not an exact analytic threshold;
108 the exact onset of the underlying homoclinic tangency is treated separately in the next subsection.

109   2.3   Numerical determination of the homoclinic tangency (ac ≈ 1.0056)
110     The value a ≈ 1.02 identified from the finite-resolution statistical scan should be distinguished from
111   the exact onset of the global topological change. The latter is governed by the first homoclinic tangency
112   of the unstable manifold of the hyperbolic fixed point with the symmetry line y = x. We computed this
113   critical parameter numerically; we do not present it as a closed-form theorem, and we have renamed this
114   subsection accordingly (it was previously, and inaccurately, titled a “mathematical proof”).

      Frontiers                                                                                                4
```

## PDF page 5

[核对 PDF 原页](../pdf/paper-05.pdf#page=5)

```text
      Wang                                                           A Hénon-Map Model for Riemann Zeros




      Figure 2. Monte Carlo scan of the area-preserving map (b = −1). As a increases toward a ≈ 1.02
      (vertical dashed-dotted line), the orbit survival rate decreases and the measured “LL” parity statistic
      on surviving orbits falls toward zero. We report this as a numerically observed transition; the value
      a ≈ 1.02 is the location at which the LL statistic vanishes within our sampling resolution. Generated by
      2-henon param scan.ipynb.

                                                    √                                            √
115   The hyperbolic fixed point is X ∗ = (−1 − 1 + a)/a, with Jacobian trace Tr(J) = 2 + 2 1 + a > 4,
116 so the fixed point is a saddle with an unstable manifold W u . We numerically iterated W u and located, by
117 scalar root-finding, the smallest a at which it becomes tangent to y = x.

118   The root-finder returns ac ≈ 1.00561 with residual of order 10−5 (Figure 3). This is the numerically
119 determined onset of the first homoclinic tangency in the 2D map. The gap between ac ≈ 1.0056 (manifold
120 tangency) and the a ≈ 1.02 at which the statistical LL transition saturates is discussed next.

121   2.4   A semiclassical resolution scale and the value a ≈ 1.02

122   Why does the statistically observed transition saturate near a ≈ 1.02 rather than at the manifold tangency
123 ac ≈ 1.0056? A natural heuristic is that the quantum/semiclassical solver has a finite resolution and
124 cannot resolve fractal structure below a fixed scale. We make this heuristic explicit but do not claim it as a
125 derivation.

126   In the Chirikov picture of overlapping resonances (Chirikov, 1979), the width of the chaotic layer near
127 onset scales as ∆W (a) ∼ κ (a − ac )3/2 . If the solver resolves phase-space structure only down to an
128 effective scale ℏeff (defined below), then structure with ∆W < ℏeff is not resolved, and the effective
129 transition appears shifted to the a at which ∆W (a) ≈ ℏeff . Using the value ℏeff ≈ 0.061 extracted


      Frontiers                                                                                                 5
```

## PDF page 6

[核对 PDF 原页](../pdf/paper-05.pdf#page=6)

```text
      Wang                                                           A Hénon-Map Model for Riemann Zeros




      Figure 3. Numerical tracking of the unstable manifold W u (red) of the hyperbolic fixed point and its
      first tangency with the symmetry line y = x (dashed). Scalar root-finding gives a tangency at ac ≈
      1.00561 with residual O(10−5 ). This is a numerical determination, not an analytic proof. Generated by
      3-henon param a 1.005.ipynb.

130 independently by the quantum solver (Section 3), this matching condition yields a ≈ 1.02 (Figure 4). We
131 present this as a consistency check between two independently obtained numbers, not as a first-principles
132 prediction.

133   2.5   Continuum Hamiltonian and quartic regularization

134   To extract a spectrum with a unitary solver, we pass to a continuous Hamiltonian. Writing the second-
135 difference form of (1), xn+1 − 2xn + xn−1 = 1 − 2xn − a x2n , and reading the left-hand side as a discrete
136 acceleration q̈ in the continuum limit gives a restoring force F (q) = 1 − 2q − a q 2 . Integrating −F yields
137 the cubic potential
                                              V0 (q) = −q + q 2 + a3 q 3 .                                    (2)
138   A cubic potential is unbounded below as q → −∞, so high-energy states leak out and the discretized
139   operator is not well posed. We therefore add a small positive quartic term to confine the spectrum:

                                       Vtotal (q) = −q + q 2 + 1.02 3       4
                                                                3 q + 0.05 q .                                (3)

140      We are careful about what this term does and does not do. The quartic term is a confining regularization:
141   it makes the potential bounded below, restores the discreteness and (approximate) self-adjointness of the
142   operator, and removes the spurious leakage of the cubic model. We do not have an analytic derivation that
143   this specific term generates the Weyl logarithmic mean density of the zeros. In the previous version we
144   stated such a derivation existed; that was incorrect, and we have removed the claim. What we can say is

      Frontiers                                                                                                 6
```

## PDF page 7

[核对 PDF 原页](../pdf/paper-05.pdf#page=7)

```text
      Wang                                                          A Hénon-Map Model for Riemann Zeros




      Figure 4. Heuristic matching between the classical chaotic-layer width ∆W (a) ∼ κ(a − ac )3/2 (solid)
      and the effective solver resolution ℏeff ≈ 0.061 (dashed). The crossing occurs near a ≈ 1.02. This is a
      consistency check between two independently obtained quantities, not a derivation of a. Generated by
      4-henon param a 1.02.ipynb.


145   empirical: with confinement in place, the numerically computed mean counting function of the operator’s
146   spectrum is consistent with a logarithmically growing density over the range we tested (Section 3). An
147   analytic treatment of the mean density via the confining potential, and a systematic parameter scan of the
148   quartic coefficient, are left to future work; we flag the value 0.05 as a chosen regularization parameter
149   rather than a derived constant. We also note that minimal-length / modified-commutator constructions
150   in the Berry–Keating tradition (Bishop et al., 2019) provide a related setting in which such confining
151   modifications arise, and a comparison would be worthwhile.


152   2.6    Three forms of the control parameter a(t)

153   The comparisons in Section 3 use three prescriptions for a during the evolution. We state plainly how
154 each is chosen and what it models; they are modeling choices, not derived laws.


155    • Static (a ≡ 1.02): the parameter is held fixed at the value identified above. This provides a stationary
156         baseline spectrum.
157    • Slow approach from below (a(t) = 1.02 − k1 / ln(t + c)): a monotone schedule chosen so that the
158      survival rate decays like 1/ ln n, matching the leading prime-number-theorem density. The constants
159      k1 , c are fitted to the leading density and are reported with the runs.
160    • Slow annealing from above (a(t) = 1.02 + k2 / ln2 (t + c)): used for spectral extraction; the ln−2
161      schedule was chosen empirically because it reduced mirror/aliasing artifacts in the extracted levels.
162      The constants k2 , c are optimization parameters, not predictions.

      Frontiers                                                                                                7
```

## PDF page 8

[核对 PDF 原页](../pdf/paper-05.pdf#page=8)

```text
      Wang                                                           A Hénon-Map Model for Riemann Zeros


163 We make no claim that these functional forms are unique or derived from first principles; they are smooth
164 schedules selected for the stated practical reasons, and other schedules with the same leading behavior
165 would be expected to give similar results.


      3     RESULTS
166 We compare the spectra of two numerically independent solvers to the Riemann zeros. The two solvers
167 share no code path and rest on different mathematics, so agreement between them is a nontrivial internal
168 check.

169   Quantum (unitary) solver. A Fourier split-operator propagator U = e−iT /ℏeff e−iV /ℏeff for the
                                                                                          b        b

170 Hamiltonian with potential (3); eigenphases are extracted from the unitary evolution. Here ℏeff is a
171 dimensionless effective resolution parameter of the rescaled map (see below), not the physical Planck
172 constant.

173   Dissipative (Markovian) solver. A discretized Fokker–Planck / Markov transition operator on a 2D
174 grid, with a small noise ϵ; the long-time steady state defines the spectrum. This solver uses only real,
175 non-negative transition probabilities and no complex phases.

176   3.1   On the meaning of ℏeff and the fitted parameters

177     The quantity we call ℏeff is the effective semiclassical resolution of the rescaled dynamical map: it sets
178   the phase-space cell size in the split-operator propagator. It is dimensionless in our nondimensionalized
179   variables and has no claim to be the physical ℏ. Operationally it is an optimization parameter, obtained
180   (together with the schedule constant astart ) by minimizing the mean-squared error to the zeros under
181   a single anchoring constraint. The optimizer was scipy.optimize.differential evolution
182   with bounds ℏeff ∈ [0.05, 0.25], astart ∈ [1.10, 1.80], population size 80, tolerance 10−13 . The extracted
183   value at N = 100 is ℏeff ≈ 0.0614. We treat this as a fitted resolution scale and report its role explicitly
184   rather than ascribing fundamental significance to it. A sensitivity discussion is given in Section 4.2.

185   3.2   Experiment I: low-order zeros (N = 6)

186     For the first six zeros, both solvers were run under the static constraint aend ≡ 1.02. The quantum
187   solver, with its resolution optimized, matched the first six ordinates with a total absolute error below
188   3 (mean absolute error < 0.6). Independently, the Markovian solver, scanned over the noise ϵ and a
189   small adiabatic increment ∆a, reached a comparable mean absolute error (best run MAE(6) ≈ 1.07) at
190   ϵ ≈ 0.047, ∆a ≈ 0.005 (Figure 5). The two solvers, despite their different mathematical bases, converge
191   to a similar low-order spectrum.

192   3.3   Experiment II: comparison to 100 zeros and a GUE surrogate

193     We then pushed both solvers to N = 100. Here the two solvers behave very differently in cost. The
194   Markovian solver must resolve increasingly dense levels and requires a 200 × 200 phase-space grid (4 × 104
195   states); even on a 256-core cluster a single evolution takes hours, and its best run reaches MAE(100) ≈ 5.9
196   (MAPE ≈ 6.5%). The unitary solver, by contrast, propagates on a 1D grid of N = 250 points and reaches
197   the same regime cheaply, with a best MAE(100) corresponding to MAPE ≈ 2.3% under a single-point
198   anchoring protocol (no global least-squares fit). We caution immediately — and quantify in Section 4.2 —
199   that this 2.3% is a sharp, finely tuned optimum; a coarse re-optimization that does not resolve the needle

      Frontiers                                                                                                 8
```

## PDF page 9

[核对 PDF 原页](../pdf/paper-05.pdf#page=9)

```text
      Wang                                                               A Hénon-Map Model for Riemann Zeros




      Figure 5. Low-order comparison (N = 6). Left: spectra from the quantum solver (ℏeff ≈ 0.03,
      red) and the Markovian solver (ϵ ≈ 0.047, blue) against the first six Riemann ordinates. Right:
      residuals. Both solvers reach MAE < 0.6–1.1 under the static a = 1.02 constraint. Generated by
      5-henon match 6 zeros.ipynb.

200   gives a more representative ≈ 10–20%, which is the level at which the agreement is robust to the grid and
201   regularization.
202     For contrast we included a GUE surrogate, and — to be maximally fair to the standard model — we
203   granted it a global least-squares scaling, i.e. access to all 100 zeros to fix its scale. Even with this advantage,
204   the GUE surrogate shows a systematic, structured deviation across the range (an “S-shaped” relative-error
205   pattern), consistent with the fact that a single global scaling cannot match a logarithmically varying mean
206   density (Figure 6). We stress the asymmetry of the comparison: the GUE curve is globally fitted while our
207   solvers use single-point anchoring, so this is a comparison of a deterministic-dynamics model against a
208   globally rescaled statistical surrogate, not a falsification of RMT’s local-statistics claims (which concern
209   unfolded correlations, not this counting-function comparison).

210   3.4   Local spectral statistics: comparison with GUE
211   The comparisons above concern the mean (global) density. The reviewers correctly emphasized that the
212 established connection between the Riemann zeros and random matrix theory is a statement about the
213 unfolded local statistics, and that these standard diagnostics — the nearest-neighbor spacing distribution
214 (NNSD), the two-level (pair) correlation, the number variance Σ2 (L), and the Dyson–Mehta spectral
215 rigidity ∆3 (L) — are the appropriate basis for comparison with the literature. We have now computed
216 them.

217     Two points about the spectral object are essential. First, the relevant object is the set of Floquet
218   eigenphases of the one-period propagator U for the time-dependent drive a(t), not the reconstructed
219   energies used for the density comparison. A periodically driven system that breaks time-reversal symmetry
220   is the discrete-time analogue of a GUE Hamiltonian; its quasi-energy (eigenphase) spectrum is where
221   level-repulsion statistics live. Second, we validate the entire diagnostic pipeline on a known answer: applied
222   to the first 100 true Riemann ordinates, it recovers GUE statistics (e.g. NNSD maximal CDF-distance
223   0.068 to GUE versus 0.349 to Poisson), as it must.
224   Applied to the Hénon Floquet eigenphases (Figure 7), the same pipeline yields GUE-type statistics:
225 the NNSD is repulsive (CDF-distance 0.038 to GUE versus 0.279 to Poisson; ⟨s2 ⟩ = 1.18, compared


      Frontiers                                                                                                        9
```

## PDF page 10

[核对 PDF 原页](../pdf/paper-05.pdf#page=10)

```text
      Wang                                                           A Hénon-Map Model for Riemann Zeros




      Figure 6. Comparison to 100 zeros. The 1D quantum solver (blue dashed) and 2D Markovian solver (red
      solid), using single-point anchoring, track the zeros with MAPE ≈ 2.3% and 6.5% respectively. A globally
      least-squares-scaled GUE surrogate (gray dash-dot) shows a systematic S-shaped relative-error pattern,
      as expected when one global scale is applied to a logarithmically varying mean density. The comparison
      is asymmetric (global fit vs. single-point anchoring) and is not a test of RMT’s unfolded local statistics.
      Generated by 6-henon 100 zeros match.ipynb.

226 with 1.27 for GUE and 2.0 for Poisson), the pair correlation shows the GUE correlation hole, and both
227 Σ2 (L) and ∆3 (L) follow the logarithmic GUE curves rather than the linear Poisson behavior. Two points
228 of interpretation are worth stating. First, GUE-type local statistics are, by themselves, generic: they are
229 shared by a wide class of time-reversal-breaking chaotic systems, most of which have nothing to do with
230 the primes. Reproducing them is therefore a necessary consistency check, not the distinctive content of
231 the model; the distinctive (and far more constrained) result is the agreement with the actual zero values,
232 i.e. the mean density of Section 3.2–3.3. Second, we observed that the GUE statistics are clearest in the
233 Floquet eigenphases, whereas the reconstructed-energy spectrum used for the density comparison appears
234 closer to Poisson; we attribute this to the phase-to-energy unwrapping (m = round(·)), which relabels
235 levels and scrambles the fine-scale spacings, rather than to a genuine loss of repulsion in the dynamics
236 — the underlying propagator is the same in both cases. These are finite-statistics estimates from 100–150
237 levels, so the diagnostics (especially R2 (r)) are noisy; we read them as consistent-with-GUE rather than
238 as a precision test. As a convergence check we also extracted larger eigenphase sets by refining the grid
239 (no parameter search, only forward passes): the GUE agreement is stable and in fact sharpens with level
240 count — the NNSD CDF-distance to GUE is 0.045, 0.034, 0.017, 0.029 for 169, 319, 519, 719 levels
241 respectively, with ⟨s2 ⟩ holding near 1.18 throughout (versus 1.27 for GUE and 2.0 for Poisson). The
242 signature is therefore not an artifact of the small sample.


243   3.5   Qualitative comparison with quantum-hardware decoherence data

244     Recent experiments have probed Riemann-zero-related quantities and many-body dynamics on driven
245   and superconducting platforms (Guo et al., 2020; Wei et al., 2025; Wu et al., 2021). We compared the
246   high-order behavior of our solver to a published hardware error profile (Figure 8). At high order the
247   hardware signal degrades, and our finite-resolution solver also degrades — both produce a downturn in
248   roughly the same range of N . We report this only as a qualitative resemblance. Importantly, a similarity
249   between two error profiles does not by itself establish a shared physical mechanism: our downturn is a

      Frontiers                                                                                              10
```

## PDF page 11

[核对 PDF 原页](../pdf/paper-05.pdf#page=11)

```text
      Wang                                                            A Hénon-Map Model for Riemann Zeros




      Figure 7. Standard local spectral diagnostics (unfolded; first 100 levels) for the Hénon Floquet eigenphases
      (red) and the true Riemann zeros (black), against GUE (blue) and Poisson (green). (a) Nearest-neighbor
      spacing distribution: both show level repulsion (suppression at s → 0) consistent with GUE, not Poisson.
      (b) Two-level correlation R2 (r), showing the GUE correlation hole. (c) Number variance Σ2 (L) and (d)
      spectral rigidity ∆3 (L), both following the logarithmic GUE curves rather than the linear Poisson behavior.
      Generated by 8-spectral diagnostics.py.



250 finite-grid/finite-ℏeff aliasing artifact, whereas the hardware downturn reflects physical decoherence. A
251 quantitative claim would require statistical-significance testing, comparison against alternative models, and
252 a careful uncertainty budget, none of which we provide here; we therefore restrict ourselves to noting the
253 qualitative resemblance and flag a fuller analysis as future work.




254   3.6   Summary of claims and their status


255   To address the request for a clear separation between proven results, numerical observations, heuristic
256 arguments, and conjectures, Table 1 classifies the main statements of the paper.


      Frontiers                                                                                                11
```

## PDF page 12

[核对 PDF 原页](../pdf/paper-05.pdf#page=12)

```text
Wang                                                                A Hénon-Map Model for Riemann Zeros




Figure 8. Qualitative comparison between our finite-resolution solver (red) and a published
superconducting-hardware error profile. Both show a high-order downturn in a similar range of N . The
resemblance is qualitative only: the solver’s downturn is a finite-resolution aliasing artifact while the
hardware’s reflects physical decoherence, and we do not claim a common mechanism. Generated by
7-henon ustc 100 zeros match.ipynb.



Table 1. Status of the main statements. “Established” refers to results in the cited literature; the remaining
rows are this paper’s contributions, labeled by epistemic status.
 Statement                                                                  Status
 Local statistics of Riemann zeros match GUE (unfolded pair correlation)    Established (Montgomery, 1973; Odlyzko, 1987)
 Subleading zero correlations ≡ Hardy–Littlewood twin-prime                 Established (Keating and Smith, 2019)
 conjecture
 Logistic band-merging symbolic dynamics ∼    = prime sieve; C2 as fixed    Published (Wang, 2026)
 point
 1D dissipative map cannot host a unitary/time-reversible spectrum          Structural argument
 Lift to 2D area-preserving Hénon restores det J = 1, time reversibility   Construction
 First homoclinic tangency at ac ≈ 1.00561                                  Numerical determination
 LL parity statistic vanishes near a ≈ 1.02 (finite sampling)               Numerical observation
 a ≈ 1.02 from matching ∆W (a) ≈ ℏeff                                       Heuristic / consistency check
 Quartic term confines spectrum and removes cubic leakage                   Numerical observation
 Quartic term derives the Weyl log-density                                  Not claimed (open)
 Two independent solvers agree with first 100 zeros (best MAPE 2.3%,        Numerical observation
 6.5%)
 Robust 10–20% fit across grids/regularizations (ℏeff re-tuned)             Numerical observation
 Sub-3% optimum is sharp (narrower than 0.001 in ℏeff )                     Numerical observation (fine-tuned)
 Floquet eigenphases show GUE local statistics (NNSD, R2 , Σ2 , ∆3 )        Numerical observation (limited statistics)
 Reconstructed-energy spectrum shows the same statistics directly           Artifact-limited (unwrapping; open)
 Solver high-order downturn resembles hardware decoherence profile          Qualitative observation
 Operator spectrum equals the Riemann zeros                                 Not claimed (conjectural)




Frontiers                                                                                                        12
```

## PDF page 13

[核对 PDF 原页](../pdf/paper-05.pdf#page=13)

```text
      Wang                                                               A Hénon-Map Model for Riemann Zeros


257   3.7    Reproducibility and numerical settings
258     For replication we record the principal settings here; full scripts and logs are in the repository (Data
259   Availability). Quantum solver: Fourier split-operator propagator, spatial grid N = 250 on q ∈ [−L, L) with
260   L = 3.5 and periodic (FFT) boundary conditions, Tsteps = 300 propagation steps, aend = 1.02; parameters
261   (ℏeff , astart ) optimized by differential evolution (bounds ℏeff ∈ [0.05, 0.25], astart ∈ [1.10, 1.80], population
262   80, tol 10−13 ); extracted ℏeff ≈ 0.0614, astart ≈ 1.552, native MSE(100) ≈ 12.2. Markovian solver:
263   200 × 200 phase-space grid (4 × 104 states), noise ϵ ≈ 0.047–0.051, adiabatic increment ∆a ≈ 0.01–0.018,
264   best MAE(100) ≈ 5.9. We note two important caveats for the reader. First, the periodic FFT boundary
265   condition introduces wrap-around artifacts at high energy (see Section 4.3), which we handle with the
266   confining quartic term; this is a known limitation of the method. Second, the differential-evolution objective
267   is non-convex and we report the best converged run; a systematic convergence and seed-sensitivity study,
268   as well as grid-refinement tests, are planned for a follow-up.

      4     DISCUSSION
269 We discuss three ablations that probe the robustness of the construction. We frame these as numerical
270 observations about the model, not as proofs about the zeros.

271   4.1    The GUE surrogate and the role of unfolding
272     The structured deviation of the globally scaled GUE surrogate in Figure 6 is expected and is not a critique
273   of the standard RMT result. A single global scale cannot reproduce a logarithmically varying mean density;
274   this is precisely why the literature unfolds the spectrum before comparing correlations (Montgomery, 1973;
275   Odlyzko, 1987). Our point is narrower and constructive: the deterministic solvers reproduce the mean
276   density directly (under single-point anchoring) without a separate unfolding step, which is the property we
277   set out to test. We have rewritten this section to avoid the earlier, inaccurate suggestion that RMT “fails” to
278   describe the zeros.

279   4.2    Robustness, sensitivity, and the sharpness of the optimum
280   We probed how the fit depends on the regularization coefficient, the resolution ℏeff , and the grid,
281 performing forward passes only (no global re-search). The picture has two distinct levels, which we report
282 together for honesty.

283     A robust level. Re-optimizing ℏeff (by a local one-dimensional scan) at each setting, a good fit persists
284   across a wide range of choices: for quartic coefficients from 0.03 to 0.08 the best achievable MAPE stays in
285   the band ≈ 8–21%, and for grids N = 200–320 it stays in ≈ 8–18%, with the optimal ℏeff simply shifting
286   (roughly 0.056–0.084) as the discretization or potential changes (Figure 9). Thus the agreement is not an
287   accident of one specific grid or one specific regularization strength; the model robustly tracks the zeros at
288   the 10–20% level, and the value 0.05 is a convenient choice rather than a unique one.
289     A sharp level. The deep optimum reported above (MAPE ≈ 2.3% at ℏeff = 0.06139, λ = 0.05, N = 250)
290   is a much narrower feature: it is sharper than the 0.001 step of our local scan, so the coarse re-optimization
291   above does not even land on it (it finds ≈ 14% nearby). This sharpness is characteristic of the nonlinear
292   phase-to-energy extraction and means the headline 2.3% should be read as a best-case, finely tuned
293   optimum, not as the typical performance. We also retain the complementary ablation: removing the
294   confining quartic term while holding a = 1.02 forces the optimizer to inflate ℏeff to ≈ 0.277 (∼ 4.5×)
295   with the error stalling at MSE ≈ 17.1, confirming that an over-coarse resolution washes out the structure.

      Frontiers                                                                                                      13
```

## PDF page 14

[核对 PDF 原页](../pdf/paper-05.pdf#page=14)

```text
      Wang                                                             A Hénon-Map Model for Riemann Zeros




      Figure 9. Best achievable MAPE on the first 100 zeros when ℏeff is re-optimized (local 1D scan) at
      each setting. (A) Versus the quartic coefficient λ; (B) versus grid size N . A fit at the ≈ 8–20% level
      persists across all settings (the optimal ℏeff shifts accordingly), so the result is not specific to one grid
      or regularization strength. The coarse scan (step 0.001 in ℏeff ) under-resolves the much narrower global
      optimum (MAPE ≈ 2.3%), which is why the curve sits near 10–15% at the nominal setting. Generated by
      9b-robustness reoptimized.py.

296   In summary, ℏeff is a fitted resolution scale, not a physical constant; a coarse re-tuning gives a robust
297 10–20% agreement across grids and regularizations, while the sub-3% optimum is a sharp, finely tuned
298 feature. We report both rather than only the best number.

299   4.3   Boundary artifacts without the confining term

300     Removing the quartic term and releasing a produces a spurious low-error solution (MSE ≈ 10.6) that,
301   on inspection, is a numerical boundary artifact: with periodic FFT boundary conditions, high-energy
302   wavefunctions that fall down the unbounded cubic potential wrap around the grid and are reflected,
303   mimicking a confining wall. The optimizer exploits this by distorting the topology (driving aend ≈ 0.985).
304   This is a cautionary example showing that a low error alone does not validate a model: it can reflect the
305   discretization rather than the dynamics. The confining quartic term removes this artifact by making the
306   continuum problem well posed. We include this ablation precisely to make the failure mode explicit.

307   4.4   Relation to prior Hilbert–Pólya constructions and what would constitute a proof

308     Our construction is in the spirit of operator-based approaches to the zeros (Berry and Keating, 1999;
309   Bender et al., 2017; Connes, 1999; Sierra and Townsend, 2008; Bishop et al., 2019), but it is numerical
310   and heuristic. To upgrade any of the present observations to a theorem one would need, at minimum: (i) a
311   well-defined self-adjoint (or unitary) operator obtained as a careful continuum limit of the regularized map
312   with controlled boundary conditions; (ii) an analytic treatment of its mean density to compare with the
313   Weyl term; and (iii) control of the local statistics against the GUE predictions. Regarding (iii), we have now
314   computed the standard diagnostics (Section 3.5): the Floquet eigenphases display GUE-type level repulsion
315   in a limited-statistics regime. We stress that this is a consistency check rather than the crux — GUE
316   statistics are generic to chaotic time-reversal-breaking systems — and that the constrained, model-specific
317   result is the agreement with the actual zero values. A full treatment would require larger spectra (more

      Frontiers                                                                                                  14
```

## PDF page 15

[核对 PDF 原页](../pdf/paper-05.pdf#page=15)

```text
      Wang                                                            A Hénon-Map Model for Riemann Zeros


318 levels), a precise statement of which operator’s spectrum is being claimed, and error-controlled diagnostics;
319 we regard this as the central open problem left by this work.


      5   CONCLUSION
320   Motivated by our recently published isomorphism between the Logistic-map band-merging dynamics
321   and the prime sieve (Wang, 2026), and by the Hilbert–Pólya viewpoint, we have studied the spectrum of
322   a two-dimensional area-preserving Hénon map near the edge of chaos as a deterministic model for the
323   Riemann zeros. The move from a 1D dissipative map to a 2D area-preserving map is structurally motivated
324   by the requirement of a unitary, time-reversible spectrum. Two numerically independent solvers — a
325   unitary Fourier propagator and a Markovian dissipative operator — produce spectra that track the first 100
326   zeros with mean absolute percentage errors of about 2.3% and 6.5% under single-point anchoring, and a
327   globally scaled GUE surrogate shows a systematic deviation in the same counting-function comparison.
328     We present these as numerical observations and heuristic arguments. We do not claim to have identified
329   the Hilbert–Pólya operator or to have proved that its spectrum equals the zeros; Table 1 states explicitly
330   what is established, observed, heuristic, or conjectural. We have computed the standard local spectral
331   diagnostics (nearest-neighbor spacing, pair correlation, number variance, spectral rigidity): the Floquet
332   eigenphases show GUE-type level repulsion consistent with the Riemann zeros in a limited-statistics regime,
333   while the reconstructed-energy spectrum that matches the mean density does not — a tension we report
334   openly as the main open problem. The most useful next steps are an analytic treatment of the mean density
335   induced by the confining potential, error-controlled diagnostics on larger spectra for direct comparison with
336   the GUE/Hardy–Littlewood results (Keating and Smith, 2019), and a quantitative, statistically controlled
337   comparison with hardware data. We hope the deterministic-dynamics viewpoint, anchored in a published
338   prime–chaos isomorphism, is a useful complement to the statistical and operator-theoretic approaches to
339   the Riemann zeros.

      CONFLICT OF INTEREST STATEMENT
340   The author declares that the research was conducted in the absence of any commercial or financial
341   relationships that could be construed as a potential conflict of interest.

      AUTHOR CONTRIBUTIONS
342   Liang Wang is the sole author. L.W. conceived the study, developed the framework, implemented and ran
343   all simulations, analyzed the data, and wrote the manuscript.

      FUNDING
344   The author received no specific funding for this work.

      ACKNOWLEDGMENTS
345 The author thanks the reviewers for their detailed and constructive criticism, which substantially improved
346 the framing and the claims of this paper. The author acknowledges the assistance of an AI language model
347 in code implementation for the numerical simulations and in auxiliary analysis of results.


      Frontiers                                                                                                 15
```

## PDF page 16

[核对 PDF 原页](../pdf/paper-05.pdf#page=16)

```text
      Wang                                                           A Hénon-Map Model for Riemann Zeros


      DATA AVAILABILITY STATEMENT
348 All code, scripts, and numerical logs are available at https://github.com/maris205/riemann_
349 henon.


      REFERENCES
350   Bender, C. M., Brody, D. C., and Müller, M. P. (2017). Hamiltonian for the zeros of the riemann zeta
351     function. Physical Review Letters 118, 130201
352   Berry, M. V. and Keating, J. P. (1999). h = xp and the riemann zeros. In Supersymmetry and Trace
353     Formulae: Chaos and Oscillators (Springer). 355–367
354   Bishop, M., Aiken, E., and Singleton, D. (2019). Modified commutation relationships from the Berry–
355     Keating program. Physical Review D 99, 026012. doi:10.1103/PhysRevD.99.026012
356   Bohigas, O., Giannoni, M.-J., and Schmit, C. (1984). Characterization of chaotic quantum spectra and
357     universality of level fluctuation laws. Physical Review Letters 52, 1–4
358   Chirikov, B. V. (1979). A universal instability of many-dimensional oscillator systems. Physics Reports 52,
359     263–379
360   Connes, A. (1999). Trace formula in noncommutative geometry and the zeros of the riemann zeta function.
361     Selecta Mathematica 5, 29–106
362   Dyson, F. J. (1962). Statistical theory of the energy levels of complex systems. i. Journal of Mathematical
363     Physics 3, 140–156
364   Guo, C., Huang, Y.-F., Li, C.-F., and Guo, G.-C. (2020). Identifying the riemann zeros by periodically
365     driving a single qubit. Physical Review A 101, 062310
366   Gutzwiller, M. C. (1990). Chaos in Classical and Quantum Mechanics (Springer)
367   Hadamard, J. (1896). Sur la distribution des zéros de la fonction ζ(s) et ses conséquences arithmétiques.
368     Bulletin de la Société Mathématique de France 24, 199–220
369   Hénon, M. (1969). Numerical study of quadratic area-preserving mappings. Quarterly of Applied
370     Mathematics 27, 291–312
371   Keating, J. P. and Smith, D. J. (2019). Twin prime correlations from the pair correlation of Riemann zeros.
372     Journal of Physics A: Mathematical and Theoretical 52, 365201. doi:10.1088/1751-8121/ab3521
373   Montgomery, H. L. (1973). The pair correlation of zeros of the zeta function. Proceedings of Symposia in
374     Pure Mathematics 24, 181–193
375   Odlyzko, A. M. (1987). On the distribution of spacings between zeros of the zeta function. Mathematics of
376     Computation 48, 273–308
377   Riemann, B. (1859). Ueber die anzahl der primzahlen unter einer gegebenen grösse. Monatsberichte der
378     Berliner Akademie , 671–680
379   Sarnak, P. (2000). Problems of the millennium: The riemann hypothesis. Clay Mathematics Institute ,
380     1–10
381   Schumayer, D. and Hutchinson, D. A. W. (2011). Physics of the riemann hypothesis. Reviews of Modern
382     Physics 83, 307
383   Sierra, G. and Townsend, P. K. (2008). Landau levels and riemann zeros. Physical Review Letters 101,
384     110201
385   Titchmarsh, E. C. and Heath-Brown, D. R. (1986). The Theory of the Riemann Zeta-Function (Oxford
386     University Press), 2nd edn.
387   Wang, L. (2026). The emergence of prime distribution from low-dimensional deterministic chaos. Research
388     in Mathematics 13. doi:10.1080/27684830.2026.2684334

      Frontiers                                                                                               16
```

## PDF page 17

[核对 PDF 原页](../pdf/paper-05.pdf#page=17)

```text
      Wang                                                         A Hénon-Map Model for Riemann Zeros


389   Wei, S. et al. (2025). The riemann hypothesis emerges in dynamical quantum phase transitions. arXiv
390    preprint arXiv:2511.11199
391   Weyl, H. (1911). über die asymptotische verteilung der eigenwerte. Nachrichten von der Gesellschaft der
392    Wissenschaften zu Göttingen , 110–117
393   Wu, Y. et al. (2021). Strong quantum computational advantage using a superconducting quantum processor.
394    Physical Review Letters 127, 180501




      Frontiers                                                                                            17
```
