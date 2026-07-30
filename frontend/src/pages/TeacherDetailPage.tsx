import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { teachersApi } from "../api";
import type { Unavailability } from "../types";

const DAYS = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"];
const HOURS = [
  "08:00–09:00",
  "09:00–10:00",
  "10:00–11:00",
  "11:00–12:00",
  "12:00–13:00",
  "13:00–14:00",
];
const HOURS_PER_DAY = 6;

function buildUnavailableSet(unavailabilities: Unavailability[]): Set<string> {
  return new Set(unavailabilities.map((u) => `${u.day_of_week}-${u.hour_slot}`));
}

export default function TeacherDetailPage() {
  const { id } = useParams<{ id: string }>();
  const teacherId = Number(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: teacher, isLoading } = useQuery({
    queryKey: ["teacher", teacherId],
    queryFn: () => teachersApi.get(teacherId),
    enabled: !isNaN(teacherId),
  });

  const addMutation = useMutation({
    mutationFn: (data: { day_of_week: number; hour_slot: number }) =>
      teachersApi.addUnavailability(teacherId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["teacher", teacherId] }),
  });

  const removeMutation = useMutation({
    mutationFn: (slotId: number) =>
      teachersApi.removeUnavailability(teacherId, slotId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["teacher", teacherId] }),
  });

  if (isLoading) return <div className="loading">Carico la scheda insegnante...</div>;
  if (!teacher) return <div className="empty-state"><p>Insegnante non trovato.</p></div>;

  const unavailable = buildUnavailableSet(teacher.unavailabilities);

  const findSlot = (day: number, hour: number): Unavailability | undefined =>
    teacher.unavailabilities.find(
      (u) => u.day_of_week === day && u.hour_slot === hour
    );

  const toggleSlot = (day: number, hour: number) => {
    const existing = findSlot(day, hour);
    if (existing) {
      removeMutation.mutate(existing.id);
    } else {
      addMutation.mutate({ day_of_week: day, hour_slot: hour });
    }
  };

  const isDayFullyUnavailable = (day: number): boolean =>
    Array.from({ length: HOURS_PER_DAY }, (_, i) => i + 1).every((hour) =>
      unavailable.has(`${day}-${hour}`)
    );

  const toggleDay = (day: number) => {
    if (isDayFullyUnavailable(day)) {
      // Remove all slots for this day
      teacher.unavailabilities
        .filter((u) => u.day_of_week === day)
        .forEach((u) => removeMutation.mutate(u.id));
    } else {
      // Add missing slots for this day
      for (let hour = 1; hour <= HOURS_PER_DAY; hour++) {
        if (!unavailable.has(`${day}-${hour}`)) {
          addMutation.mutate({ day_of_week: day, hour_slot: hour });
        }
      }
    }
  };

  const isMutating = addMutation.isPending || removeMutation.isPending;

  return (
    <div>
      <div className="page-header">
        <div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => navigate("/teachers")}
            style={{ marginBottom: "0.5rem" }}
          >
            ← Torna all'elenco insegnanti
          </button>
          <h2>
            {teacher.first_name} {teacher.last_name}
          </h2>
          <p>{teacher.email || "Email non presente"}</p>
        </div>
      </div>

      {/* Teacher info */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-header">
          <h3>Dettagli</h3>
        </div>
        <div style={{ padding: "1rem", display: "flex", gap: "2rem", flexWrap: "wrap" }}>
          <div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Preferenze
            </span>
            <div style={{ marginTop: "0.25rem" }}>
              <span className="badge">{teacher.schedule_preference}</span>
            </div>
          </div>
          <div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Materie
            </span>
            <div className="badge-list" style={{ marginTop: "0.25rem" }}>
              {teacher.matters.length > 0
                ? teacher.matters.map((m) => (
                    <span key={m.id} className="badge badge-primary">
                      {m.name}
                    </span>
                  ))
                : <span style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>None assigned</span>}
            </div>
          </div>
        </div>
      </div>

      {/* Unavailability grid */}
      <div className="card">
        <div className="card-header">
          <h3>Indisponibilità</h3>
          <span style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
            {teacher.unavailabilities.length} / {DAYS.length * HOURS_PER_DAY} slot bloccati
          </span>
        </div>
        <div style={{ padding: "1rem", overflowX: "auto" }}>
          <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
           Clicca su uno slot per renderlo non disponibile. Clicca sul giorno per bloccare/sbloccare tutto il giorno.
          </p>
          <table style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr>
                <th style={thStyle}></th>
                {DAYS.map((day, dayIdx) => {
                  const full = isDayFullyUnavailable(dayIdx);
                  return (
                    <th key={day} style={{ ...thStyle, cursor: "pointer", userSelect: "none" }}>
                      <button
                        onClick={() => toggleDay(dayIdx)}
                        disabled={isMutating}
                        title={full ? "Clicca per sbloccare tutto il giorno" : "Clicca per sbloccare tutto il giorno"}
                        style={dayHeaderBtnStyle(full)}
                      >
                        {day}
                        {full && (
                          <span style={{ marginLeft: "0.35rem", fontSize: "0.7rem" }}>🚫</span>
                        )}
                      </button>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {HOURS.map((label, hourIdx) => {
                const hour = hourIdx + 1;
                return (
                  <tr key={hour}>
                    <td style={tdLabelStyle}>{label}</td>
                    {DAYS.map((_, dayIdx) => {
                      const key = `${dayIdx}-${hour}`;
                      const blocked = unavailable.has(key);
                      return (
                        <td key={dayIdx} style={tdStyle}>
                          <button
                            onClick={() => toggleSlot(dayIdx, hour)}
                            disabled={isMutating}
                            title={blocked ? "Clicca per ripristinare la disponibilità" : "Clicca per renderlo non disponibile"}
                            style={slotBtnStyle(blocked)}
                          />
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Inline styles ──────────────────────────────────────────────────────────────

const thStyle: React.CSSProperties = {
  padding: "0.5rem 0.75rem",
  textAlign: "center",
  fontWeight: 600,
  fontSize: "0.8rem",
  borderBottom: "2px solid var(--border-color)",
};

const tdStyle: React.CSSProperties = {
  padding: "0.3rem 0.5rem",
  textAlign: "center",
  borderBottom: "1px solid var(--border-color)",
};

const tdLabelStyle: React.CSSProperties = {
  padding: "0.4rem 0.75rem",
  fontSize: "0.8rem",
  color: "var(--text-muted)",
  whiteSpace: "nowrap",
  borderBottom: "1px solid var(--border-color)",
  borderRight: "2px solid var(--border-color)",
};

const dayHeaderBtnStyle = (full: boolean): React.CSSProperties => ({
  background: full ? "var(--danger-color)" : "transparent",
  color: full ? "#fff" : "inherit",
  border: "none",
  borderRadius: "4px",
  padding: "0.25rem 0.5rem",
  cursor: "pointer",
  fontWeight: 600,
  fontSize: "0.8rem",
  width: "100%",
});

const slotBtnStyle = (blocked: boolean): React.CSSProperties => ({
  width: "2.5rem",
  height: "2rem",
  borderRadius: "4px",
  border: "1px solid",
  cursor: "pointer",
  transition: "background 0.1s",
  backgroundColor: blocked ? "var(--danger-color)" : "var(--background-color)",
  borderColor: blocked ? "var(--danger-color)" : "var(--border-color)",
});
