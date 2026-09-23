## Context

See proposal.md for the motivation. The export (`frontend/src/utils/globalTeacherTimetableExcel.ts`) matches lessons to cells by name: saved schedules store `slot.class` as a string such as `"3A"`, not a class id. The export already fetches teachers when the user clicks export. The class form limits a workspace to 30 classes (years 1–5 × sections A–F).

## Goals / Non-Goals

**Goals:**
- Stable per-class colors that don't change when other classes are deleted.
- Defaults guaranteed distinct and readable, checked by a test rather than by eye.

**Non-Goals:**
- Enforcing uniqueness of user-chosen colors (only a UI warning).
- Using colors in on-screen grids or PDF prints.
- A "reset to default" action. Picking a palette color again achieves the same result.

## Decisions

**Persist the color when the class is created, not derive it at read time.**
`classes.color` is a `String(7)` NOT NULL column. The alternative was to leave it null and use the palette color at the class's position in its list. That shifts every later class's color whenever one is deleted, so exports would change from week to week.

**The backend assigns the default.**
The palette lives in the backend. `create_class` loads the workspace's used colors, then takes the first palette entry not in that set. If all entries are used, it uses `palette[count % len]`. The frontend never needs the palette. The alternative, assigning in the frontend, would duplicate the logic and could not assign colors to classes created through the API.

**A hand-picked, hardcoded 30-color palette.**
Use light tints across the hue wheel, with lightness around 75–90% so that each color reaches at least about 10:1 against black. The order alternates hues so that the first few classes get clearly different colors. A pytest test checks that there are 30 unique entries and that each has a contrast ratio of at least 4.5 with black, using the WCAG relative-luminance formula. Generating the palette with HSL math would not make the check any stronger, so it isn't worth doing.

**The migration embeds its own copy of the palette.**
Migrations should not import application code that may change later. The migration adds the column as nullable, backfills each workspace's classes in `id` order with `palette[i % 30]`, and then sets the column to NOT NULL.

**Validation.**
In the schemas, `color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")` on create and update, and `color: str` on the response. Colors are stored lowercase, which matches what `<input type="color">` returns.

**Picker: the browser's built-in `<input type="color">`, no library.**
It sits next to the selected class header on `ClassesPage` and saves on `change` through the existing update mutation. The duplicate warning is computed on the client from the already-loaded class list.

**Export.**
`downloadTeacherTimetableExcel` in `SchedulingPage` also calls `classesApi.list()` and passes a `name -> color` map. For each lesson cell, the export sets `fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FF" + hex } }`. It uses white text when the contrast ratio with black is below 4.5. This needs a small luminance helper, about 5 lines.

## Risks / Trade-offs

- [A class renamed after a timetable was saved no longer matches by name] → That cell gets no fill. This is the same behavior the export already has for teachers.
- [A user picks a dark color] → The export switches the text to white, so the cell stays readable.
- [Duplicate user colors make two classes look alike] → This is accepted. The page warns the user, and there's no database constraint.

## Migration Plan

Run the alembic upgrade (the new revision follows `1f72c1dcb74d`). To roll back, drop the `color` column. Nothing else depends on it.
