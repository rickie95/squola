## 1. Backend

- [x] 1.1 Add the 30-color `CLASS_COLOR_PALETTE` constant and a `contrast_with_black(hex)` helper. Add a pytest test asserting 30 unique `#rrggbb` entries, each with contrast >= 4.5, and verify it passes.
- [x] 1.2 Add `color: Mapped[str] = mapped_column(String(7))` to `SchoolClass`. Add a `color` field to the create/update schemas (optional, `#rrggbb` pattern) and to the response schema. Verify that an invalid color returns 422 in a test.
- [x] 1.3 In `create_class`, assign the first unused palette color in the workspace when no color is given, cycling when all are used. In `update_class`, save the color (lowercased). Add tests for distinct defaults, per-workspace isolation, and an accepted duplicate on update, and verify they pass.
- [x] 1.4 Add an alembic migration after `1f72c1dcb74d` with its own palette copy: add the column as nullable, backfill per workspace in id order, set it NOT NULL. Verify that `alembic upgrade head` and `downgrade -1` both succeed on a database with existing classes.

## 2. Frontend

- [x] 2.1 Add `color` to `SchoolClass` and `color?` to `SchoolClassCreate`/`SchoolClassUpdate` in `types/index.ts`. Verify that `npm run build` type-checks.
- [x] 2.2 On `ClassesPage`, add `<input type="color">` next to the selected class header that saves through the update mutation, plus a warning when another class has the same color. Verify manually that the color persists after a reload and that the warning appears on a duplicate.
- [x] 2.3 In `SchedulingPage`, fetch `classesApi.list()` during the Excel export and pass a `name -> color` map. In `globalTeacherTimetableExcel.ts`, fill lesson cells with the class color, use white text when contrast with black is below 4.5, and apply no fill for unknown class names. Verify manually by exporting a timetable and opening it in a spreadsheet app.
