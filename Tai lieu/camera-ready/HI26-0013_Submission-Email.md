# Thư nộp bản camera-ready — HI26-0013

Gửi tới: **healthinfo@uit.edu.vn**
Cc: Võ Hoàng Khang (vh.khang@hutech.edu.vn)
Đính kèm: 7 file trong thư mục này (bỏ chính file hướng dẫn này ra)

> **Lưu ý trước khi gửi:** tên bài đã đổi theo yêu cầu của Phản biện 1. Thư dưới
> đây nói rõ việc đó ngay đoạn đầu, vì form camera-ready yêu cầu tên bài khớp
> với bài đã nộp. Đừng cắt đoạn đó đi.

---

**Subject:** HI26-0013 — Camera-ready submission (revised title, see note)

---

Dear HEALTHINFO IV Organising Committee,

Please find attached the camera-ready submission for paper **HI26-0013**
(Reference HI4-LOA-0013, Track B), together with our response to the reviewers.

**Please note a change of title.** Reviewer 1 asked us either to add a patient
comprehension study or to narrow the title, and we took the second option. The
title is now:

> **A Rule-Constrained Large Language Model Pipeline for Rule-Consistent
> Explanation of Vietnamese Complete Blood Count Results**

It was previously *"...for Patient-Friendly Interpretation of Vietnamese Blood
Test Results"*. The new wording follows the reviewer's own suggestion and
narrows the claim in two ways: we did not measure patient comprehension, and
our experiments cover complete blood count panels only. If the committee would
prefer us to keep the original title in the proceedings, we are happy to do so;
please let us know.

The author list and affiliations are unchanged from the submission form:

- Vo Hoang Khang (corresponding author), Vietnam-Korea Institute of Technology and Faculty of Information Technology, HUTECH University
- Truong Quang Dai, Vietnam-Korea Institute of Technology and Faculty of Information Technology, HUTECH University; FPT Telecom

**Attached files**

| File | Content |
|---|---|
| HI26-0013_Camera-Ready_Paper.pdf | Final paper, 11 pages, LNCS template |
| HI26-0013_Camera-Ready_Paper.docx | Editable source of the same paper |
| HI26-0013_Response-to-Reviewers.pdf | Point-by-point response, 12 points from Reviewer 1 and 8 from Reviewer 2 |
| HI26-0013_Supplementary-Appendices.pdf | Appendix A (benchmark and rule tables), B (validator specification), C (worked error examples) |
| HI26-0013_Supplementary-Code-and-Data.zip | Code, data, and the raw output of all runs |

The .docx versions of the response and the appendices are also attached in case
editable copies are useful.

**Summary of the revision**

Both reviewers asked for stronger evidence rather than different claims, and
the revision follows that. The main additions are:

- Four new configurations, giving seven in total, which separate the
  contributions of rule-assigned labels, prompt constraints, the validator and
  the regeneration loop. One of them is a template-only configuration that uses
  no language model at all.
- A second model, Qwen2.5-7B, on all three main configurations.
- Five repeated runs of one configuration, to separate decoding variability
  from the differences between configurations.
- Wilson confidence intervals on every proportion and McNemar tests for paired
  comparisons.
- A full specification of the validator, and provenance tables for every
  reference interval and forbidden term.

The 7B comparison turned out to be the most informative addition, because model
size moves safety in opposite directions depending on whether the rules are
present. Without them, the larger model is worse on the error that matters
most: it asserts that everything is normal on 46.7% of panels against 32.0% for
the 3B model. Given the same rule-assigned labels and prompt constraints, it is
much better: the validator-pass rate rises from 48.0% to 89.3% and false
reassurance falls to 1.3%. Capability alone does not make a patient-facing
explainer safer; it makes it a more fluent source of false reassurance.

Two other results weakened claims we had made, and we report them as such: a
deterministic template reaches the same validator-pass rate as the full
pipeline, and the prompt constraints do not improve that rate significantly
over rule-assigned labels alone. The metric is renamed from "safe output" to
"validator-pass rate" throughout, to avoid suggesting that it measures clinical
safety.

We also correct an error of our own. The submitted version described the test
machine as having no GPU. It has an NVIDIA GTX 1050 Ti, and we verified by
re-measurement that the 3B model is offloaded to it in full, so all reported
runtimes were obtained with GPU acceleration. Section 4.2 and Section 6.1 have
been corrected accordingly.

The paper is 11 pages, one page over the 10-page guideline. We would of course
shorten it if the committee requires the limit to be met; the material we would
remove first is the qualitative error analysis in Section 5, which Reviewer 1
requested.

We are grateful to both reviewers for the time they spent on this, and to the
committee for the opportunity to present at the conference.

Best regards,

Truong Quang Dai
on behalf of the authors
HUTECH University
