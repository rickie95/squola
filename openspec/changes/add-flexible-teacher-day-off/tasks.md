## 1. Teacher preference persistence and API

- [x] 1.1 Add a non-null `prefers_day_off` teacher field and an Alembic migration that defaults and backfills it to `false`; verify migrated existing teachers and newly created teachers have the field set to `false`.
- [x] 1.2 Add the flexible day-off field to backend teacher create, update, and response schemas and wire it through the teachers router; verify API tests cover default, enable, disable, and response behavior.
- [x] 1.3 Add the flexible day-off field to frontend teacher contracts and API payload handling; verify the frontend TypeScript build accepts the updated contracts.

## 2. Scheduling behavior

- [x] 2.1 Model opted-in teachers' working weekdays and a soft flexible-day-off violation in the CP-SAT generator without changing fixed unavailability behavior; verify a feasible opted-in teacher schedule contains at least one fully free weekday.
- [x] 2.2 Combine flexible-day-off violations with existing preference terms using a calculated dominant coefficient; verify solver tests prove day-off fulfillment outranks early, late, and gap preferences.
- [x] 2.3 Preserve feasibility when a flexible day-off request cannot be met and retain hard blocked slots; verify solver tests cover a forced five-day schedule and a schedule that includes both fixed unavailability and an enabled request.

## 3. User interface and scheduling preview

- [x] 3.1 Add a clearly labelled, independently editable flexible day-off toggle to teacher management and explain its solver-selected, relaxable behavior; verify `npm run build` succeeds.
- [x] 3.2 Extend the scheduling preview backend response and frontend types/UI with the enabled-request count and per-teacher setting; verify API tests and `npm run build` succeed.

## 4. Documentation and integration validation

- [x] 4.1 Update the teacher and schedule-generation product specifications to distinguish hard blocked slots from the optional flexible day-off request; verify the documented defaults and priority match the OpenSpec delta.
- [x] 4.2 Run the relevant backend test suite and frontend production build after implementation; verify `uv run pytest tests/` and `cd frontend && npm run build` pass.
