# PP1 verification record

Verified on 2026-10-11 (Asia/Colombo).

- Backend: `python -m pytest tests -q --junitxml=../docs/eesi/test-results.xml` -> **48 passed**, including 27 EESI cases and 21 existing module cases. One dependency deprecation warning from Starlette/AnyIO.
- Frontend: `npm.cmd run build` -> TypeScript compilation and Vite production build passed.
- Offline evidence: `python scripts/export_eesi_evidence.py` -> **100 employees scored, zero rejected**, six economic months, three candidates and four controlled scenarios.
- Real data: `python scripts/prepare_lfs2024.py` -> **2,304 eligible employees from 17,771 respondents**. Monthly and salary-band counts each reconcile to 2,304. Raw source and private intermediate are ignored by Git. Official economic PDF tables were visually inspected.
- Real-data checks: previous-month year rollover, quarterly period alignment, invalid/absent salaries and weights, working-age eligibility, missing economic months, weighted means, small-group suppression, separate normalization with deflation, constant-range rejection, aggregate preparation and API profile validation.
- Calculation check: midpoint economic inputs and equal reference/employee salary produce baseline 50, additive 50, interaction 25. Contribution sums, salary direction, inflation direction, clipping, invalid salary, extreme finite income, endpoints, outcome exclusion and database-independent API behaviour are tested.
- Browser layout/interaction check was unavailable: no browser is connected to this tool session. Rehearse the UI locally before presenting.
- Existing frontend dependencies produced npm audit findings. No dependency upgrades were made as part of the EESI implementation.

This record establishes calculation and implementation checks, not empirical stress accuracy. Survey validation, final formula selection, database persistence and Module 1/3 integration remain outstanding.
