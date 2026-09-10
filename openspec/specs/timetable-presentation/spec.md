# timetable-presentation Specification

## Purpose

Provide consistent, printable weekly timetable views that staff can distribute to individual classes and teachers.

## Requirements

### Requirement: Teacher weekly grid
The system SHALL display a weekly timetable grid for every teacher in a completed timetable, for both newly generated and saved schedules. The grid SHALL use the same weekday columns and time-slot rows as the class timetable grid. Each occupied teacher cell SHALL identify the subject and class, and each unoccupied slot SHALL be visibly empty.

#### Scenario: Viewing a generated schedule by teacher
- **WHEN** a user selects the teacher grouping for a newly generated completed timetable
- **THEN** the system displays one weekly grid per teacher with subject and class details in occupied cells

#### Scenario: Viewing a saved schedule by teacher
- **WHEN** a user opens a saved completed timetable and selects the teacher grouping
- **THEN** the system displays one weekly grid per teacher with the same layout and cell information

### Requirement: Individual printable timetable export
The system SHALL allow a user to open a print-to-PDF flow for one displayed class or teacher timetable. The printable output SHALL contain the selected recipient's type and name followed by its weekly grid on one landscape A4 page, without application navigation, controls, or schedule metadata.

#### Scenario: Printing one class timetable
- **WHEN** a user requests a printable export for a displayed class timetable
- **THEN** the system opens a print-to-PDF flow containing that class's grid on one landscape A4 page

#### Scenario: Printing one teacher timetable
- **WHEN** a user requests a printable export for a displayed teacher timetable
- **THEN** the system opens a print-to-PDF flow containing that teacher's grid on one landscape A4 page

### Requirement: Batch printable timetable export
The system SHALL allow a user to open a print-to-PDF flow for all class timetables or all teacher timetables in the active grouping. The output SHALL place each recipient's type and name followed by its complete weekly grid on a separate landscape A4 page without application navigation, controls, or schedule metadata.

#### Scenario: Printing all class timetables
- **WHEN** a user requests a batch printable export while the class grouping is active
- **THEN** the system opens a print-to-PDF flow with one page for every class timetable

#### Scenario: Printing all teacher timetables
- **WHEN** a user requests a batch printable export while the teacher grouping is active
- **THEN** the system opens a print-to-PDF flow with one page for every teacher timetable

### Requirement: Existing timetable exports remain available
The system SHALL retain the existing JSON download and individual and batch print-to-PDF export options for newly generated and saved completed timetables alongside the global teacher Excel export.

#### Scenario: Using another export format
- **WHEN** a user views a completed timetable after the global teacher Excel export is available
- **THEN** the user can still choose the existing JSON download and applicable print-to-PDF actions

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
