## Why

Staff need a single spreadsheet view of the full teaching timetable for operational planning and distribution. The current schedule page provides individual grids, print-to-PDF, and raw JSON, but no consolidated Excel report that includes every teacher in the workspace.

## What Changes

- Add a downloadable Excel global teacher timetable for both newly generated and saved completed schedules.
- Include every teacher currently registered in the active workspace, including teachers without lessons in the selected timetable.
- Lay out one teacher per row, with weekday column groups split into the six daily time slots and the assigned class in each occupied cell.
- Preserve the existing JSON download and printable timetable actions.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `timetable-presentation`: Add a global Excel teacher-timetable export alongside the existing individual and batch printable exports.

## Impact

- Affects `frontend/src/pages/SchedulingPage.tsx` and related frontend API/type usage.
- Adds a browser-side XLSX generation dependency.
- Reuses the existing authenticated teacher-list API and schedule data; no database migration or backend export endpoint is required.
