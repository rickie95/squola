import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { classesApi, mattersApi, teachersApi } from "../api";
import type {
  SchoolClass,
  SchoolClassWithAssignments,
  SchoolClassCreate,
  ClassMatterAssignmentCreate,
  ClassMatterAssignment,
  Matter,
} from "../types";
import { MatterRequirement, REQUIREMENT_LABELS } from "../types";
import Modal from "../components/Modal";

const ROMAN_NUMERALS = ["I", "II", "III", "IV", "V"];
const SECTIONS = ["A", "B", "C", "D", "E", "F"];

export default function ClassesPage() {
  const queryClient = useQueryClient();
  const [isClassModalOpen, setIsClassModalOpen] = useState(false);
  const [isAssignmentModalOpen, setIsAssignmentModalOpen] = useState(false);
  const [editingClass, setEditingClass] = useState<SchoolClass | null>(null);
  const [selectedClass, setSelectedClass] = useState<SchoolClassWithAssignments | null>(null);
  const [classFormData, setClassFormData] = useState<SchoolClassCreate>({
    year: "I",
    section: "A",
  });
  const [assignmentFormData, setAssignmentFormData] = useState<ClassMatterAssignmentCreate>({
    matter_id: 0,
    teacher_id: 0,
    hours_per_week: 1,
    requirements: [],
  });
  const [editingAssignment, setEditingAssignment] = useState<ClassMatterAssignment | null>(null);

  const { data: classes, isLoading: classesLoading } = useQuery({
    queryKey: ["classes"],
    queryFn: classesApi.list,
  });

  const { data: matters } = useQuery({
    queryKey: ["matters"],
    queryFn: mattersApi.list,
  });

  const { data: teachers } = useQuery({
    queryKey: ["teachers"],
    queryFn: teachersApi.list,
  });

  // Class mutations
  const createClassMutation = useMutation({
    mutationFn: classesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classes"] });
      closeClassModal();
    },
  });

  const updateClassMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: SchoolClassCreate }) =>
      classesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classes"] });
      closeClassModal();
    },
  });

  const deleteClassMutation = useMutation({
    mutationFn: classesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classes"] });
      setSelectedClass(null);
    },
  });

  // Assignment mutations
  const createAssignmentMutation = useMutation({
    mutationFn: ({ classId, data }: { classId: number; data: ClassMatterAssignmentCreate }) =>
      classesApi.createAssignment(classId, data),
    onSuccess: () => {
      if (selectedClass) {
        refetchSelectedClass(selectedClass.id);
      }
      closeAssignmentModal();
    },
  });

  const updateAssignmentMutation = useMutation({
    mutationFn: ({ classId, assignmentId, data }: { classId: number; assignmentId: number; data: ClassMatterAssignmentCreate }) =>
      classesApi.updateAssignment(classId, assignmentId, data),
    onSuccess: () => {
      if (selectedClass) {
        refetchSelectedClass(selectedClass.id);
      }
      closeAssignmentModal();
    },
  });

  const deleteAssignmentMutation = useMutation({
    mutationFn: ({ classId, assignmentId }: { classId: number; assignmentId: number }) =>
      classesApi.deleteAssignment(classId, assignmentId),
    onSuccess: () => {
      if (selectedClass) {
        refetchSelectedClass(selectedClass.id);
      }
    },
  });

  const refetchSelectedClass = async (classId: number) => {
    const updatedClass = await classesApi.get(classId);
    setSelectedClass(updatedClass);
  };

  const openCreateClassModal = () => {
    setEditingClass(null);
    setClassFormData({ year: "I", section: "A" });
    setIsClassModalOpen(true);
  };

  const openEditClassModal = (schoolClass: SchoolClass) => {
    setEditingClass(schoolClass);
    setClassFormData({ year: schoolClass.year, section: schoolClass.section });
    setIsClassModalOpen(true);
  };

  const closeClassModal = () => {
    setIsClassModalOpen(false);
    setEditingClass(null);
    setClassFormData({ year: "I", section: "A" });
  };

  const openAssignmentModal = (matter?: Matter) => {
    setEditingAssignment(null);
    const defaultReqs = matter?.default_requirements || [];
    setAssignmentFormData({
      matter_id: matter?.id || matters?.[0]?.id || 0,
      teacher_id: teachers?.[0]?.id || 0,
      hours_per_week: 1,
      requirements: defaultReqs,
    });
    setIsAssignmentModalOpen(true);
  };

  const openEditAssignmentModal = (assignment: ClassMatterAssignment) => {
    setEditingAssignment(assignment);
    setAssignmentFormData({
      matter_id: assignment.matter_id,
      teacher_id: assignment.teacher_id,
      hours_per_week: assignment.hours_per_week,
      requirements: assignment.requirements || [],
    });
    setIsAssignmentModalOpen(true);
  };

  const closeAssignmentModal = () => {
    setIsAssignmentModalOpen(false);
    setEditingAssignment(null);
    setAssignmentFormData({
      matter_id: 0,
      teacher_id: 0,
      hours_per_week: 1,
      requirements: [],
    });
  };

  const handleSelectClass = async (schoolClass: SchoolClass) => {
    const fullClass = await classesApi.get(schoolClass.id);
    setSelectedClass(fullClass);
  };

  const handleClassSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingClass) {
      updateClassMutation.mutate({ id: editingClass.id, data: classFormData });
    } else {
      createClassMutation.mutate(classFormData);
    }
  };

  const handleAssignmentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedClass) {
      if (editingAssignment) {
        updateAssignmentMutation.mutate({
          classId: selectedClass.id,
          assignmentId: editingAssignment.id,
          data: assignmentFormData,
        });
      } else {
        createAssignmentMutation.mutate({
          classId: selectedClass.id,
          data: assignmentFormData,
        });
      }
    }
  };

  // When matter selection changes, load default requirements
  const handleMatterChange = (matterId: number) => {
    const matter = matters?.find((m) => m.id === matterId);
    setAssignmentFormData({
      ...assignmentFormData,
      matter_id: matterId,
      requirements: matter?.default_requirements || [],
    });
  };

  const handleDeleteClass = (id: number) => {
    if (window.confirm("Are you sure you want to delete this class?")) {
      deleteClassMutation.mutate(id);
    }
  };

  const handleDeleteAssignment = (assignment: ClassMatterAssignment) => {
    if (selectedClass && window.confirm(`Remove ${assignment.matter.name} from this class?`)) {
      deleteAssignmentMutation.mutate({
        classId: selectedClass.id,
        assignmentId: assignment.id,
      });
    }
  };

  // Get matters not yet assigned to the selected class
  const getAvailableMatters = () => {
    if (!matters || !selectedClass) return [];
    const assignedMatterIds = selectedClass.matter_assignments.map((a) => a.matter_id);
    return matters.filter((m) => !assignedMatterIds.includes(m.id));
  };

  if (classesLoading) {
    return <div className="loading">Carico le classi...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h2>Classes</h2>
        <p>Gestisci le classi e gli assegnamenti delle materie</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        {/* Classes List */}
        <div className="card">
          <div className="card-header">
            <h3>Tutte le classi</h3>
            <button className="btn btn-primary" onClick={openCreateClassModal}>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="16" height="16">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
             Nuova Classe
            </button>
          </div>

          {classes && classes.length > 0 ? (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Classi</th>
                    <th>Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {classes.map((schoolClass) => (
                    <tr
                      key={schoolClass.id}
                      style={{
                        backgroundColor:
                          selectedClass?.id === schoolClass.id
                            ? "var(--background-color)"
                            : undefined,
                        cursor: "pointer",
                      }}
                      onClick={() => handleSelectClass(schoolClass)}
                    >
                      <td>
                        <strong>{schoolClass.name}</strong>
                      </td>
                      <td>
                        <div className="action-buttons">
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              openEditClassModal(schoolClass);
                            }}
                          >
                            Modifica
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteClass(schoolClass.id);
                            }}
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
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342M6.75 15a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm0 0v-3.675A55.378 55.378 0 0 1 12 8.443m-7.007 11.55A5.981 5.981 0 0 0 6.75 15.75v-1.5" />
              </svg>
              <p>No classes found. Add your first class!</p>
            </div>
          )}
        </div>

        {/* Class Details */}
        <div className="card">
          <div className="card-header">
            <h3>{selectedClass ? `Class ${selectedClass.name} - Subjects` : "Select a Class"}</h3>
            {selectedClass ? (<h4> {selectedClass.matter_assignments.reduce((accu, assignment) => accu + assignment.hours_per_week, 0)}/30 hours </h4>) : null}
            {selectedClass && (
              <button className="btn btn-primary btn-sm" onClick={() => openAssignmentModal()}>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="16" height="16">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Aggiungi materia
              </button>
            )}
          </div>

          {selectedClass ? (
            selectedClass.matter_assignments.length > 0 ? (
              <div className="assignment-list">
                {selectedClass.matter_assignments.map((assignment) => (
                  <div key={assignment.id} className="assignment-item">
                    <div className="assignment-info">
                      <span className="matter-name">{assignment.matter.name}</span>
                      <span className="teacher-name">
                        {assignment.teacher.first_name} {assignment.teacher.last_name}
                      </span>
                      <span className="hours">{assignment.hours_per_week} hours/week</span>
                      {assignment.requirements && assignment.requirements.length > 0 && (
                        <div className="requirements-tags" style={{ marginTop: "0.25rem" }}>
                          {assignment.requirements.map((req) => (
                            <span key={req} className="requirement-tag requirement-tag-sm">
                              {REQUIREMENT_LABELS[req]}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="action-buttons">
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => openEditAssignmentModal(assignment)}
                      >
                        Modifica
                      </button>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDeleteAssignment(assignment)}
                      >
                        Rimuovi
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>Nessuna materia associate al momento.</p>
              </div>
            )
          ) : (
            <div className="empty-state">
              <p>Seleziona una classe per gestire le materie</p>
            </div>
          )}
        </div>
      </div>

      {/* Class Modal */}
      <Modal
        isOpen={isClassModalOpen}
        onClose={closeClassModal}
        title={editingClass ? "Modifica classe" : "Aggiungi una nuova classe"}
      >
        <form onSubmit={handleClassSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="year">Anno</label>
              <select
                id="year"
                value={classFormData.year}
                onChange={(e) => setClassFormData({ ...classFormData, year: e.target.value })}
              >
                {ROMAN_NUMERALS.map((numeral) => (
                  <option key={numeral} value={numeral}>
                    {numeral}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="section">Sezione</label>
              <select
                id="section"
                value={classFormData.section}
                onChange={(e) => setClassFormData({ ...classFormData, section: e.target.value })}
              >
                {SECTIONS.map((section) => (
                  <option key={section} value={section}>
                    {section}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ marginTop: "1rem", padding: "1rem", backgroundColor: "var(--background-color)", borderRadius: "0.5rem" }}>
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
              Il nome della classe sarà: <strong>{classFormData.year}{classFormData.section}</strong>
            </p>
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={closeClassModal}>
              Annulla
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={createClassMutation.isPending || updateClassMutation.isPending}
            >
              {editingClass ? "Aggiorna" : "Crea"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Assignment Modal */}
      <Modal
        isOpen={isAssignmentModalOpen}
        onClose={closeAssignmentModal}
        title={editingAssignment ? `Modifica la materia ${editingAssignment.matter.name}` : `Aggiungi materia a ${selectedClass?.name}`}
      >
        <form onSubmit={handleAssignmentSubmit}>
          {!editingAssignment && (
            <div className="form-group">
              <label htmlFor="matter">Materia</label>
              {getAvailableMatters().length > 0 ? (
                <select
                  id="matter"
                  value={assignmentFormData.matter_id}
                  onChange={(e) => handleMatterChange(Number(e.target.value))}
                >
                  <option value={0}>Seleziona una materia...</option>
                  {getAvailableMatters().map((matter) => (
                    <option key={matter.id} value={matter.id}>
                      {matter.name}
                    </option>
                  ))}
                </select>
              ) : (
                <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                  Tutte le materie disponibili sono state associate a questa classe.
                </p>
              )}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="teacher">Insegnanti</label>
            {teachers && teachers.length > 0 ? (
              <select
                id="teacher"
                value={assignmentFormData.teacher_id}
                onChange={(e) =>
                  setAssignmentFormData({
                    ...assignmentFormData,
                    teacher_id: Number(e.target.value),
                  })
                }
              >
                <option value={0}>Seleziona un insegnante...</option>
                {teachers.map((teacher) => (
                  <option key={teacher.id} value={teacher.id}>
                    {teacher.first_name} {teacher.last_name}
                  </option>
                ))}
              </select>
            ) : (
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                Nessun insegnante disponibile, aggiungine uno.
              </p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="hours">Ore settimanali</label>
            <input
              type="number"
              id="hours"
              min={1}
              max={20}
              value={assignmentFormData.hours_per_week}
              onChange={(e) =>
                setAssignmentFormData({
                  ...assignmentFormData,
                  hours_per_week: Number(e.target.value),
                })
              }
            />
          </div>

          <div className="form-group">
            <label>Requisiti</label>
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
              Puoi aggiungere requisiti aggiuntivi, oltre a quelli già previsti dall'insegnamento.
            </p>
            <div className="checkbox-group">
              {Object.values(MatterRequirement).map((req) => (
                <label key={req} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={assignmentFormData.requirements?.includes(req) || false}
                    onChange={(e) => {
                      const currentReqs = assignmentFormData.requirements || [];
                      if (e.target.checked) {
                        setAssignmentFormData({
                          ...assignmentFormData,
                          requirements: [...currentReqs, req],
                        });
                      } else {
                        setAssignmentFormData({
                          ...assignmentFormData,
                          requirements: currentReqs.filter((r) => r !== req),
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
            <button type="button" className="btn btn-secondary" onClick={closeAssignmentModal}>
              Annulla
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={
                createAssignmentMutation.isPending ||
                updateAssignmentMutation.isPending ||
                (!editingAssignment && assignmentFormData.matter_id === 0) ||
                assignmentFormData.teacher_id === 0
              }
            >
              {editingAssignment ? "Aggionra" : "Aggiungi materia"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
