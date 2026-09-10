## Why

The generator can currently schedule a teacher for a single hour on a working day and can permit six daily hours, both of which violate the applicable daily service rule. The timetable must enforce the legal daily workload for every scheduled teacher.

## What Changes

- Add a universal hard scheduling constraint that a teacher has either no lessons or from two through five lessons on each weekday.
- **BREAKING**: Timetables that require a teacher to teach exactly one hour on a day, or more than five hours on a day, become infeasible.
- Align the implemented maximum daily workload with the documented five-hour limit.
- Add solver coverage for valid, invalid, multi-assignment, and fixed-lesson daily workloads.

## Capabilities

### New Capabilities
- `teacher-daily-workload`: Enforce the legal per-teacher daily teaching-hours range during timetable generation.

### Modified Capabilities

## Impact

- Affects the CP-SAT constraints in `src/squola/scheduler.py`.
- Affects scheduler tests, including cases with fixed lessons and assignments spanning multiple classes.
- Does not change teacher configuration, API contracts, persistence, or dependencies.
