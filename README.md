# Employee Retention and Turnover Prediction System Using Macroeconomic Factors

**Retention Intelligence**
Research project: **KND_CDAP_IT_01**

## Project vision

Retention Intelligence is a planned decision-support system that combines
employee information with macroeconomic conditions to help organisations
understand turnover risk and plan appropriate retention actions.

The system will bring four connected functions into one platform: data
integration, employee economic exposure analysis, turnover prediction and
retention strategy support. It will help HR teams move from disconnected
spreadsheets to traceable analysis of employee circumstances and the wider
economy.

This README describes the intended final deliverable and the plan for achieving
it. Features, research decisions and acceptance criteria below are planned
requirements, not claims that they have already been completed or validated.

## Problem the system will address

Employee turnover can disrupt operations, increase recruitment and training
costs, and reduce organisational knowledge. HR records describe workplace
conditions, but external economic conditions can also affect employees' financial
circumstances and employment decisions.

Inflation, changing prices and labour-market conditions may affect employees
differently depending on income and financial commitments. The project will
investigate whether incorporating this context provides useful information
beyond HR attributes alone. It will not assume that an economic indicator causes
turnover or that a calculated index measures actual stress without validation.

## Objectives

1. Create a reliable pipeline for importing and integrating approved HR and
   macroeconomic data.
2. Develop and evaluate an Employee Economic Stress Index (EESI) that represents
   proposed economic exposure at employee level.
3. Build and evaluate turnover prediction models using HR information, then
   investigate the additional value of EESI.
4. Provide explainable, prioritised retention options that HR users can review
   alongside model evidence and employee context.
5. Support reproducible analysis through data provenance, versioned calculations,
   model metadata, validation records and downloadable reports.
6. Protect employee information and keep consequential decisions under human
   review.

## Intended users

| User | Main responsibilities |
| --- | --- |
| HR analyst | Prepare datasets, inspect quality, calculate EESI, review predictions and compare scenarios |
| HR manager | Review workforce summaries and prioritised retention options; decide which actions deserve follow-up |
| Authorised researcher | Evaluate formulas and models, inspect evidence and compare alternative approaches |
| System administrator | Manage approved access, configuration and operational maintenance |

Access to employee-level information will be limited according to role and
organisational requirements. The platform will support HR judgement rather than
automatically making employment decisions.

## End-to-end user journey

1. **Sign in:** access an authorised organisational workspace.
2. **Import data:** upload HR records and economic indicators with clear units,
   periods, source definitions and permitted uses.
3. **Review data quality:** inspect missing fields, duplicates, invalid values
   and incompatible formats; approve or resolve identified issues.
4. **Align economic context:** associate employee observations with the relevant
   economic period using a documented temporal-mapping policy.
5. **Generate integrated records:** create a validated, traceable dataset for
   economic analysis and prediction.
6. **Explore EESI:** view employee scores, formula inputs, contribution breakdowns
   and appropriate group summaries.
7. **Review turnover predictions:** inspect the predicted outcome, probability,
   model version and supported explanations.
8. **Compare scenarios:** explore conditional changes to supported inputs without
   modifying the original employee records.
9. **Review retention options:** inspect suggested actions, reasons, priorities
   and assumptions before deciding on follow-up.
10. **Export evidence:** download authorised summaries and reports with their
    source, formula and model versions.

## System architecture

```text
Approved HR data                 Macroeconomic reference data
       |                                      |
       +------------------+-------------------+
                          v
           Module 1: Data Management and Integration
           Validation, cleaning and temporal alignment
                          |
                          v
           Module 2: Employee Economic Stress Index
           Versioned economic exposure calculation
                          |
                 HR features + EESI
                          v
           Module 3: Turnover Prediction
           Evaluated model and supported explanations
                          |
          Employee context + EESI + model prediction
                          v
           Module 4: Retention Strategy Support
           Prioritised options and scenario comparisons
                          |
                          v
                 Human-led HR review
```

A shared web interface will connect these modules through a backend API.
Organisational data, model artifacts and research datasets will retain separate
identities and access rules. Survey respondents and synthetic examples will not
be joined to organisational employees without a valid identity relationship.

## Module 1: Data Management and Integration

### Purpose

