## Context

See `proposal.md` for the motivation and `specs/teacher-daily-workload/spec.md` for the behavior contract. The CP-SAT model creates one Boolean decision variable for each assignment, weekday, and hourly slot. It already groups assignments by teacher and builds a daily sum for an upper-bound constraint, but the bound currently defaults to six periods even though the documented maximum is five. No persisted service-day concept exists: a zero assigned-hour total represents a teacher not being in service on that weekday.

## Goals / Non-Goals

**Goals:**
- Enforce the required daily set `{0, 2, 3, 4, 5}` from the combined hours of all assignments for each teacher.
- Preserve fixed lessons and unavailability as hard constraints, allowing the solver to declare infeasibility when they cannot compose legally.
- Keep the daily workload rule independent from soft scheduling preferences, including the flexible day-off request.

**Non-Goals:**
- Adding teacher service calendars, daily workload configuration, or an exception mechanism.
- Changing the six hourly timetable slots or subject-level consecutive-lesson rules.
- Explaining individual infeasibility causes in the generation API response.

## Decisions

### Model the permitted daily totals as a hard CP-SAT domain constraint

For each teacher and weekday, aggregate every assignment and hourly decision variable into a daily-hours expression. Constrain that expression to the enumerated legal values `0, 2, 3, 4, 5`.

This makes the zero-hour exception explicit and prevents both a one-hour day and the existing six-hour maximum. A reified "works that day" Boolean plus minimum and maximum inequalities was considered, but an allowed-domain constraint expresses the legal set directly and avoids introducing auxiliary state that is not otherwise needed.

### Aggregate by teacher rather than assignment or class

The daily-hours expression will include lessons from every class-matter assignment held by the teacher. This reflects the legal workload, prevents several individually valid one-hour assignments from bypassing the rule, and works with the existing no-overlap constraint.

Applying the constraint individually to each assignment was rejected because it would prohibit valid two-hour teaching days split between subjects or classes.

### Keep existing hard constraints authoritative

The new constraint is added alongside weekly-hour, overlap, unavailability, and fixed-lesson constraints. If fixed lessons or limited availability force an illegal daily total, the solver returns infeasible rather than moving a fixed lesson or relaxing the daily workload rule.

Adding a repair path that alters fixed lessons or treats the rule as an optimization objective was rejected because the daily range is mandatory.

### Correct the maximum daily limit through the unified constraint

Replace the standalone maximum-hours-per-day constraint with the legal daily-workload constraint, using five as the maximum permitted nonzero total. This eliminates the divergence between implementation and generation documentation.

Keeping the old maximum constraint in addition to the enumerated domain was considered redundant and risks separate limits drifting over time.

## Risks / Trade-offs

- [Existing schedules relying on one-hour or six-hour teacher days become unschedulable] -> Treat infeasibility as the correct legal outcome and cover it with solver tests.
- [A low weekly load, such as one total weekly hour, has no legal distribution] -> Return infeasible without adding an unsupported exception.
- [Existing flexible-day-off tests use loads whose feasibility changes with the five-hour maximum] -> Adjust fixture loads and expectations to keep their intended soft-preference assertions distinct from this hard rule.
- [Fixed lessons can introduce an otherwise hidden illegal daily total] -> Test both pairable and unpairable fixed lessons.

## Migration Plan

1. Deploy the generator constraint and aligned tests without data migration because the rule uses existing assignment and lesson data.
2. Regenerate timetables after deployment; preexisting schedules are not modified by generation.
3. Roll back by restoring the previous generator constraint; no persisted schema or API contract requires reversal.
