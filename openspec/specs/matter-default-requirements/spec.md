# Matter Default Requirements Specification

## Purpose

Keeps a matter's default requirements and the requirements of that matter's existing class assignments in step, and refuses any write that would leave an assignment with a combination of requirements no timetable can satisfy.

## Requirements

### Requirement: Changing a matter's default requirements propagates to existing assignments
When a matter's default requirements change, the system SHALL apply that change to every existing class-matter assignment of that matter within the workspace. The change SHALL be applied as a delta: each requirement added to the matter's defaults SHALL be added to those assignments, each requirement removed from the matter's defaults SHALL be removed from them, and a requirement the assignment carries that appears in neither the previous nor the new defaults SHALL be left in place.

#### Scenario: A requirement is added to the defaults
- **WHEN** a matter's default requirements change from `[at_least_twice_per_week]` to `[at_least_twice_per_week, max_two_hours_per_day]`
- **AND** an assignment of that matter carries `[at_least_twice_per_week, one_lesson_of_two_hours_per_week]`
- **THEN** that assignment carries `[at_least_twice_per_week, one_lesson_of_two_hours_per_week, max_two_hours_per_day]`

#### Scenario: A requirement is removed from the defaults
- **WHEN** a matter's default requirements change from `[at_least_twice_per_week, max_two_hours_per_day]` to `[at_least_twice_per_week]`
- **AND** an assignment of that matter carries `[at_least_twice_per_week, one_lesson_of_two_hours_per_week, max_two_hours_per_day]`
- **THEN** that assignment carries `[at_least_twice_per_week, one_lesson_of_two_hours_per_week]`

#### Scenario: Per-assignment requirements outside the delta survive
- **WHEN** a matter's default requirements change in a way that neither adds nor removes `one_lesson_of_two_hours_per_week`
- **AND** an assignment of that matter carries `one_lesson_of_two_hours_per_week` while the matter does not declare it by default
- **THEN** that assignment still carries `one_lesson_of_two_hours_per_week`

#### Scenario: Propagation is limited to the matter and the workspace
- **WHEN** a matter's default requirements change
- **THEN** assignments of other matters are unchanged
- **AND** assignments of a matter with the same name in another workspace are unchanged

#### Scenario: Updating a matter without changing its defaults leaves assignments alone
- **WHEN** a matter is updated and its default requirements are unchanged or absent from the request
- **THEN** no assignment's requirements change

#### Scenario: Setting defaults on a matter with no assignments
- **WHEN** a matter's default requirements change and the matter has no class assignments
- **THEN** the new defaults are stored and no assignment is written

### Requirement: Requirements that cannot be scheduled are rejected at write time
The system SHALL reject a write that sets requirements, on a matter's defaults or on a class-matter assignment, when the resulting requirements of any affected assignment are impossible to schedule for arithmetic reasons that hold regardless of the rest of the timetable. The response SHALL be a client error identifying the affected assignments, and the system SHALL NOT write any part of the request. A combination SHALL be treated as impossible when the resulting daily hour cap is smaller than the hours of the longest single lesson the resulting requirements demand, or when the assignment's weekly hours exceed the resulting daily hour cap multiplied by the number of weekdays.

#### Scenario: A pushed default conflicts with an assignment's required long lesson
- **WHEN** `max_two_hours_per_day` is added to a matter's default requirements
- **AND** an assignment of that matter carries `one_lesson_of_three_hours_per_week`
- **THEN** the system rejects the request with a client error naming that assignment
- **AND** the matter's default requirements are unchanged
- **AND** no assignment's requirements change

#### Scenario: A pushed default leaves too few weekdays for the weekly hours
- **WHEN** `max_one_hour_per_day` is added to a matter's default requirements
- **AND** an assignment of that matter requires six weekly hours across a five-weekday week
- **THEN** the system rejects the request with a client error naming that assignment
- **AND** no assignment's requirements change

#### Scenario: The same check applies to editing one assignment
- **WHEN** an assignment is updated to carry both `max_two_hours_per_day` and `one_lesson_of_three_hours_per_week`
- **THEN** the system rejects the request with a client error
- **AND** the assignment is unchanged

#### Scenario: The same check applies to creating a matter or an assignment
- **WHEN** a matter is created with default requirements that are impossible in combination, or an assignment is created with such requirements
- **THEN** the system rejects the request with a client error
- **AND** nothing is created

#### Scenario: Both cap requirements together are not a conflict
- **WHEN** a write would leave an assignment carrying both `max_one_hour_per_day` and `max_two_hours_per_day`
- **AND** the resulting one-hour cap is compatible with the assignment's other requirements and weekly hours
- **THEN** the system accepts the write

#### Scenario: Deeper infeasibility is left to generation
- **WHEN** the resulting requirements pass the arithmetic check but no timetable satisfies them once teacher unavailability and other classes are taken into account
- **THEN** the system accepts the write
- **AND** schedule generation reports the infeasibility