Turn authorised HR and macroeconomic inputs into consistent, analysis-ready
records while retaining evidence of their origin and transformations.

### Planned capabilities

- Import supported CSV and Excel datasets with schema and file validation.
- Map source columns to documented internal fields.
- Validate identifiers, dates, units, categories and numerical ranges.
- Identify missing values, duplicates and inconsistent records.
- Provide explicit cleaning policies and retain an audit of transformations.
- Maintain dataset versions and report accepted and rejected records.
- Align economic information to the appropriate employee observation period.
- Distinguish observation dates, income reference periods and economic
  publication dates where available.
- Generate integrated datasets and downloadable validation reports.

### Inputs and outputs

**Inputs:** employee identifiers, observation dates, approved HR attributes,
salary information, available financial fields and sourced economic indicators.

**Outputs:** validated employee/economic records, quality flags, source metadata,
cleaning history and integration versions.

### Acceptance criteria

Invalid records must be rejected or flagged with clear reasons. Missing values
must follow an explicit policy. Repeating the same processing configuration
should reproduce the same output. Downstream modules must be able to identify
the dataset version and economic period used for each result.

## Module 2: Employee Economic Stress Index

### Purpose

Investigate a transparent way to represent employees' economic exposure using
economic conditions and supported salary or financial information.

### Planned capabilities

- Normalise economic indicators using documented, versioned reference ranges.
- Compare candidate formulas before selecting a final research-supported index.
- Display employee scores, relevant group summaries and calculation breakdowns.
- Show input availability, clipping warnings and formula assumptions.
- Support controlled what-if calculations without changing saved records.
- Export score evidence with formula, normalisation and source versions.
- Supply the selected EESI to Module 3 under an explicit integration contract.

### Candidate formula families

These equations are proposed research candidates. The final selection and
parameter choices will depend on independent validation and sensitivity analysis.

| Family | Basic candidate | Extended candidate |
| --- | --- | --- |
| A - Economic Baseline | `100 * (I+C+U)/3` | Not applicable |
| B - Additive Financial Exposure | `100 * (I+C+U+V)/4` | `100 * (I+C+U+V+F)/5` |
| C - Financial Interaction | `100 * ((I+C+U)/3) * V` | `100 * ((I+C+U)/3) * ((V+F)/2)` |
| D - Real-Wage / Purchasing Power | `100 * (alpha*G + (1-alpha)*U_D)` | Not applicable |

Definitions:

```text
I, C, U = normalised inflation, CPI and unemployment
Normalisation = clip((value - lower)/(upper - lower), 0, 1)
V = R/(R+S)
S = monthly base salary
R = documented salary reference

T = monthly base salary + monthly allowances
M = household expenses + monthly debt repayments
F_raw = M/T, when T > 0
F = min(1, F_raw)

RW = 100*S/CPI
G = clip((Z-RW)/Z, 0, 1)
Z = reference income expressed in the same purchasing-power units as RW
U_D = unemployment normalised for the relevant Formula D reference profile
```

The default illustrative alpha is 0.5. Annual bonuses are excluded from the
financial extension unless a separately justified future specification is agreed.
Expenses and debt may only be added when their definitions establish that debt
is not already included. A synthetic-data assumption must never silently become
a real-data rule. Raw and capped burden will both be visible.

Extended formulas will be unavailable when required financial fields or
compatible definitions are missing. Formula D will remain restricted to its
supported HIES research context unless a separate extension is explicitly
specified and evaluated.

### Research and acceptance criteria

The project will examine equal weighting, CPI/inflation overlap, salary entering
both V and F, capping effects, and the mismatch between household commitments
and individual income. Suitable independent financial-stress or well-being
measurements will be used to assess validity; generating labels from the same
formula will not count as validation.

Scores must be finite, reproducible and within their specified range. Their
interpretation must distinguish economic exposure from diagnosed stress and
turnover probability. The selected formula must be versioned before it is used
for model training or inference.

## Module 3: Turnover Prediction

### Purpose

Estimate a clearly defined employee turnover outcome and evaluate whether
including economic exposure adds useful predictive information.

### Planned capabilities

- Define the prediction target and time horizon before training.
- Select approved predictors and prevent identifiers, future information or
  outcome-related fields from leaking into model inputs.
