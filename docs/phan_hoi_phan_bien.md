# Response to Reviewers — HI26-0013

**Paper:** A Rule-Constrained Large Language Model Pipeline for Patient-Friendly
Interpretation of Vietnamese Blood Test Results
**Authors:** Vo Hoang Khang, Truong Quang Dai

We thank both reviewers for comments that were specific enough to act on. Every change
below is in the revised manuscript, and the two re-analyses we report are reproducible
from the scripts and raw outputs in the supplementary archive. Page and section numbers
refer to the revised version.

---

## Reviewer 2

### R2.1 — "The baseline is confounded by formatting: 97.3% of baseline outputs used display names instead of canonical codes, so part of its 0.0% safe output may reflect format mismatch rather than content errors."

This was the comment we found most important, because the 0.0% figure carries much of the
paper's argument. We tested it directly rather than arguing from design.

Every baseline output was re-scored after mapping each returned analyte name back to its
canonical code through the alias table, which eliminates code-format errors completely
(1,253 names were remapped across the 150 panels). Results, now in Section 5 and Table 3:

| Metric | As scored | After removing all format errors |
|---|---|---|
| Safe output | 0.0% | **0.7%** |
| Direction mismatch | 91.3% | **92.7%** |
| False reassurance | 32.0% | 32.0% |
| Contradictory wording | 56.0% | 56.0% |
| Forbidden terms | 79.3% | 80.0% |
| Code-format errors | 97.3% | 0.0% |

Removing formatting entirely moves safe output from zero to one panel in 150. Direction
mismatch rises slightly, because items previously counted as fabricated analytes are now
resolved to a real analyte and judged on their stated direction. The baseline fails on
content, not on format. The re-scoring script is `src/cham_lai_bo_loi_dinh_dang.py`.

### R2.2 — "One stated contribution (the unit-normalisation failure) has no quantitative results in Section 5."

Correct, and now fixed. We added a deterministic experiment on the same 150 panels that
needs no model call: compare the labels produced with unit conversion against the labels a
system without conversion would produce. Results, now in Section 5:

- 143 of 2,118 analyte readings (6.8%) were reported in a unit of different magnitude.
- Without conversion, 135 of those 143 (94.4%) receive the wrong label.
- 97 of 150 panels (64.7%) contain at least one such error.
- All 135 are false alarms at the most severe level; none run in the safer direction.

Script: `src/thu_nghiem_don_vi.py`; output: `results/thu_nghiem_don_vi.json`.

### R2.3 — "The Constrained configuration bundles rule-assigned labels, prompt constraints, and the JSON schema, so RQ2 cannot separate their contributions, and a validator-only configuration is missing."

Accepted, and this drove the main new experiment. Three further configurations were run on
the same 150 panels with the same model and the same scoring code:

- **Labels only** — rule-assigned labels and the JSON schema, with the content prohibitions removed from the system prompt.
- **Constraints only** — content prohibitions and the JSON schema, with raw values and no labels.
- **Validator only** — the baseline prompt unchanged, plus Layer 4: validation, regeneration up to the retry limit, and template fallback.

Results, now in Table 3 of the revised paper (% of panels, except the last column):

| Configuration | Safe | Model text | Direction | False reass. | Forbidden | Time (s) |
|---|---|---|---|---|---|---|
| Baseline | 0.0 | 0.0 | 91.3 | 32.0 | 79.3 | 38.9 |
| Labels only | 38.7 | 38.7 | 14.0 | 10.7 | 46.0 | 38.4 |
| Constraints only | 0.0 | 0.0 | 87.3 | 43.3 | 35.3 | 27.0 |
| Validator only | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 95.5 |
| Constrained | 48.0 | 48.0 | 12.7 | 8.0 | 15.3 | 35.8 |
| Full | 100.0 | 64.0 | 0.0 | 0.0 | 0.0 | 68.3 |

The three mechanisms turn out to do different jobs, and only one of them fixes correctness:

1. **The labels carry the correctness gain.** Supplying them alone cuts direction mismatch
   from 91.3% to 14.0% and false reassurance from 32.0% to 10.7%, and produces 38.7% safe
   output where the baseline produces none.
2. **The prompt constraints do not improve correctness at all.** With no labels, direction
   mismatch stays at 87.3% and false reassurance *rises* to 43.3%, above the baseline's
   32.0%. Their one measurable effect is on vocabulary: forbidden terms fall from 79.3% to
   35.3%. Instructing the model to be careful makes it speak more cautiously, not more
   correctly — which is precisely the failure mode the paper argues against, and we now
   have a number for it.
