# Attention looks like soft k-NN

Half-baked, but it keeps nagging me: a single self-attention head is basically
**kernel smoothing / soft nearest-neighbours**. Query q, keys kᵢ, values vᵢ:

    out = Σᵢ softmax(q·kᵢ / √d) · vᵢ

The softmax weights form a similarity kernel over the keys — swap the scaled
dot-product for an RBF and it's essentially Nadaraya–Watson. So "attention" ≈
instance-based learning (SaD L11) with a *learned* similarity metric instead of
a fixed one.

Threads to pull later:
- Is the √d scaling just bandwidth selection in disguise?
- Instance-based methods are lazy / non-parametric — at what point does attention
  stop being non-parametric once Q/K/V become learned projections?
- Does this connect the AML kernel material to transformers cleanly enough to be
  *one* Fortress note, or is it really two (kernels; attention)?

#ml #attention #kernels #instance-based #spark

> Example seed note — safe to delete. It exists to show the Garden format and to
> give the Nebula something to group by the `#tags` above.
