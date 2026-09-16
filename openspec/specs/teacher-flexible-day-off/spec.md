# Teacher Flexible Day Off Specification

## Purpose

Allows a teacher to request an unspecified weekday off while preserving a feasible timetable and all fixed availability restrictions.

## Requirements

### Requirement: Teachers can configure a flexible day-off request
The system SHALL expose a per-teacher flexible day-off preference. The preference SHALL be disabled by default for existing and newly created teachers, and an authorized user SHALL be able to enable or disable it while creating or updating a teacher, except where the teacher has a fully hard-blocked weekday. Teacher responses SHALL include the current preference value. See `teacher-workweek-distribution` for the exclusivity rule between this preference and fixed whole-day unavailability.

#### Scenario: New teacher has no flexible day-off request
- **WHEN** an authorized user creates a teacher without specifying the flexible day-off preference
- **THEN** the teacher is created with the preference disabled

#### Scenario: User enables a teacher's flexible day-off request
- **WHEN** an authorized user enables the preference for a teacher
- **THEN** later teacher responses show the preference as enabled

#### Scenario: User disables a teacher's flexible day-off request
- **WHEN** an authorized user disables the preference for an opted-in teacher
- **THEN** the teacher no longer contributes a flexible day-off request during future schedule generation

### Requirement: Flexible day-off requests are solver-selected hard unavailability
For every teacher with the flexible day-off preference enabled, the system SHALL schedule all of that teacher's lessons within no more than four weekdays. The system SHALL select the free weekday and SHALL NOT require the user to specify it. A weekly load that cannot fit within four weekdays SHALL make schedule generation infeasible rather than place the teacher on all five weekdays.

#### Scenario: Solver selects a free weekday
- **WHEN** a schedule can satisfy an opted-in teacher's teaching load while leaving at least one weekday without lessons
- **THEN** the generated schedule leaves at least one weekday completely free for that teacher

#### Scenario: Request that cannot be satisfied makes generation infeasible
- **WHEN** hard scheduling constraints would require an opted-in teacher to teach on all five weekdays
- **THEN** schedule generation reports an infeasible result instead of returning a schedule without a fully free weekday

### Requirement: Flexible day-off requests take precedence over other teacher preferences
The system SHALL prioritize fulfilling the greatest possible number of enabled flexible day-off requests after satisfying hard constraints and before optimizing early, late, or gap preferences.

#### Scenario: Day-off request outranks a timing preference
- **WHEN** a valid schedule can give an opted-in teacher a fully free weekday but an alternative schedule better satisfies an early, late, or gap preference while requiring that teacher to work all five days
- **THEN** the system selects the schedule with the fully free weekday

### Requirement: Fixed unavailability remains non-negotiable
The system SHALL continue to treat explicitly blocked teacher time slots as hard constraints independently of the flexible day-off preference.

#### Scenario: Fixed blocked slot and flexible request coexist
- **WHEN** a teacher has one or more explicitly blocked slots and an enabled flexible day-off preference
- **THEN** the generated schedule contains no lesson in a blocked slot and still attempts to leave one additional solver-selected weekday free

### Requirement: Scheduling preview exposes flexible day-off request data
The scheduling preview SHALL report the count of teachers with flexible day-off requests and SHALL identify whether each listed teacher has the preference enabled.

#### Scenario: Preview shows configured request
- **WHEN** an authorized user previews scheduling data after enabling a teacher's flexible day-off preference
- **THEN** the preview includes that teacher as having a flexible day-off request and increments the request count
