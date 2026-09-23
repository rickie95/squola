## MODIFIED Requirements

### Requirement: Global teacher timetable Excel export
The system SHALL allow a user viewing a newly generated or saved completed timetable to download a single Excel workbook containing a global teacher timetable for the active workspace. The workbook SHALL include one row for every teacher currently registered in the active workspace, ordered alphabetically by teacher name, including teachers with no lessons in the selected timetable.

The worksheet SHALL provide a `Docente` column and five weekday column groups. Each weekday group SHALL contain the six configured daily time slots in chronological order. Each teacher-time-slot cell with a scheduled lesson SHALL contain the class name, and cells with no scheduled lesson SHALL be blank. The weekday and time-slot headers SHALL make the group and slot structure unambiguous.

Each lesson cell SHALL use as background the current color of the workspace class with that name. When the class color is dark enough that black text would fall below a 4.5:1 contrast ratio, the cell text SHALL be white. A lesson cell whose class name matches no current workspace class SHALL keep no background fill.

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

#### Scenario: Coloring lesson cells by class
- **WHEN** a user downloads a global teacher Excel export
- **THEN** each lesson cell has the background color of its class

#### Scenario: Readable text on a dark class color
- **WHEN** a class color would give black text a contrast ratio below 4.5:1
- **THEN** that class's lesson cells in the export use white text

#### Scenario: Lesson for a class that no longer exists
- **WHEN** a saved timetable contains a class name that matches no current workspace class
- **THEN** that lesson cell shows the class name without a background fill
