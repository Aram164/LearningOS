---
id: note-icop-l01-mock-exam
type: note
role: mock-exam
title: ICOP Chapter 1 — 30-minute LP oral self-test
created: '2026-10-23'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
concepts:
- concept-convexity
sources:
- source-icop-hu-ws2627
---

# ICOP 01: Linear Programming - 30-Minute Mock Oral

Use this as a closed-notes oral rehearsal. Speak definitions with their assumptions, show the essential calculation, and defend why a certificate is valid. These are original questions at the chapter's proof-and-computation level. They are not a prediction of the actual examination; no actual exam paper was supplied. Source tags refer to **physical PDF pages** of Kratsch's `ico_linearprogramming.pdf`, WS 2026/27.

The timed examination ends at 30 minutes. Follow-up questions are an optional second round. Solutions begin only after the divider. Record answers, errors, and elapsed time as evidence; the document does not record completion or declare mastery.

## Timed questions

### Q1. Minutes 0-4: What problem are we solving? (6 points)

A divisible production plan is

$$\max 5a+3b\quad\text{s.t. }a+b\le5,\quad2a+b\le8,\quad a,b\ge0.$$

Give its **course canonical** and **course standard** forms, including all new-variable signs and objective coefficients. Explain how to recover the original optimum value. State what infeasible and unbounded mean, and explain whether an unbounded feasible region must imply an unbounded objective. Why can different books disagree on the name “standard form”? [Deck pp. 9-10, 14-21.]

### Q2. Minutes 4-12: One pivot, fully justified (10 points)

Use the standard-form variable order $(a,b,s_1,s_2)$ and current basis $B=(a,s_1)$, with current point $(4,0,1,0)$.

1. Compute $A_B^{-1}$, the reduced costs of $(b,s_2)$, and decide whether to stop.
2. Carry out an improving pivot, showing direction, admissible step, and leaving variable.
3. Give all reduced costs for the final nonbasic variables and prove optimality using the objective identity for an arbitrary feasible point.
4. In the same notation, explain the branch that would instead prove unboundedness. [Deck pp. 69-80.]

### Q3. Minutes 12-19: Derive a certificate and complementary slackness (8 points)

Derive the dual of Q1's **original maximization** LP as a problem of finding an upper bound. Find a feasible dual point with objective equal to the result of Q2, and prove the resulting optimality claim without appealing to simplex. State the complementary slackness products and show they vanish. Explain why a tight primal row need not have a positive dual multiplier. Finally, state the standard-form minimization primal/dual pair with the correct dual-variable restrictions. [Deck pp. 94-111, 117-123.]

### Q4. Minutes 19-25: Defend the finite search space (8 points)

For $P=\{x:Ax=b,x\ge0\}$, state the equivalence linking vertices, extreme points, and basic feasible solutions. Prove that dependent columns on the positive support of a feasible point contradict extremality. Then explain why an optimal non-vertex can be replaced by an optimal feasible point with smaller support, and why the process terminates. Name the assumption that would fail if you made the same vertex claim for a whole line of free-variable solutions. [Deck pp. 44-55.]

### Q5. Minutes 25-30: Feasibility, complexity, and logical limits (8 points)

For $x_1+x_2=-2$ with $x_1,x_2\ge0$, formulate a phase-I minimization and determine its optimum without running simplex. Explain why the auxiliary LP cannot be unbounded below. State why polynomial work per pivot does not prove polynomial total time, and distinguish a practical-performance statement from a worst-case bound. If a primal is infeasible, must its dual be unbounded? Give a counterexample with its dual. [Deck pp. 82-91, 113-114.]

## Optional examiner follow-ups

Attempt any three after the timed test. Each asks for a proof or construction beyond repeating a definition.