- Fit preprocessing on training data only.
- Establish a transparent baseline, then compare justified alternatives.
- Compare HR-only models with HR-plus-EESI models using comparable splits.
- Evaluate on held-out data, with temporal evaluation where suitable.
- Report class probabilities, confusion matrices, precision, recall, F1 and
  ROC-AUC where applicable; assess calibration and imbalance where relevant.
- Provide model-supported explanations and clearly identify their method.
- Store feature contracts, target meaning, class labels and model versions.
- Return a clear unavailable result when required inputs or a compatible model
  are missing.

### Inputs and outputs

**Inputs:** validated HR features and, for an EESI-enabled model, the exact
formula/version used during training.

**Outputs:** predicted class, class probabilities, supported explanatory factors,
model metadata and evaluation evidence.

### Acceptance criteria

Training and inference must use compatible features and EESI definitions. A
formula display change must not silently alter predictions. A change to the
selected EESI requires an explicit model update and re-evaluation. Intention to
leave and observed attrition must be treated as different targets. Risk bands
must not be presented as validated without evidence supporting their thresholds.

## Module 4: Retention Strategy Support

### Purpose

Help HR users review relevant retention options using employee context, economic
exposure and prediction evidence.

### Planned capabilities

- Combine compatible Module 1, 2 and 3 outputs for the same employee and period.
- Identify supported, actionable factors rather than treating every predictor
  as something HR should intervene on.
- Generate retention options using documented rules and model evidence.
- Rank options using explicit priority criteria and explain the ranking.
- Compare supported salary, workload or workplace-condition scenarios.
- Recalculate dependent outputs consistently for each declared scenario policy.
- Show changes in predictions and options without overwriting original data.
- Allow a valid empty result when evidence does not support a recommendation.
- Export recommendations with their assumptions and provenance.

### Inputs and outputs

**Inputs:** employee context, EESI, model prediction and supported explanations.

**Outputs:** reviewable retention options, priority information, explanations and
scenario comparisons.

### Acceptance criteria

Suggestions must be traceable to their inputs and rule versions. Sensitive or
nonactionable attributes must not be converted directly into interventions.
Model sensitivity is not proof of causal effectiveness. Expert review and an
appropriate evaluation design will be needed before claiming that recommended
actions reduce turnover.

## Cross-module data contracts

| Handover | Required checks |
| --- | --- |
| Module 1 to Module 2 | Employee identity, observation month, economic period, units, required fields and quality flags |
| Module 2 to Module 3 | Finite score, valid range, formula ID/version, normalisation profile and compatibility with the trained model |
| Module 3 to Module 4 | Employee identity, prediction target, class labels, valid probabilities, model version and explanation meaning |
| Complete pipeline | Source consistency, reproducibility, explicit unavailable states and no silent substitution of incompatible data or results |

The system will preserve original records, distinguish saved observations from
hypothetical scenarios, and record the versions needed to reproduce results.
Experimental comparison scores will not enter prediction models until the team
explicitly approves and evaluates that integration.

## Data strategy

- Use synthetic records for development, demonstrations and software testing.
- Use authorised survey data to explore economic relationships and formula
  behaviour within the limits of those surveys.
- Obtain suitable real employee data and independent validation measurements
  for empirical research, subject to consent and approval requirements.
- Document source definitions, sampling, exclusions, missingness and intended use.
- Keep organisational, survey and synthetic cohorts separate.
- Avoid claiming that a convenience sample represents an entire workforce or
  that real input data alone proves a formula is valid.
- Keep private source data and model artifacts out of public version control.

Final dataset sizes and evaluation splits will be determined by access,
approvals, target availability and the agreed study design, rather than treating
a prototype sample size as a final research requirement.

## Validation and evaluation plan

| Level | Planned evidence |
| --- | --- |
| Data quality | Schema tests, missingness checks, duplicate checks, unit/date validation and audit reports |
| Calculation correctness | Hand-worked examples, boundary tests, contribution checks and deterministic outputs |
| EESI validity | Comparison with suitable independent measurements, uncertainty assessment, sensitivity analysis and subgroup checks |
| Predictive performance | Held-out evaluation, leakage checks, calibration where relevant and HR-only versus HR+EESI comparisons |
| Retention usefulness | Expert review of action relevance, explanation quality and prioritisation; separate evidence for effectiveness claims |
| Integration | Tests that outputs satisfy the next module's input contract and retain the correct employee, period and versions |
| Usability | Task-based review with intended users covering upload, analysis, scenario comparison and reporting |
| Operational readiness | Access-control, error-handling, backup/recovery and deployment verification |

