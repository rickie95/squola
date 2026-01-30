import { useState, useEffect } from "react";
import { schedulingApi } from "../api";
import type {
  GeneratedSchedule,
  SchedulingPreview,
  ScheduleSlot,
} from "../types";

type ViewMode = "by_class" | "by_teacher" | "by_day";

const DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const HOUR_ORDER = [
  "08:00-09:00",
  "09:00-10:00",
  "10:00-11:00",
  "11:00-12:00",
  "12:00-13:00",
];

export default function SchedulingPage() {
  const [preview, setPreview] = useState<SchedulingPreview | null>(null);
  const [schedule, setSchedule] = useState<GeneratedSchedule | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("by_class");
  const [timeLimit, setTimeLimit] = useState(30);

  useEffect(() => {
    fetchPreview();
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

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const data = await schedulingApi.generate({
        time_limit_seconds: timeLimit,
      });
      setSchedule(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate schedule");
    } finally {
      setGenerating(false);
    }
  };

  const downloadSchedule = () => {
    if (!schedule) return;
    const blob = new Blob([JSON.stringify(schedule, null, 2)], {
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
          <h3>Scheduling Preview</h3>
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
            <div className="stat-label">Teachers</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{preview.summary.classes_count}</div>
            <div className="stat-label">Classes</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {preview.summary.assignments_count}
            </div>
            <div className="stat-label">Assignments</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {preview.summary.total_hours_to_schedule}
            </div>
            <div className="stat-label">Hours to Schedule</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {preview.summary.total_slots_available}
            </div>
            <div className="stat-label">Slots Available</div>
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
              ⚠️ Potential Issues
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

        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <div className="form-group" style={{ marginBottom: 0, flex: 1 }}>
            <label htmlFor="timeLimit">Time Limit (seconds)</label>
            <input
              type="number"
              id="timeLimit"
              value={timeLimit}
              onChange={(e) => setTimeLimit(Number(e.target.value))}
              min={1}
              max={600}
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={handleGenerate}
            disabled={
              generating || preview.summary.assignments_count === 0
            }
            style={{ alignSelf: "flex-end" }}
          >
            {generating ? (
              <>
                <span className="spinner"></span> Generating...
              </>
            ) : (
              "Generate Schedule"
            )}
          </button>
        </div>
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
            <h3>Generated Schedule</h3>
            <p
              style={{
                fontSize: "0.875rem",
                color: "var(--text-secondary)",
                marginTop: "0.25rem",
              }}
            >
              Status: <strong>{schedule.metadata.status}</strong> | Solved in{" "}
              {schedule.metadata.solve_time_seconds.toFixed(3)}s |{" "}
              {schedule.metadata.total_slots} slots
            </p>
          </div>
          <button className="btn btn-secondary" onClick={downloadSchedule}>
            Download JSON
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
              By Class
            </button>
            <button
              className={`btn ${viewMode === "by_teacher" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setViewMode("by_teacher")}
            >
              By Teacher
            </button>
            <button
              className={`btn ${viewMode === "by_day" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setViewMode("by_day")}
            >
              By Day
            </button>
          </div>
        </div>

        {viewMode === "by_day" ? (
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
                          <th>Hour</th>
                          <th>Class</th>
                          <th>Teacher</th>
                          <th>Subject</th>
                        </tr>
                      </thead>
                      <tbody>
                        {scheduleData[day]
                          .toSorted(
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
                    No classes scheduled
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            {Object.entries(scheduleData).map(([key, slots]) => (
              <div key={key}>
                <h4 style={{ marginBottom: "0.75rem", color: "var(--primary-color)" }}>
                  {key}
                </h4>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Day</th>
                        <th>Hour</th>
                        {viewMode === "by_class" && <th>Teacher</th>}
                        {viewMode === "by_teacher" && <th>Class</th>}
                        <th>Subject</th>
                      </tr>
                    </thead>
                    <tbody>
                      {slots
                        .toSorted(
                          (a, b) =>
                            DAY_ORDER.indexOf(a.day) - DAY_ORDER.indexOf(b.day) ||
                            HOUR_ORDER.indexOf(a.hour) - HOUR_ORDER.indexOf(b.hour)
                        )
                        .map((slot) => (
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
        )}
      </div>
    );
  };

  return (
    <div>
      <div className="page-header">
        <h2>Scheduling</h2>
        <p>Generate and manage school schedules</p>
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

      {loading ? (
        <div className="card">
          <div className="loading-state">
            <span className="spinner"></span> Loading scheduling data...
          </div>
        </div>
      ) : (
        <>
          {renderPreview()}
          {schedule && renderScheduleGrid()}
        </>
      )}
    </div>
  );
}
