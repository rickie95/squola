## Context

The scheduling page receives already-grouped `by_class` and `by_teacher` schedule data for both newly generated and saved schedules. The class grouping is rendered as a five-day by time-slot matrix, but the teacher grouping falls through to a chronological table. The frontend has no PDF dependency, and the existing JSON download is client-side.

See proposal.md for motivation and specs/timetable-presentation/spec.md for behavioral requirements.

## Goals / Non-Goals

**Goals:**

- Use a single reusable weekly-grid representation for class and teacher timetable groups.
- Support individual and batch print-to-PDF flows without changing schedule data, APIs, or persistence.
- Produce readable landscape A4 output with one recipient timetable per page.

**Non-Goals:**

- Changing scheduler constraints, lesson allocation, timetable data shape, or saved-schedule APIs.
- Replacing JSON download, generating PDF files server-side, or adding a third-party PDF library.
- Redesigning the day-based timetable view.

## Decisions

### Share the matrix renderer across class and teacher groups

The timetable renderer will create the same day/hour slot map for `by_class` and `by_teacher`, parameterizing the secondary cell label by grouping: teacher for a class grid and class for a teacher grid. A shared renderer prevents the two views from drifting in ordering, empty-cell treatment, or print output.

The alternative is a separate teacher-grid branch. That repeats the matrix and creates two layouts that need to stay visually and behaviorally equivalent.

### Build a document-specific print surface

Individual grid actions will build a print surface for the selected recipient; grouping-level actions will build it for every entry in the active class or teacher grouping. Each print document contains only printable headers and grids, instead of the SPA navigation, controls, metadata panels, or unrelated schedule view.

Printing the whole current page was rejected because its interactive controls and layout do not provide a predictable one-recipient-per-page document. Server-rendered PDFs were rejected because the inputs are already client-side, the app is local and single-user, and it adds a rendering and file-delivery surface without improving the tabular result.

### Use browser-native print-to-PDF

The print surface will invoke the browser print dialog. The operating system/browser's Save as PDF destination creates the PDF, preserving selectable text and vector table rendering without introducing a PDF package. Actions will be labeled as print/save-to-PDF so the browser-mediated file step is clear.

Client-side canvas/PDF libraries were rejected because they increase bundle and layout complexity and tend to rasterize or require separate table-layout logic.

### Isolate print styling

Print-specific CSS will set landscape A4 pages, hide non-document elements, repeat table headers, and use page-break rules so a recipient grid is not split between pages. The recipient header will identify the class or teacher, schedule, and creation date on each page.

The main limitation is browser print-engine variation. Conservative table sizing, print color adjustment, and testing in supported browsers mitigate layout differences.

## Risks / Trade-offs

- [Browser print settings can differ] -> Present the native print dialog and use CSS-defined landscape A4 defaults; users retain normal printer controls.
- [A timetable may exceed a single physical page with future longer days] -> Keep the grid compact and prevent unintended page splits; revisit pagination only if the timetable model grows beyond the current five-day, six-slot layout.
- [Duplicate display and print markup can diverge] -> Reuse the same weekly-grid component/data transformation and vary only document wrappers and print styles.

## Migration Plan

The frontend-only change can be deployed without data migration. If a print-layout regression is found, remove the print actions and styles while leaving the existing visualizations and JSON export intact.
