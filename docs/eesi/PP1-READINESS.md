# PP1 readiness review

Reviewed 2026-10-11 against the supplied PP1 mark sheet and EESI TAF scope.

Individual scoring evidence, a hand-worked example, and the proposed independent evaluation protocol are in [VALIDATION-PLAN.md](VALIDATION-PLAN.md). Calculation checks have been rerun: 48 tests passed. Empirical validation remains pending.

Verdict: implementation is ready for an EESI proof-of-concept demonstration. Full presentation readiness is conditional on the research-gap evidence, approved progress plan, slides and rehearsal, which were not provided for this review. No claim of excellent marks or an objectively measured 50% completion is made.

| Assessment area | Weight | Finding |
| --- | ---: | --- |
| Proven gap / creative solution | 10% | Working proof of concept exists. The literature-backed gap and novelty argument remain under-supported. |
| Specialized knowledge and technologies | 25% | Normalization, salary exposure, alternative aggregation, data preparation, FastAPI and React are implemented. Presenter must explain choices and assumptions. |
| Solution implementation | 40% | Core TAF operations work on real data. Requirements, architecture, tests and risks are documented. Completion relative to the approved project plan cannot be verified without that plan. |
| Effective communication | 15% | A demo sequence and examiner answers exist. Slides, allotted duration and rehearsal have not been assessed. |
| Commercialization / entrepreneurship | 10% | HR benefits are proposed. Stakeholder demand, willingness to pay and realized business benefits have not been evidenced. |

## Implementation evidence checked

- 48 backend tests pass, including existing Module 1 tests and EESI checks.
- TypeScript/Vite production build passes.
- 2,304 eligible real monthly salaried respondents from 17,771 LFS records.
- Economic input sources and visual table checks documented.
- Previous-month income assumption and quarterly unemployment mapping are explicit.
- Three candidate formulas, aggregate comparisons, controlled salary scenarios, and synthetic contribution breakdowns.
- Private microdata is excluded from Git; the real-data endpoint exposes aggregates.
- Calculation versions and separate normalization references prevent implicit comparison of synthetic and real scores.

## Before the presentation

1. Prepare a cited literature comparison: prior approach, inputs, validation, limitation, and your proposed contribution. Establish the gap from actual papers; do not claim that no existing system uses economic conditions without evidence.
2. Explain why the three candidates are being compared and why no winner is selected yet. The LKR 50,000 parameter and equal weighting are exploratory assumptions. OECD methodology does not endorse these specific choices.
3. Map completed and pending tasks to the actual approved project plan. Show dates and next milestones. The rubric's approximately 50% descriptor is not a fixed checklist of software features.
4. Include a specific independent-validation plan: target financial-stress measure, participants/recruitment, sample-size rationale, development/evaluation separation, metrics, uncertainty and sensitivity checks.
5. Show realistic user benefits and the intended HR research/analytics use. Label business potential as proposed unless supported by interviews or other evidence.
6. Rehearse the UI locally, capture a backup demo recording/screenshots, and confirm the presentation duration. No connected browser was available for visual/interaction verification during this review.

## Claims to defend accurately

Say: "I implemented and tested three exploratory EESI candidates using real Sri Lankan employee income records and official economic indicators. The current milestone establishes reproducible calculation and proof of concept. Independent validation and final formula selection are next."

Do not claim: a validated stress score, an accuracy percentage, proven prediction improvement, proven novelty, representative nationwide employee stress, or a completed integration pipeline.

The strongest likely examiner challenges are the arbitrary salary reference, inflation/CPI overlap, narrow normalization ranges, only twelve shared economic months despite thousands of respondents, income reference timing, and absence of an independent stress target. These limitations are acknowledged in REAL-DATA.md and should appear briefly in the presentation.
