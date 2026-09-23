import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import axios from "axios";
import { classesApi, schedulingApi } from "../api";
import { getApiErrorMessage } from "../api/errors";
import { DAY_ORDER, HOUR_ORDER, compareTeacherNames, contrastWithBlack, getDayIndex } from "../utils/teacherGrid";
import type {
  AppliedSwap,
  SwapCandidate,
  SwapCell,
  SwapSlot,
  SwapWarning,
  UnlinkedLesson,
} from "../types";

interface GridCell extends SwapSlot {
  teacher: string;
  teacher_id?: number; // missing for an unlinked old timetable, which is read-only
  class: string;
  matter: string;
}

interface Selection {
  teacherId: number;
  teacher: string;
  slot: SwapSlot;
}

const cellKey = (teacher: string, slot: SwapSlot) => `${teacher}|${slot.day}|${slot.hour}`;
const sameSlot = (a: SwapSlot, b: SwapSlot) => a.day === b.day && a.hour === b.hour;
const slotLabel = (slot: SwapSlot) => `${DAY_ORDER[slot.day]} ${slot.hour}a ora`;

const WARNING_LABELS: Record<SwapWarning["metric"], string> = {
  excess_gap_hours: "ore di buco oltre la franchigia",
  long_runs: "filate di 4 ore consecutive",
};

const unlinkedFrom = (error: unknown): UnlinkedLesson[] | null => {
  if (!axios.isAxiosError<{ detail?: { unlinked?: UnlinkedLesson[] } }>(error)) return null;
  if (error.response?.status !== 409) return null;
  return error.response.data?.detail?.unlinked ?? null;
};

