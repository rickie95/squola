## Why

In the global teacher Excel export, every lesson cell looks the same, so staff can't scan the sheet by class. Giving each class its own background color makes the timetable readable at a glance, and the defaults need to stay legible with black text.

## What Changes

- Each school class has a persisted background color (`#rrggbb`).
- When a class is created, it gets the first color of a fixed 30-color light palette that no other class in the workspace uses. The palette covers every class the UI allows (years 1–5 × sections A–F), so defaults are always distinct.
- Every palette color has a contrast ratio of at least 4.5:1 against black text (WCAG AA).
- Existing classes are backfilled with palette colors by a migration.
- Users can change a class color with a color picker on the Classes page. A color that another class already uses is allowed, and the page shows a warning.
- The class API accepts and returns `color`; `color` is optional on create and update.
- In the global teacher Excel export, each lesson cell is filled with its class's color. Text switches to white on dark user-chosen fills.
- Non-goal: class colors are not used in on-screen grids or print-to-PDF output.

## Capabilities

### New Capabilities
- `class-color`: Each class has a color. Distinct, readable defaults come from a fixed palette, and users can override them on the Classes page.

### Modified Capabilities
- `timetable-presentation`: The "Global teacher timetable Excel export" requirement now fills each lesson cell with the class color.

## Impact

- Backend: `SchoolClass` model (new `color` column), class schemas, `routers/classes.py` (default assignment on create, color on update), new alembic migration with backfill.
- Frontend: `SchoolClass` types, `ClassesPage.tsx` (color picker), `utils/globalTeacherTimetableExcel.ts` and its call site in `SchedulingPage.tsx` (fetch classes, apply fills).
- No new dependencies.
