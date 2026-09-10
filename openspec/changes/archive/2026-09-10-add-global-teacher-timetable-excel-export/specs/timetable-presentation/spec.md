## ADDED Requirements

### Requirement: Global teacher timetable Excel export
The system SHALL allow a user viewing a newly generated or saved completed timetable to download a single Excel workbook containing a global teacher timetable for the active workspace. The workbook SHALL include one row for every teacher currently registered in the active workspace, ordered alphabetically by teacher name, including teachers with no lessons in the selected timetable.

The worksheet SHALL provide a `Docente` column and five weekday column groups. Each weekday group SHALL contain the six configured daily time slots in chronological order. Each teacher-time-slot cell with a scheduled lesson SHALL contain the class name, and cells with no scheduled lesson SHALL be blank. The weekday and time-slot headers SHALL make the group and slot structure unambiguous.

#### Scenario: Exporting a newly generated timetable
- **WHEN** a user requests the global teacher Excel export after generating a completed timetable
- **THEN** the system downloads one workbook with all current workspace teachers and their lesson classes positioned by weekday and time slot

#### Scenario: Exporting a saved timetable
- **WHEN** a user requests the global teacher Excel export while viewing a saved completed timetable
- **THEN** the system downloads one workbook with the selected timetable's lesson classes and all teachers currently registered in the active workspace

#### Scenario: Including a teacher without timetable lessons
- **WHEN** a teacher is currently registered in the active workspace but has no lesson in the selected timetable
- **THEN** the exported worksheet includes that teacher in an alphabetically ordered row with blank timetable cells

#### Scenario: Preserving workspace isolation
- **WHEN** a user downloads a global teacher Excel export
- **THEN** the workbook includes neither teachers nor timetable entries from another workspace

### Requirement: Existing timetable exports remain available
The system SHALL retain the existing JSON download and individual and batch print-to-PDF export options for newly generated and saved completed timetables alongside the global teacher Excel export.

#### Scenario: Using another export format
- **WHEN** a user views a completed timetable after the global teacher Excel export is available
- **THEN** the user can still choose the existing JSON download and applicable print-to-PDF actions