export default function SwapsPage() {
  const scheduleId = Number(useParams().id);
  const navigate = useNavigate();
  const [applied, setApplied] = useState<AppliedSwap[]>([]);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [preview, setPreview] = useState<SwapCandidate | null>(null);
  const [nickname, setNickname] = useState("");

  const savedQuery = useQuery({
    queryKey: ["savedSchedule", scheduleId],
    queryFn: () => schedulingApi.getSaved(scheduleId),
  });
  const classesQuery = useQuery({ queryKey: ["classes"], queryFn: classesApi.list });
  const draftQuery = useQuery({
    queryKey: ["swapDraft", scheduleId, applied],
    queryFn: () => schedulingApi.swapDraft(scheduleId, applied),
    placeholderData: (previous) => previous,
    retry: false,
  });
  const suggestQuery = useQuery({
    queryKey: ["swapSuggest", scheduleId, applied, selection],
    queryFn: () =>
      schedulingApi.suggestSwaps(scheduleId, applied, selection!.teacherId, selection!.slot),
    enabled: selection !== null && draftQuery.isSuccess,
    retry: false,
  });
  const saveMutation = useMutation({
    mutationFn: () => schedulingApi.saveSwaps(scheduleId, applied, nickname.trim() || null),
    onSuccess: () => navigate("/scheduling", { state: { tab: "history" } }),
  });

  const unlinked = unlinkedFrom(draftQuery.error);

  // The draft when it loads; the saved timetable as-is when it cannot be linked.
  const cells: GridCell[] = useMemo(() => {
    if (draftQuery.data) return draftQuery.data;
    if (!unlinked || !savedQuery.data) return [];
    return Object.entries(savedQuery.data.schedule_data.by_teacher).flatMap(([teacher, slots]) =>
      slots.flatMap((slot) => {
        const day = getDayIndex(slot.day);
        const hour = HOUR_ORDER.indexOf(slot.hour) + 1;
        return day === undefined || hour === 0
          ? []
          : [{ teacher, day, hour, class: slot.class ?? "", matter: slot.matter }];
      })
    );
  }, [draftQuery.data, unlinked, savedQuery.data]);

  const cellByKey = useMemo(
    () => new Map(cells.map((cell) => [cellKey(cell.teacher, cell), cell])),
    [cells]
  );
  const teachers = useMemo(
    () => [...new Set(cells.map((cell) => cell.teacher))].sort(compareTeacherNames),
    [cells]
  );
  const classColors = useMemo(
    () => Object.fromEntries((classesQuery.data ?? []).map((c) => [c.name, c.color])),
    [classesQuery.data]
  );
  const unlinkedKeys = useMemo(
    () => new Set((unlinked ?? []).map((lesson) => cellKey(lesson.teacher, lesson))),
    [unlinked]
  );

  // Hovering a suggestion shows the chain's cells in their state after the swap.
  const previewCells = useMemo(() => {
    const overrides = new Map<string, SwapCell | null>();
    if (!preview || !selection) return overrides;
    for (const teacher of preview.teachers) {
      overrides.set(cellKey(teacher.teacher, selection.slot), teacher.before_s2);
      overrides.set(cellKey(teacher.teacher, preview.s2), teacher.before_s1);
    }
    return overrides;
  }, [preview, selection]);

  const applySwap = (candidate: SwapCandidate) => {
    if (!selection) return;
    setApplied([...applied, { teacher_id: selection.teacherId, s1: selection.slot, s2: candidate.s2 }]);
    setSelection(null);
    setPreview(null);
  };

  const undo = () => {
    setApplied(applied.slice(0, -1));
    setSelection(null);
    setPreview(null);
  };

  const renderCell = (teacher: string, slot: SwapSlot) => {
    const key = cellKey(teacher, slot);
    const inPreview = previewCells.has(key);
    const shown: { class: string; matter: string } | null | undefined = inPreview
      ? previewCells.get(key)
      : cellByKey.get(key);
    const lesson = cellByKey.get(key);
    const selected = selection?.teacher === teacher && sameSlot(selection.slot, slot);
    const color = shown ? classColors[shown.class] : undefined;
    const clickable = lesson?.teacher_id !== undefined && !unlinked;

    return (
      <td
        key={key}
        title={shown ? `${shown.class} - ${shown.matter}` : undefined}
        onClick={
          clickable
            ? () => {
                setSelection({ teacherId: lesson!.teacher_id!, teacher, slot });
                setPreview(null);
              }
            : undefined
        }
        style={{
          padding: "0.25rem",
          minWidth: "2.75rem",
          textAlign: "center",
          fontSize: "0.8rem",
          cursor: clickable ? "pointer" : "default",
          background: color ?? "transparent",
          color: color && contrastWithBlack(color) < 4.5 ? "#fff" : "inherit",
          border: "1px solid var(--border-color)",
          outline: selected
            ? "3px solid var(--primary-color)"
            : inPreview
              ? "2px dashed var(--primary-color)"
              : unlinkedKeys.has(key)
                ? "2px solid var(--danger-color)"
                : undefined,
          outlineOffset: "-2px",
        }}
      >
        {shown?.class ?? ""}
      </td>
    );
  };

  const renderCandidate = (candidate: SwapCandidate, index: number) => {
    const s1 = selection!.slot;
    const free = (cell: SwapCell | null) => cell?.class ?? "libero";
    return (
      <li
        key={index}
        onMouseEnter={() => setPreview(candidate)}
        onMouseLeave={() => setPreview(null)}
        style={{
          padding: "0.75rem",
          borderBottom: "1px solid var(--border-color)",
          background: preview === candidate ? "var(--background-color)" : undefined,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.5rem" }}>
          <strong>
            Con {slotLabel(candidate.s2)} · {candidate.teachers.length} docenti
          </strong>
          <button className="btn btn-primary btn-sm" onClick={() => applySwap(candidate)}>
            Applica
          </button>
        </div>
        <ul style={{ margin: "0.5rem 0 0", paddingLeft: "1.25rem", fontSize: "0.875rem" }}>
          {candidate.teachers.map((teacher) => (
            <li key={teacher.teacher_id}>
              {teacher.teacher}: {slotLabel(s1)} {free(teacher.before_s1)} → {free(teacher.before_s2)};{" "}
              {slotLabel(candidate.s2)} {free(teacher.before_s2)} → {free(teacher.before_s1)}
            </li>
          ))}
        </ul>
        {candidate.warnings.map((warning, warningIndex) => (
          <div key={warningIndex} className="status-badge status-warning" style={{ marginTop: "0.5rem" }}>
            {warning.teacher}, {DAY_ORDER[warning.day]}: {WARNING_LABELS[warning.metric]} {warning.before} →{" "}
            {warning.after}
          </div>
        ))}
      </li>
    );
  };

  const renderSuggestions = () => {
    if (!selection) {
      return <p className="empty-state">Seleziona una lezione nella griglia per vedere i cambi possibili.</p>;
    }
    if (suggestQuery.isPending) return <p className="loading">Cerco i cambi...</p>;
    if (suggestQuery.isError) {
      return <p className="form-error">{getApiErrorMessage(suggestQuery.error, "Errore nella ricerca dei cambi")}</p>;
    }
    if (suggestQuery.data.length === 0) {
      return <p className="empty-state">Nessun cambio possibile per questa lezione.</p>;
    }
    return <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>{suggestQuery.data.map(renderCandidate)}</ul>;
  };

  const schedule = savedQuery.data;
  const draftError =
    draftQuery.isError && !unlinked ? getApiErrorMessage(draftQuery.error, "Errore nel caricamento della bozza") : null;

  return (
    <div>
      <div className="page-header">
        <h2>Cambi{schedule ? `: ${schedule.nickname || schedule.name}` : ""}</h2>
        <Link to="/scheduling" state={{ tab: "history" }} className="btn btn-secondary">
          Torna agli orari
        </Link>
      </div>

      {unlinked && (
        <div className="card form-error" style={{ marginBottom: "1rem" }}>
          <p>
            Questo orario non corrisponde più ai dati attuali, quindi non è modificabile. Lezioni non
            ricollegate (bordate in rosso):
          </p>
          <ul>
            {unlinked.map((lesson, index) => (
              <li key={index}>
                {slotLabel(lesson)}: {lesson.teacher}, {lesson.class}, {lesson.matter}
              </li>
            ))}
          </ul>
        </div>
      )}
      {draftError && <p className="form-error">{draftError}</p>}

      {!unlinked && (
        <div className="card" style={{ marginBottom: "1rem", display: "flex", gap: "1rem", alignItems: "flex-end", flexWrap: "wrap" }}>
          <span>
            Cambi applicati: <strong>{applied.length}</strong>
          </span>
          <button className="btn btn-secondary" onClick={undo} disabled={applied.length === 0}>
            Annulla ultimo
          </button>
          <div className="form-group" style={{ marginBottom: 0, flex: 1, minWidth: "200px" }}>
            <label htmlFor="swap-nickname">Nome del nuovo orario</label>
            <input
              id="swap-nickname"
              type="text"
              value={nickname}
              maxLength={255}
              onChange={(e) => setNickname(e.target.value)}
              placeholder={schedule ? `${schedule.nickname || schedule.name} (cambi)` : ""}
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={() => saveMutation.mutate()}
            disabled={applied.length === 0 || saveMutation.isPending}
          >
            {saveMutation.isPending ? "Salvo..." : "Salva come nuovo orario"}
          </button>
          {saveMutation.isError && (
            <p className="form-error">{getApiErrorMessage(saveMutation.error, "Errore nel salvataggio")}</p>
          )}
        </div>
      )}

      <div style={{ display: "flex", gap: "1rem", alignItems: "flex-start", flexWrap: "wrap" }}>
        <div className="card" style={{ flex: "3 1 600px", overflowX: "auto" }}>
          {draftQuery.isPending ? (
            <p className="loading">Carico l'orario...</p>
          ) : (
            <table style={{ borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th rowSpan={2} style={{ textAlign: "left", padding: "0.25rem 0.5rem" }}>
                    Docente
                  </th>
                  {DAY_ORDER.map((day) => (
                    <th key={day} colSpan={HOUR_ORDER.length} style={{ borderLeft: "2px solid var(--border-color)" }}>
                      {day}
                    </th>
                  ))}
                </tr>
                <tr>
                  {DAY_ORDER.flatMap((day) =>
                    HOUR_ORDER.map((_, hourIndex) => (
                      <th key={`${day}-${hourIndex}`} style={{ fontSize: "0.75rem", fontWeight: "normal" }}>
                        {hourIndex + 1}a
                      </th>
                    ))
                  )}
                </tr>
              </thead>
              <tbody>
                {teachers.map((teacher) => (
                  <tr key={teacher}>
                    <td style={{ whiteSpace: "nowrap", padding: "0.25rem 0.5rem" }}>{teacher}</td>
                    {DAY_ORDER.flatMap((_, day) =>
                      HOUR_ORDER.map((_, hourIndex) => renderCell(teacher, { day, hour: hourIndex + 1 }))
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {!unlinked && (
          <div className="card" style={{ flex: "1 1 320px" }}>
            <div className="card-header">
              <h3>
                {selection
                  ? `Cambi per ${selection.teacher}, ${slotLabel(selection.slot)}`
                  : "Cambi possibili"}
              </h3>
            </div>
            {renderSuggestions()}
          </div>
        )}
      </div>
    </div>
  );
}
