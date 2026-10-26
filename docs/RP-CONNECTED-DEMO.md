# Connected retention recommendation progress demo

In **Retention Strategies**, choose **Connected synthetic pilot** (default),
select `module1_hr_pilot_300_employees.csv`, enter `PILOT-0001`, and analyze.
Dataset labels include row counts so older 100-person versions remain distinct.

The flow is:

1. Read the selected Module 1 employee and its mapped observation-month economic
   indicators from Supabase. Matching records and economic mappings must exist.
2. Calculate Module 2 EESI using the saved model's selected formula and the 2023
   synthetic pilot reference profile.
3. Run the saved Module 3 classifier, verifying EESI formula/version and feature
   contracts. The local model must be the 300-row synthetic demo. A source-record
   comparison rejects unrelated employees and differing historical versions.
4. Probe overtime off, job satisfaction 4 (when currently 1/2), and salary +10%.
   Each probe changes one model input, holding all others, including EESI, fixed.
   A positive baseline-minus-probe probability difference supplies an actionable
   sensitivity. Age, gender and other protected or nonactionable attributes do
   not generate retention suggestions. Empty recommendations are valid when no
   supported positive sensitivity is present.
5. Rank existing prototype actions with their configurable weights. The economic
   component uses continuous EESI/100; it does not invent economic-pressure bands.

Risk remains **Unclassified (synthetic demo)**. Sensitivities are displayed in
percentage points and are not additive decompositions, SHAP values or causal
intervention effects. Priority levels are existing prototype recommendation
rankings, not scientifically validated employee-risk classifications.

The what-if simulator recalculates both EESI and prediction for the temporary
employee, reruns sensitivity probes, and compares recommendations. Its probability
difference is in percentage points. No employee, economic, model or recommendation
record is written. Work-life balance is not in this saved model's feature contract
and does not directly change its probability.

HIES household data remain separate; they have no attrition labels or verified
identity relationship with these synthetic employees. This integration does not
claim real-world turnover validity or retention effectiveness.

API: add `demo=true` to the existing recommendations and simulation endpoints,
with the selected `upload_id`. Without this query parameter, existing configured
mock/real provider behavior remains unchanged. Missing models, wrong source
versions or incomplete mappings fail clearly without silently falling back to
mock values. No environment credentials or provider defaults were changed.

The saved artifacts are local under `artifacts/module3_synthetic`. If another
machine lacks them, prepare the synthetic Module 3 model there before the demo.
