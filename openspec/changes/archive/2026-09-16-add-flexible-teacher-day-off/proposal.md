## Why

Teachers who also work at other schools may need one weekday kept free, but they cannot always specify which weekday in advance. The timetable generator needs to accommodate this flexible request without making the schedule infeasible or changing the existing hard unavailability rules.

## What Changes

- Add an optional, per-teacher flexible day-off preference that is disabled by default.
- Let the scheduler choose which weekday to leave completely free for an opted-in teacher.
- Treat the preference as a primary soft objective: fulfill as many flexible day-off requests as possible after hard constraints, before early/late and gap preferences.
- Retain specific teacher unavailability slots as hard constraints for fixed commitments.
- Surface the preference in teacher management and scheduling previews.

## Capabilities

### New Capabilities
- `teacher-flexible-day-off`: Teachers can request an unspecified weekday off as an optional, solver-selected scheduling preference.

### Modified Capabilities

## Impact

- Affects the teacher persistence model, migration, request and response schemas, and teachers API.
- Affects the React teacher detail view, frontend types, and scheduling preview presentation.
- Affects the CP-SAT scheduling objective, generation metadata or preview data, and backend tests.
- Does not add external dependencies.
