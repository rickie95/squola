## ADDED Requirements

### Requirement: Daily workload tends to a balanced band
Within the legal daily workload range, the system SHALL derive for each teacher a
target daily band from that teacher's total weekly assignment hours divided by
their number of eligible teaching weekdays. Eligible teaching weekdays SHALL
exclude fully hard-blocked weekdays and, for a teacher with an enabled flexible
day-off request, one further weekday. The band SHALL span the floor and the
ceiling of that division. All other hard constraints being satisfied, the system
SHALL prefer timetables whose daily teacher workloads fall inside the band, and
SHALL penalise a daily workload in proportion to its distance from the band. A
weekday on which the teacher teaches no lessons SHALL NOT be penalised.

#### Scenario: Balanced week preferred over a concentrated one
- **WHEN** a teacher's weekly load can be distributed either as an even spread across their eligible weekdays or concentrated into fewer heavier days, and both satisfy every hard constraint
- **THEN** the system generates the even spread

#### Scenario: Reduced weekly hours shrink the band
- **WHEN** a teacher teaches at another school and therefore has fewer weekly hours in this institute
- **THEN** the system derives a lower target band from that teacher's own weekly hours rather than applying a fixed daily target

#### Scenario: Unavailability reduces the eligible weekdays
- **WHEN** a teacher has one fully hard-blocked weekday
- **THEN** the system derives the band by dividing the weekly hours across the remaining eligible weekdays only

#### Scenario: Load that cannot fit the band
- **WHEN** a teacher's weekly hours cannot be distributed so that every teaching day falls inside the band
- **THEN** the system still generates a timetable respecting every hard constraint and keeps the total distance from the band as small as possible

## MODIFIED Requirements

### Requirement: Flexible day off is a hard solver-selected unavailability
The system SHALL treat an enabled flexible day-off request as a requirement to
leave at least one weekday completely free when no weekday is fully
hard-blocked. The system SHALL choose the free weekday. Among schedules that
satisfy this requirement and all hard constraints, the system SHALL prefer those
that spread the teacher's lessons over the greatest number of weekdays, subject to
the legal daily workload range. This preference SHALL follow from the balanced
daily band and SHALL NOT take unconditional precedence over the other optimised
criteria.

#### Scenario: Flexible request distributes a compatible load across four days
- **WHEN** a teacher with an enabled flexible day-off request has a weekly load that can be taught across four weekdays
- **THEN** the generated timetable leaves one solver-selected weekday free and distributes the load across four weekdays

#### Scenario: Low load permits additional free days
- **WHEN** a teacher with an enabled flexible day-off request has too few weekly lessons to meet the daily minimum across four weekdays
- **THEN** the generated timetable leaves at least one weekday free and uses the greatest feasible number of teaching weekdays

#### Scenario: Flexible request cannot fit the weekly load
- **WHEN** a teacher with an enabled flexible day-off request has a weekly load that cannot fit in four weekdays within the daily maximum
- **THEN** schedule generation reports the timetable as infeasible instead of scheduling that teacher on all five weekdays
