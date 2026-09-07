## 1. Unify timetable grids

- [ ] 1.1 Extract the class timetable matrix into a reusable weekly-grid renderer that accepts class and teacher schedule groups, and verify both groupings render Monday-to-Friday columns and all configured time-slot rows.
- [ ] 1.2 Render the teacher grouping with the shared grid, showing subject and class in occupied cells and visible empty slots, and verify the behavior for both newly generated and saved schedules.

## 2. Add printable exports

- [ ] 2.1 Add an individual print/save-to-PDF action to each class and teacher timetable grid, and verify its print document contains only that recipient's grid and identifying schedule metadata.
- [ ] 2.2 Add an active-group batch print/save-to-PDF action, and verify class and teacher batch exports each produce one recipient grid per page.
- [ ] 2.3 Add print-specific landscape A4 styles, including table-header repetition and no grid page splits, and verify the browser print preview excludes application navigation and controls.

## 3. Preserve existing behavior

- [ ] 3.1 Retain JSON export for generated and saved schedules alongside print actions, and verify the downloaded file still includes the schedule metadata and grouped slot data.
- [ ] 3.2 Run `cd frontend && npm run lint && npm run build` and manually inspect individual and batch print previews for generated and saved class and teacher schedules.
