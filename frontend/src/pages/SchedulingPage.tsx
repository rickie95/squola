import { useState, useEffect } from "react";
import { schedulingApi } from "../api";
import type {
  GeneratedSchedule,
  SchedulingPreview,
  ScheduleSlot,
  SavedScheduleListItem,
  SavedSchedule,
} from "../types";

type ViewMode = "by_class" | "by_teacher" | "by_day";
type TabMode = "generate" | "history";

const DAY_ORDER = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"];
const HOUR_ORDER = [
  "08:00-09:00",
  "09:00-10:00",
  "10:00-11:00",
  "11:00-12:00",
  "12:00-13:00",
];

const sortByDayThenHour = (a: ScheduleSlot, b: ScheduleSlot) =>
  DAY_ORDER.indexOf(a.day) - DAY_ORDER.indexOf(b.day) ||
  HOUR_ORDER.indexOf(a.hour) - HOUR_ORDER.indexOf(b.hour);

export default function SchedulingPage() {
  const [tabMode, setTabMode] = useState<TabMode>("generate");
  const [preview, setPreview] = useState<SchedulingPreview | null>(null);
  const [schedule, setSchedule] = useState<GeneratedSchedule | null>(null);
  const [savedSchedules, setSavedSchedules] = useState<SavedScheduleListItem[]>([]);
  const [selectedSavedSchedule, setSelectedSavedSchedule] = useState<SavedSchedule | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("by_class");
  const [timeLimit, setTimeLimit] = useState(30);
  const [nickname, setNickname] = useState("");
  const [editingNickname, setEditingNickname] = useState<number | null>(null);
  const [newNickname, setNewNickname] = useState("");

  useEffect(() => {
    fetchPreview();
    fetchSavedSchedules();
  }, []);

  const fetchPreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await schedulingApi.preview();
      setPreview(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load scheduling data");
    } finally {
      setLoading(false);
    }
  };

  const fetchSavedSchedules = async () => {
    try {
      const data = await schedulingApi.listSaved();
      setSavedSchedules(data);
    } catch (err: any) {
      console.error("Failed to fetch saved schedules", err);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const data = await schedulingApi.generate({
        time_limit_seconds: timeLimit,
        nickname: nickname || undefined,
      });
      setSchedule(data);
      setNickname("");
      fetchSavedSchedules(); // Refresh the list
    } catch (err: any) {
      setError(err.response?.data?.detail || "Errore durante la generazione dell'orario");
    } finally {
      setGenerating(false);
    }
  };

  const handleLoadSavedSchedule = async (id: number) => {
    try {
      const data = await schedulingApi.getSaved(id);
      setSelectedSavedSchedule(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Errore durante il caricamento dell'orario");
    }
  };

  const handleDeleteSchedule = async (id: number) => {
    if (!confirm("Sei sicuro di voler cancellare questo orario?")) return;
    try {
      await schedulingApi.deleteSaved(id);
      fetchSavedSchedules();
      if (selectedSavedSchedule?.id === id) {
        setSelectedSavedSchedule(null);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Errore durante la cancellazione dell'orario");
    }
  };

  const handleUpdateNickname = async (id: number) => {
    try {
      await schedulingApi.updateSaved(id, { nickname: newNickname || undefined });
      setEditingNickname(null);
      setNewNickname("");
      fetchSavedSchedules();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to update nickname");
    }
  };

  const downloadSchedule = () => {
    const scheduleToDownload = tabMode === "generate" ? schedule : selectedSavedSchedule;
    if (!scheduleToDownload) return;

    const dataToDownload = tabMode === "generate"
      ? scheduleToDownload
      : {
          metadata: {
            status: selectedSavedSchedule!.status,
            solve_time_seconds: selectedSavedSchedule!.solve_time_seconds,
            total_slots: selectedSavedSchedule!.total_slots,
            created_at: selectedSavedSchedule!.created_at,
          },
          schedule: selectedSavedSchedule!.schedule_data,
        };

    const blob = new Blob([JSON.stringify(dataToDownload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `schedule_${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderPreview = () => {
    if (!preview) return null;

    return (
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-header">
          <h3>Anteprima orario</h3>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
            gap: "1rem",
            marginBottom: "1.5rem",
          }}
        >
          <div className="stat-card">
            <div className="stat-value">{preview.summary.teachers_count}</div>
            <div className="stat-label">Insegnanti</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{preview.summary.classes_count}</div>
            <div className="stat-label">Classi</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {preview.summary.assignments_count}
            </div>
            <div className="stat-label">Materie</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {preview.summary.total_hours_to_schedule}
            </div>
            <div className="stat-label">Ore da programmare</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {preview.summary.total_slots_available}
            </div>
            <div className="stat-label">Slot disponibili</div>
          </div>
        </div>

        {preview.issues.length > 0 && (
          <div
            style={{
              backgroundColor: "#fef2f2",
              border: "1px solid #fecaca",
              borderRadius: "0.5rem",
              padding: "1rem",
              marginBottom: "1rem",
            }}
          >
            <h4 style={{ color: "#dc2626", marginBottom: "0.5rem" }}>
              ⚠️ Potenziali problemi
            </h4>
            <ul style={{ margin: 0, paddingLeft: "1.5rem" }}>
              {preview.issues.map((issue) => (
                <li key={issue} style={{ color: "#991b1b" }}>
                  {issue}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div style={{ display: "flex", gap: "1rem", alignItems: "flex-end", flexWrap: "wrap" }}>
          <div className="form-group" style={{ marginBottom: 0, flex: 1, minWidth: "150px" }}>
            <label htmlFor="timeLimit">Tempo max per il calcolo</label>
            <input
              type="number"
              id="timeLimit"
              value={timeLimit}
              onChange={(e) => setTimeLimit(Number(e.target.value))}
              min={1}
              max={600}
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0, flex: 2, minWidth: "200px" }}>
            <label htmlFor="nickname">Nome (optional)</label>
            <input
              type="text"
              id="nickname"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              placeholder="e.g., Orario provvisorio settembre"
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={handleGenerate}
            disabled={
              generating || preview.summary.assignments_count === 0
            }
          >
            {generating ? (
              <>
                <span className="spinner"></span> Sto calcolando...
              </>
            ) : (
              "Genera Orario"
            )}
          </button>
        </div>
      </div>
    );
  };

  const renderSavedSchedulesList = () => {
    return (
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-header">
          <h3>Orari salvati</h3>
        </div>

        {savedSchedules.length === 0 ? (
          <div className="empty-state">
            <p>Nessun orario salvato al momento.</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Nickname</th>
                  <th>Stato</th>
                  <th>Slot</th>
                  <th>Creato il</th>
                  <th>Azioni</th>
                </tr>
              </thead>
              <tbody>
                {savedSchedules.map((s) => (
                  <tr key={s.id}>
                    <td>{s.name}</td>
                    <td>
                      {editingNickname === s.id ? (
                        <div style={{ display: "flex", gap: "0.5rem" }}>
                          <input
                            type="text"
                            value={newNickname}
                            onChange={(e) => setNewNickname(e.target.value)}
                            placeholder="Inserisci il nickname"
                            style={{ width: "120px" }}
                          />
                          <button
                            className="btn btn-primary"
                            style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }}
                            onClick={() => handleUpdateNickname(s.id)}
                          >
                            Salva
                          </button>
                          <button
                            className="btn btn-secondary"
                            style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }}
                            onClick={() => setEditingNickname(null)}
                          >
                            Annulla
                          </button>
                        </div>
                      ) : (
                        <button
                          className="btn btn-secondary"
                          style={{
                            padding: "0.25rem 0.5rem",
                            fontSize: "0.875rem",
                            color: s.nickname ? "inherit" : "var(--text-secondary)",
                            background: "transparent",
                            border: "1px dashed var(--border-color)",
                          }}
                          onClick={() => {
                            setEditingNickname(s.id);
                            setNewNickname(s.nickname || "");
                          }}
                          title="Clicca per modificare"
                        >
                          {s.nickname || "Aggiungi nickname"}
                        </button>
                      )}
                    </td>
                    <td>
                      <span
                        className={`status-badge ${s.status === "OPTIMAL" ? "status-success" : "status-warning"}`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td>{s.total_slots}</td>
                    <td>{new Date(s.created_at).toLocaleString()}</td>
                    <td>
                      <div style={{ display: "flex", gap: "0.5rem" }}>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }}
                          onClick={() => handleLoadSavedSchedule(s.id)}
                        >
                          Visualizza
                        </button>
                        <button
                          className="btn btn-danger"
                          style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }}
                          onClick={() => handleDeleteSchedule(s.id)}
                        >
                          Cancella
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  const renderSelectedSavedSchedule = () => {
    if (!selectedSavedSchedule) return null;

    const scheduleData = selectedSavedSchedule.schedule_data[viewMode];

    return (
      <div className="card">
        <div
          className="card-header"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <h3>
              {selectedSavedSchedule.nickname || selectedSavedSchedule.name}
            </h3>
            <p
              style={{
                fontSize: "0.875rem",
                color: "var(--text-secondary)",
                marginTop: "0.25rem",
              }}
            >
              Status: <strong>{selectedSavedSchedule.status}</strong> |{" "}
              {selectedSavedSchedule.total_slots} slots |{" "}
              Creato il: {new Date(selectedSavedSchedule.created_at).toLocaleString()}
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button className="btn btn-secondary" onClick={downloadSchedule}>
              Scarica JSON
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => setSelectedSavedSchedule(null)}
            >
              Chiudi
            </button>
          </div>
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
            <button
              className={`btn ${viewMode === "by_class" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setViewMode("by_class")}
            >
              Per Classe
            </button>
            <button
              className={`btn ${viewMode === "by_teacher" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setViewMode("by_teacher")}
            >
              Per insegnante
            </button>
            <button
              className={`btn ${viewMode === "by_day" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setViewMode("by_day")}
            >
              Per giorno
            </button>
          </div>
        </div>

        {renderScheduleTable(scheduleData)}
      </div>
    );
  };

  const renderScheduleTable = (scheduleData: Record<string, ScheduleSlot[]>) => {
    if (viewMode === "by_day") {
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {DAY_ORDER.map((day) => (
            <div key={day}>
              <h4 style={{ marginBottom: "0.75rem", color: "var(--primary-color)" }}>
                {day}
              </h4>
              {scheduleData[day]?.length > 0 ? (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Ora</th>
                        <th>Classe</th>
                        <th>Insegnante</th>
                        <th>Materia</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...(scheduleData[day] || [])]
                        .sort(
                          (a: ScheduleSlot, b: ScheduleSlot) =>
                            HOUR_ORDER.indexOf(a.hour) - HOUR_ORDER.indexOf(b.hour)
                        )
                        .map((slot: ScheduleSlot) => (
                          <tr key={`${slot.hour}-${slot.class}-${slot.matter}`}>
                            <td>{slot.hour}</td>
                            <td>{slot.class}</td>
                            <td>{slot.teacher}</td>
                            <td>{slot.matter}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p style={{ color: "var(--text-secondary)", fontStyle: "italic" }}>
                  Nessuna classe prevista
                </p>
              )}
            </div>
          ))}
        </div>
      );
    }

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {Object.entries(scheduleData)
          .sort(([a], [b]) => a.localeCompare(b, "it"))
          .map(([key, slots]) => (
          <div key={key}>
            <h4 style={{ marginBottom: "0.75rem", color: "var(--primary-color)" }}>
              {key}
            </h4>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Giorno</th>
                    <th>Ora</th>
                    {viewMode === "by_class" && <th>Insegnante</th>}
                    {viewMode === "by_teacher" && <th>Classe</th>}
                    <th>Materie</th>
                  </tr>
                </thead>
                <tbody>
                  {[...slots]
                    .sort(sortByDayThenHour)
                    .map((slot: ScheduleSlot) => (
                      <tr key={`${slot.day}-${slot.hour}-${slot.matter}`}>
                        <td>{slot.day}</td>
                        <td>{slot.hour}</td>
                        {viewMode === "by_class" && <td>{slot.teacher}</td>}
                        {viewMode === "by_teacher" && <td>{slot.class}</td>}
                        <td>{slot.matter}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderScheduleGrid = () => {
    if (!schedule) return null;

    const scheduleData = schedule.schedule[viewMode];

    return (
      <div className="card">
        <div
          className="card-header"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <h3>Genera Orario</h3>
            <p
              style={{
                fontSize: "0.875rem",
                color: "var(--text-secondary)",
                marginTop: "0.25rem",
              }}
            >
              Status: <strong>{schedule.metadata.status}</strong> | Calcolato in{" "}
              {schedule.metadata.solve_time_seconds.toFixed(3)}s |{" "}
              {schedule.metadata.total_slots} slots
            </p>
          </div>
          <button className="btn btn-secondary" onClick={downloadSchedule}>
            Scarica JSON
          </button>
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <div
            style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}
          >
            <button
              className={`btn ${viewMode === "by_class" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setViewMode("by_class")}
            >
              Per Classe
            </button>
            <button
              className={`btn ${viewMode === "by_teacher" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setViewMode("by_teacher")}
            >
              Per Insegnante
            </button>
            <button
              className={`btn ${viewMode === "by_day" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setViewMode("by_day")}
            >
              Per Giorno
            </button>
          </div>
        </div>

        {renderScheduleTable(scheduleData)}
      </div>
    );
  };

  return (
    <div>
      <div className="page-header">
        <h2>Orario</h2>
        <p>Genera e gestisci gli orari</p>
      </div>

      {error && (
        <div
          style={{
            backgroundColor: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: "0.5rem",
            padding: "1rem",
            marginBottom: "1rem",
            color: "#dc2626",
          }}
        >
          {error}
        </div>
      )}

      {/* Tab Navigation */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem" }}>
        <button
          className={`btn ${tabMode === "generate" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setTabMode("generate")}
        >
          Calcola un nuovo orario
        </button>
        <button
          className={`btn ${tabMode === "history" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setTabMode("history")}
        >
          Orari salvati ({savedSchedules.length})
        </button>
      </div>

      {loading ? (
        <div className="card">
          <div className="loading-state">
            <span className="spinner"></span> Carico gli orari salvati...
          </div>
        </div>
      ) : (
        <>
          {tabMode === "generate" && (
            <>
              {renderPreview()}
              {schedule && renderScheduleGrid()}
            </>
          )}
          {tabMode === "history" && (
            <>
              {renderSavedSchedulesList()}
              {selectedSavedSchedule && renderSelectedSavedSchedule()}
            </>
          )}
        </>
      )}
    </div>
  );
}
