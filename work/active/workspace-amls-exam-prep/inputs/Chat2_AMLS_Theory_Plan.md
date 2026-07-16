# Chat 2: AMLS Theory — Block-by-Block Study Plan

*Generated: 21 April 2026 (KW 17) | Built from all 13 lecture slide PDFs + exam questions*
*Updated: 2026-06-13 (KW 24) — **EXAM RESTRUCTURE**: AMLS exam moved from Jul 23 to **2. Prüfungszeitraum (Sept/Okt)**. S.X exam prep block no longer KW 29–30; rescheduled to Aug/Sept interleaved with AL. Calendar below updated. ⚠️ **Confirm exam format** (written vs oral) — SS23 Boehm TU Berlin was 100% oral; if 2026 SoSe follows the same pattern, S.X becomes explain-aloud drill like AL.X. Click-test one Boehm SS23 tubcloud recording link.*
*Status (KW 24): L01–L08 attended (lag strategy), L09 upcoming Jun 18. Deep processing deferred until matching F blocks done. Booking of 2. PZ Prüfungstermin open.*

---

## Step ID Convention

All steps in this plan use the prefix **S** (Systems). Reference format: **S.{Block}.{Step#}**

| ID | Meaning | Example |
|---|---|---|
| S.A1 | Block A, Step 1 (AMLS L01) | "Completed S.A1" |
| S.B3 | Block B, Step 3 (L03 slides 24-43, rewrites) | "Working on S.B3" |
| S.A-test | Block A self-test | "Passed S.A-test" |
| S.X4 | Exam prep Step 4 (MMChain practice) | "Need to do S.X4" |

**When updating SEMESTER-STATUS.md:** write step IDs exactly as above. This chat (the brain) uses them to track dependencies.

---

## Why This Plan Exists

AMLS is not a "learn algorithm X" course — it's a **systems course** that assumes you already know what linear regression, gradient descent, and neural networks ARE, and asks instead: *how do you make them run fast, at scale, reliably, and fairly?* The danger is studying it like an ML theory course and missing the systems thinking. This plan structures the 13 lectures into prerequisite blocks so each concept lands on solid ground.

---

## How AMLS Relates to AML (Chat 1 Cross-References)

AMLS sits "below" AML in the stack. Every algorithm AML teaches, AMLS asks: how does the system compile, optimize, parallelize, and serve it? Here are the key bridges:

| AML concept (Chat 1) | AMLS systems view (Chat 2) | When it matters |
|---|---|---|
| Linear regression β̂=(XᵀX)⁻¹Xᵀy (Block E) | L03: the compiler rewrites this LA expression, infers sizes, chooses sparse/dense ops | Block B here |
| Gradient descent / SGD (Blocks E, J) | L05–L06: data-parallel SGD, parameter servers, BSP vs ASP, mini-batch scaling | Block C here |
| Neural network forward/backward pass (Block L) | L04: operator fusion eliminates intermediate materialization in the compute graph | Block B here |
| CNN/RNN architectures (Block M) | L07: how transformers/LLMs train at scale (pipeline/tensor/data parallelism) | Block D here |
| Bias-variance, cross-validation (Block D) | L11: hyperparameter tuning as a systems optimization problem (grid/random/Bayesian) | Block F here |
| Feature engineering, data cleaning | L10: feature transformations, encoding, standardization — the system pipeline view | Block F here |
| Overfitting, model evaluation | L12: model debugging, slice finding, LIME/SHAP, fairness constraints | Block G here |

**Rule of thumb:** If AML tells you *what* an algorithm does, AMLS tells you *what the system does to make it work*. You don't need to have finished the AML block before the corresponding AMLS block — but when you DO reach the AML topic later, revisit the AMLS systems view. The connection will be much richer.

---

## Prerequisite Dependency Graph

```
L01 (Intro: what is an ML system, lifecycle, SystemDS/DAPHNE overview)
  │
  ▼
L02 (DS lifecycle, ML systems stack, language abstractions, system landscape, benchmarks)
  │
  ├──────────────────────────────────────────────┐
  ▼                                              ▼
L03 (Compilation: size inference,            L05 (Data/task-parallel execution:
     rewrites, operator selection,                MapReduce, Spark, distributed
     auto-diff, MMChain optimization)             matrix ops, parfor)
  │                                              │
  ▼                                              ▼
L04 (Advanced compilation: runtime           L06 (Parameter servers: data-parallel
     adaptation, operator fusion,                 & model-parallel PS, BSP/ASP/SSP,
     JIT, MLIR, XLA)                             federated learning, SGD optimizers)
  │                                              │
  └──────────────────┬───────────────────────────┘
                     ▼
               L07 (LLM training & inference:
                    transformers, scaling laws,
                    pre-training, fine-tuning, RLHF,
                    KV-cache, vLLM)
                     │
                     ▼
               L08 (HW accelerators: GPUs architecture,
                    V100→H100→B200, Tensor Cores, Amdahl's law,
                    FPGAs, ASICs/TPUs, TVM)
                     │
                     ▼
               L09 (Data access: caching, buffer mgmt,
                    partitioning, indexing, lossless compression,
                    quantization FP32→FP16→INT8, bfloat16)
                     │
  ┌──────────────────┼──────────────────┐
  ▼                  ▼                  ▼
L10 (Data acq.,   L11 (Model sel.,   L12 (Debugging,
 cleaning, feat.   augmentation,      fairness, LIME,
 transforms,       AutoML/NAS,        SHAP, SliceLine,
 encoding,         model mgmt,        EU AI Act)
 validation)       lineage reuse)       │
  │                  │                  │
  └──────────────────┼──────────────────┘
                     ▼
               L13 (Model serving: ONNX, embedded/serverless,
                    quantization for inference, distillation,
                    monitoring, concept drift, GDPR unlearning)
```

---

## Block-by-Block Study Plan

Organized into **prerequisite blocks**, not calendar weeks. Each block unlocks the next. Within a block, strict order.

---

### BLOCK A: What Is an ML System?
**Time: ~4 hours | Prerequisites: none (but AML L01 context helps)**

This block establishes the vocabulary and mental model for the entire course: what sits above the algorithms, what sits below, and why systems engineering matters.

| Step | Source | Slides/Pages | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| A1 | **AMLS L01** | 43 slides | ML system definition (narrow: SW system executing ML apps; broad: apps → compiler/runtime → hardware), data science lifecycle (KDD/CRISP-DM), real-world use cases (car reacquisition, manufacturing), existing ML system categories (#1 numerical frameworks, #2 ML-centric, #3 DNN frameworks), Apache SystemDS architecture (HOP/LOP DAGs, rewrites, lineage), DAPHNE architecture | The "what is an ML system" definition (slides 13-14) is foundational — every exam question assumes you know this stack. SystemDS's compilation chain (slide 30) previews L03-L04. |
| A2 | **AMLS L02** slides 3-22 | 20 slides | DS lifecycle in detail (CRISP-DM phases), ML pipeline example (training vs scoring), ML systems stack (apps → languages → compilation → runtime → hardware), memory-vs-compute-intensive workloads (CPU vs GPU characteristics), ML-vs-DL-centric systems (sparse matrices vs dense tensors), batch algorithms (data-parallel + task-parallel), resilience at scale, optimization scopes (#1 eager, #2 lazy, #3 program-level) | The **ML systems stack** (slide 13) is THE conceptual framework. Every subsequent lecture maps to a layer. The optimization scope spectrum (slide 18) explains why some systems are fast and others aren't. |
| A3 | **Vijay Ch 1** (Introduction) | pp 45-84 | Engineering revolution in AI, how ML systems differ from traditional software, ML lifecycle and deployment spectrum, five-pillar framework | Vijay gives the textbook version of what Boehm covers in slides. Read for depth and the "five engineering disciplines" framing. |
| A4 | **Chip Huyen Ch 1-2** | pp 18-75 | When to use ML, research vs production ML, system requirements (reliability, scalability, maintainability, adaptability), framing ML problems | Chip Huyen complements with the **production mindset**: what makes ML systems different from ML research. Her "research vs production" table (Ch 1) is an exam-relevant framing. |

**⟷ AML Cross-wire:** AML L01 (Chat 1, Block B) covers "what is ML" from the algorithm side. AMLS L01-L02 answers the same question from the system side. Together they give you the full picture: algorithms + the infrastructure that runs them.

**Self-test after Block A:**
- [ ] Draw the ML systems stack (5 layers) from memory and give one example system per layer
- [ ] Explain the difference between ML-centric and DL-centric systems (data representations, operations, hardware)
- [ ] What are the three optimization scopes? Give one advantage of each.
- [ ] Name three ways ML systems differ from traditional software systems

---

### BLOCK B: Compilation — How ML Programs Become Execution Plans
**Time: ~8 hours | Prerequisites: Block A. Linear algebra basics (matrix multiply dimensions, transpose). Partial derivatives help for auto-diff section.**

This is the hardest conceptual block in the course — it draws on compiler theory and database query optimization. The payoff: understanding why `X @ W` in PyTorch actually runs fast.

| Step | Source | Slides/Pages | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| B1 | **AMLS L02** slides 20-39 | 20 slides | Language abstractions (DSLs vs libraries vs embedded), landscape of ML systems (classification: SystemDS, TensorFlow, Spark MLlib, etc.), UDFs, Pregel/graph processing via sparse LA, comparison to database query optimization, system categories (#1-#6), benchmarks (BigBench, SLAB, MLPerf, MLBench) | The **system landscape** slide (21-22) is the map of the entire field. The comparison to query optimization (slide 27) is KEY — AMLS compilation = database query optimization applied to linear algebra. |
| B2 | **AMLS L03** slides 3-23 | 21 slides | Compilation overview (parsing → HOPs → LOPs → runtime), comparison to DB query optimization (rule/cost-based rewrites), operator DAG construction, size inference (dimensions, sparsity, #nnz), sparsity estimation techniques (#1 naïve, #4 density map, #6 MNC sketch), memory estimates, cost model (FLOP counts, memory bandwidth), auto-differentiation overview | **Size inference** is the workhorse — without knowing matrix dimensions and sparsity, the compiler can't choose between sparse and dense operators. The density map and MNC sketch are exam-level content. |
| B3 | **AMLS L03** slides 24-43 | 20 slides | **Rewrites**: CSE (common subexpression elimination), constant folding, branch removal, algebraic simplifications (trace(X%*%Y)→sum(X*t(Y))), TF constant push-down, relaxed DNN graph substitutions, PyTorch JIT rewrites, loop transformations, SPOOF/SPORES (sum-product optimization), **matrix multiplication chain optimization** (dynamic programming, O(n³)), sparsity-aware MMChain, deferred standardization, operator selection criteria | **MMChain optimization** is an exam favorite (see exam Q5c). It's the same DP algorithm as in DB query optimization for join ordering. Deferred standardization (slide 39) is a beautiful example of why a system-level view beats manual optimization. |
| B4 | **AMLS L04** slides 3-15 | 13 slides | Why runtime adaptation is needed (#1 unknown sizes, #2 changing sparsity, #3 iterative feature selection), AOT vs JIT compilation, adaptive query processing analogy, **dynamic recompilation** (split DAGs at recompilation hooks, recompile-once functions) | The key insight: ML programs have **data-dependent control flow** (e.g., convergence loops), so static compilation isn't enough. Recompilation hooks are how SystemDS handles this. |
| B5 | **AMLS L04** slides 16-39 | 24 slides | **Operator fusion**: motivation (eliminate intermediate materialization), data flow graphs vs operator kernels, 1st gen handwritten fused ops (BLAS AXPY), automatic fusion landscape, SystemDS codegen (template skeletons: Row/Cell/MAgg/Outer), memo table + cost-based fusion plan enumeration, TF XLA compilation, **MLIR** multi-level IR, DAPHNE vectorized execution, zero-copy input slicing | Operator fusion is one of THE performance techniques. Understanding the tradeoff between materialization cost and fusion complexity is exam-relevant. MLIR (slide 34-35) is the industry direction for ML compilers. |
| B6 | **Vijay Ch "AI Frameworks"** | pp 475-572 | Computational graphs, automatic differentiation (forward/reverse mode), data structures (tensors, sparse), programming models (eager vs graph), framework ecosystem (TF, PyTorch, JAX) | Vijay's auto-diff section (pp 493-512) is the best textbook treatment. Read after B2 for the formal derivation that the slides only sketch. |

**⟷ AML Cross-wire:** When AML L03 (Chat 1, Block E) derives β̂=(XᵀX)⁻¹Xᵀy, AMLS shows what happens under the hood: the compiler represents this as an operator DAG, infers that XᵀX is nxn (small if n<<m), rewrites the expression to avoid dense intermediates, and selects sparse operators if X is sparse. Same formula, completely different concerns.

**Self-test after Block B:**
- [ ] Draw the SystemDS compilation chain (parsing → HOPs → rewrites → LOPs → runtime)
- [ ] Given matrices A(10×7), B(7×3), C(3×5), D(5×12), E(12×2): compute the cost of ((AB)C)(DE) vs A(B(C(DE))) — which parenthesization is cheaper?
- [ ] Explain CSE on a DAG: why is it different from CSE in a traditional compiler?
- [ ] What is the advantage of operator fusion? Draw a simple example where fusing two ops avoids materializing an intermediate.
- [ ] Explain forward-mode vs reverse-mode auto-differentiation. Why is reverse-mode preferred for neural networks?

---

### BLOCK C: Parallel Execution — Making ML Scale
**Time: ~7 hours | Prerequisites: Block A (systems stack). AML GD basics (Chat 1 Block E/J) helpful but not required — AMLS re-derives SGD.**

Two lectures that cover how to scale ML from one machine to clusters. L05 covers data/task parallelism for batch LA algorithms. L06 covers parameter servers for mini-batch DNN training.

| Step | Source | Slides/Pages | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| C1 | **AMLS L05** slides 3-12 | 10 slides | Problem formulation (find θ* = argmin f(D,θ)), batch vs mini-batch ML algorithms, data representations (files, objects, partitioned matrices), **Flynn's classification** (SISD/SIMD/MISD/MIMD), scale-up node example (compute peak: FLOPs calculation), distributed data-parallel computation, resilience problem at scale | Flynn's taxonomy (slide 8) gives you the vocabulary for all parallelism discussion. The FLOP calculation (slide 9) is a practical skill — you need it to understand whether you're compute- or memory-bound. |
| C2 | **AMLS L05** slides 13-32 | 20 slides | **MapReduce** (programming model, execution model, shuffle/sort), **Apache Spark** (RDD abstraction, transformations vs actions, lazy evaluation, caching, lineage-based fault tolerance, partitioning), Dask, Modin | MapReduce and Spark are foundational distributed systems. The RDD abstraction (immutable, partitioned, lazy) is a design pattern you'll see everywhere. |
| C3 | **AMLS L05** slides 23-42 | 20 slides | **Data-parallel execution** for batch ML: block-partitioned matrices, distributed matrix operations (elementwise, aggregations, matrix multiply), operator selection criteria, shuffle optimization (preserve partitioning), **task-parallel execution** (parfor): task partitioning schemes (naive, static, fixed, self-scheduling, factoring), hybrid parallelization | The **distributed matrix multiply** strategies and **parfor** optimization are exam-level. Understanding when to use data-parallel vs task-parallel execution is a core systems decision. |
| C4 | **AMLS L06** slides 4-21 | 18 slides | **Data-parallel parameter servers**: mini-batch SGD formulation, PS system architecture (M servers, N workers), evolution (1st gen key-value → 2nd gen → 3rd gen), **update strategies**: BSP (bulk synchronous parallel), ASP (asynchronous), SSP (stale synchronous parallel) — tradeoffs (convergence guarantee vs speed), data partitioning, SGD optimizers (vanilla SGD, momentum, Adam), batch size effects, sparse communication | **BSP vs ASP vs SSP is a guaranteed exam topic** (see exam Q1b). Adam optimizer details (slide 18) connect directly to AML. Understanding why larger batch sizes reduce communication but may hurt convergence (slide 19-20) is key. |
| C5 | **AMLS L06** slides 22-47 | 26 slides | **Model-parallel PS** (when model doesn't fit in one device), TF distributed placement, GSPMD/XLA, **distributed RL** (Ray/RLlib, actor model, Anakin/Sebulba), **federated learning** (FedAvg algorithm, decentralized aggregation, differential privacy, SystemDS federated backend, federated quantiles, TFF) | Model parallelism becomes essential for LLMs (connects to L07). Federated learning is both a privacy technique and a distributed training paradigm — increasingly exam-relevant. |
| C6 | **Vijay Ch "AI Training"** | pp 587-700 | Training pipeline architecture, mathematical foundations (optimization, backprop), pipeline optimizations (prefetching, mixed-precision, gradient accumulation, checkpointing), distributed systems (data/model/hybrid parallelism, efficiency metrics), HW acceleration | Vijay's treatment of distributed training (pp 659-680) gives the textbook depth. Read the parallelism strategy comparison (p 679) for exam prep. |

**⟷ AML Cross-wire:** AML L06 (Chat 1, Block J) teaches SGD as "the update rule w ← w - η∇L." AMLS L06 asks: what happens when you have 100 GPUs each computing gradients on different mini-batches? How do you aggregate? What if one GPU is slow (stragglers)? BSP waits for all (safe but slow), ASP doesn't wait (fast but may diverge), SSP is the compromise. This is the **same SGD** from AML, but the systems challenges are entirely new.

**Self-test after Block C:**
- [ ] Describe the BSP, ASP, and SSP update strategies. Draw a timeline diagram for each with 3 workers.
- [ ] What is the tradeoff between BSP and ASP? Name one advantage and one disadvantage of each.
- [ ] Explain data parallelism vs model parallelism. When do you need model parallelism?
- [ ] Write the FedAvg algorithm in pseudocode (select clients, local training, aggregate)
- [ ] Given a matrix A (1M × 10K) and vector v (10K × 1), describe how you'd distribute the computation of A*v across 4 workers

---

### BLOCK D: LLM Systems — Training and Serving at Scale
**Time: ~5 hours | Prerequisites: Block C (parallelism, parameter servers). AML neural network basics (Chat 1 Block L) helpful for understanding transformer architecture.**

This lecture connects the parallelism concepts from Block C to the most important current application: large language models.

| Step | Source | Slides/Pages | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| D1 | **AMLS L07** slides 4-15 | 12 slides | Transformer basics (tokens, encoder-decoder, self-attention mechanism Q/K/V, multi-head attention), dense vs sparse (MoE) models, LLM training/inference workflow, **data preprocessing** (web crawling, deduplication, tokenization: BPE, positional encoding) | You need to understand the transformer architecture at the systems level — not "how attention learns" but "what are the compute/memory costs of attention." The QKV matrix multiply is the bottleneck that drives all optimization. |
| D2 | **AMLS L07** slides 16-27 | 12 slides | **Scaling laws** (Kaplan et al: loss scales as power law with compute/data/params, Chinchilla: compute-optimal allocation), training costs (GPT-3: $4.5M, GPT-4: $100M), DeepSeek-V3 training setup (16-way pipeline parallelism), sparse transformers (MoE: mixture of experts), **post-training**: SFT (supervised fine-tuning), RLHF, DPO, LoRA (parameter-efficient fine-tuning) | Scaling laws are the quantitative framework for LLM training decisions. The Chinchilla result (data and model should scale equally) changed industry practice. LoRA (slides 25-26) is how you fine-tune without retraining everything. |
| D3 | **AMLS L07** slides 28-34 | 7 slides | **LLM inference**: zero-shot, few-shot, RAG, model variants, **vLLM** (PagedAttention for KV-cache management), **FlashAttention** (tiled attention to reduce memory I/O), compound AI systems (multi-LLM pipelines) | vLLM's PagedAttention (slide 31) and FlashAttention (slide 32) are the two most impactful inference optimizations. Understanding the KV-cache memory problem is essential. |
| D4 | **Vijay Ch "Efficient AI"** | pp 707-750 | Scaling laws (formal treatment), efficiency framework (algorithmic, compute, data), tradeoffs | Deepens D2 with the mathematical foundations of scaling laws. |
| D5 | **Chip Huyen Ch 7** (selected sections) | pp 237-257 | Model compression (low-rank factorization, distillation, pruning, quantization), edge deployment, model compilers | Practical complement to the systems view. |

**⟷ AML Cross-wire:** AML L10-L11 (Chat 1, Block M) teach CNN and RNN architectures. AMLS L07 shows what replaced RNNs (transformers/attention) and why, from a systems perspective: attention is more parallelizable than sequential RNN computation. When you study AML's RNN lecture, remember that AMLS explained why the industry moved to transformers — it's a systems efficiency story, not just an accuracy story.

**Self-test after Block D:**
- [ ] Explain the self-attention mechanism: given Q, K, V matrices, write the attention formula and explain the softmax
- [ ] What do scaling laws predict? State the Chinchilla finding in one sentence.
- [ ] Explain why the KV-cache is a memory bottleneck during autoregressive generation
- [ ] What is PagedAttention (vLLM) and how does it solve the KV-cache fragmentation problem?
- [ ] Compare full fine-tuning vs LoRA: when would you choose each?

---

### BLOCK E: Hardware — From CPUs to TPUs
**Time: ~6 hours | Prerequisites: Block B (compilation concepts). Block C (parallelism) helps.**

Two lectures covering the bottom of the ML systems stack: what hardware actually executes the computation, and how data is accessed efficiently.

| Step | Source | Slides/Pages | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| E1 | **AMLS L08** slides 4-27 | 24 slides | Why HW specialization (end of Dennard scaling, end of Moore's law), **GPU architecture**: NVIDIA V100 (GPCs, SMs, CUDA cores, Tensor Cores, HBM), warp execution (SIMT, 32 threads), Tensor Cores (4×4 fused matrix multiply-add), GPU evolution (A100, H100, B200), **Amdahl's law** (speedup = 1/(s + (1-s)/p)), PCIe vs NVLink interconnects, GPU memory management (live variable analysis, operator placement), sparse tensor support limitations | Amdahl's law (slide 20) is exam-relevant and appears in calculations. Understanding the GPU memory hierarchy (HBM → L2 → shared memory → registers) explains why fusion matters (Block B). Tensor Cores show why matrix multiply is so fast on GPUs. |
| E2 | **AMLS L08** slides 28-47 | 20 slides | **FPGAs** (field-programmable gate arrays: definition, Stratix 10, Microsoft Catapult/Brainwave, DAnA), **ASICs** (Google TPU v1→v5→Ironwood: systolic arrays, TPU pods, torus topology), other accelerators (SambaNova, Cerebras wafer-scale), TVM code generation, quantum computing outlook | TPU architecture (systolic arrays for matrix multiply) is exam-relevant. The progression from general (CPU) → somewhat specialized (GPU) → highly specialized (TPU/ASIC) illustrates a fundamental systems tradeoff: flexibility vs efficiency. |
| E3 | **AMLS L09** slides 4-20 | 17 slides | Data access overview (tall-skinny vs wide matrices), **caching** (distributed caching, buffer pool management), **partitioning** (Spark RDD partitioning, NUMA-aware replication), **indexing** (B-trees over linearized arrays, 2D array storage managers), data prefetching for mini-batch training | Buffer pool management (slide 11) connects to database systems (DBT!). NUMA-aware data placement (slide 13) is a practical optimization that matters on modern multi-socket servers. |
| E4 | **AMLS L09** slides 21-40 | 20 slides | **Compression**: null suppression, general-purpose (Snappy/LZ4/Zstd), **lossless matrix compression** (column-wise compression, OLE/RLE/DDC encoding, compressed matrix-vector multiply), compression size estimation, **quantization**: FP32→FP16→INT8→INT4, mixed-precision training, bfloat16, numerical stability (Kahan summation), min-max quantization, sparsification/pruning, mantissa truncation | **Quantization** is heavily exam-tested (see exam Q6a: describe min-max quantization FP64→UINT8). Understanding why bfloat16 works (same exponent range as FP32, less precision) is key. Compressed matrix operations (slide 26) show how you can compute directly on compressed data. |
| E5 | **Vijay Ch "AI Acceleration"** | pp 897-1022 | AI compute primitives, memory systems (memory wall), hardware mapping, dataflow optimization, compiler/runtime support, multi-chip scaling | Read selectively — the memory hierarchy section (pp 932-946) and compiler support (pp 984-994) deepen the lecture content. |

**⟷ AML Cross-wire:** AML never discusses hardware. But when AML L09 (Chat 1, Block L) teaches backpropagation and you compute ∂L/∂W layer by layer, AMLS shows that each layer's gradient is a matrix multiply — and Tensor Cores on the GPU execute these 4×4 blocks in a single instruction. The chain rule from calculus becomes a hardware pipeline.

**Self-test after Block E:**
- [ ] Apply Amdahl's law: if 80% of your computation is parallelizable, what is the maximum speedup with 16 cores?
- [ ] Explain what a GPU Tensor Core does in one sentence
- [ ] Describe min-max quantization from FP64 to UINT8: give the formula and explain why it speeds up inference
- [ ] What is bfloat16? Why is it preferred over FP16 for training?
- [ ] Explain lossless column-wise matrix compression: how can you do matrix-vector multiply without decompressing?

---

### BLOCK F: ML Lifecycle — Data to Model Selection
**Time: ~6 hours | Prerequisites: Block A (lifecycle), Block B (compilation for lineage concepts). AML feature engineering concepts (Chat 1 Block E) helpful.**

Two lectures covering the "before training" (data) and "during training" (model selection) phases of the lifecycle.

| Step | Source | Slides/Pages | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| F1 | **AMLS L10** slides 5-19 | 15 slides | **Data acquisition and integration**: terminology (integration, fusion, matching), data formats (CSV, JSON, Parquet, Protobuf), types of heterogeneity, data catalogs, schema detection, schema matching, entity resolution, data extraction from unstructured sources, **data validation** (TensorFlow Data Validation, constraints and metrics) | Data sourcing = 80-90% of a data scientist's time (slide 4). Schema matching and entity resolution are systems problems that AML ignores entirely. TFDV (slide 19) is a real tool — understand what constraints it checks. |
| F2 | **AMLS L10** slides 20-44 | 25 slides | **Feature transformations**: recoding (categorical→integer), binning (equi-width, equi-height), one-hot encoding, feature hashing, NLP features (bag-of-words, TF-IDF, n-grams, word embeddings), sklearn Transformer API (fit/transform), feature transformation during training vs scoring (consistency!), **data cleaning**: standardization ((x-μ)/σ), deferred standardization (push through computation), outlier detection, missing value imputation, automatic cleaning pipeline generation | **Recoding + one-hot encoding** is a guaranteed exam topic (exam Q2a). Deferred standardization (slide 38) is a beautiful systems optimization — instead of densifying your sparse matrix by centering, you push the mean subtraction into the computation. Feature hashing advantage over recoding (exam Q2b). |
| F3 | **AMLS L11** slides 4-13 | 10 slides | **Data augmentation**: image augmentations (scaling, distortions, rotations, color jittering), training on simulated images, AutoAugment (learned augmentation policies), **weak supervision**: heuristic labeling, data programming (labeling functions), Snorkel | Data augmentation directly connects to your AMLS Project (Chat 3, Task 1.3). Understanding AutoAugment and data programming gives you systems-level tools beyond manual augmentation. |
| F4 | **AMLS L11** slides 14-39 | 26 slides | **Model selection**: hyperparameter tuning (grid search, random search), simulated annealing, **Bayesian optimization** (Gaussian processes, acquisition functions, exploitation vs exploration), multi-armed bandits, Auto-WEKA, Alpine Meadow (logical/physical ML pipelines), **NAS** (neural architecture search: search space, strategies, performance estimation), **model management**: experiment tracking (MLflow, TensorBoard), ModelHub (DNN versioning), DEX dataset versioning, HELIX (lineage-based pipeline reuse), multi-level lineage reuse | **Bayesian optimization** is exam-relevant (exam Q3b). GridSearch computation: n parameters × 10 values each = 10^n models (exam Q3a). Lineage-based reuse (slides 36-38) connects directly to PPDS (Chat 4) — provenance tracking enables caching and reuse of pipeline intermediates. |
| F5 | **Chip Huyen Ch 4-6** | selected sections | Training data (sampling, labeling, class imbalance), feature engineering (leakage detection!), model development (ensembles, distributed training, AutoML) | Chip Huyen's **data leakage** section (pp 172-174) is directly relevant to PPDS DataLeakage analysis. Read after F2. |

**⟷ AML Cross-wire:** AML L04 (Chat 1, Block H) teaches Ridge/Lasso as regularization with hyperparameter λ. AMLS L11 asks: how do you find the best λ? Grid search tries all values (expensive), Bayesian optimization learns where to look (smart). Cross-validation from AML L02 (Block D) is the evaluation method inside each model selection iteration. Same concepts, systems optimization perspective.

**⟷ PPDS Cross-wire:** AMLS L11's lineage-based reuse (HELIX) is essentially what mlprov does — tracking data transformations so you can reuse intermediates. When you implement MLProvManager in Chat 4, remember AMLS's lineage tracking architecture.

**Self-test after Block F:**
- [ ] Given raw data with columns [Age(num), City(cat), Income(num), Dept(cat)]: apply recoding, one-hot encoding to categorical columns and equi-width binning (3 bins) to numerical columns (exam Q2a)
- [ ] What is feature hashing and why is it advantageous over recoding? (exam Q2b)
- [ ] Explain Bayesian optimization: what is the surrogate model, what is the acquisition function, how does it balance exploitation/exploration? (exam Q3b)
- [ ] Grid search with 3 hyperparameters × 10 values each: how many models to train?
- [ ] What is the training-serving skew problem for feature transformations?

---

### BLOCK G: Model Debugging, Fairness, and Explainability
**Time: ~4 hours | Prerequisites: Block A (lifecycle), Block F (model selection). AML classification concepts (Chat 1 Block I) help for confusion matrices.**

The "after training" phase: how do you know if your model works, where it fails, and whether it's fair?

| Step | Source | Slides/Pages | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| G1 | **AMLS L12** slides 4-19 | 16 slides | **Model debugging**: data validation (sanity checks), visualization (predictions, residuals), regression statistics, generalized confusion matrices (hierarchical, multi-label), overfitting detection (train vs test gap), **explainability**: occlusion explanations (slide gray square over image regions), saliency maps (gradient of class score w.r.t. input), Clever Hans examples (wolf=snow, horse=watermark), **SliceLine** (finding problematic data slices: scoring function, pruning, efficient enumeration) | SliceLine (slides 17-19) is Boehm's own research and very exam-relevant. The scoring function balances slice error rate, slice size, and how much worse the slice is than average. Clever Hans examples (slide 15) illustrate why explainability matters. |
| G2 | **AMLS L12** slides 20-38 | 19 slides | **LIME** (model-agnostic local explanations: perturb input, fit simple model locally), **SHAP** (Shapley additive explanations: fair attribution of each feature's contribution, game-theoretic foundation), scalable SHAP computation, **fairness**: sources of bias (selection, measurement, algorithmic), fairness metrics (statistical parity, equalized odds, predictive parity, false discovery rate parity), **fairness constraints** formulation (triplet: group g, metric f, threshold ε), EU AI Act overview | **LIME vs SHAP** comparison is exam-relevant (exam Q4c asks about occlusion explanations). Fairness metrics (statistical parity etc.) connect directly to PPDS GroupFairness analysis (Chat 4). EU AI Act (slides 36-37) is the regulatory context — know the risk categories. |
| G3 | **Vijay Ch "Responsible AI"** | pp 1543-1628 (selected) | Transparency, fairness technical foundations, bias detection/mitigation, validation | Read selectively: the fairness metrics section (pp 1574-1582) and risk mitigation (pp 1582-1589). |
| G4 | **Chip Huyen Ch 8, 11** | selected sections | Data distribution shifts, monitoring, responsible AI case studies | Ch 8 on distribution shifts complements L13's concept drift coverage. Ch 11's case studies are good exam prep. |

**⟷ AML Cross-wire:** AML L02 (Chat 1, Block D) teaches bias-variance and train/test evaluation. AMLS L12 goes beyond: *where* does your model fail (SliceLine), *why* does it make a prediction (LIME/SHAP), and *is it fair* across groups? These are the questions that matter in production but never appear in AML.

**⟷ PPDS Cross-wire:** AMLS L12's fairness metrics (statistical parity, equalized odds) are exactly what you'll implement in GroupFairness analysis in Chat 4. The formal triplet (g, f, ε) gives you the framework.

**Self-test after Block G:**
- [ ] Explain occlusion-based explanations by example (classifying a handwritten digit) — exam Q4c
- [ ] What is LIME? Describe the three steps: perturb, predict, fit local model
- [ ] Define statistical parity and equalized odds. Can a model satisfy both simultaneously? (hint: usually not)
- [ ] Describe the SliceLine scoring function: what makes a "problematic" slice?
- [ ] Name three sources of bias in ML and one mitigation strategy for each (exam Q4a)

---

### BLOCK H: Model Serving — From Training to Production
**Time: ~4 hours | Prerequisites: Block E (quantization, hardware), Block F (model management). Block D (LLM inference) helps.**

The final lifecycle stage: deploying trained models and keeping them working.

| Step | Source | Slides/Pages | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| H1 | **AMLS L13** slides 4-24 | 21 slides | **Model exchange**: definition of deployed model (weights + computation graph + pre/post-processing), open standards (PMML, PFA, **ONNX**), **serving patterns**: embedded (TF Lite), serverless (FaaS), in-database scoring (SystemDS JMLC), model batching, **serving optimizations**: quantization for inference (INT8), sparsification/pruning, result caching, compiled scoring (XLA), **model vectorization** (tree traversal as matrix operations, GEMM strategies), **model distillation** (ensemble → single NN), model cascading (NoScope: cheap model first, expensive model if uncertain) | ONNX (slide 8) is the industry standard for model exchange. Model distillation and quantization are the two main compression techniques for inference. The serving optimization toolbox (slides 14-24) is exam-relevant: know at least 3 techniques and when to use each. |
| H2 | **AMLS L13** slides 25-35 | 11 slides | **Model monitoring**: deployment workflow (integration → validation → serving → monitoring → retraining), monitoring goals (check training/serving data deviations, feature drift, model staleness), alerting guidelines, **concept drift** (features→labels relationship changes over time), **model updates**: periodic retraining (window of latest data, data weighting), event-based retraining (performance predictor triggers), **GDPR "right to be forgotten"** (machine unlearning: HedgeCut approach using Extremely Randomized Trees) | Concept drift (slide 29) is a fundamental production ML problem — your model degrades over time because the world changes. GDPR unlearning (slides 33-34) is increasingly exam-relevant and connects to PPDS data provenance concerns. |
| H3 | **Chip Huyen Ch 7, 9** | selected sections | Batch vs online prediction, model compression techniques, continual learning (stateless retraining vs stateful), A/B testing, canary releases, bandits | Chip Huyen's continual learning chapter (Ch 9) is the best treatment of how to keep models fresh in production. |

**⟷ AML Cross-wire:** AML teaches model evaluation with a static test set. AMLS L13 reveals the production reality: your test set's distribution may drift from production data over time. The model that scored 95% accuracy last month may be at 80% today because the input distribution changed. This is why monitoring and retraining matter.

**Self-test after Block H:**
- [ ] Name three serving optimizations and explain when to use each (exam Q7a)
- [ ] What is ONNX and why is an open model exchange format important?
- [ ] Explain concept drift. Give an example where a model's performance degrades over time.
- [ ] Describe two model update strategies: periodic vs event-based. Advantages of each?
- [ ] What is the GDPR "right to be forgotten" challenge for ML models?

---

### BLOCK X: Exam Preparation
**Time: ~8–12 hours | Prerequisites: All blocks A–H | Timing: 2. PZ (Sept/Okt) — runs Aug/Sept interleaved with AL.X and AN.X (if AN → Scenario 2)**

> ⚠️ **CONFIRM EXAM FORMAT FIRST.** SS23 Boehm (TU Berlin) was 100% oral exam, project as prerequisite. If the 2026 SoSe AMLS is also oral, the prep format below shifts: written drill (Q2a recoding on paper, MMChain DP table) is replaced by **explain-aloud drill** like AL.X (explain sheets + speak-through proofs + mock 30-min session). Watch one SS23 recording from tubcloud (LEARNING-RESOURCES §2 → AMLS row) to calibrate the depth expected in that context.

**If written exam (standard Klausur format) — 7 exam areas from L13 slides 36-49:**

| Exam area | Points (approx) | Source blocks | Key topics to drill |
|---|---|---|---|
| Parameter servers (Q1) | ~16 | Block C | Architecture diagram, BSP vs ASP, stragglers |
| Feature engineering (Q2) | ~13 | Block F | Recoding + one-hot + binning (BY HAND), feature hashing |
| Model selection (Q3) | ~13 | Block F | GridSearch combinatorics, Bayesian optimization |
| Fairness & explainability (Q4) | ~8+ | Block G | Bias sources, occlusion explanations, LIME/SHAP |
| Compilation & rewrites (Q5) | ~10+ | Block B | CSE algorithm, MMChain DP, rewrites |
| Quantization (Q6) | ~8+ | Block E | Min-max quantization formula, precision formats |
| Model serving (Q7) | ~8+ | Block H | Serving optimizations, monitoring, drift |

**Written exam prep steps:**
- [ ] X1: Work through ALL exam questions from L13 slides 36-49 under timed conditions
- [ ] X2: Create a 1-page cheat sheet per block (8 sheets total)
- [ ] X3: Practice recoding/encoding/binning transformations on paper (exam Q2a)
- [ ] X4: Practice MMChain optimization DP table on paper (exam Q5c)
- [ ] X5: Practice min-max quantization calculation (exam Q6a)
- [ ] X6: Draw parameter server architecture from memory and annotate BSP/ASP (exam Q1a/Q1b)

**If oral exam (like SS23 — same 5-part pattern as AL.X):**
- [ ] X1: **Explain sheets** — one A4 per block (A–H), structured as: *define the core concept / state the key theorem or technique / sketch the mechanism or proof idea / hand-run one micro-example / answer "why not simpler?"*
- [ ] X2: **Speak-through drill** — re-explain each block aloud after watching the matching SS23 Boehm lecture. Record yourself; check for gaps.
- [ ] X3: **Calculation fluency** — even in an oral, you may need to run a small MMChain table, a recoding example, or a min-max quantization — practice these on a whiteboard while talking
- [ ] X4: **CMU 10-414 / MIT 6.172 questions aloud** — pick one problem per block from the practice bank (LEARNING-RESOURCES §6 → AMLS), solve it in writing, then re-explain the solution verbally
- [ ] X5: **Mock 30-min oral** — sample questions from all 7 areas; run with a study partner or self-test against your explain sheets; grade honestly
- [ ] X6: Gap pass — re-explain whatever broke in X5

---

## Mapping Blocks to Calendar Weeks

Given ~5-6 hours/week for AMLS theory (from Theorieplan), with lectures Thu 4-6pm:

| KW | Dates | AMLS Lecture | Block | Hours | Notes |
|----|-------|-------------|-------|-------|-------|
| **17** | Apr 21-27 | (L01 done) | **A** (start) | ~3h | Read Vijay Ch1 + Chip Huyen Ch1-2 |
| **18** | Apr 28 – May 4 | L02 (Apr 24 was last wk) | **A** (finish) + **B** (start) | ~5h | L02 is dense — language abstractions + system landscape |
| **19** | May 5-11 | L03 (May 2 was last wk) | **B** (continue: compilation) | ~6h | Steepest wall. Focus on size inference + rewrites + MMChain |
| **20** | May 12-18 | L04 (May 9 was last wk) | **B** (finish: fusion + JIT) | ~5h | Operator fusion + MLIR. No AMLS lecture May 14 (Ascension) but L04 was May 9 |
| **21** | May 19-25 | L05 (May 15 was last wk) | **C** (start: data/task parallel) | ~5h | MapReduce, Spark, distributed matrix ops |
| **22** | May 26 – Jun 1 | L06 (May 22 was last wk) | **C** (finish: parameter servers) | ~6h | Parameter servers + federated learning |
| **23** | Jun 2-8 | L07 (Jun 5) | **D** (LLM systems) | ~5h | Transformers, scaling laws, vLLM. Heavy lecture. |
| **24** | Jun 9-15 | L08 (Jun 12) | **E** (start: HW accel.) | ~5h | GPU architecture, TPUs, FPGAs |
| **25** | Jun 16-22 | L09 (Jun 19) | **E** (finish: data access) | ~5h | Compression, quantization — exam favorite |
| **26** | Jun 23-29 | L10 (Jun 26) | **F** (start: data + model) | ~5h | Feature transforms, encoding |
| **27** | Jun 30 – Jul 6 | L11 (Jul 3) | **F** (finish) + **G** (start) | ~6h | Model selection + debugging |
| **28** | Jul 7-13 | L12 (Jul 10) | **G** (finish) | ~5h | Fairness, LIME/SHAP |
| **29** | Jul 14-20 | L13 (Jul 17) | **H** (serving) | ~5h | Last lecture + serving content |
| **30** | Jul 21–27 | — | ~~**X** (exam prep)~~ — **exam prep deferred** | 0h | ~~Exam: Jul 23 16:00~~ **MOVED to 2. PZ (Jun 12).** KW 30 hours now belong to F.N + AN.X (1. Termin written exams late July). |
| **Aug–Sep** | 2. PZ block | — | **S.X** (exam prep, ~8–12h) | ~8–12h | Run after AL.X and AN.X are done; interleave with AMLS+Algo2 oral prep per §7 2. PZ block. Confirm exam format → follow written or oral S.X path. |

**Timing note vs Chat 1:** Chat 1's Block E (linear regression, KW 18) aligns with AMLS Block B (compilation) — when you learn β̂=(XᵀX)⁻¹Xᵀy in AML, you'll simultaneously learn how the system compiles and optimizes that exact expression. Chat 1's Block J (SGD, KW 21) aligns with AMLS Block C (parameter servers) — perfect timing.

---

## Quick Reference: The 6 Cross-Wire Moments

1. **β̂ as a DAG (Block B, L03):** AML's closed-form regression solution β̂=(XᵀX)⁻¹Xᵀy is an operator DAG for the AMLS compiler. The system infers sizes, rewrites (e.g., exploit X's sparsity), and selects operators — things you never see when you just call `sklearn.fit()`.

2. **SGD becomes distributed (Block C, L06):** AML's simple update rule w ← w - η∇L becomes a distributed systems problem: N workers compute gradients, a parameter server aggregates. BSP vs ASP is the fundamental tradeoff between convergence safety and training speed.

3. **RNNs → Transformers as a systems choice (Block D, L07):** AML teaches RNNs as sequential architectures. AMLS shows why transformers won: attention is embarrassingly parallelizable (no sequential dependency between tokens), enabling massive data-parallel training on GPU clusters.

4. **Backprop meets Tensor Cores (Block E, L08):** AML's chain rule ∂L/∂W involves matrix multiplies at every layer. AMLS shows that GPU Tensor Cores execute these as fused 4×4 multiply-accumulate — the hardware was literally designed for this operation.

5. **Cross-validation as systems optimization (Block F, L11):** AML uses k-fold CV to evaluate models. AMLS L11 wraps this in Bayesian optimization to search hyperparameter space efficiently, and adds lineage-based reuse so you don't recompute pipeline intermediates for every fold.

6. **Fairness = GroupFairness analysis (Block G, L12 + PPDS):** AMLS L12 defines fairness metrics (statistical parity, equalized odds). PPDS Chat 4 implements these as provenance analyses. The formal triplet (g, f, ε) from AMLS becomes code in mlprov.

---

## Recommended Reading Priority

The lectures are primary. For each block, the supplementary reading priority:

| Priority | Source | When to read | What it adds |
|---|---|---|---|
| 🔴 **Must** | AMLS lecture slides (all 13) | Before/after each lecture | THE exam source |
| 🔴 **Must** | **Boehm SS23 TU Berlin recordings** ⭐ — tubcloud mp4s, all 12 lectures (link in LEARNING-RESOURCES §2 → AMLS row, upgraded KW 24) | **S.X exam prep — watch AFTER learning each block** | Only video recordings of Boehm's own AMLS lectures known to exist publicly. SS23 grading was 100% oral — if 2026 follows the same format, these become your primary oral rehearsal material (re-explain after each video). |
| 🟡 **High** | Vijay: AI Frameworks (pp 475-530), AI Training (pp 587-700), AI Acceleration (pp 897-1000) | Blocks B, C, E | Textbook depth for the hardest material |
| 🟡 **High** | Chip Huyen: Ch 1-2, Ch 7 | Block A, Block H | Production mindset |
| 🟡 **High** | **CMU 10-414 HW0–4 + community solutions** ⭐, **MIT 6.172 practice quizzes w/ solutions** ⭐ | Block X (exam prep) | Only solved/checkable AMLS-adjacent practice material. 10-414 = autodiff + compilation + parallelism + NNs (Blocks B/C); 6.172 = performance engineering quizzes (Blocks B/E). See LEARNING-RESOURCES §6 → AMLS subsection. |
| 🟢 **Medium** | Vijay: Introduction, Responsible AI | Blocks A, G | Broader framing |
| 🟢 **Medium** | Chip Huyen: Ch 4-6, Ch 8-9 | Blocks F, G, H | Data engineering + monitoring |
| 🟢 **Medium** | **CS149 ISPC/CUDA written assignments (2020, solved)** | Block E (hardware) | Practical parallel-compute problems with solutions |
| ⚪ **Optional** | DLSys lectures (CMU 10-414) | If Block B feels too hard | Alternative explanation of compilation + auto-diff |
| ⚪ **Optional** | Vijay: remaining chapters | Exam prep week | Reference for specific topics |
