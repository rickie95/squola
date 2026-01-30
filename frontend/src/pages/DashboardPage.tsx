import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { mattersApi, teachersApi, classesApi } from "../api";

export default function DashboardPage() {
  const { data: matters } = useQuery({
    queryKey: ["matters"],
    queryFn: mattersApi.list,
  });

  const { data: teachers } = useQuery({
    queryKey: ["teachers"],
    queryFn: teachersApi.list,
  });

  const { data: classes } = useQuery({
    queryKey: ["classes"],
    queryFn: classesApi.list,
  });

  const stats = [
    {
      label: "Subject Matters",
      value: matters?.length || 0,
      link: "/matters",
      color: "#4f46e5",
    },
    {
      label: "Teachers",
      value: teachers?.length || 0,
      link: "/teachers",
      color: "#0891b2",
    },
    {
      label: "Classes",
      value: classes?.length || 0,
      link: "/classes",
      color: "#059669",
    },
  ];

  return (
    <div>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Overview of your school scheduling data</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>
        {stats.map((stat) => (
          <Link
            key={stat.label}
            to={stat.link}
            style={{ textDecoration: "none" }}
          >
            <div className="card" style={{ textAlign: "center", cursor: "pointer", transition: "transform 0.2s" }}>
              <div style={{ fontSize: "2.5rem", fontWeight: "bold", color: stat.color }}>
                {stat.value}
              </div>
              <div style={{ color: "var(--text-secondary)", marginTop: "0.5rem" }}>
                {stat.label}
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Quick Start Guide</h3>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: "1rem" }}>
            <div style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: "var(--primary-color)",
              color: "white",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: "bold",
              flexShrink: 0,
            }}>
              1
            </div>
            <div>
              <strong>Add Subject Matters</strong>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginTop: "0.25rem" }}>
                Start by adding the subjects taught in your school (e.g., Mathematics, History, Science).
              </p>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "flex-start", gap: "1rem" }}>
            <div style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: "var(--primary-color)",
              color: "white",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: "bold",
              flexShrink: 0,
            }}>
              2
            </div>
            <div>
              <strong>Add Teachers</strong>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginTop: "0.25rem" }}>
                Add teachers to the roster and assign them the subjects they can teach.
              </p>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "flex-start", gap: "1rem" }}>
            <div style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: "var(--primary-color)",
              color: "white",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: "bold",
              flexShrink: 0,
            }}>
              3
            </div>
            <div>
              <strong>Create Classes</strong>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginTop: "0.25rem" }}>
                Create school classes (e.g., IIIA, IIB) and assign subjects with their teachers and weekly hours.
              </p>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "flex-start", gap: "1rem" }}>
            <div style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: "var(--primary-color)",
              color: "white",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: "bold",
              flexShrink: 0,
            }}>
              4
            </div>
            <div>
              <strong>Generate Schedule</strong>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginTop: "0.25rem" }}>
                Once all data is entered, use the Scheduling page to generate an optimized timetable.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
