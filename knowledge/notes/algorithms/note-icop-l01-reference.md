---
id: note-icop-l01-reference
type: note
role: reference
title: ICOP Chapter 1 — Linear Programming reference
created: '2026-10-22'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  source_id: source-icop-hu-ws2627
  material: algorithms/structures/icop-hu-ws2627/ico_linearprogramming.pdf
  recorded_source_digest: 76f3c809e569606b1d7422867ec0887f062aab814e6abeda31f2c990e15f45d1
  live_source_digest: 76f3c809e569606b1d7422867ec0887f062aab814e6abeda31f2c990e15f45d1
  inspected_range:
    start: 1
    end: 129
  frozen_input_sha256: 61ca406bc7055ef7c502586cfc8128baff25a60e16509cc183301b09e4d795f2
  frozen_input_bytes: 16260
---

# ICOP 01: Linear Programming - Lecture Reference

Scope: the complete 129-page Linear Programming chapter in Stefan Kratsch's ICOP WS 2026/27 deck. All page citations below refer to **physical PDF pages** of `ico_linearprogramming.pdf`; the printed page numbers coincide. This is an original synthesis with an original numerical example. A worked example is a demonstration, not evidence that the learner has completed it.

## 1. What an LP models

An LP optimizes a linear objective over real variables subject to finitely many linear equalities and non-strict inequalities. With $A\in\mathbb R^{m\times n}$, $x,c\in\mathbb R^n$, and $b\in\mathbb R^m$, the rows of $Ax\le b$ are $a_i^T x\le b_i$, and the comparison is componentwise. Feasibility means satisfying every constraint, independently of objective value. Infeasibility means the feasible set is empty; unboundedness means arbitrarily good objective values, not merely an unbounded feasible region. An ILP adds integrality restrictions; solving its LP relaxation need not give an integer optimum. The deck motivates LP through shortest paths, spanning trees, flows, matching, optimality certificates, and approximation algorithms. [Deck pp. 3-10.]

**Original running model.** Produce divisible quantities $u,v\ge0$ using two limited resources. Their usages are $(1,2)$ for one unit of $u$ and $(1,1)$ for one unit of $v$; capacities are $(4,6)$ and returns are $(3,2)$:

$$\max\ 3u+2v\qquad\text{s.t. }u+v\le4,\quad2u+v\le6,\quad u,v\ge0.$$

The units must be divisible for this to describe an LP directly; whole-item production requires an ILP. This example will connect a model, geometry, a simplex computation, and a dual certificate.

A second useful model is a unit $s$-$t$ flow: minimize $\sum_e w_e f_e$ with $f_e\ge0$, net outflow $1$ at $s$, net inflow $1$ at $t$, and flow conservation elsewhere. With positive edge weights, removing cycles cannot increase cost; any feasible flow decomposes into $s$-$t$ paths plus cycles, so the optimum is a shortest-path length. If no $s$-$t$ path exists, this model is infeasible. This is a derivation of the modeling exercise posed in the deck, not a quoted solution. [Deck pp. 23, 115.]

## 2. Forms and transformations: use the course's convention

The names are **source-specific**. The course follows Blum on physical p. 21:

| Course name | Objective | Constraints |
|---|---|---|
| Canonical form | $\min c^T x$ | $Ax\le b,\ x\ge0$ |
| Standard form | $\min c^T x$ | $Ax=b,\ x\ge0$ |

On p. 10 the deck separately presents Korte-Vygen's formulation $\max c^T x$ subject to $Ax\le b$ with unrestricted $x$. Do not transfer a book's form name without checking its definition. [Deck pp. 10, 21-22.]

The transformations preserve the relevant feasible assignments through an explicit recovery map:

- Maximize $c^T x$ by minimizing $-c^T x$; negate the reported optimum value when returning to the original objective.
- Replace a free variable $x_j$ by $x_j^+-x_j^-$, with both parts nonnegative, **in every row and the objective**. The representation need not be unique.
- Replace a nonpositive variable by the negative of a nonnegative one. Alternatively retain a sign restriction as an ordinary linear inequality.
- Reverse an inequality by multiplying the entire row, including its right side, by $-1$.
- Replace $a^T x=b$ by the pair $a^T x\le b$ and $-a^T x\le-b$.
- Replace $a^T x\le b$ by $a^T x+s=b$, $s\ge0$. For $a^T x\ge b$, use $a^T x-s=b$, $s\ge0$. New slack/surplus variables have objective coefficient zero.