1. **Convexity:** prove local implies global optimality, and identify precisely where convexity and linearity enter. What changes if the objective is identically zero? [Deck pp. 29-34, 36-37.]
2. **Signs:** derive the dual of $\min 4x+r$ subject to $x-r=2$, $2x+r\ge1$, $x$ free, $r\ge0$. Explain both the equality and the sign restriction you obtain. [Deck pp. 103-111.]
3. **Dual of the dual:** for $\max\{c^Tx:Ax\le b,x\ge0\}$ and its min-$\ge$ dual, normalize the latter into the course's minimization rule and dualize it to recover the original. [Deck p. 112.]
4. **Degeneracy:** give an optimal degenerate BFS with a chosen basis having a negative reduced cost; explain why “negative reduced cost implies a positive improving step” fails. [Deck's nondegeneracy assumption p. 67; apply pp. 74-78 critically.]
5. **Ball model:** model the largest Euclidean ball inside $Az\le b$, derive the row coefficient of its radius, and explain why this is an LP. State possible infeasible or unbounded cases. [Deck p. 128.]
6. **Certificates:** prove that $y\ge0,y^TA=0,y^Tb<0$ rules out $Ax\le b$. Which direction of an alternative theorem have you proved, and which is still missing? [Deck p. 128.]
7. **Rational arithmetic:** explain how determinants bound the bit lengths of basis solutions for rational input and why a polynomial arithmetic-operation count alone would not be sufficient. [Deck pp. 88-89.]

---

## Solutions and marking guide

Award points only for stated assumptions and justified steps. The weights help locate gaps; a total score is not a claim of mastery or a prediction of examination performance.

### Q1 solution (6)

The course canonical form minimizes $-5a-3b$ under $a+b\le5$, $2a+b\le8$, $a,b\ge0$. Its standard form has equalities $a+b+s_1=5$, $2a+b+s_2=8$, all four variables nonnegative, with cost vector $(-5,-3,0,0)$. Negate the transformed optimum to recover original maximum return. These are Blum's names on p. 21; the deck explicitly notes alternative book conventions on p. 10. (3 points)

Infeasibility means no feasible assignment. For maximization, unboundedness means that for every real threshold there is a feasible assignment with larger objective. An unbounded feasible set need not have unbounded objective: $\min x$ subject to $x\ge0$ has optimum zero on a ray. (3 points)

### Q2 solution (10)

$$A=\begin{pmatrix}1&1&1&0\\2&1&0&1\end{pmatrix},\quad A_B=\begin{pmatrix}1&1\\2&0\end{pmatrix},\quad A_B^{-1}=\begin{pmatrix}0&1/2\\1&-1/2\end{pmatrix}.$$

At $B=(a,s_1)$, $c_B=(-5,0)^T$, so $c_B^TA_B^{-1}=(0,-5/2)$. The reduced costs for $(b,s_2)$ are $(-1/2,5/2)$; the negative first component allows $b$ to enter. (3 points)

The direction is $A_B^{-1}a_b=(1/2,1/2)^T$. With current basic values $(4,1)$, the ratios are $8$ and $2$. Thus $\theta=2$, $s_1$ leaves, and the next point is $(3,2,0,0)$, with cost $-21$. (3 points)

Now $B=(a,b)$ and $A_B^{-1}=\begin{pmatrix}-1&1\\2&-1\end{pmatrix}$, so $c_B^TA_B^{-1}=(-1,-2)$. Final reduced costs for $(s_1,s_2)$ are $(1,2)$. Every feasible point satisfies

$$c^Tx=-21+s_1+2s_2\ge-21.$$

This proves optimality and original maximum $21$. (3 points)

If an entering variable has negative reduced cost and direction $d=A_B^{-1}a_j\le0$, then $x_B-\theta d\ge0$ for every $\theta\ge0$ while cost decreases without bound. (1 point)

### Q3 solution (8)

Use nonnegative weights $p,q$ on the resource upper bounds. To upper-bound the return coefficientwise, require $p+2q\ge5$ and $p+q\ge3$. The dual is

$$\min 5p+8q\quad\text{s.t. }p+2q\ge5,\quad p+q\ge3,\quad p,q\ge0.$$

The point $(p,q)=(1,2)$ is feasible with value $21$. For every primal feasible $(a,b)$ and dual feasible $(p,q)$,

$$5a+3b\le(p+2q)a+(p+q)b=p(a+b)+q(2a+b)\le5p+8q.$$

At primal $(3,2)$ and dual $(1,2)$, equality gives optimality on both sides. (4 points)

The products are $p(5-a-b)$, $q(8-2a-b)$, $a(p+2q-5)$, $b(p+q-3)$; all vanish. Tightness permits a zero multiplier; it does not force positivity. For an explicit example on the same region, objective $a+b$ admits primal $(3,2)$ and dual $(p,q)=(1,0)$, both value $5$; the second primal resource row is tight although $q=0$. (2 points)

For $\min c^Tx$ subject to $Ax=b,x\ge0$, the dual is $\max b^Ty$ subject to $A^Ty\le c$, with $y$ unrestricted. (2 points)

### Q4 solution (8)

For this nonnegative equality-form polyhedron, vertex, extreme point, and BFS are equivalent. “Basic” means that $Ax=b$ and the support columns are independent; feasibility additionally requires $x\ge0$. (2 points)

If support columns are dependent, choose nonzero $d$ supported on the positive positions with $Ad=0$. A sufficiently small $\varepsilon>0$ keeps $x\pm\varepsilon d\ge0$, since all coordinates that may change begin strictly positive. Equalities hold because $Ad=0$. Two distinct feasible points around $x$ contradict extremality. (3 points)

At an optimum the two-sided feasible direction has $c^Td=0$, since either nonzero sign would improve the objective. Select a sign with a negative component and take $\theta=\min_{d_j<0}-x_j/d_j$. The new point $x+\theta d$ is feasible with unchanged cost and at least one additional zero; existing zeros stay zero. Support cannot shrink indefinitely, so a BFS is reached. The whole line with free $x$ and objective zero has no vertex: the nonnegativity structure of the theorem is absent. (3 points)

### Q5 solution (8)

Normalize to $-x_1-x_2=2$ and add $h\ge0$. Phase I minimizes $h$ subject to $-x_1-x_2+h=2$, all variables nonnegative. Thus $h=2+x_1+x_2\ge2$, with optimum $2$ at $(x_1,x_2,h)=(0,0,2)$. Its positive optimum proves infeasibility of the original system. More generally the auxiliary objective is a sum of nonnegative artificials and cannot decrease without bound. (3 points)

A polynomial per-pivot bound multiplied by an exponential pivot count can be exponential. Finiteness alone gives no polynomial bound; the deck presents exponentially long simplex choices despite strong practical performance. Keep arithmetic bit-size costs in the per-pivot claim. (2 points)

Infeasible does not imply dual unbounded. The standard-form primal $\min -x$ subject to $0x=1$, $x\ge0$ is infeasible. Its dual $\max y$ subject to $0y\le-1$, with free $y$, is also infeasible. (3 points)

## Follow-up solution sketches

1. If feasible $y$ has lower cost than $x$, convex combinations $x+t(y-x)$ remain feasible and have strictly lower cost for every $t>0$. They approach $x$, contradicting local optimality. Convexity supplies feasibility and linearity supplies the strict cost comparison. For zero objective every feasible point is optimal, including interior points.
2. With $\alpha$ for the equality and $\beta\ge0$ for the $\ge$ row, the dual is $\max 2\alpha+\beta$ subject to $\alpha+2\beta=4$, $-\alpha+\beta\le1$, $\alpha$ free. The free $x$ requires equality; the primal $\ge$ row requires a nonnegative multiplier in a minimization lower bound.
3. The dual is $\min\{b^Ty:A^Ty\ge c,y\ge0\}$. Applying the minimization rules gives $\max c^Tx$ with $Ax\le b,x\ge0$, the original primal. A transpose swaps rows and columns; the inequality/sign correspondences reverse the roles exactly.
4. Use $\min -x_2$ subject to $x_1+x_2=0$, $x_1,x_2\ge0$. The only feasible point is $(0,0)$, so it is optimal. Choose basis $B=\{1\}$. The reduced cost of $x_2$ is $-1$, but its direction is $1$ and ratio test permits only step $0$. The basis is degenerate; increasing $x_2$ would force $x_1<0$. Thus a negative reduced cost need not imply a feasible positive improvement at an optimal degenerate BFS.
5. Maximize $r\ge0$ over free center $z$ with $a_i^Tz+\|a_i\|_2r\le b_i$ for every row. Cauchy-Schwarz gives the largest left side over a radius-$r$ ball; equality is attained in the row-normal direction. All row norms are input constants. Empty polyhedra give infeasibility; sets containing balls of arbitrarily large radius give unbounded objective. An unbounded polyhedron such as a strip can still have a finite largest radius.
6. A feasible $x$ would satisfy $0=y^TAx\le y^Tb<0$, impossible. This proves that a certificate implies infeasibility; the converse existence of a certificate for every infeasible system is the remaining direction.
7. Clear rational denominators using polynomial bit length. Each coordinate of a basis solution is a ratio of determinants by Cramer's rule. Bounds on determinants give a polynomial bound on numerator and denominator bit lengths in the input size. Arithmetic with such rational numbers can therefore be charged by bit cost; a count that treats arbitrarily large integers as constant-size would not suffice.
