import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi } from "../api";

export default function RegisterPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      navigate("/", { replace: true });
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail || "Registrazione non riuscita");
    },
  });

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    registerMutation.mutate({
      username,
      password,
      workspace_name: workspaceName || undefined,
    });
  };

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "1rem" }}>
      <div className="card" style={{ width: "100%", maxWidth: "460px", marginBottom: 0 }}>
        <div className="page-header" style={{ marginBottom: "1rem" }}>
          <h2>Registrati</h2>
          <p>Crea il tuo account e workspace</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              minLength={3}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password (min 12 caratteri)</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={12}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="workspace_name">Nome workspace (opzionale)</label>
            <input
              id="workspace_name"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              placeholder="Es. Liceo Scientifico Rossi"
            />
          </div>
          {error ? (
            <div style={{ color: "var(--danger-color)", fontSize: "0.875rem", marginBottom: "1rem" }}>
              {error}
            </div>
          ) : null}
          <button className="btn btn-primary" type="submit" disabled={registerMutation.isPending}>
            {registerMutation.isPending ? "Creazione in corso..." : "Crea account"}
          </button>
        </form>
        <p style={{ marginTop: "1rem", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
          Hai già un account? <Link to="/login">Accedi</Link>
        </p>
      </div>
    </div>
  );
}

