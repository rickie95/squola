## Why

Completed timetables are difficult to distribute because the class grid is not available for teachers and the only export is machine-readable JSON. Staff need a consistent, printable view that can be handed directly to each class or teacher.

## What Changes

- Display saved and newly generated teacher timetables in the same weekly grid format used for class timetables.
- Provide a printable, PDF-ready rendition for either one selected class or teacher timetable, or every timetable in the active grouping.
- Format exported documents as one landscape A4 timetable per page with only the recipient label, without application chrome or schedule metadata, while retaining JSON download.

## Capabilities

### New Capabilities

- `timetable-presentation`: Interactive weekly-grid visualization and printable exports for completed timetables grouped by class or teacher.

### Modified Capabilities

- None.

## Impact

- Affects the React scheduling page, timetable rendering structure, and global print styles.
- Reuses the schedule groupings already returned by the generation and saved-schedule APIs; no solver, persistence, or API changes are expected.
- Uses the browser print dialog and its Save as PDF destination, so no PDF library or backend renderer is required.