The final two operations move inequalities between ordinary rows and variable restrictions; they do not eliminate every inequality. With only equalities and free variables, feasibility is a linear-system question and a nonconstant feasible objective direction gives unboundedness. Ordinary LP constraints do not directly express strict inequalities. [Deck pp. 12-20.]

For the running LP the course canonical form minimizes $-3u-2v$ with its original inequalities. Its standard form is

$$\min -3u-2v,\quad u+v+s_1=4,\quad2u+v+s_2=6,\quad(u,v,s_1,s_2)\ge0.$$

Thus $A=\begin{pmatrix}1&1&1&0\\2&1&0&1\end{pmatrix}$, $b=(4,6)^T$, and $c=(-3,-2,0,0)^T$. The maximum return is the negative of the minimum transformed cost. [Method: deck pp. 14, 19, 61.]

## 3. Geometry and why local optimality is global

A nonzero row $a^T x\le b$ describes a closed halfspace, bounded by the affine hyperplane $a^T x=b$. A polyhedron is an intersection of finitely many halfspaces; a bounded polyhedron is a polytope. Convexity means containing $\lambda x+(1-\lambda)y$ whenever it contains $x,y$ and $0\le\lambda\le1$. Halfspaces are convex by linearity, and intersections preserve convexity. [Deck pp. 25-32.]

If a feasible point $x$ for minimization has a better feasible point $y$, then every $z=(1-t)x+ty$ with $0<t\le1$ is feasible and has smaller cost. Taking $t$ arbitrarily small contradicts local optimality. This proves every local optimum is global; it does **not** say an optimum is unique. [Deck pp. 33-34.]

A supporting hyperplane touches the polyhedron while leaving it wholly on one side. The intersection is a face; zero-dimensional faces are vertices, one-dimensional faces are edges. For a full-dimensional polyhedron in $\mathbb R^n$, facets have dimension $n-1$. Points of the boundary lie on supporting hyperplanes; the ambient interior contains a small Euclidean ball. If $c\ne0$, an interior point cannot minimize $c^T x$: a short move in direction $-c$ is feasible and decreases cost by $\delta\|c\|^2$. If $c=0$, every feasible point is optimal. [Deck pp. 35-37.]

Objective level sets $c^T x=w$ are parallel hyperplanes. At a finite optimum they touch an optimal face. The picture of sliding them is explanatory: deciding where intersection is nonempty and detecting unboundedness still need an algorithm. In the running example the vertices are $(0,0),(3,0),(2,2),(0,4)$, with returns $0,9,10,8$. The unique optimal vertex is $(2,2)$; with return $u+v$ instead, the entire segment from $(0,4)$ to $(2,2)$ is optimal. [Method: deck pp. 38-40.]

## 4. Vertices as basic feasible solutions

Now use course standard form $P=\{x:Ax=b,\ x\ge0\}$. A point is extreme when no nonzero $d$ has both $x+d$ and $x-d$ feasible. Let $S(x)=\{j:x_j\ne0\}$ denote its support. The deck calls $x$ basic if $Ax=b$ and the **columns** indexed by $S(x)$ are linearly independent, and basic feasible if also $x\ge0$. There are at most $m$ nonzero coordinates. For this polyhedron, vertex, extreme point, and basic feasible solution (BFS) are equivalent. [Deck pp. 42-50; the definition on p. 44 fixes columns.]

The key proof mechanism is worth reconstructing. If the support columns are dependent, take a nonzero vector $d$ supported there with $Ad=0$. Because all supported coordinates of a feasible $x$ are positive, sufficiently small moves $x\pm\varepsilon d$ remain nonnegative, so $x$ is not extreme. Conversely, independence makes the point unique after its zero coordinates are fixed; minimizing the sum of those coordinates exposes it as a vertex. In the special case with no zero coordinates, independence makes the entire feasible set a singleton, which is itself a vertex. [Deck pp. 47-49; last case makes the exposing argument explicit.]

For a feasible LP in standard form with finite optimum, some optimal point is a vertex. Starting at an optimal non-vertex, a feasible two-sided direction must have zero objective slope; otherwise one sign improves the cost. Move in a zero-cost direction until an additional coordinate becomes zero. Repeating reduces support and reaches a BFS. This theorem is scoped to the nonnegative standard-form polyhedron: a line with free variables can have finite constant objective and no vertices. [Deck pp. 51-55.]

