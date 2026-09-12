# Scheduling Generation

## Overview

The scheduling generation uses Google OR-Tools CP-SAT (Constraint Programming - Satisfiability) solver to generate valid weekly schedules for all classes, teachers, and subject matters.

## API Endpoints

### POST /api/scheduling/generate
Generate a new schedule based on current database data.

**Request Body:**
```json
{
  "time_limit_seconds": 60.0,
  "save_to_file": false,
  "output_path": "./schedule_output.json"
}
```

**Response:**
Returns schedule grouped by class, teacher, and day with metadata about the solve.

### GET /api/scheduling/preview
Preview scheduling data and potential issues before generation, including any
teacher whose own assignments can never form a legal daily workload (see
below), reported as a human-readable entry in `issues`.

## Constraints Implemented

### Hard Constraints (Must be satisfied)

1. **Hours per week**: Each class-matter assignment must be scheduled exactly its required `hours_per_week` times.

2. **Teacher no overlap**: A teacher cannot teach in two different classes at the same time slot.

3. **Class no overlap**: A class can only have one lesson (one teacher, one matter) at any given time slot.

4. **Teacher blacklist**: Teachers cannot be scheduled during their blacklisted time slots (for teachers working at multiple schools).

5. **Daily teacher workload**: On each weekday, a teacher has either no lessons or between 2 and 5 lessons across all assigned classes and matters. A timetable that cannot meet this legal range is infeasible.

### Unsatisfiable Workload Detection

Some combinations are impossible for a single teacher regardless of everyone
else's schedule - most commonly a low-hour assignment (e.g. 2 hours/week)
tagged `at_least_twice_per_week`, which forces a 1-hour day with no other
lesson available to reach the legal 2-hour minimum. Because generation solves
one joint model for every teacher and class, a single such teacher makes the
**entire** generation report `INFEASIBLE` with no indication of the cause.

To avoid this, the system checks each teacher's own assignments, fixed
lessons, and unavailabilities in isolation before reporting a result:
- `GET /api/scheduling/preview` lists any affected teacher as an entry in
  `issues`, before generation is attempted.
- `POST /api/scheduling/generate` names the affected teacher(s) in the `422`
  error detail instead of a generic infeasibility message, when this is the
  cause.

### Soft Constraints (Optimized)

Teacher preferences are used as optimization objectives:

1. **EARLY**: Prefer scheduling lessons in early hours (minimize hour index)
2. **LATE**: Prefer scheduling lessons in later hours
3. **MINIMIZE_GAPS**: Group lessons together, minimize free periods between lessons
4. **MAXIMIZE_GAPS**: Spread lessons out, maximize free periods between lessons
5. **Flexible day off**: For teachers who request it, prefer leaving one solver-selected weekday completely free. This is prioritized over the other soft preferences and is relaxed when required to produce a valid schedule.

## Model Variables

For each assignment `a`, day `d` (0-4), and hour `h` (1-6):
- `x[a, d, h]` ∈ {0, 1}: Binary variable indicating if assignment `a` is scheduled at day `d`, hour `h`

## Schedule Output Format

```json
{
  "metadata": {
    "status": "OPTIMAL|FEASIBLE|INFEASIBLE",
    "solve_time_seconds": 1.234,
    "generated_at": "2026-01-31T10:00:00",
    "total_slots": 125
  },
  "schedule": {
    "by_class": {
      "2A": [
        {"day": "Monday", "hour": "08:00-09:00", "teacher": "John Smith", "matter": "Mathematics"}
      ]
    },
    "by_teacher": {
      "John Smith": [
        {"day": "Monday", "hour": "08:00-09:00", "class": "3A", "matter": "Mathematics"}
      ]
    },
    "by_day": {
      "Monday": [
        {"hour": "08:00-09:00", "class": "3A", "teacher": "John Smith", "matter": "Mathematics"}
      ]
    }
  }
}
```

## Status Codes

- **OPTIMAL**: Best possible solution found
- **FEASIBLE**: Valid solution found (may not be optimal)
- **INFEASIBLE**: No valid schedule exists with current constraints
- **NO_DATA**: No assignments found in the database
