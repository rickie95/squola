## 1. Requirement values and cap resolution

- [x] 1.1 Add `MAX_ONE_HOUR_PER_DAY = "max_one_hour_per_day"` and `MAX_TWO_HOURS_PER_DAY = "max_two_hours_per_day"` to `MatterRequirements` in `src/squola/models.py`, and verify an existing assignment can be loaded and saved with the new values without a migration (the column is `EnumArray` over JSON).
- [x] 1.2 Add a single shared mapping from cap requirement to hours (`max_one_hour_per_day` → 1, `max_two_hours_per_day` → 2) and a helper that resolves a list of requirements to a daily cap, returning the smallest cap present and `MAX_DAILY_ASSIGNMENT_HOURS` when none is. Verify with unit assertions covering: no cap, one cap, both caps present (tightest wins).

## 2. Scheduler

- [x] 2.1 In `_build_lookups` (around `src/squola/scheduler.py:461`), record each assignment's resolved daily cap alongside the existing requirement sets. Verify the map holds 3 for an assignment with no cap requirement.
- [x] 2.2 Change `_add_daily_assignment_cap_constraint` to bound each assignment by its resolved cap instead of the constant. Verify the existing `tests/test_matter_daily_limits.py` still passes unchanged.
- [x] 2.3 Extend `tests/test_matter_daily_limits.py`: 3 hours in a day is infeasible under `max_two_hours_per_day`; 2 + gap + 1 in a day is infeasible under `max_two_hours_per_day` (the cap is a daily total, not a run length); 6 weekly hours under `max_two_hours_per_day` spread over at least 3 days; 2 hours in a day infeasible under `max_one_hour_per_day`; both flags together behave as a 1-hour cap.

## 3. Shared conflict check

- [x] 3.1 Add a validator that takes a requirement list and a weekly hour count and reports whether the combination is arithmetically unschedulable: cap smaller than the hours demanded by `one_lesson_of_two_hours_per_week` (2) or `one_lesson_of_three_hours_per_week` (3), or `hours_per_week > cap * DAYS_OF_WEEK`. Verify with unit assertions over each conflicting pair and over the non-conflicting both-caps case.
- [x] 3.2 Call the validator from `POST /classes/{class_id}/assignments` and `PUT /classes/{class_id}/assignments/{assignment_id}` in `src/squola/routers/classes.py`, returning `400` and leaving the assignment unchanged. Verify with API tests for both endpoints.
- [x] 3.3 Call the requirement-only part of the validator from `POST /matters` in `src/squola/routers/matters.py` (no weekly hours are known at matter level), returning `400`. Verify with an API test that an impossible default combination is refused and nothing is created.

## 4. Default requirement propagation

- [x] 4.1 In `PUT /matters/{matter_id}` (`src/squola/routers/matters.py`), compute `added = new - old` and `removed = old - new` over `default_requirements` and apply `(requirements | added) - removed` to every `ClassMatterAssignment` of that matter in the workspace. Verify with API tests for: requirement added, requirement removed, untouched per-assignment requirement preserved, matter with no assignments, defaults absent from the request leaving assignments alone.
- [x] 4.2 Run the conflict validator over each affected assignment's resulting requirements and its `hours_per_week` before writing anything; on any conflict return `400` naming the offending assignment ids and commit nothing. Verify with API tests that both the matter defaults and every assignment are unchanged after a rejected push.
- [x] 4.3 Verify propagation does not cross workspace boundaries by extending `tests/test_workspace_isolation.py` with a matter of the same name in a second workspace.

## 5. Frontend

- [x] 5.1 Add `MAX_ONE_HOUR_PER_DAY` and `MAX_TWO_HOURS_PER_DAY` to `MatterRequirement` and `REQUIREMENT_LABELS` in `frontend/src/types/index.ts`, with labels naming the daily total ("Max 1 ora al giorno", "Max 2 ore al giorno") rather than lesson length. Verify the new checkboxes appear on both the matter form and the assignment form, which render from `Object.values(MatterRequirement)`.
- [x] 5.2 Surface the `400` detail from a rejected matter or assignment save so the user sees which assignments conflict instead of a generic failure. Verify by saving a conflicting combination in the UI.

## 6. Documentation

- [x] 6.1 Update `CONTEXT.md` (`MatterRequirements` entry) with the two new values and the daily-total semantics, and record that matter defaults now propagate to existing assignments. Verify the glossary no longer describes `default_requirements` as applied only at assignment creation.
- [x] 6.2 Update `specs/03 - matters.md` and `specs/05 - constraints.md` to name the daily cap requirement. Verify both read consistently with the delta specs in this change.
