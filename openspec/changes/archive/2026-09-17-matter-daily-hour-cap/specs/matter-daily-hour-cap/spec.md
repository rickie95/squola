## Purpose

Bounds how many hours of a single class-matter assignment a generated timetable may place in one weekday, and lets a matter or an individual assignment declare a cap tighter than the system-wide one.

## ADDED Requirements

### Requirement: A class-matter assignment has a daily hour cap
The system SHALL limit the hours of one class-matter assignment scheduled on a single weekday to that assignment's daily hour cap. This SHALL be a hard generation constraint. When an assignment declares no cap requirement, its daily hour cap SHALL be three hours, which is the system-wide default and preserves the behaviour of assignments created before cap requirements existed.

#### Scenario: Assignment without a cap requirement keeps the default cap
- **WHEN** an assignment declares neither `max_one_hour_per_day` nor `max_two_hours_per_day`
- **THEN** the timetable may schedule up to three hours of that assignment on a weekday
- **AND** the timetable SHALL NOT schedule four or more hours of it on a weekday

#### Scenario: Cap applies to the daily total, not to consecutive runs
- **WHEN** an assignment's daily hour cap is two hours
- **AND** satisfying the remaining constraints would schedule two consecutive hours of that assignment and a further hour of it later the same day
- **THEN** the system SHALL not return that assignment in a generated timetable

#### Scenario: Cap is independent per weekday
- **WHEN** an assignment's daily hour cap is two hours and it requires six weekly hours
- **THEN** the timetable may schedule two hours of it on each of three different weekdays

### Requirement: A matter or an assignment can declare a tighter daily cap
The system SHALL offer `max_one_hour_per_day` and `max_two_hours_per_day` as matter requirements, settable both as a matter's default requirements and as the requirements of an individual class-matter assignment, alongside the existing requirements. `max_one_hour_per_day` SHALL set the assignment's daily hour cap to one hour and `max_two_hours_per_day` SHALL set it to two hours.

#### Scenario: Matter declares a two-hour daily cap
- **WHEN** a matter's default requirements include `max_two_hours_per_day`
- **THEN** the requirement propagates to that matter's assignments under the matter default requirements capability
- **AND** each assignment that carries it is limited to two hours of that matter per weekday in its class

#### Scenario: Assignment overrides its matter's cap
- **WHEN** an assignment carries `max_one_hour_per_day` and its matter declares no cap by default
- **THEN** only that assignment is limited to one hour per weekday

#### Scenario: Cap is scoped to one assignment, not to the class or the teacher
- **WHEN** two assignments in the same class each carry `max_two_hours_per_day`
- **THEN** each assignment is independently limited to two hours per weekday
- **AND** the class may still be taught four hours of those two matters combined on that weekday

### Requirement: The tightest declared cap wins
The system SHALL resolve an assignment's daily hour cap to the smallest cap among the cap requirements the assignment carries. An assignment carrying both `max_one_hour_per_day` and `max_two_hours_per_day` SHALL be treated as capped at one hour, and SHALL NOT be rejected as contradictory.

#### Scenario: Both cap requirements are present
- **WHEN** an assignment carries both `max_one_hour_per_day` and `max_two_hours_per_day`
- **THEN** its daily hour cap is one hour

### Requirement: Generation reports infeasibility when a daily cap cannot be met
The system SHALL report schedule generation as infeasible when no timetable can satisfy the required weekly hours of every assignment, all other hard constraints, and every assignment's daily hour cap.

#### Scenario: Weekly hours exceed what the cap allows across the week
- **WHEN** an assignment requires six weekly hours and carries `max_one_hour_per_day`
- **AND** the week has five weekdays
- **THEN** the system SHALL report the generation as infeasible

#### Scenario: Cap conflicts with a required long lesson
- **WHEN** an assignment carries `max_two_hours_per_day` and `one_lesson_of_three_hours_per_week`
- **THEN** the system SHALL report the generation as infeasible
