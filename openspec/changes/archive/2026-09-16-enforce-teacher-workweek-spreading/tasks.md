## 1. Solver workweek distribution

- [x] 1.1 Derive each teacher's fully hard-blocked weekdays from their unavailable periods and enforce 2 to 5 lessons on every remaining weekday for teachers without a flexible request; verify solver tests cover five eligible weekdays, a full-day block, and partial unavailability.
- [x] 1.2 Replace the current relaxable flexible-day objective with a hard at-most-four-workday constraint and exact workday indicators, then maximize the number of teaching weekdays before timing and gap preferences; verify solver tests cover four-day distribution, low-load additional free days, and an infeasible load above four daily maxima.
- [x] 1.3 Update isolated workload validation and generation/preview diagnostics to identify workweek-spreading and hard flexible-day infeasibility; verify API tests return actionable teacher-specific errors.

## 2. Teacher availability API invariants

- [x] 2.1 Detect when creating an unavailability period completes a fully blocked weekday and clear the teacher's flexible request in the same transaction; verify API tests preserve partial blocks and clear the request only after the final daily period is blocked.
- [x] 2.2 Reject enabling a flexible request for a teacher with a fully blocked weekday and return an explanatory validation error; verify API tests cover rejection and allow the setting when only partial unavailability exists.

## 3. Teacher-management experience

- [x] 3.1 Update teacher availability and flexible-day controls to explain that a full-day block supersedes the flexible request and show when completing a full-day block clears it; verify the production TypeScript build succeeds.
- [x] 3.2 Disable or prevent enabling the flexible-day control while a full weekday is blocked and surface the backend validation message if state changes concurrently; verify the interface reflects both allowed and rejected configurations.

## 4. Product documentation and integration

- [x] 4.1 Update the teacher and schedule-generation product specifications and README to describe required workweek spreading, the hard solver-selected flexible day, and the non-cumulative full-day block rule.
- [x] 4.2 Run the focused backend solver/API tests and the frontend production build; verify the new constraints, conflict handling, and UI guidance work together without regressions.
