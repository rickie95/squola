import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { mattersApi } from "../api";
import type { Matter, MatterCreate } from "../types";
import { MatterRequirement, REQUIREMENT_LABELS } from "../types";
import Modal from "../components/Modal";

export default function MattersPage() {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMatter, setEditingMatter] = useState<Matter | null>(null);
  const [formData, setFormData] = useState<MatterCreate>({ name: "", default_requirements: [] });

  const { data: matters, isLoading } = useQuery({
    queryKey: ["matters"],
    queryFn: mattersApi.list,
  });

  const createMutation = useMutation({
    mutationFn: mattersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matters"] });
      closeModal();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: MatterCreate }) =>
      mattersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matters"] });
      closeModal();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: mattersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matters"] });
    },
  });

  const openCreateModal = () => {
    setEditingMatter(null);
    setFormData({ name: "", default_requirements: [] });
    setIsModalOpen(true);
  };

  const openEditModal = (matter: Matter) => {
    setEditingMatter(matter);
    setFormData({ name: matter.name, default_requirements: matter.default_requirements || [] });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingMatter(null);
    setFormData({ name: "", default_requirements: [] });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingMatter) {
      updateMutation.mutate({ id: editingMatter.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleDelete = (id: number) => {
    if (globalThis.confirm("Are you sure you want to delete this matter?")) {
      deleteMutation.mutate(id);
    }
  };

  if (isLoading) {
    return <div className="loading">Loading matters...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h2>Subject Matters</h2>
        <p>Manage the subjects taught in your school</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>All Matters</h3>
          <button className="btn btn-primary" onClick={openCreateModal}>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="16" height="16">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Add Matter
          </button>
        </div>

        {matters && matters.length > 0 ? (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Default Requirements</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {matters.map((matter) => (
                  <tr key={matter.id}>
                    <td>{matter.id}</td>
                    <td>{matter.name}</td>
                    <td>
                      {matter.default_requirements && matter.default_requirements.length > 0 ? (
                        <div className="requirements-tags">
                          {matter.default_requirements.map((req) => (
                            <span key={req} className="requirement-tag">
                              {REQUIREMENT_LABELS[req]}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span style={{ color: "var(--text-secondary)" }}>None</span>
                      )}
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => openEditModal(matter)}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDelete(matter.id)}
                        >
                          Delete
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
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
            </svg>
            <p>No matters found. Add your first subject matter!</p>
          </div>
        )}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingMatter ? "Edit Matter" : "Add New Matter"}
      >
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Name</label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Mathematics, History, Science"
              required
            />
          </div>
          <div className="form-group">
            <label>Default Requirements</label>
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
              These requirements will be applied by default when assigning this matter to a class.
            </p>
            <div className="checkbox-group">
              {Object.values(MatterRequirement).map((req) => (
                <label key={req} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.default_requirements?.includes(req) || false}
                    onChange={(e) => {
                      const currentReqs = formData.default_requirements || [];
                      if (e.target.checked) {
                        setFormData({ ...formData, default_requirements: [...currentReqs, req] });
                      } else {
                        setFormData({
                          ...formData,
                          default_requirements: currentReqs.filter((r) => r !== req),
                        });
                      }
                    }}
                  />
                  {REQUIREMENT_LABELS[req]}
                </label>
              ))}
            </div>
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={closeModal}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {editingMatter ? "Update" : "Create"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
