import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { accountApi, authApi } from "../api";
import { useAuth } from "../auth/AuthProvider";

export default function AccountPage() {
  const queryClient = useQueryClient();
  const { session, isLoading } = useAuth();
  const [workspaceName, setWorkspaceName] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [workspaceMessage, setWorkspaceMessage] = useState<string | null>(null);

  const renameWorkspaceMutation = useMutation({
    mutationFn: accountApi.renameWorkspace,
    onSuccess: async (data) => {
      await queryClient.setQueryData(["auth", "me"], data);
      setWorkspaceMessage("Nome workspace aggiornato");
    },
    onError: (err: any) => {
      setWorkspaceMessage(err?.response?.data?.detail || "Errore durante l'aggiornamento");
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: accountApi.changePassword,
    onSuccess: async () => {
      setCurrentPassword("");
      setNewPassword("");
      setPasswordMessage("Password aggiornata. Effettua nuovamente il login.");
      await queryClient.setQueryData(["auth", "me"], null);
      window.location.href = "/login";
    },
    onError: (err: any) => {
      setPasswordMessage(err?.response?.data?.detail || "Errore durante il cambio password");
    },
  });

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: async () => {
      await queryClient.setQueryData(["auth", "me"], null);
      window.location.href = "/login";
    },
  });

  if (isLoading || !session) {
    return <div className="loading">Carico account...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h2>Account</h2>
        <p>Gestisci workspace, password e sessione</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Profilo</h3>
        </div>
        <p><strong>Username:</strong> {session.user.username}</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Workspace</h3>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setWorkspaceMessage(null);
            renameWorkspaceMutation.mutate({ name: workspaceName || session.workspace.name });
          }}
        >
          <div className="form-group">
            <label htmlFor="workspaceName">Nome workspace</label>
            <input
              id="workspaceName"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              placeholder={session.workspace.name}
            />
          </div>
          {workspaceMessage ? (
            <p style={{ fontSize: "0.875rem", marginBottom: "1rem" }}>{workspaceMessage}</p>
          ) : null}
          <button className="btn btn-primary" disabled={renameWorkspaceMutation.isPending}>
            Salva nome workspace
          </button>
        </form>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Password</h3>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setPasswordMessage(null);
            changePasswordMutation.mutate({
              current_password: currentPassword,
              new_password: newPassword,
            });
          }}
        >
          <div className="form-group">
            <label htmlFor="currentPassword">Password attuale</label>
            <input
              id="currentPassword"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="newPassword">Nuova password (min 12 caratteri)</label>
            <input
              id="newPassword"
              type="password"
              minLength={12}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
          </div>
          {passwordMessage ? (
            <p style={{ fontSize: "0.875rem", marginBottom: "1rem" }}>{passwordMessage}</p>
          ) : null}
          <button className="btn btn-primary" disabled={changePasswordMutation.isPending}>
            Aggiorna password
          </button>
        </form>
      </div>

      <div className="card">
        <button
          className="btn btn-secondary"
          onClick={() => logoutMutation.mutate()}
          disabled={logoutMutation.isPending}
        >
          Logout
        </button>
      </div>
    </div>
  );
}