3. **The validator can guarantee safety without labels, but only by discarding the output.**
   Validator-only reaches 100.0% safe, the same as the full pipeline, yet 0.0% of panels are
   served by model text: all 150 fall back to templates after a mean of 3 regeneration
   attempts, at 95.5 s per panel. The full pipeline reaches the same 100.0% with 64.0% model
   text and lower latency. Layer 4's contribution is therefore the guarantee; what the labels
   and constraints buy is the share of panels that keep a generated explanation.

This also answers the implicit question of what "Constrained" adds over "Labels only": 9.3
further points of safe output (38.7% → 48.0%) and a drop in forbidden terms from 46.0% to
15.3%, with direction mismatch and false reassurance only slightly improved. The ablation is
reproducible with `python src/run_experiment.py --config chi_nhan|chi_rang_buoc|chi_kiem_chung`;
the comparison table is built by `src/phan_tich_ablation.py` and stored in
`results/bang_ablation.json`.

One implementation note, reported for completeness: the constraints-only configuration
produced outputs whose JSON structure was valid but whose field types were not what the
validator expected, which raised exceptions during scoring. Rather than drop those panels we
added a wrapper that records them as a `malformed_structure` violation, so an unscoreable
output counts as unsafe rather than disappearing from the denominator.

### R2.4 — "Only Qwen2.5-3B is tested, yet the abstract and introduction speak of general-purpose language models that patients use, which are mostly much larger."

Accepted. We narrowed the claims rather than extrapolating. The abstract now states that
the results bound what a small on-premises model does, not what larger hosted services
would do, and the introduction no longer uses the single tested model as evidence about
general-purpose assistants. The motivating observation about patients pasting reports into
chatbots is retained as motivation, not as a measured result.

### R2.5 — "Patient-friendliness is not measured: no readability score, comprehension test, or human rating, and 36% of panels receive templates that are no better than the report."

Accepted, and we did not try to cover it with a proxy metric. The abstract and Section 6
now state that the evaluation establishes consistency with assigned labels only, and that
readability and comprehension remain unmeasured. The 36% template share is reported in the
abstract, in Section 5 and in Section 6 wherever the 100% figure appears.

### R2.6 — "Limited novelty: rules plus an LLM paraphraser plus a validator with template fallback is a well-known guardrail and data-to-text pattern, and the related work does not engage with that literature."

Accepted. Section 2 now places the architecture in that literature and states plainly that
it contributes nothing architecturally, citing NeMo Guardrails for programmable rails
around a model, Gatt and Krahmer for the separation of content selection from realisation,
Wiseman et al. for neural generators misstating facts present in their input, and Thomson
and Reiter for accuracy evaluation in data-to-text. The contribution is restated more
narrowly: false reassurance measured as its own class, the cost of the guarantee reported
alongside it, and a quantified failure of the deterministic layer under Vietnamese unit
conventions.

### R2.7 — "The severity factors (0.15–0.50) were set heuristically, so the claim that classification is exact by construction holds only relative to unvalidated thresholds."

Accepted. The sentence now reads that classification is exact with respect to the
configured intervals and severity factors, and explicitly not a claim that those thresholds
are clinically validated. We also added a per-analyte provenance table
(`data/nguon_khoang_tham_chieu.csv`) recording, for each of the 22 analytes, the reference
interval, its source, the severity factor, and its validation status. A companion table
(`data/tu_cam_nguon.csv`) records every forbidden-term pattern with the behaviour it
blocks and its basis, which is the scope of medical practice: diagnosis and prescription
are reserved to licensed practitioners under Vietnamese Law 15/2023/QH15, and EFLM advises
against diagnostic use of language models on laboratory results. Both tables are checked
against the running code by unit tests, so documentation and implementation cannot drift.

### R2.8 — "No sex- or age-specific intervals, which matter clinically for haemoglobin and haematocrit."

Accepted. Section 6 now states this as a separate limitation with its consequence: a
woman's result may be labelled abnormal against a male-derived interval. The provenance
table marks haemoglobin, haematocrit and red cell count as sex-dependent.

---

## Reviewer 1

[CHỜ ĐỌC FILE ĐÍNH KÈM — chưa tải được bản nhận xét chi tiết]

We thank Reviewer 1 for the assessment that the design is sound and that the paper does not
overstate clinical benefit. Detailed points from the attached review are addressed below.

---

## Summary of changes

| Change | Where |
|---|---|
| Format-normalised re-scoring of the baseline | Section 5, Table 3 |
| Quantitative unit-normalisation experiment | Section 5 |
| Ablation of labels, constraints and validator | Section 4.2, Section 5 |
| Claims narrowed to one small local model | Abstract, Section 1 |
| Patient-friendliness stated as unmeasured | Abstract, Section 6 |
| Related work engages guardrail and data-to-text literature | Section 2 |
| "Exact by construction" qualified | Section 3.2 |
| Sex- and age-specific intervals as a separate limitation | Section 6 |
| Provenance tables for intervals and forbidden terms | Supplementary archive |
