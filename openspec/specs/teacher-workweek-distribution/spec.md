# Teacher Workweek Distribution Specification

## Purpose

Distributes each teacher's lessons across their eligible workweek while making
fixed whole-day unavailability and solver-selected flexible days unambiguous.

## Requirements

### Requirement: Teacher workloads span all eligible weekdays
The system SHALL schedule a teacher with assignments for 2 to 5 lessons on
every weekday that is not fully hard-blocked for that teacher. A weekday is
fully hard-blocked when every configured daily teaching period is unavailable
to the teacher. The system SHALL schedule no lessons on a fully hard-blocked
weekday.

#### Scenario: Teacher with no full-day unavailability works each weekday
- **WHEN** a teacher has no fully hard-blocked weekday and has a weekly load that can satisfy the daily workload range across five weekdays
- **THEN** the generated timetable assigns the teacher 2 to 5 lessons on each weekday

#### Scenario: Teacher works every remaining weekday after a full-day block
- **WHEN** a teacher has one fully hard-blocked weekday and has a weekly load that can satisfy the daily workload range across the four remaining weekdays
- **THEN** the generated timetable assigns no lessons on the blocked weekday and 2 to 5 lessons on each remaining weekday

#### Scenario: Partial unavailability does not create a day off
- **WHEN** a teacher has unavailable periods but at least one period remains available on a weekday
- **THEN** that weekday remains a required teaching weekday under the daily workload rule

### Requirement: Flexible day off is a hard solver-selected unavailability
The system SHALL treat an enabled flexible day-off request as a requirement to
leave at least one weekday completely free when no weekday is fully
hard-blocked. The system SHALL choose the free weekday. Among schedules that
satisfy this requirement and all hard constraints, the system SHALL maximize
the number of weekdays on which the teacher teaches, subject to the legal
daily workload range.

#### Scenario: Flexible request distributes a compatible load across four days
- **WHEN** a teacher with an enabled flexible day-off request has a weekly load that can be taught across four weekdays
- **THEN** the generated timetable leaves one solver-selected weekday free and distributes the load across four weekdays

#### Scenario: Low load permits additional free days
- **WHEN** a teacher with an enabled flexible day-off request has too few weekly lessons to meet the daily minimum across four weekdays
- **THEN** the generated timetable leaves at least one weekday free and uses the greatest feasible number of teaching weekdays

#### Scenario: Flexible request cannot fit the weekly load
- **WHEN** a teacher with an enabled flexible day-off request has a weekly load that cannot fit in four weekdays within the daily maximum
- **THEN** schedule generation reports the timetable as infeasible instead of scheduling that teacher on all five weekdays

### Requirement: Flexible requests and fixed whole-day unavailability are exclusive
The system SHALL treat a flexible day-off request and a fully hard-blocked
weekday as mutually exclusive. When a teacher's unavailable periods create a
fully hard-blocked weekday, the system SHALL automatically disable that
teacher's flexible day-off request. The system SHALL reject an attempt to
enable a flexible day-off request while the teacher has a fully hard-blocked
weekday. The teacher interface SHALL explain both outcomes.

#### Scenario: Completing a full-day block clears the flexible request
- **WHEN** a teacher with an enabled flexible day-off request is made unavailable for every teaching period of a weekday
- **THEN** the system creates the full-day block and records the flexible day-off request as disabled

#### Scenario: Existing full-day block prevents flexible request
- **WHEN** a teacher has a fully hard-blocked weekday and a user attempts to enable the flexible day-off request
- **THEN** the system rejects the update and explains that the hard-blocked weekday already provides the day off

#### Scenario: Partial block does not prevent flexible request
- **WHEN** a teacher has unavailable periods that do not fully block any weekday
- **THEN** the user can enable the flexible day-off request
