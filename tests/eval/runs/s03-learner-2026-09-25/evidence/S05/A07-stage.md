
## 2026-09-22 — reading: stride paper excerpt (filed by the operator)

From Waldspurger & Weihl, "Stride Scheduling" (1995), §2:

"Each client has a ticket allocation, a stride inversely proportional to its
tickets, and a pass value. The client with the minimum pass is selected, and
its pass is advanced by its stride. … Stride scheduling achieves
proportional-share allocation deterministically: the relative error in any
client's allocation is bounded by a constant, independent of the allocation
period, whereas lottery scheduling's expected error grows with the square root
of the number of allocations."