Gaussian elimination on $(A\mid b)$ detects contradictory rows and removes redundant equalities. After obtaining full row rank, extend the independent support columns to a basis $B$ of $m$ columns. Solve $x_B=A_B^{-1}b$, set $x_N=0$, and retain only nonnegative points. Trying all $\binom nm$ candidate bases is finite but can be exponential; the bounded-case enumerator does not detect unboundedness. A BFS with fewer than $m$ positive entries is degenerate and can have multiple basis representations. [Deck pp. 57-62, 67.]

## 5. Simplex phase II: derive the pivot

Assume full row rank and, as the deck does for its strict-improvement presentation, no degenerate BFS. For current basis $B$ and complementary index set $N$,

$$x_B=A_B^{-1}(b-A_Nx_N),$$
$$c^Tx=c_B^TA_B^{-1}b+\underbrace{(c_N^T-c_B^TA_B^{-1}A_N)}_{\bar c_N^T}x_N.$$

The entries of $\bar c_N$ are reduced costs for **minimization**. If all are nonnegative, every feasible $x_N\ge0$ has objective at least the current constant, proving optimality. Otherwise choose $j\in N$ with $\bar c_j<0$. Put $d=A_B^{-1}a_j$ and increase $x_j=\theta$; then $x_B(\theta)=x_B(0)-d\theta$. [Deck pp. 69-76.]

If $d\le0$, every $\theta\ge0$ is feasible and the cost decreases without bound. Otherwise take

$$\theta=\min_{i\in B:\ d_i>0}\frac{(x_B)_i}{d_i}.$$

A minimizing index leaves the basis and $j$ enters. Only positive $d_i$ restrict the step: negative components increase their basic variables. Under nondegeneracy the step is positive and a single basic variable reaches zero. Basis exchange corresponds geometrically to an adjacent vertex. Strict improvement plus finitely many bases gives termination under these assumptions; degeneracy requires additional care and the informal no-revisit argument does not apply unchanged. [Deck pp. 64-81.]

**Running example, fully worked.** Start with basis $(s_1,s_2)$ at $(u,v,s_1,s_2)=(0,0,4,6)$; reduced costs of $(u,v)$ are $(-3,-2)$. Enter $u$: $d=(1,2)$ and $\theta=\min(4,6/2)=3$. The new point is $(3,0,1,0)$, with basis $(u,s_1)$ and cost $-9$.

Here $A_B^{-1}=\begin{pmatrix}0&1/2\\1&-1/2\end{pmatrix}$. For entering $v$, $d=(1/2,1/2)$ and $\bar c_v=-1/2$. Thus $\theta=\min(3/(1/2),1/(1/2))=2$; $s_1$ leaves, giving $(2,2,0,0)$ and cost $-10$. With basis $(u,v)$, $A_B^{-1}=\begin{pmatrix}-1&1\\2&-1\end{pmatrix}$ and the reduced costs for $(s_1,s_2)$ are $(1,1)$. This proves optimality and returns maximum profit $10$. [Method: deck pp. 71-80.]

## 6. Simplex phase I and running-time claims

A slack basis is immediately feasible for $Ax+s=b$ only when $b\ge0$. For a general standard-form system, first flip equality rows with negative right side. Add artificial variables $h\ge0$ and solve

$$\min\mathbf1^Th\quad\text{s.t. }Ax+h=b,\quad x,h\ge0.$$

The artificial columns form an identity basis with initial solution $x=0,h=b$. Its objective is always nonnegative. Optimum zero is equivalent to feasibility of the original system: nonnegativity forces every artificial variable to zero. A positive optimum proves infeasibility. The auxiliary minimization cannot be unbounded below. A returned zero-artificial BFS has independent positive original-variable columns, hence gives an original BFS; zero basic artificial variables may still require basis cleanup before a concrete phase-II implementation. [Deck pp. 82-88.]

Separate time per pivot from number of pivots. The deck explains polynomial bit-size control for rational input using basis solutions and Cramer's rule. It then gives an exponential pivot example, $2^n-1$, and distinguishes practical simplex performance from its worst-case guarantee. These are the chapter's claims; the mention of the Hirsch conjecture on p. 91 is a reading lead. The course's open-problem statement concerns a worst-case polynomial pivot rule, not whether LP has polynomial algorithms: the outlook lists ellipsoid and interior-point methods. [Deck pp. 89-91, 126.]

## 7. Duality as a bound and certificate

For the standard-form minimization primal

$$\min\{c^Tx:Ax=b,\ x\ge0\},$$

the dual is

$$\max\{b^Ty:A^Ty\le c,\ y\text{ unrestricted}\}.$$

