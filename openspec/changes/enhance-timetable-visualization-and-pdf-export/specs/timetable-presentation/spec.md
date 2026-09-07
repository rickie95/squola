## Purpose

Provide consistent, printable weekly timetable views that staff can distribute to individual classes and teachers.

## ADDED Requirements

### Requirement: Teacher weekly grid
The system SHALL display a weekly timetable grid for every teacher in a completed timetable, for both newly generated and saved schedules. The grid SHALL use the same weekday columns and time-slot rows as the class timetable grid. Each occupied teacher cell SHALL identify the subject and class, and each unoccupied slot SHALL be visibly empty.

#### Scenario: Viewing a generated schedule by teacher
- **WHEN** a user selects the teacher grouping for a newly generated completed timetable
- **THEN** the system displays one weekly grid per teacher with subject and class details in occupied cells

#### Scenario: Viewing a saved schedule by teacher
- **WHEN** a user opens a saved completed timetable and selects the teacher grouping
- **THEN** the system displays one weekly grid per teacher with the same layout and cell information

### Requirement: Individual printable timetable export
The system SHALL allow a user to open a print-to-PDF flow for one displayed class or teacher timetable. The printable output SHALL contain only the selected recipient's weekly grid together with the schedule name, recipient name and type, and the schedule creation date.

#### Scenario: Printing one class timetable
- **WHEN** a user requests a printable export for a displayed class timetable
- **THEN** the system opens a print-to-PDF flow containing that class's grid on one landscape A4 page

#### Scenario: Printing one teacher timetable
- **WHEN** a user requests a printable export for a displayed teacher timetable
- **THEN** the system opens a print-to-PDF flow containing that teacher's grid on one landscape A4 page

### Requirement: Batch printable timetable export
The system SHALL allow a user to open a print-to-PDF flow for all class timetables or all teacher timetables in the active grouping. The output SHALL place each recipient's complete weekly grid on a separate landscape A4 page and include the schedule name, recipient name and type, and schedule creation date on every page.

#### Scenario: Printing all class timetables
- **WHEN** a user requests a batch printable export while the class grouping is active
- **THEN** the system opens a print-to-PDF flow with one page for every class timetable

#### Scenario: Printing all teacher timetables
- **WHEN** a user requests a batch printable export while the teacher grouping is active
- **THEN** the system opens a print-to-PDF flow with one page for every teacher timetable

### Requirement: Existing data export remains available
The system SHALL retain the existing JSON download option for newly generated and saved completed timetables alongside the printable export options.

#### Scenario: Downloading timetable data
- **WHEN** a user chooses the JSON download action for a completed timetable
- **THEN** the system downloads the current timetable data in JSON format
