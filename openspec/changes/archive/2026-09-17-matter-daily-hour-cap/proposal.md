## Why

Some matters must not pile up in a single day of a class timetable: "no more than two hours of Maths per day in 2B". The scheduler already caps a class-matter assignment at three hours a day, but the value is a hardcoded global constant (`MAX_DAILY_ASSIGNMENT_HOURS`), identical for every matter. There is no way to tighten it for the matters that need it.

At the same time, `Matter.default_requirements` is dead code on the server. It is read only by the frontend, as a pre-fill of the assignment form at creation time. Editing a matter's defaults never reaches the assignments that already exist, so matter defaults and assignment requirements drift apart silently — the current database already shows assignments that no longer match their matter's defaults.

## What Changes

- Two new `MatterRequirements` values, `max_one_hour_per_day` and `max_two_hours_per_day`, settable on a matter as a default and on a single `ClassMatterAssignment`, like every other requirement.
- The scheduler's daily assignment cap becomes per-assignment: the tightest cap present on the assignment, falling back to the existing global value of three when none is set. Absence of both flags therefore keeps today's behaviour exactly.
- `PUT /matters/{id}` propagates a change of `default_requirements` to every existing assignment of that matter in the workspace, as a delta: requirements added to the default are added to the assignments, requirements removed from the default are removed from them, and per-assignment requirements untouched by the delta survive.
- Both write paths that set requirements — `PUT /matters/{id}` and `PUT /classes/{id}/assignments/{assignment_id}` — reject, with `400` and the list of offending assignments, any write that would leave an assignment in a combination that is arithmetically impossible to schedule. Nothing is written when the check fails.

Not breaking: no stored value changes meaning, and an assignment carrying neither new flag behaves as it does today.

## Capabilities

### New Capabilities

- `matter-daily-hour-cap`: how many hours of one class-matter assignment may be scheduled in a single day, how a matter or an assignment declares a tighter cap, and how a cap is resolved when several are present.
- `matter-default-requirements`: how a matter's default requirements propagate to the assignments of that matter, and when a write that sets requirements is rejected as unschedulable.

### Modified Capabilities

None. No existing spec under `openspec/specs/` describes the daily assignment cap or the propagation of matter defaults.

## Impact

- `src/squola/models.py` — two values added to the `MatterRequirements` enum. No migration: `default_requirements` and `requirements` are `EnumArray` over a JSON column.
- `src/squola/scheduler.py` — `_add_daily_assignment_cap_constraint` resolves the cap per assignment instead of using the constant directly; the requirement lookup built around line 461 gains the two new flags.
- `src/squola/routers/matters.py` — the update endpoint gains the delta propagation and the pre-write check.
- `src/squola/routers/classes.py` — the assignment update endpoint calls the same check.
- `frontend/src/types/index.ts` — two enum values and two labels. Both `MattersPage.tsx` and `ClassesPage.tsx` render their checkbox lists from `Object.values(MatterRequirement)`, so no component changes are needed.
- `tests/` — extends `test_matter_daily_limits.py` and adds coverage for propagation and rejection.
- No new dependency, no schema migration, no change to saved schedules.
