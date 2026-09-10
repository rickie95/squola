## 1. Daily Workload Constraint

- [x] 1.1 Replace the current teacher maximum-hours-per-day constraint with a hard per-teacher, per-weekday constraint that permits only totals of 0, 2, 3, 4, or 5 across all assignments; verify the targeted scheduler tests pass.
- [x] 1.2 Wire the unified daily-workload constraint into model construction without altering the independence of unavailability, fixed lessons, or soft preferences; verify an otherwise valid schedule still respects those constraints.

## 2. Solver Regression Coverage

- [x] 2.1 Add focused solver tests proving daily totals of 0, 2, 3, 4, and 5 are feasible and that totals of 1 and 6 are rejected; verify the new test cases pass.
- [x] 2.2 Add a solver test confirming the total combines a teacher's assignments across classes or subjects, allowing two one-hour assignments on the same day while prohibiting either in isolation; verify the test passes.
- [x] 2.3 Add fixed-lesson solver coverage for a pairable one-hour fixed lesson and an unpairable fixed lesson that must report infeasible; verify the test cases pass.
- [x] 2.4 Update any existing day-off or generation fixtures whose weekly loads become constrained by the five-hour hard maximum, preserving their original behavior assertions; verify the affected test module passes.

## 3. Documentation and Validation

- [x] 3.1 Align the scheduling generation documentation with the enforced legal daily workload set and infeasibility behavior; verify the documented rule matches the solver constraint.
- [x] 3.2 Run the complete backend test suite with `uv run pytest tests/` and verify it passes.
