# Individual EESI scoring: verification and validation plan

Status: calculation implemented and tested; independent empirical validation pending. No final formula has been selected.

## Evidence available for PP1

Each eligible individual receives three candidate scores from their salary and the economic indicators mapped to their income period. The synthetic employee view shows individual inputs and contributions; the real-data dashboard publishes aggregates of 2,304 individual calculations. Neither output is an observed financial-stress label.

The economic-only candidate is a baseline: individuals sharing a period receive the same value. Additive and interaction candidates incorporate individual salary. Employees with identical inputs also receive identical scores; the index does not model debt, dependants or household expenses.

Let I, C and U be the normalized inflation, price-index and unemployment values, and V = R/(R + salary). R is currently an exploratory LKR 50,000 monthly reference.

| Candidate | Formula | Purpose |
| --- | --- | --- |
| Economic baseline | 100 × (I + C + U)/3 | Comparison without salary |
| Additive | 100 × (I + C + U + V)/4 | Salary exposure contributes independently |
| Interaction | 100 × ((I + C + U)/3) × V | Salary exposure scales economic pressure |

Hand-worked example using the pilot reference: salary = R = 50,000; inflation = 32.6; CPI = 107.635; unemployment = 4.7. All four components equal 0.5. Expected scores are 50, 50 and 25 respectively. These results are covered by automated tests, as are contribution sums, input rejection, clipping, reproducibility and expected directional changes. See VERIFICATION.md and test-results.xml for executed checks.

## Independent validation protocol (proposed, not completed)

1. Agree the target construct with the supervisor: economic exposure is narrower than overall financial stress. Use an independently administered financial well-being questionnaire as convergent evidence, rather than relabeling EESI outputs as ground truth.
2. A candidate instrument is the CFPB Financial Well-Being Scale. Use its official questionnaire and scoring instructions, including age and administration requirements. It measures financial well-being; higher values are expected to associate with lower EESI. Its original development does not establish validity for Sri Lankan employees. Review language suitability, translation and comprehension locally before deployment.
3. Recruit consenting salaried employees across salary groups and, where feasible, multiple employers and collection periods. Collect pseudonymous study ID, relevant income period, gross monthly salary, questionnaire responses and scoring metadata. Keep research identifiers separate from HR identities. Collect optional household context separately for interpretation, not as an EESI-derived target.
4. Run a small comprehension pilot first. Determine the main sample size from the planned association, desired power/precision and employer/period clustering, with supervisor or statistical advice. Do not present an arbitrary respondent count as a sufficient validation sample.
5. Freeze candidate definitions, normalization bounds, data alignment and missing-data rules before evaluating. If any parameters are tuned, use a development sample and reserve an untouched evaluation sample. Separate employers or time periods where feasible; avoid leakage from repeated participants. Record any changes and version the formula.
6. Compare each candidate against questionnaire scores using Spearman rank correlation, with the expected negative direction. Report uncertainty and sample characteristics. Use paired comparisons on the same respondents; account for employer/period clustering where present. Financial well-being and EESI are different constructs, so equal 0–100 ranges do not justify MAE or an accuracy percentage.
7. Test sensitivity to the salary reference (for example 25,000, 50,000 and 75,000 LKR), indicator omission (especially inflation/CPI overlap), weights, bounds and consistent alternative price-index inputs. Report score and rank changes. These are robustness experiments, not independent validation.
8. Select a formula only if independent evidence and robustness support it. Consider uncertainty, interpretability and subgroup behaviour alongside association. If the evidence cannot distinguish candidates, report that result and retain provisional status rather than choosing the largest mean score.

A survey collected in one economic period mainly evaluates salary-related differences. It cannot establish that the macroeconomic part tracks changes over time. Historical 2024 LFS records cannot be paired with newly collected questionnaire responses as if they describe the same people and period.

## PP1 demonstration and wording

Show one synthetic employee's inputs, the hand-worked calculation and contribution breakdown. Change salary with economic inputs fixed. Then show the real-data coverage and aggregate comparisons, followed by the test evidence and this planned study.

Suggested statement: "Individual score generation is implemented and computationally tested. The three formulas remain provisional. Independent questionnaire-based evaluation, sensitivity analysis and final formula selection are the next research stage."

## Primary instrument references

- [CFPB scale guide, questionnaires and scoring materials](https://www.consumerfinance.gov/data-research/research-reports/financial-well-being-scale/)
- [CFPB scale development technical report](https://www.consumerfinance.gov/data-research/research-reports/financial-well-being-technical-report/)

These sources support the proposed instrument choice, not the current EESI weights, salary reference or a claim of local validity.
