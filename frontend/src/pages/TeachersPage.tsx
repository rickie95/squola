import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { teachersApi, mattersApi } from "../api";
import type { Teacher, TeacherWithMatters, TeacherCreate, SchedulePreference } from "../types";
import Modal from "../components/Modal";

const SCHEDULE_PREFERENCES: { value: SchedulePreference; label: string }[] = [
  { value: "none", label: "Nessuna preferenza" },
  { value: "early", label: "Preferisce le prime ore" },
  { value: "late", label: "Preferisce le ultime ore" },
  { value: "minimize_gaps", label: "Minimizza i buchi" },
  { value: "maximize_gaps", label: "Massimizza i buchi" },
];

export default function TeachersPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState<TeacherWithMatters | null>(null);
  const [formData, setFormData] = useState<TeacherCreate>({
    first_name: "",
    last_name: "",
    email: "",
    schedule_preference: "none" as SchedulePreference,
    matter_ids: [],
  });

  const { data: teachers, isLoading: teachersLoading } = useQuery({
    queryKey: ["teachers"],
    queryFn: teachersApi.list,
  });

  const { data: matters } = useQuery({
    queryKey: ["matters"],
    queryFn: mattersApi.list,
  });

  const createMutation = useMutation({
    mutationFn: teachersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teachers"] });
      closeModal();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: TeacherCreate }) =>
      teachersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teachers"] });
      closeModal();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: teachersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teachers"] });
    },
  });

  const openCreateModal = () => {
    setEditingTeacher(null);
    setFormData({
      first_name: "",
      last_name: "",
      email: "",
      schedule_preference: "none" as SchedulePreference,
      matter_ids: [],
    });
    setIsModalOpen(true);
  };

  const openEditModal = async (teacher: Teacher) => {
    // Fetch full teacher details including matters
    const fullTeacher = await teachersApi.get(teacher.id);
    setEditingTeacher(fullTeacher);
    setFormData({
      first_name: fullTeacher.first_name,
      last_name: fullTeacher.last_name,
      email: fullTeacher.email || "",
      schedule_preference: fullTeacher.schedule_preference,
      matter_ids: fullTeacher.matters.map((m) => m.id),
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingTeacher(null);
    setFormData({
      first_name: "",
      last_name: "",
      email: "",
      schedule_preference: "none" as SchedulePreference,
      matter_ids: [],
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      ...formData,
      email: formData.email || null,
    };
    if (editingTeacher) {
      updateMutation.mutate({ id: editingTeacher.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleDelete = (id: number) => {
    if (globalThis.confirm("Sei sicuro di voler rimuovere questo insegnante dall'elenco?")) {
      deleteMutation.mutate(id);
    }
  };

  const toggleMatter = (matterId: number) => {
    const currentIds = formData.matter_ids || [];
    const newIds = currentIds.includes(matterId)
      ? currentIds.filter((id) => id !== matterId)
      : [...currentIds, matterId];
    setFormData({ ...formData, matter_ids: newIds });
  };

  if (teachersLoading) {
    return <div className="loading">Carico la lista insegnanti...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h2>Insegnanti</h2>
        <p>Gestisci l'elenco dei docenti</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Lista insegnanti</h3>
          <button className="btn btn-primary" onClick={openCreateModal}>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="16" height="16">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Aggiungi un insegnante
          </button>
        </div>

        {teachers && teachers.length > 0 ? (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Nome</th>
                  <th>Email</th>
                  <th>Preferenze</th>
                  <th>Azioni</th>
                </tr>
              </thead>
              <tbody>
                {teachers.map((teacher) => (
                  <tr key={teacher.id}>
                    <td>{teacher.id}</td>
                    <td>{teacher.first_name} {teacher.last_name}</td>
                    <td>{teacher.email || "-"}</td>
                    <td>
                      <span className="badge">
                        {SCHEDULE_PREFERENCES.find((p) => p.value === teacher.schedule_preference)?.label || teacher.schedule_preference}
                      </span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => navigate(`/teachers/${teacher.id}`)}
                        >
                          Scheda
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => openEditModal(teacher)}
                        >
                          Modifica
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDelete(teacher.id)}
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
        ) : (
          <div className="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
            </svg>
            <p>Nessun isegnante presente, aggiungine uno!</p>
          </div>
        )}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingTeacher ? "Modifica un insegnante" : "Aggiungi un insegnante"}
      >
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name">Nome</label>
              <input
                type="text"
                id="first_name"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="last_name">Cognome</label>
              <input
                type="text"
                id="last_name"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email">Email (opzionale)</label>
            <input
              type="email"
              id="email"
              value={formData.email || ""}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label htmlFor="schedule_preference">Preferenze d'orario</label>
            <select
              id="schedule_preference"
              value={formData.schedule_preference}
              onChange={(e) => setFormData({ ...formData, schedule_preference: e.target.value as SchedulePreference })}
            >
              {SCHEDULE_PREFERENCES.map((pref) => (
                <option key={pref.value} value={pref.value}>
                  {pref.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Materie insegnate</label>
            {matters && matters.length > 0 ? (
              <div className="checkbox-list">
                {matters.map((matter) => (
                  <label key={matter.id} className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={formData.matter_ids?.includes(matter.id) || false}
                      onChange={() => toggleMatter(matter.id)}
                    />
                    {matter.name}
                  </label>
                ))}
              </div>
            ) : (
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                Nessuna materia. Aggiungine una con il bottone in alto.
              </p>
            )}
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={closeModal}>
              Annulla
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {editingTeacher ? "Aggiorna" : "Crea"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
