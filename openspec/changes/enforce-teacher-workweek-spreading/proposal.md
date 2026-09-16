## Why

The scheduler currently allows a teacher to have any number of zero-lesson
weekdays. This can concentrate a normal teacher's load unnecessarily and makes
the relationship between fixed whole-day unavailability and a flexible day-off
request unclear.

## What Changes

- Require teachers to work on every weekday that is not fully hard-blocked,
  subject to the existing legal daily workload of 2 to 5 lessons.
- Treat a fully hard-blocked weekday as the teacher's day off.
- Treat the flexible day-off setting as a hard solver-selected full-day
  unavailability when no weekday is fully hard-blocked, while maximizing the
  teacher's teaching weekdays within that restriction.
- Make a fully hard-blocked weekday and a flexible day-off request mutually
  exclusive: creating the former automatically clears the latter, and enabling
  the latter while the former exists is rejected.
- Update the teacher interface and scheduling documentation to make the
  precedence and consequences visible.

## Capabilities

### New Capabilities
- `teacher-workweek-distribution`: Teachers' weekly workload is distributed
  across eligible weekdays, with defined interaction between hard full-day
  unavailability and the optional flexible day-off request.

### Modified Capabilities

- None.

## Impact

- Affects the CP-SAT teacher daily-workload constraints and flexible day-off
  objective.
- Affects teacher unavailability and preference API behavior, persistence
  updates, frontend controls, validation messaging, previews, and tests.
- Updates the teacher and schedule-generation product specifications.
- Adds no external dependencies.
