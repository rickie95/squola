## MODIFIED Requirements

### Requirement: Flexible day-off requests take precedence over other teacher preferences
The system SHALL guarantee every enabled flexible day-off request as a hard
constraint, so that no optimised preference - early, late, gap, daily balance, or
day shape - can trade away a teacher's free weekday. When a request cannot be
satisfied, the system SHALL report the generation as infeasible rather than return
a timetable that places the teacher on all five weekdays.

#### Scenario: Day-off request outranks a timing preference
- **WHEN** a valid schedule can give an opted-in teacher a fully free weekday but an alternative schedule better satisfies an early, late, or gap preference while requiring that teacher to work all five days
- **THEN** the system selects the schedule with the fully free weekday

#### Scenario: Day-off request outranks daily balance
- **WHEN** a valid schedule can give an opted-in teacher a fully free weekday but an alternative schedule spreads that teacher's load more evenly across all five weekdays
- **THEN** the system selects the schedule with the fully free weekday
