# Response to Reviewers — HI26-0013

- **Paper:** A Rule-Constrained Large Language Model Pipeline for Rule-Consistent Explanation of Vietnamese Complete Blood Count Results
- **Previous title:** ...for Patient-Friendly Interpretation of Vietnamese Blood Test Results (changed at Reviewer 1's request, point 5)
- **Authors:** Vo Hoang Khang, Truong Quang Dai
- **Date:** 22 October 2026

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

Accepted twice over: we narrowed the claims *and* ran a larger model.

The abstract now states that the results bound what locally served open models do, and the
introduction no longer uses one tested model as evidence about general-purpose assistants.

We then ran **Qwen2.5-7B** on the same 150 panels, scored by the same code, for the baseline
and the full pipeline. The result supports the paper's argument rather than weakening it:

| | 3B | 7B |
|---|---|---|
| Baseline, validator pass | 0.0% | 0.0% |
| Baseline, false reassurance | 32.0% | **46.7%** (95% CI 38.9–54.6) |
| Baseline, fabricated analytes | 32.0% | **41.3%** |
| Baseline, direction mismatch | 91.3% | 76.0% |
| Baseline, forbidden terms | 79.3% | 61.3% |
| Baseline, omitted analytes | 71.3% | 57.3% |
| Full, validator pass | 100.0% | 100.0% |
| Full, model text | 64.0% | **96.0%** (91.5–98.2) |
| Full, attempts per panel | 1.97 | 1.16 |
| Full, seconds per panel | 68.3 | 161.5 |

A model more than twice the size is **not safer under unconstrained generation**: it
misstates directions and omits analytes less often, but it asserts that everything is normal
*more* often, and fabricates more. What it buys is inside the pipeline, where it cuts the
template share from 36.0% to 4.0%. Size therefore reduces what the guard rails have to throw
away; it does not remove the need for them.

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

We thank Reviewer 1 for a review detailed enough to act on point by point. Two of the twelve
points changed our reading of our own results, and we report both outcomes even where they
weaken the original claims. The title has been changed to the one the reviewer proposed.

### R1.1 (Critical) — "Safe output is defined entirely by an internal validator, so the 100% figure is self-referential."

Accepted without reservation, and this is the single largest change to the paper.

The metric is renamed throughout. "Safe output" is now **validator-pass rate**, defined in
Section 4.2 with the reason attached: the validator is both the filter and the measure, so a
high rate shows that nothing was returned that violates the implemented checks, not that the
output is clinically appropriate or comprehensible.

We then tested how little the metric distinguishes. A **template-only** configuration was
added, which prints the Layer 2 labels through the fixed template and never calls a model. It
passes on all 150 panels in 0.38 s for the whole benchmark, against 68.3 s per panel for the
full pipeline. McNemar's test on the paired panels cannot separate the two (p = 1.000), and
the same holds for validator-only. The paper now states this in Section 5 and in Section 6.2
rather than leaving it to be inferred: a pass rate defined by consistency with the rules is
maximised by output the rules wrote, and what the pipeline adds over the template is the
64.0% of panels that keep generated prose, whose readability we did not measure.

We did not arrange blind expert rating before the camera-ready deadline, and we do not claim
to have. Section 6.2 lists independent expert review and a patient comprehension study as the
first items of future work, and the conclusion no longer describes the result as safety.

### R1.2 (Critical) — "Monitor and seek care carry triage implications but rest on heuristic severity factors."

Accepted. Section 3.2 now states that the names denote deviation categories computed from the
configured intervals, not triage advice, and that mapping a deviation category to
patient-facing wording would require validation against a laboratory's critical-value policy
and clinician review before deployment. The same qualification appears in Section 6.2.

We also made the thresholds auditable rather than only disclaimed. `data/nguon_khoang_tham_chieu.csv`
records, for each of the 22 analytes, the reference interval, its source, the severity factor,
whether the interval is sex-dependent, and its validation status, which is "not checked
against literature" for every row. A unit test keeps the file in step with the running code.
Appendix A.3 reproduces the table.

### R1.3 (High) — "The synthetic generator is not described well enough to reproduce or to check for bias."

Accepted. Section 4.1 now gives the generator parameters and the distributions, and
**Appendix A** supplies the rest: the generator is `src/generate_data.py` with
`n_per_group=50`, `seed=42`, `borderline_rate=0.15`, so the benchmark regenerates exactly.
Appendix A reports the panel-label split (50/50/50), analytes per panel (10–18, mean 14.1,
2,118 readings), abnormal analytes per panel (0–4, mean 1.5), the high/low split (124/102),
the 46 panels with a borderline value, the per-analyte abnormality counts, the reference
interval and severity factor per analyte, the unit conversion factors, and the alias table.
`data/synthetic_panels.json` is supplied as generated.

We also state what the reviewer suspected. Appendix A notes that no reading lacks a unit and
no panel lacks an analyte name, because the generator emits structured panels only; Section
6.2 carries this as a limitation rather than a footnote.

### R1.4 (High) — "The baseline is weak; at least five stronger baselines and ablations are needed."

Accepted. The paper now compares **seven** configurations on the same 150 panels, covering
four of the five the reviewer listed:

| Configuration | Validator pass | Model text | Direction | False reass. | Forbidden | Time (s) |
|---|---|---|---|---|---|---|
| Baseline (raw LLM) | 0.0 | 0.0 | 91.3 | 32.0 | 79.3 | 38.9 |
| Template only (rules, no model) | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.003 |
| Labels only | 38.7 | 38.7 | 14.0 | 10.7 | 46.0 | 38.4 |
| Constraints only (schema, no labels) | 0.0 | 0.0 | 87.3 | 43.3 | 35.3 | 27.0 |
| Validator only | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 95.5 |
| Constrained (labels + constraints) | 48.0 | 48.0 | 12.7 | 8.0 | 15.3 | 35.8 |
| Full, no retry | 100.0 | 46.0 | 0.0 | 0.0 | 0.0 | 35.2 |
| Full | 100.0 | 64.0 | 0.0 | 0.0 | 0.0 | 68.3 |

This separates what was previously bundled:

- **Labels carry the correctness gain.** Alone they cut direction mismatch from 91.3% to 14.0% and false reassurance from 32.0% to 10.7%.
- **Prompt constraints do not improve correctness.** Without labels, direction mismatch stays at 87.3% and false reassurance *rises* to 43.3%, above the baseline. Their measurable effect is on vocabulary (forbidden terms 79.3% → 35.3%). Added on top of labels they raise the pass rate from 38.7% to 48.0%, which does not reach significance on 150 panels (McNemar, p = 0.082).
- **The validator supplies the pass, not the quality.** Validator-only reaches 100.0% with 0.0% model text: all 150 panels fall back to templates after a mean of 3 attempts.
- **Regeneration buys model text, not safety.** Full without retry reaches the same 100.0% with 46.0% model text at 35.2 s; retry raises that to 64.0% at 68.3 s.

The fifth item, a larger model, has now been run as well: Qwen2.5-7B on the baseline and the
full pipeline, reported under R2.4 above and in Section 5. It raises unconstrained false
reassurance from 32.0% to 46.7% while cutting the template share from 36.0% to 4.0%.

### R1.5 (High) — "Patient comprehension is not evaluated, so the patient-friendly claim is unsupported; otherwise change the title."

Accepted, and we took the reviewer's second option because we could not run a comprehension
study before the deadline and did not want to keep a claim we had not measured. The title is
now:

> **A Rule-Constrained Large Language Model Pipeline for Rule-Consistent Explanation of Vietnamese Complete Blood Count Results**

This follows the reviewer's own wording and narrows the scope twice over: *rule-consistent
explanation* instead of *patient-friendly interpretation*, and *complete blood count* instead
of *blood test*, which also answers R1.8. The abstract, introduction and conclusion were
rewritten to match, and Section 6.2 states that readability, comprehension, perceived anxiety
and actionability were not measured.

### R1.6 (High) — "No confidence intervals, no repeated runs, no decoding parameters."

Addressed on all three counts.

Every proportion in Sections 4 and 5 now carries a **95% Wilson confidence interval**, chosen
over Wald because several rates are 0% or 100%, where Wald gives a zero-width interval.
Configurations are compared with **McNemar's test**, the paired test this design calls for,
since all configurations see the same 150 panels. Two of those comparisons changed what we
could claim: constraints over labels is not significant (p = 0.082), and template-only against
full is indistinguishable (p = 1.000).

Decoding parameters are now in Section 4.2: Ollama, Q4_K_M quantisation, temperature 0.2,
2,048-token limit, JSON output mode, no fixed seed.

**Repeated runs** were carried out for the constrained configuration, five times on the same
panels. We chose that configuration because its pass rate is neither 0% nor 100% and therefore
has room to vary; repeating a configuration pinned at 100% by construction would measure
little on the same hours of compute.

| | mean | SD | range |
|---|---|---|---|
| Validator pass | 50.3% | 2.4 | 48.0–53.3 |
| False reassurance | 10.1% | 1.6 | 8.0–12.0 |
| Direction mismatch | 11.9% | 0.6 | 11.3–12.7 |
| Forbidden terms | 16.4% | 2.5 | 13.3–19.3 |
| Omitted analytes | 23.6% | 3.1 | 20.7–28.7 |
| Seconds per panel | 33.9 | 1.1 | 33.2–35.8 |

The single run reported in Table 2 (48.0%) sits at the low end of ordinary variation, and no
per-class rate moves by more than about three points. The more interesting result is at the
panel level: across the five runs only **31 of 150 panels pass every time and 37 fail every
time, while 82 (54.7%) pass in some runs and fail in others**. Aggregate rates on 150 panels
are reproducible to within a few points, but an individual explanation is not reproducible at
all. We read this as an argument for checking every output rather than for trusting a
configuration that scored well once, and Section 5 now says so.

Scripts: `src/thong_ke_tin_cay.py` and `src/phan_tich_7b_va_lap.py`.

### R1.7 (High) — "The validator is not specified well enough to audit."

Accepted. **Appendix B** now specifies it in full: the algorithm in pseudo-code, the
normalisation applied before matching (accent stripping and reference-phrase masking, with
the comparator rule that governs the masking), the complete pattern tables for status words,
false reassurance and forbidden terms, and a section on what the checks cannot see. The
appendix is generated from the running code by `src/dung_phu_luc.py`, so it cannot drift from
the implementation.

On precision and recall we report what we have rather than an estimate we cannot support.
Appendix B.5 documents a **systematic false positive we found while preparing this response**:
the contradictory-wording check masks interval-naming phrases only when a comparator precedes
them, so a sentence that quotes the interval as a fact is read as a status claim. A pattern
scan identifies 50 of the 206 flagged sentences in the baseline log (24.3%) as candidates for
this mistake. We left the behaviour unchanged, because retuning the validator after seeing
the results would invalidate comparisons already scored with it, and we state the direction of
the bias: it inflates the fallback rate and understates the model, and does not inflate the
pass rate. Section 6.2 now carries this. A proper precision and recall estimate needs
human-annotated statements and is listed as future work.

### R1.8 (High) — "Scope is wider than the experiments: real reports are not structured CBC panels."

Accepted. The title now says complete blood count, the abstract and Section 6.2 state that
only structured CBC panels are supported, and the introduction no longer generalises from one
local model to hosted assistants. Parsing, OCR, missing reference intervals, multi-panel
reports and age- or sex-specific intervals are named as untested.

### R1.9 (Medium) — "Runtime analysis is insufficient for deployment."

Addressed from the existing logs, and in the course of doing so we found and corrected an
error of our own. The submitted version described the test machine as "an Intel Core i5-9400F
with 24 GB RAM and no GPU", and Section 6.1 argued that the pipeline "avoids GPU cost for
provincial hospitals". That was wrong. The machine has an **NVIDIA GTX 1050 Ti with 4 GB**, and
we verified by re-measurement that Qwen2.5-3B at Q4_K_M occupies about 3 GB and is offloaded to
the card **in full**, at 100% GPU utilisation. Every 3B timing in the paper was obtained with
GPU acceleration. Section 4.2 now states the actual hardware and the offload split, and Section
6.1 now argues from a consumer graphics card released in 2016 rather than from no card at all.
The 7B model does not fit in 4 GB and runs roughly half on the card, which is why it is 2.4
times slower rather than 2.3 times as its parameter count would suggest.

Section 5 now reports, for the full pipeline, 68.3 s per
panel with SD 33.7 and p50/p95/p99 of 66.4/121.5/134.1 s, against a baseline mean of 38.9 s
(p95 63.6), and Section 6.1 quotes the 95th percentile rather than the mean alone. Per-panel
attempts are 1.97 on average.

We also answer where the cost goes. Re-scoring the outputs Layer 4 rejected shows that of the
54 panels ending in a template, 66.7% had omitted an analyte, 38.9% contained a forbidden
term, 29.6% misstated a direction and 18.5% falsely reassured. Omission, not vocabulary, is
what regeneration is mostly fighting.

Peak memory, token counts and concurrency behaviour are not reported; we did not instrument
them during the runs and did not want to quote figures from a later, differently loaded
machine.

### R1.10 (Medium) — "No qualitative error analysis."

Accepted. Section 5 now carries a paragraph of real instances, and **Appendix C** tabulates
one worked example per error class with the panel, the rule label, the analyte, the generated
text and the reason Layer 4 rejected it. Every example is taken from the stored run logs; none
is constructed. The false-reassurance example is the one the reviewer would expect: on a
monitor panel, the baseline closing statement opens *"Tất cả các chỉ số đều nằm trong khoảng
bình thường"* and then names two abnormal analytes.

### R1.11 (Medium) — "Related work does not position the contribution precisely enough."

Accepted. Section 2 now engages the guardrail and data-to-text literature directly, citing
NeMo Guardrails for programmable rails, Gatt and Krahmer for the separation of content
selection from realisation, Wiseman et al. for neural generators misstating facts present in
their input, and Thomson and Reiter for accuracy evaluation in data-to-text, and states
plainly that the architecture contributes nothing new. The contribution paragraph is rewritten
around the three gaps the reviewer identified: clinical judgement externalised from the model,
semantic validation distinguished from structural validation, and false reassurance measured
separately.

### R1.12 (Medium) — "Absolute claims should be softened."

Accepted. "Produced no unsafe output" is now "left no output that violated the implemented
checks"; "the pipeline never returns unverified text" is "no unvalidated model text is
returned"; "the guarantee supplied by Layer 4" is "what Layer 4 enforces". The word guarantee
no longer appears in the paper. The conclusion now states that the result should be read as
rule consistency under the implemented checks and not as clinical safety.

### Priority checklist

| # | Reviewer 1's item | Status |
|---|---|---|
| 1 | Rename safe output | Done — validator-pass rate throughout |
| 2 | Publish generator, analytes, units, intervals, factors, seed | Done — Section 4.1 and Appendix A |
| 3 | Template-only / rules-only baseline | Done — new configuration, and it ties with Full |
| 4 | Ablate labels, schema, constraints, retry, fallback | Done — seven configurations plus a 7B run, Table 3 |
| 5 | Confidence intervals, repeated runs, decoding parameters | Done — CIs, McNemar, parameters, and five repeated runs of the constrained configuration |
| 6 | Validator pseudo-code and pattern tables | Done — Appendix B, generated from the code |
| 7 | Error-analysis table with examples | Done — Section 5 and Appendix C |
| 8 | Reduce claims from clinical safety to rule consistency | Done — title, abstract, Section 5, Section 6, conclusion |
| 9 | Human comprehension or clinician review, else retitle | Retitled, as the reviewer proposed; the study is named as future work |

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
| Title narrowed to rule-consistent explanation of CBC | Title, Abstract, Section 1, Section 7 |
| Metric renamed to validator-pass rate, with the reason | Section 4.2 and throughout |
| Template-only and no-retry configurations | Section 4.1, Section 5, Table 3 |
| Wilson confidence intervals and McNemar tests | Sections 4.2, 5 |
| Decoding parameters and quantisation | Section 4.2 |
| Latency percentiles and regeneration failure reasons | Section 5, Section 6.1 |
| Qualitative error instances | Section 5, Appendix C |
| Benchmark distributions, seed and rule tables | Section 4.1, Appendix A |
| Validator algorithm and pattern tables | Appendix B |
| Validator false-positive mode disclosed | Section 6.2, Appendix B.5 |
| Absolute wording removed | Sections 3.2, 5, 6, 7 |
| Provenance tables for intervals and forbidden terms | Supplementary archive |
