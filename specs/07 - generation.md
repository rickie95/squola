# Scheduling Generation

## Overview

The scheduling generation uses Google OR-Tools CP-SAT (Constraint Programming - Satisfiability) solver to generate valid weekly schedules for all classes, teachers, and subject matters.

## API Endpoints

### POST /api/scheduling/generate
Generate a new schedule based on current database data.

**Request Body:**
```json
{
  "time_limit_seconds": 120.0,
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

5. **Daily teacher workload and workweek distribution**: A teacher without a flexible day off has between 2 and 5 lessons on every weekday that is not fully blacklisted. A fully blacklisted weekday has no lessons. A teacher with a flexible day off has at most four teaching weekdays, each with 2 to 5 lessons.

6. **Daily cap per assignment**: A single class-matter assignment occupies at most 3 hours in one day. The cap applies to the daily total, not to consecutive hours, so `3 hours + gap + 1 hour` of the same matter in one day is rejected just like 4 hours in a row. This replaces the earlier rule that only limited windows of 4 consecutive hours.

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

The solver minimises a single weighted sum. Every term applies to every teacher
whatever their preference, including no preference at all - which previously
contributed no objective term, leaving the solver free to return the first legal
timetable it found.

| Term | Penalises | Weight |
|---|---|---|
| `W_DAILY_BALANCE` | Daily load away from the band `[floor(T/D), ceil(T/D)]`, `T` weekly hours and `D` eligible weekdays | 16 |
| `W_EXTRA_GAP` | Gap hours beyond the first in a day | 12 |
| `W_CLASS_BLOCK` | Each start of a run of consecutive hours in one class | 10 |
| `W_LONG_RUN` | Each window of 4 consecutive teaching hours | 6 |
| `W_GAP` | Each gap hour | 2 |
| `W_TIME_PREFERENCE` | Distance from the preferred end of the day (`EARLY`/`LATE`) | 1 |

`MINIMIZE_GAPS` doubles and `MAXIMIZE_GAPS` halves the gap and contiguity
weights for that teacher; neither flips their sign.

A flexible day off is not part of the objective: it is the hard constraint
`sum(works_on_day) <= 4`. Spreading the load over the remaining weekdays follows
from the balance band.

### Quality Diagnostics

A successful generation reports `metadata.quality` with a total per dimension -
`class_blocks`, `gap_hours`, `long_runs`, `balance_deviation` - and, under
`worst`, the teacher-day pairs contributing most to each. Computed from the
extracted slots alone, and not persisted with saved schedules.

Because the objective is now dense, `OPTIMAL` is rare and `FEASIBLE` is the norm
within the time limit. `FEASIBLE` does not mean a worse timetable: on a realistic
instance the solution quality plateaus within seconds while proving optimality
does not finish. Read the quality metrics, not the status label.

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
    "total_slots": 125,
    "quality": {
      "class_blocks": 3,
      "gap_hours": 11,
      "long_runs": 0,
      "balance_deviation": 2,
      "worst": {
        "class_blocks": [{"teacher": "Azzurra Lami", "day": "Monday", "value": 2}]
      }
    }
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
