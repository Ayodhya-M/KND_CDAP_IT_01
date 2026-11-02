# Module 4 Proposal Evaluation Prototype

## Research problem and objective

Turnover prediction identifies employees whose records receive elevated model-based risk estimates, but it does not by itself tell an HR reviewer which non-automated actions are relevant. Module 4 investigates a transparent decision-support layer that links supplied risk factors to personalized retention options, ranks them, and explains each link. It supports human judgment; it does not make employment decisions.

## Proposed novelty and functional scope

The proposal prototype demonstrates a traceable chain: Module 1 employee context + Module 2 economic context + Module 3 risk explanation → supported factor → retention option → transparent priority → human-readable explanation. It provides employee lookup, risk and economic summaries, factor-linked recommendations, ranking, provenance, and a non-persistent illustrative scenario comparison.

The current default upstream providers are deterministic mock fixtures. They validate the integration design and are not research results, calculated EESI values, trained-model predictions, or SHAP explanations.

## Component architecture

```text
Module 1 read-only repository
          +
Module2Provider / Module3Provider (mock by default)
          ↓
RiskAnalyzer → RecommendationEngine → PriorityEngine → ExplanationEngine
          ↓
RetentionDecisionService → FastAPI → React dashboard
          ↓
Illustrative in-memory rule comparison (no database write or new prediction)
```

Provider interfaces preserve a route for later real Module 2 and Module 3 integration without replacing the recommendation services.

## Rule-based recommendation methodology

Rules are provisional mappings for verified Module 1 factors only. Overtime maps to overtime/scheduling review; job satisfaction to feedback/check-in; work-life balance to balance/flexible-work support; environment satisfaction to environment review; business travel and distance from home to policy-dependent arrangement discussions; and salary to equitable compensation review only when salary is supplied as an important factor. Overtime is the present workload-related proxy because Module 1 has no separate `workload` field. Protected characteristics are excluded.

Every result retains `related_factor`, so its origin can be audited. Positive supplied contributions are required; the engine does not infer new risk factors. These mappings require literature review and HR/expert validation before final research use.

## Provisional priority calculation

The visible prototype formula is:

`100 × (0.35 × turnover risk + 0.30 × factor contribution + 0.20 × pressure value + 0.15 × intervention relevance)`

Pressure mappings, weights, and Low/Medium/High priority boundaries are configurable prototype assumptions in `backend/app/module4/config.py`. They are not scientifically validated constants.

## Illustrative simulator assumptions

The simulator accepts salary, overtime, job satisfaction, and work-life balance changes. It copies the employee context in memory, never updates Module 1, and keeps the mock turnover probability and risk level unchanged. It only checks whether an already supplied factor remains applicable: overtime is removed when false; satisfaction factors are removed above level 2. Contributions are unchanged, no new factor is created, and salary has no applicability threshold. The output is therefore labeled **Illustrative What-if Prototype — Not a Validated Turnover Forecast**. It shows rule behavior, not causality or intervention effectiveness.

## Self-evaluation criteria

| Criterion | Proposed measurement |
|---|---|
| Recommendation rule correctness | Percentage of test cases matching the documented rule table |
| Factor traceability | Percentage of recommendations containing a supported `related_factor` present in the input explanation |
| Priority consistency | Repeated identical inputs return identical descending scores; weight changes are independently testable |
| Explanation completeness | Percentage containing factor-aware reason and suggested action without causal claims |
| Scenario reproducibility | Identical employee and scenario inputs produce identical comparisons |
| API reliability | Automated success/error-contract pass rate across supported, invalid, unavailable, and unknown-employee cases |

These are evaluation criteria, not measured study results. Future evaluation should define test sets and acceptance targets before reporting outcomes.

## Limitations and future validation

- Module 2 and Module 3 are mock-default; their values cannot support final conclusions.
- Rule mappings, relevance values, priority weights, pressure mappings, and thresholds need literature and expert validation.
- The illustrative simulator does not rerun a trained prediction pipeline and cannot estimate causal impact.
- The small verified feature set limits intervention coverage; missing attributes must not be invented.
- Final work should align real provider contracts, establish approved EESI/risk classifications, validate feature semantics, add genuine model explanations where available, and evaluate relevance and usability with an approved research protocol.