Automated test passes demonstrate specified software behavior. They will be
reported separately from evidence of research validity, predictive accuracy or
real-world retention effectiveness.

## Planned user interface

One application will provide these workspaces:

- **Overview:** dataset readiness and analysis status.
- **Data Management:** HR/economic imports, quality checks and integration.
- **Economic Intelligence:** formula selection, EESI breakdowns and scenarios.
- **Turnover Analytics:** employee prediction, explanations and evaluation.
- **Retention Strategies:** prioritised options and scenario comparison.
- **Reports:** authorised exports with source and version information.

The interface will use consistent employee selection, formula labels and result
layouts. Detailed research notes will remain accessible without overwhelming
the main workflow. Missing or unsupported results will be explained clearly.

## Planned technical architecture

| Layer | Planned technology / responsibility |
| --- | --- |
| Web interface | React, TypeScript and Vite |
| Backend | Python, FastAPI and validated API schemas |
| Organisational storage | Supabase PostgreSQL and controlled file storage |
| Data processing | pandas and NumPy |
| Model pipeline | scikit-learn with saved preprocessing and model metadata |
| Testing | Automated backend, calculation, contract and integration checks; frontend build verification |
| Deployment | Environment-specific configuration, protected credentials, controlled access and documented recovery procedures |

Deployment topology and hosting will be finalised during delivery planning.
Research-only local stores will not be assumed to provide production access
control or backup requirements without further work.

## Privacy and responsible use

The delivered system will aim to minimise collected fields, restrict access to
employee-level data, protect backend credentials and retain an audit trail of
important processing actions. Reports and summaries will use appropriate
aggregation and disclosure controls.

Users must be able to distinguish facts, model estimates and hypothetical
scenarios. Economic exposure and turnover estimates will support discussion,
not serve as automatic grounds for disciplinary or adverse employment decisions.
Applicable organisational, research and data-protection requirements will be
reviewed before real-data deployment.

## Delivery roadmap

| Stage | Main work | Exit criteria |
| --- | --- | --- |
| 1. Requirements and study design | Confirm users, target outcomes, permitted data, research questions and success measures | Agreed scope, data definitions and validation protocol |
| 2. Data foundation | Establish imports, quality checks, temporal mapping and provenance | Reproducible integrated records and tested handover contract |
| 3. EESI research | Implement candidate comparison, evaluate assumptions and collect independent validation evidence | Documented formula selection or clearly justified unresolved findings |
| 4. Prediction evaluation | Establish baseline, compare HR-only/HR+EESI and evaluate held-out performance | Reproducible model report and versioned input contract |
| 5. Retention support | Define action rules, explanations, ranking and scenarios with HR review | Traceable options and reviewed limitations |
| 6. End-to-end verification | Test module handovers, usability, privacy and failure handling | Acceptance evidence across the complete workflow |
| 7. Delivery | Prepare environment, operational guidance, demonstrations and final research reports | Reviewable system package and documented remaining limitations |

Calendar dates, ownership and measurable performance targets will be agreed with
the project team and supervisors. No unverified accuracy or effectiveness target
is assumed in this plan.

## Final deliverables

1. A unified web application connecting all four modules.
2. A documented backend API and versioned module data contracts.
3. Data import, quality, integration and provenance workflows.
4. An evaluated EESI approach with formula assumptions and validation evidence.
5. A reproducible turnover prediction pipeline and evaluation report.
6. Explainable retention options and controlled scenario comparisons.
7. Automated software test evidence and end-to-end acceptance results.
8. User guidance, administration instructions and deployment documentation.
9. A research report separating supported findings from unresolved limitations.

## Definition of a successful delivery

The intended outcome is a coherent, traceable workflow that helps HR users
understand employee and economic context, assess a clearly defined turnover
outcome, and review retention options. Success requires working integration,
credible evaluation and understandable limitations, rather than a dashboard
alone or an unsupported claim of prediction accuracy.
