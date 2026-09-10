## Purpose

Ensures every generated teacher timetable complies with the mandatory daily teaching-hours range.

## ADDED Requirements

### Requirement: Teacher daily teaching workload is legally bounded
The system SHALL calculate each teacher's daily teaching workload as the total scheduled lessons across all of that teacher's class-matter assignments. On every weekday, the total SHALL be either zero, or no fewer than two and no more than five hours. This SHALL be a hard generation constraint for every teacher and SHALL be independent of teacher scheduling preferences.

#### Scenario: Teacher is not in service on a weekday
- **WHEN** the timetable assigns no lessons to a teacher on a weekday
- **THEN** the teacher has a legal daily workload of zero hours

#### Scenario: Teacher has a legal working day
- **WHEN** the timetable assigns a teacher two, three, four, or five lessons across one or more assignments on a weekday
- **THEN** the timetable treats the daily workload as valid

#### Scenario: Single-hour day is prohibited
- **WHEN** satisfying the remaining scheduling constraints would assign a teacher exactly one lesson on a weekday
- **THEN** the system SHALL not return that assignment in a generated timetable

#### Scenario: Daily workload exceeds the legal maximum
- **WHEN** satisfying the remaining scheduling constraints would assign a teacher more than five lessons on a weekday
- **THEN** the system SHALL not return that assignment in a generated timetable

### Requirement: Generation rejects workloads that cannot meet the daily rule
The system SHALL report schedule generation as infeasible when no timetable can satisfy the required weekly assignment hours, all other hard constraints, and each teacher's legal daily teaching workload.

#### Scenario: Only an isolated lesson can be scheduled
- **WHEN** a teacher's required hours and hard scheduling constraints permit exactly one lesson on a weekday but do not permit another lesson for that teacher on the same weekday
- **THEN** schedule generation reports an infeasible result

#### Scenario: Fixed lesson can be paired on the same day
- **WHEN** a fixed lesson would otherwise leave a teacher with one daily hour and another of that teacher's required lessons can be scheduled on the same weekday
- **THEN** the system may generate a timetable that includes both lessons and meets the daily workload rule
