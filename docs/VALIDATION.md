# MVP validation

Verified locally on Windows with Python 3.12.14 and Node.js 24.19.0.

- Backend: **29 passing pytest cases** covering deterministic ranking, score bounds, factor totals, comfort influence, matchup uncertainty, role eligibility, exclusion, input validation, damage threats, every role, API responses, and mocked AI success/failure.
- Frontend: **TypeScript compilation and Vite production build pass**.
- Browser: **5 passing Playwright scenarios** against the running frontend and backend, covering the demo, results details, draft editing/search, comfort, duplicate prevention, every role, partial drafts, empty pools, API failure recovery, keyboard focus/Escape, and mobile overflow.
- Visual review: inspected desktop draft/results and mobile draft captures. Screenshots are generated under the ignored `.test-artifacts/` folder.
- Optional paid OpenAI requests were not made. The integration is verified with mocked provider responses and outages. Template mode is the default.

Run instructions and verification commands are in the root README. Data accuracy is limited to the clearly labeled historical/static snapshot and handcrafted sample model; no claim of current-patch performance is made.
