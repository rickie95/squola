import type { ScheduleSlot, Teacher } from "../types";

const DAY_ORDER = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"];
const HOUR_ORDER = [
  "08:00-09:00",
  "09:00-10:00",
  "10:00-11:00",
  "11:00-12:00",
  "12:00-13:00",
  "13:00-14:00",
];

const DAY_LABEL_TO_INDEX: Record<string, number> = {
  lunedì: 0,
  lunedi: 0,
  monday: 0,
  martedì: 1,
  martedi: 1,
  tuesday: 1,
  mercoledì: 2,
  mercoledi: 2,
  wednesday: 2,
  giovedì: 3,
  giovedi: 3,
  thursday: 3,
  venerdì: 4,
  venerdi: 4,
  friday: 4,
};

interface GlobalTeacherTimetableExport {
  teachers: Teacher[];
  slotsByTeacher: Record<string, ScheduleSlot[]>;
  scheduleName: string;
}

const getDayIndex = (day: string): number | undefined => {
  const normalizedDay = day.trim().toLowerCase();
  const mappedDay = DAY_LABEL_TO_INDEX[normalizedDay];

  if (mappedDay !== undefined) {
    return mappedDay;
  }

  const numericDay = Number(normalizedDay);
  if (Number.isInteger(numericDay) && numericDay >= 0 && numericDay < DAY_ORDER.length) {
    return numericDay;
  }

  return undefined;
};

const getExportFilename = (scheduleName: string): string => {
  const safeScheduleName = scheduleName
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
  const date = new Date().toISOString().slice(0, 10);

  return `orario-docenti-${safeScheduleName || "orario"}-${date}.xlsx`;
};

export async function downloadGlobalTeacherTimetable({
  teachers,
  slotsByTeacher,
  scheduleName,
}: GlobalTeacherTimetableExport): Promise<void> {
  const { Workbook } = await import("exceljs");
  const workbook = new Workbook();
  const worksheet = workbook.addWorksheet("Orario docenti");
  const headerStyle = {
    font: { bold: true, color: { argb: "FFFFFFFF" } },
    fill: { type: "pattern" as const, pattern: "solid" as const, fgColor: { argb: "FF1D4ED8" } },
    alignment: { horizontal: "center" as const, vertical: "middle" as const, wrapText: true },
  };
  const border = {
    top: { style: "thin" as const, color: { argb: "FFD1D5DB" } },
    left: { style: "thin" as const, color: { argb: "FFD1D5DB" } },
    bottom: { style: "thin" as const, color: { argb: "FFD1D5DB" } },
    right: { style: "thin" as const, color: { argb: "FFD1D5DB" } },
  };

  worksheet.mergeCells(1, 1, 2, 1);
  const teacherHeader = worksheet.getCell(1, 1);
  teacherHeader.value = "Docente";
  teacherHeader.style = headerStyle;
  teacherHeader.border = border;

  DAY_ORDER.forEach((day, dayIndex) => {
    const firstColumn = 2 + dayIndex * HOUR_ORDER.length;
    const lastColumn = firstColumn + HOUR_ORDER.length - 1;

    worksheet.mergeCells(1, firstColumn, 1, lastColumn);
    const dayHeader = worksheet.getCell(1, firstColumn);
    dayHeader.value = day;
    dayHeader.style = headerStyle;
    dayHeader.border = border;

    HOUR_ORDER.forEach((hour, hourIndex) => {
      const hourHeader = worksheet.getCell(2, firstColumn + hourIndex);
      hourHeader.value = `${hourIndex + 1}a\n${hour}`;
      hourHeader.style = headerStyle;
      hourHeader.border = border;
    });
  });

  const collator = new Intl.Collator("it", { sensitivity: "base" });
  const orderedTeachers = [...teachers].sort((first, second) =>
    collator.compare(
      `${first.first_name} ${first.last_name}`,
      `${second.first_name} ${second.last_name}`
    )
  );

  orderedTeachers.forEach((teacher, teacherIndex) => {
    const rowNumber = teacherIndex + 3;
    const teacherName = `${teacher.first_name} ${teacher.last_name}`;
    const row = worksheet.getRow(rowNumber);
    row.getCell(1).value = teacherName;

    for (let column = 1; column <= DAY_ORDER.length * HOUR_ORDER.length + 1; column += 1) {
      const cell = row.getCell(column);
      cell.border = border;
      cell.alignment = {
        horizontal: column === 1 ? "left" : "center",
        vertical: "middle",
        wrapText: true,
      };
    }

    for (const slot of slotsByTeacher[teacherName] ?? []) {
      const dayIndex = getDayIndex(slot.day);
      const hourIndex = HOUR_ORDER.indexOf(slot.hour);

      if (dayIndex === undefined || hourIndex === -1 || !slot.class) {
        continue;
      }

      row.getCell(2 + dayIndex * HOUR_ORDER.length + hourIndex).value = slot.class;
    }
  });

  worksheet.getColumn(1).width = 28;
  for (let column = 2; column <= DAY_ORDER.length * HOUR_ORDER.length + 1; column += 1) {
    worksheet.getColumn(column).width = 14;
  }
  worksheet.getRow(1).height = 24;
  worksheet.getRow(2).height = 32;
  worksheet.views = [{ state: "frozen", xSplit: 1, ySplit: 2 }];

  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = getExportFilename(scheduleName);
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