For feasible $x,y$, $b^Ty=y^TAx\le c^Tx$; $x\ge0$ is essential in the inequality. This is weak duality. Equal feasible objective values certify optimality without repeating the optimizer's algorithm. Strong duality states that if both are feasible, finite optimum values agree and are attained. In the deck's nondegenerate simplex setting an optimal basis has $\bar c_N\ge0$; choosing $y^T=c_B^TA_B^{-1}$ proves dual feasibility and equality. For degenerate problems, one cannot infer dual feasibility from an arbitrary optimal basis without checking its reduced costs. [Deck pp. 93-102, with the assumption from p. 67.]

For the deck's more general **minimization** primal, derive signs by asking which row multipliers preserve a lower bound:

| Primal feature | Corresponding dual feature |
|---|---|
| Equality row $A_i x=b_i$ | $y_i$ unrestricted |
| Row $A_i x\ge b_i$ | $y_i\ge0$ |
| Nonnegative variable $x_j\ge0$ | $y^Ta_j\le c_j$ |
| Free variable $x_j$ | $y^Ta_j=c_j$ |

A $\le$ row can be negated first, yielding a nonpositive multiplier in the original row coordinates. A nonpositive variable likewise reverses its dual inequality. The dual has one variable per primal row and one constraint per primal variable; dualizing twice recovers the primal after normalization. [Deck pp. 103-112.]

For the original running **maximization** model, the upper-bound dual is

$$\min\ 4p+6q\quad\text{s.t. }p+2q\ge3,\quad p+q\ge2,\quad p,q\ge0.$$

For every feasible pair, $3u+2v\le p(u+v)+q(2u+v)\le4p+6q$. Choosing $(u,v)=(2,2)$ and $(p,q)=(1,1)$ gives $10=10$, an optimality certificate. In the transformed standard-form minimization, the corresponding unrestricted dual solution is $y=(-1,-1)$ and both objectives are $-10$.

Possible status pairs are: both feasible with finite optima; one unbounded and the other infeasible; or both infeasible. Infeasibility of one side alone does not tell which of the last two occurs. Weak duality rules out a feasible side opposite an unbounded side; strong duality pairs finite feasible optima. [Deck pp. 113-115.]

## 8. Complementary slackness, further problems, and boundaries

For the general minimization pair above and **feasible** $x,y$, complementary slackness is

$$y_i(A_i x-b_i)=0\quad\text{for every primal row},$$
$$(c_j-y^Ta_j)x_j=0\quad\text{for every primal variable}.$$

Equality rows and free variables make their respective products zero automatically. For other rows/variables, the factors are nonnegative. The duality gap decomposes as

$$c^Tx-b^Ty=\sum_i y_i(A_i x-b_i)+\sum_j(c_j-y^Ta_j)x_j.$$

Every summand is nonnegative; their sum is zero exactly when every product is zero. Strong duality proves necessity for optimal pairs; weak duality proves sufficiency. Neither feasibility nor signs may be skipped. A strictly slack primal inequality forces its dual multiplier to zero; a positive multiplier forces tightness. Tightness alone does **not** force a positive multiplier. A positive nonnegative primal variable forces its dual inequality tight, with the analogous one-way warning. [Deck pp. 117-123.]

For the original maximization example these products are $p(4-u-v)$, $q(6-2u-v)$, $u(p+2q-3)$, and $v(p+q-2)$. They all vanish at $(u,v,p,q)=(2,2,1,1)$.

The final exercises extend the same ideas: a largest Euclidean ball in $\{x:Ax\le b\}$ is modeled by center $z$, radius $r\ge0$, and rows $a_i^Tz+\|a_i\|_2r\le b_i$; the row norms are input constants, so the model is linear. A vertex of $\{x:Ax\le b,\ 0\le x\le u\}$ with integer $u$ has at most $m$ coordinates strictly between their bounds, by the support-perturbation argument; consequently an optimal vertex has at most $m$ noninteger coordinates. An infeasibility certificate for $Ax\le b$ is $y\ge0$ with $y^TA=0$ and $y^Tb<0$, since it would imply $0\le y^Tb<0$ for any purported feasible $x$. These connect to the deck's final problems; proving certificate existence in the infeasible case needs the alternative theorem, not this one-line contradiction alone. [Deck p. 128.]

Ellipsoid methods, interior-point methods, integrality, separation oracles, semidefinite programming, and convex programming are outlook topics here; the deck lists them without developing their algorithms. Simplex tableaux are a suggested implementation-oriented follow-up rather than the representation used in this chapter. [Deck pp. 124-129.]
