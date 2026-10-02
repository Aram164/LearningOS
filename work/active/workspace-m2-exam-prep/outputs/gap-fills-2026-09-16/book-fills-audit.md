# Book fills — firsthand read record, 2026-09-16

Nine routes onto material the operator already owns. Every page below was read in
extracted full text from the local PDF before the route was written; page numbers
are PDF pages. Quotations are verbatim from the extraction.

## L02 `knowledge-sad-l02-sampling` — Géron pp. 52–53
Read in full. p.52 states the principle: "even very large samples can be
nonrepresentative if the sampling method is flawed. This is called sampling bias",
followed by the 1936 Literary Digest case. p.53 names the two mechanisms — the
sampling frame skewing wealthy, and "less than 25% of the people who received the
poll answered", i.e. non-response. Both pages are prose, no exercises.

## L04 `knowledge-sad-l04-framing` — Tijms p. 16 (and p. 27)
p.16: "Probability and intuition do not always agree. In no other branch of
mathematics is it so easy to make mistakes as in probability theory." p.27
returns to "The psychology of probability intuition is a main feature of some of
these problems." This supplies the node's motivation half only; the gain/loss
experiment itself comes from the paired video route. Recorded as orientation
depth for that reason.

## L10 `knowledge-sad-l10-multiple` — ISLP ch. 13, pp. 564–594
Chapter located and read at its section boundaries: p.564 opens "13. Multiple
Testing" and announces that "challenges are presented in Section 13.3, and more
contemporary solutions in Sections 13.4 and 13.5"; p.565 begins §13.1 "A Quick
Review of Hypothesis Testing"; the worked statistic T = 2.33 appears on p.567.
The chapter runs continuously to p.594.

## L10 `knowledge-sad-l10-multiple` — Fahrmeir p. 446
German, matching the lecture. The page carries the error-inflation table (values
0.401 at k = 10 rising to 0.994 at k = 100) and then states the correction:
"lässt sich etwa die Bonferroni-Korrektur anwenden, bei der jeder Test zum Niveau
α/k statt zum Niveau α durchgeführt wird." Indexed as "Bonferroni-Korrektur, 435"
in the printed index; PDF page is 446.

## L11 `knowledge-sad-l11-pipeline` — Kelleher §1.5, pp. 48–52
p.48 opens "1.5 The Predictive Data Analytics Project Lifecycle: CRISP-DM"; p.49
carries "Figure 1.4 A diagram of the CRISP-DM process that shows the six key
phases and indicates the important relationships between them"; p.50 continues
into Deployment. The feedback relationships — the part the L11 deck flattens into
a list — are explicit in the figure caption.

## L12 `knowledge-sad-l12-stacking` — ESL §8.8, pp. 307–309
p.307 opens "8.8 Model Averaging and Stacking"; p.308 carries the posterior-mean
weighted-average expression (8.54). The chapter introduction on p.280 lists
"committee methods, bagging, stacking and bumping" as the section's subject.

## L13 `knowledge-sad-l13-lsh` — Mining of Massive Datasets ch. 3
Fetched from infolab.stanford.edu (HTTP 200, 59 pages) and read. §3.4.1 opens
"LSH for Minhash Signatures One general approach to LSH is to 'hash' items several
times, in such a way that similar items…". Term counts over the chapter:
minhash 67, Jaccard similarity 58, candidate pair 34, locality-sensitive hashing
15, banding 7.

**Negative result, recorded deliberately:** no book in the local library teaches
LSH. Kelleher's index lists "locality sensitive hashing, 238" but pp. 237–239
contain no hashing content at all, and its only real mention is a further-reading
pointer on p. 272 citing the Andoni–Indyk survey. Murphy mentions LSH twice
(pp. 565, 580) in passing, the second time citing [LRU14] — this same book.
CSC411 p.21 states plainly: "The cost of searching can be mitigated with spatial
data-structures … such as k-d-trees and locality-sensitive hashing. We will not
cover these methods here."

## L13 `knowledge-sad-l13-exact-indexing` — Kelleher pp. 234–240
p.234 defines the index and builds it: "The k-d tree, which is short for
k-dimensional tree, is one of the best known of these indices… To construct a k-d
tree, we first pick a feature and split the data into two partitions using the
median value of this feature." The recursion and feature cycling follow on the
same page; retrieval continues to p.240.

## L14 `knowledge-sad-l14-bayes-net` + `knowledge-sad-l14-markov` — Kelleher §6.4.4, pp. 324–335
One continuous treatment, so one route carrying both nodes. p.328 defines the
independence structure: "The set of nodes in a graph that make a node independent
of the rest of the graph are known as the Markov blanket of a node", with
"Figure 6.10 A depiction of the Markov blanket of a node. The gray nodes define
the Markov blanket of the black node." Bayes' Theorem is applied on the same page
to compute a conditional from the network.
