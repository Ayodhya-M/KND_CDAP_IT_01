# EESI: Progress Presentation 1

## Real-data milestone

The demo now includes 2,304 real monthly salaried employees from LFS 2024, matched to official economic indicators for the preceding income month. **Real Sri Lankan data** opens by default; **Synthetic pilot / worked examples** retains the original explanation workflow. See [REAL-DATA.md](REAL-DATA.md) for cohort selection, period alignment, normalization, sources and limits. Real records remain private and the UI exposes aggregates only. Empirical accuracy remains unestablished.

## Assessment interpretation and scope

The supplied PP1 mark sheet allocates 10% to gap/proof of concept, 25% to specialized knowledge and technology, 40% to implementation, 15% to communication, and 10% to business potential. The excellent completion descriptor says approximately 50% where applicable, judged against the project plan. This document maps evidence to those criteria; it does not claim an objectively measured 50% completion or guarantee marks.

The EESI TAF tasks are normalization, relating economic conditions to employee salary, and producing employee economic stress scores. This milestone implements those operations as exploratory candidate formulas. Final formula selection and empirical validation remain research work.

## Run the demonstration

From the repository root, using the existing environment or after the README setup:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

In another terminal:

```powershell
cd frontend
npm.cmd run dev
```

Open the Vite address and select **EESI prototype** in the sidebar. The EESI endpoints need no Supabase credentials, uploads, or Module 1 completion. Other module screens retain their existing dependencies.

Offline calculation evidence:

```powershell
python scripts/export_eesi_evidence.py
```

