import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi } from "../api";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(from || "/", { replace: true });
    },
    onError: () => {
      setError("Credenziali non valide");
    },
  });

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    loginMutation.mutate({ username, password });
  };

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "1rem" }}>
      <div className="card" style={{ width: "100%", maxWidth: "420px", marginBottom: 0 }}>
        <div className="page-header" style={{ marginBottom: "1rem" }}>
          <h2>Accedi</h2>
          <p>Inserisci username e password</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error ? (
            <div style={{ color: "var(--danger-color)", fontSize: "0.875rem", marginBottom: "1rem" }}>
              {error}
            </div>
          ) : null}
          <button className="btn btn-primary" type="submit" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? "Accesso in corso..." : "Accedi"}
          </button>
        </form>
        <p style={{ marginTop: "1rem", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
          Non hai ancora un account? <Link to="/register">Registrati</Link>
        </p>
      </div>
    </div>
  );
}

