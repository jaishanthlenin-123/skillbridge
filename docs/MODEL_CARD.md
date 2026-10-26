# SkillBridge Model Card & NLP Pipeline Specification

## 1. Overview
SkillBridge incorporates a hybrid Natural Language Processing (NLP) architecture designed for explainable, fair, and evidence-grounded resume-to-job matching.

- **Primary Architecture**: Hybrid Weighted Ensemble combining Rule-Based Canonical Skill Matching, Requirement Weighting, and Dense Semantic Vector Embeddings.
- **Semantic Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors fine-tuned for semantic textual similarity and retrieval).
- **Fallback Architecture**: Normalized Token TF-IDF / Jaccard Cosine Similarity when embedding weights or hardware accelerators are unavailable.

## 2. Intended Use & Boundaries
- **Intended Use**: Candidate self-assessment, gap identification, learning roadmap formulation, and interview preparation.
- **Strict Limitation**: SkillBridge is NOT an automated screening, hiring, or rejection system.
- **Fairness & Privacy Safeguards**: Model inference does not inspect, parse, or weight demographic attributes (race, gender, age, nationality, address, photographs).

## 3. Mathematical Formulation of the Hybrid Scoring Engine

The final score $S_{\text{hybrid}} \in [0, 100]$ is computed as:

$$S_{\text{hybrid}} = w_1 S_{\text{weighted}} + w_2 S_{\text{coverage}} + w_3 S_{\text{semantic}}$$

Where the default calibrated configuration is:
- $w_1 = 0.45$ (Requirement-Weighted Coverage)
- $w_2 = 0.35$ (Canonical Skill Overlap Coverage)
- $w_3 = 0.20$ (Dense Semantic Similarity)
- $\sum w_i = 1.00$

### Component A: Canonical Skill Coverage ($S_{\text{coverage}}$)
Given the canonical set of unique job requirements $R = \{r_1, r_2, \dots, r_m\}$ and candidate extracted skills $C = \{c_1, c_2, \dots, c_k\}$:

$$S_{\text{coverage}} = 100 \times \frac{|R \cap C|}{|R|} \quad (\text{if } |R| > 0 \text{ else } 0)$$

### Component B: Dense Semantic Similarity ($S_{\text{semantic}}$)
Each requirement text $r_i$ and candidate section evidence snippet $e_j$ are embedded into normalized unit vectors $\mathbf{u}_i, \mathbf{v}_j \in \mathbb{R}^d$:

$$\text{sim}(r_i, e_j) = \frac{\mathbf{u}_i \cdot \mathbf{v}_j}{\|\mathbf{u}_i\|_2 \|\mathbf{v}_j\|_2}$$

For each requirement $r_i$, we compute its maximum evidence alignment: $\hat{s}_i = \max_j \text{sim}(r_i, e_j)$.
Then $S_{\text{semantic}} = 100 \times \text{clamp}\left(\frac{1}{|R|} \sum_{i=1}^{|R|} \hat{s}_i, 0, 1\right)$.

### Component C: Requirement-Weighted Coverage ($S_{\text{weighted}}$)
Every job requirement $i$ is assigned an importance multiplier:
- Mandatory requirement: $W_i = 1.0$
- Preferred requirement: $W_i = 0.5$

Match value $M_i \in [0, 1]$:
- Exact canonical match: $M_i = 1.0$
- Related skill match (e.g. PyTorch $\rightarrow$ Deep Learning): $M_i = 0.65$
- Semantic evidence match ($\hat{s}_i \ge 0.75$): $M_i = 0.50$
- Missing evidence: $M_i = 0.0$

$$S_{\text{weighted}} = 100 \times \frac{\sum_{i=1}^{|R|} W_i M_i}{\sum_{i=1}^{|R|} W_i}$$

## 4. Explainability & Output Contract
The model guarantees evidence attribution. If a skill is classified as `missing`, the system explicitly records: *"No supporting evidence found in the analyzed document text"*.
