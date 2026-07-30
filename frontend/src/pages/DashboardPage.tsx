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
      label: "Materie",
      value: matters?.length || 0,
      link: "/matters",
      color: "#4f46e5",
    },
    {
      label: "Insegnanti",
      value: teachers?.length || 0,
      link: "/teachers",
      color: "#0891b2",
    },
    {
      label: "Classi",
      value: classes?.length || 0,
      link: "/classes",
      color: "#059669",
    },
  ];

  return (
    <div>
      <div className="page-header">
        <h2>Home</h2>
        <p>Panoramica dei dati della tua scuola</p>
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
          <h3>Guida Rapida</h3>
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
              <strong>Aggiungi le materie</strong>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginTop: "0.25rem" }}>
                Inizia aggiungendo le materie presenti nella tua scuola (e.g., Matematica, Storia, Scienze).
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
              <strong>Aggiungi gli Insegnanti</strong>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginTop: "0.25rem" }}>
                Crea l'anagrafica insegnanti e associali alle materie.
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
              <strong>Crea le Classi</strong>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginTop: "0.25rem" }}>
                Aggiungi le classi (e.g., IIIA, IIB) e assegna le materie con gli insegnanti e le ore settimanali previste.
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
              <strong>Genera l'orario</strong>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginTop: "0.25rem" }}>
                Una volta inseriti tutti i dati, usa la sezione Orario per generare uno schema ottimizzato secondo i tuoi criteri.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