Tests and build:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
```

```powershell
cd frontend
npm.cmd run build
```

## Demo sequence (approximately five minutes)

1. Explain the problem: economic conditions are shared, but salary may change employee exposure. This is the hypothesis being tested, not an established causal finding.
2. Show 100 pilot employee calculations matched to six observation months. State that HR records are synthetic and economic values are supplied pilot data, not independently verified official data.
3. Compare the three candidate formulas. Explain that an economic-only baseline cannot distinguish employees with different salaries in the same month.
4. Select an employee and explain normalized components and the contribution bars.
5. Run the default midpoint: salary 50,000; inflation 32.6; CPI 107.635; unemployment 4.7. The three scores are 50, 50, and 25.
6. Change salary to 25,000 and then 100,000, holding the economy fixed. The baseline stays unchanged while the salary candidates decrease with higher income.
7. Change inflation alone. Show how all candidate scores respond. Enter an out-of-reference inflation value and show the clipping warning.
8. Download evidence; show the test report and explain that these demonstrate reproducibility and calculation correctness, not accuracy against real employee stress.

## Formula specification and rationale

Version: `pp1-exploratory-v1`. Scores use a proposed 0-100 presentation scale. They are neither probabilities nor validated stress categories.

For each economic indicator, `N(x) = clip((x - L) / (H - L), 0, 1)`. Frozen pilot bounds are inflation 12-53.2%, CPI 100-115.27, and unemployment 4.6-4.8%. `I`, `C`, and `U` denote their normalized values.

Salary exposure is `V = R / (R + salary)` where `R = LKR 50,000/month` by default. This is a bounded, smooth, decreasing proposed income adjustment. At salary R, V is 0.5. R is an illustrative scale parameter, not a living wage, household expense estimate, or empirically fitted coefficient. Both salary inputs must be positive finite numbers and must use the same currency and period.

| Candidate | Formula | Research question / limitation |
| --- | --- | --- |
| Economic baseline | `100 * (I+C+U)/3` | Transparent equal-weight comparator; ignores income |
| Additive salary exposure | `100 * (I+C+U+V)/4` | Does a separate salary component help? Allows compensation between components |
| Salary interaction | `100 * ((I+C+U)/3) * V` | Does income moderate pressure? Returns zero at economic reference minima, even for low salaries |

These are competing hypotheses. None has been selected as the final formula. Equal weighting avoids claiming unsupported importance estimates; it is itself an assumption, not evidence that inputs are equally important. The additive candidate changes the economic share to 75%; comparisons test both structure and this weighting consequence.

Inflation and CPI follow the TAF's purchasing-power/cost-of-living channels, but price level and price change can overlap. Positive unemployment direction is a proposed economic insecurity channel; unemployment can have a different relation to turnover. More literature and validation are needed for this sign. Narrow unemployment bounds amplify small changes. Pilot normalization must be replaced or justified using a suitable reference population/period for deployment. Constant-reference ranges would require an explicit policy before using a new configuration.

The [OECD/JRC composite indicator handbook](https://www.oecd.org/en/publications/handbook-on-constructing-composite-indicators-methodology-and-user-guide_9789264043466-en.html) is a methodological source for index construction, including normalization, weighting, and robustness analysis. It does **not** validate these EESI formulas or the chosen salary parameter.

The [CFPB Financial Well-Being Scale guide](https://www.consumerfinance.gov/data-research/research-reports/financial-well-being-scale/) provides a potential independent survey measure. Suitability, cultural/language adaptation, scoring instructions, and local validation must be assessed. Financial well-being and economic stress are related constructs, not interchangeable labels.

## Architecture and integration contract

`pilot CSV adapter -> validated numeric inputs -> frozen normalization -> candidate calculations -> contributions/results -> API -> React demo`

- `GET /api/v1/eesi/metadata`: formula definitions, parameters, limitations, version.
- `GET /api/v1/eesi/pilot`: supplied pilot data, employee scores, rejected records, summaries.
- `POST /api/v1/eesi/scenario`: salary, inflation, CPI, unemployment, optional reference_salary; returns all candidate scores and contributions.

Future Module 1 input: employee identifier, monthly salary in LKR, observation month, matched economic indicators with source and units. The pilot adapter uses ObservationDate and ignores Attrition and all turnover outcomes. Future Module 3 output: employee identifier/month, selected EESI, formula version, normalization version. Agree the integration contract before replacing the adapter.

## Requirements demonstrated

| Requirement | Evidence |
| --- | --- |
| Compute economic stress candidates without waiting for Module 1 | Pure calculation service and local pilot adapter |
| Normalize heterogeneous economic inputs | Frozen ranges exposed through metadata and screen |
| Incorporate employee salary | Additive and interaction candidates; scenario comparison |
| Explain score generation | Formula definitions, raw inputs, normalized components, point contributions |
| Compare alternative formulas | Same employees/inputs, three columns and scenario results |
| Reject invalid inputs | API schema constraints and service finite-number checks |
| Reproduce calculations | Versioned service, JSON export, hand-worked midpoint test |

User: HR analyst/researcher exploring workforce economic exposure. This screen supports comparisons and explanations. It does not authorize individual HR decisions based on unvalidated scores.

## PP1 evidence mapping

| Criterion | What to show | What is still needed |
| --- | --- | --- |
| Problem and proof of concept | Baseline versus salary candidates for employees in the same economy | Literature evidence establishing the broader research gap |
| Specialized knowledge and technology | Feature normalization, bounded exposure, aggregation; Python, FastAPI, React/TypeScript | Explain your own choices and limitations during Q&A |
| Design and completion | Independent service/API/UI, documented module boundary | Align completed tasks with your actual approved project schedule |
| Best practices | Determinism, input validation, version metadata, outcome exclusion, tests | Empirical and security review before deployment |
| Requirements | Requirements table and working demo | Confirm requirements with stakeholders |
| Risk mitigation | Risk table below and staged validation plan | Execute data collection and validation |
| Communication | Demo sequence, formula comparison, worked example | Rehearse and fit the allotted presentation duration |
| Business potential | Proposed benefit: explain economic context and compare exposure across staff | Stakeholder interviews; no claimed ROI or market validation |

## Risks and remaining work

| Risk | Mitigation implemented / planned |
| --- | --- |
| Module 1 delay or unavailable database | Implemented: isolated service and pilot adapter |
| Unsupported accuracy claims | Implemented: prototype labels, no stress categories or accuracy percentages |
| Synthetic data mistaken for validation | Implemented: explicit data provenance limitations |
| Arbitrary reference salary and weights | Implemented: exposed assumptions; planned: sensitivity and independent comparison |
| Inflation/CPI redundancy | Planned: remove one at a time and compare results |
| Narrow reference ranges and clipping | Implemented: visible bounds/warnings; planned: wider justified reference period |
| Missing household context | Planned: assess debt, dependents, expenses and income measurement using survey design |
| Outcome leakage and overfitting | Implemented: no Attrition input; planned: choose/tune using development data only |
| Privacy and inappropriate HR use | Current demo uses synthetic HR data; planned: consent, minimization, access controls and reviewed use |

After PP1: select an independent survey instrument and analysis protocol; collect appropriate data; compare candidates on held-out employees and preferably periods; assess correlation with stress or inverse well-being, uncertainty, subgroup behaviour, normalization/weight sensitivity and indicator ablation; select and version the formula based on that evidence. Coordinate HR-only versus HR+EESI prediction comparisons with Module 3. Do not manufacture survey labels from a candidate formula and then claim validation against them.

## Answers to likely examiner questions

- **Why this formula?** Three explicit hypotheses are implemented for comparison. Final selection awaits independent evidence; the midpoint and behavioural tests establish correctness only.
- **How accurate is it?** Empirical accuracy is not established. The present evidence is deterministic calculation, expected controlled behaviour, and complete pilot processing.
- **Why 50,000?** An illustrative monthly-LKR scale parameter, exposed for scenario testing; it must be justified or calibrated later.
- **Why not train weights now?** There are no independent stress labels in the pilot. Learning from synthetic outcomes would not establish stress validity.
- **Is this 50% complete?** The core normalization, salary linkage, score generation, API and demonstration are implemented; validation, final selection, persistence and integration remain. Completion percentage must be assessed against the actual project plan.
