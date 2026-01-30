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
Preview scheduling data and potential issues before generation.

## Constraints Implemented

### Hard Constraints (Must be satisfied)

1. **Hours per week**: Each class-matter assignment must be scheduled exactly its required `hours_per_week` times.

2. **Teacher no overlap**: A teacher cannot teach in two different classes at the same time slot.

3. **Class no overlap**: A class can only have one lesson (one teacher, one matter) at any given time slot.

4. **Teacher blacklist**: Teachers cannot be scheduled during their blacklisted time slots (for teachers working at multiple schools).

5. **Max hours per day**: Teachers cannot exceed the maximum hours per day (default: 5 hours).

### Soft Constraints (Optimized)

Teacher preferences are used as optimization objectives:

1. **EARLY**: Prefer scheduling lessons in early hours (minimize hour index)
2. **LATE**: Prefer scheduling lessons in later hours
3. **MINIMIZE_GAPS**: Group lessons together, minimize free periods between lessons
4. **MAXIMIZE_GAPS**: Spread lessons out, maximize free periods between lessons

## Model Variables

For each assignment `a`, day `d` (0-4), and hour `h` (1-5):
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
      "IIIA": [
        {"day": "Monday", "hour": "08:00-09:00", "teacher": "John Smith", "matter": "Mathematics"}
      ]
    },
    "by_teacher": {
      "John Smith": [
        {"day": "Monday", "hour": "08:00-09:00", "class": "IIIA", "matter": "Mathematics"}
      ]
    },
    "by_day": {
      "Monday": [
        {"hour": "08:00-09:00", "class": "IIIA", "teacher": "John Smith", "matter": "Mathematics"}
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