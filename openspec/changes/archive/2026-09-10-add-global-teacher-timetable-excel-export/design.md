## Context

The schedule page can display newly generated and saved timetable data, download it as JSON, and print individual or batch grids. A generated or saved timetable stores lesson slots grouped by teacher, but this data omits teachers with no scheduled lessons. The authenticated teacher API provides the current workspace roster.

See proposal.md for the motivation and scope.

## Goals / Non-Goals

**Goals:**

- Create one downloadable spreadsheet that maps every teacher in the current workspace roster to the selected timetable's weekly lesson slots.
- Produce a readable, conventional timetable layout with a teacher column, weekday groups, and six time-slot columns per weekday.
- Make the action available for both generated and loaded saved schedules without changing the timetable-generation API or persistence model.

**Non-Goals:**

- Preserving the teacher roster as it existed when a schedule was generated.
- Exporting class-centric, day-centric, or per-teacher workbook variants.
- Replacing the existing JSON or print-to-PDF export flows.
- Adding server-side file generation or storage.

## Decisions

### Generate the workbook in the browser

The Scheduling page already has the selected timetable and can obtain the current workspace teacher roster through the existing authenticated API. A frontend XLSX library will construct and download the workbook, avoiding a new download endpoint, server-side file handling, and duplicate schedule serialization.

Alternative considered: a FastAPI export endpoint with a Python spreadsheet library. This would centralize document creation but adds a new API surface and dependency while the needed data already exists in the browser.

### Use the current workspace roster for every export

The export queries the current teacher list and creates one row per teacher, sorted using the application's Italian locale. A teacher without a matching entry in the selected timetable receives an otherwise blank row. This intentionally makes the report reflect the current staff roster even when viewing a historical saved schedule.

Alternative considered: storing a roster snapshot in each saved schedule. This would make historical reports immutable but requires changing persisted schedule data and leaves existing saved schedules without a snapshot.

### Use a single global-teacher worksheet

The worksheet has two header rows: a vertically merged `Docente` header and one horizontally merged header per weekday, each spanning its six time-slot columns. Every populated schedule cell contains the class name only; cells with no lesson are blank. The export action is independent of the currently selected on-screen grouping, so it always creates the global teacher report.

Alternative considered: one worksheet per teacher. That duplicates the existing printable per-teacher experience and does not provide the requested consolidated report.

## Risks / Trade-offs

- [Current staff changes alter rows in exports of old schedules] -> This is the explicitly chosen report semantics; the export does not claim to be a historical roster snapshot.
- [Spreadsheet libraries increase frontend bundle size] -> Add only the required package and defer workbook construction until the user requests the export.
- [Legacy schedule payloads use English day labels while the UI displays Italian] -> Normalize day labels into the application's canonical weekday order before placing cells.
- [Long teacher names or dense reports reduce readability] -> Set practical column widths, styled headers, and frozen header/teacher panes.

## Migration Plan

1. Add the frontend spreadsheet dependency and export action.
2. Release without database or API migration because the teacher roster API and persisted schedule slots already exist.
3. If the export needs rollback, remove the frontend action and dependency; existing schedules and exports remain unaffected.
