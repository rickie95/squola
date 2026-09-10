## 1. Spreadsheet export foundation

- [x] 1.1 Add the minimal browser-side XLSX generation dependency to `frontend/package.json` and lockfile, then verify the frontend dependency installation and production build succeed.
- [x] 1.2 Add a typed global-teacher workbook builder that combines the selected timetable's `by_teacher` slots with the current workspace teacher roster, normalizes weekday labels, and orders teachers and all 30 time slots deterministically; verify its output maps lessons and blank cells to the required positions.

## 2. Workbook layout and download

- [x] 2.1 Format the workbook as one global teacher worksheet with a `Docente` column, merged weekday headers, six chronological hour columns per weekday, practical widths, and frozen identifying headers; verify the downloaded workbook opens in Excel-compatible software with the specified layout.
- [x] 2.2 Name and download the workbook through the browser using the active timetable context; verify the exported filename is valid and the workbook contains no data from another workspace.

## 3. Scheduling page integration

- [x] 3.1 Add a `Scarica Excel docenti` action to both newly generated and loaded saved timetable headers without removing or changing the JSON and print-to-PDF actions; verify it is available regardless of the active on-screen grouping.
- [x] 3.2 Retrieve the current authenticated workspace teacher roster when the Excel action is used, surface retrieval/export failures through the page's existing error handling, and include roster teachers with no selected-timetable lessons as blank rows; verify with a workspace containing at least one unscheduled teacher.

## 4. Validation

- [x] 4.1 Run the frontend lint and production build, and manually inspect exports for both generated and saved timetables to verify all requirements in the timetable-presentation delta.
