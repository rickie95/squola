import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { classesApi, mattersApi, teachersApi } from "../api";
import type {
  SchoolClass,
  SchoolClassWithAssignments,
  SchoolClassCreate,
  ClassMatterAssignmentCreate,
  ClassMatterAssignment,
} from "../types";
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
  });

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

  const openAssignmentModal = () => {
    setAssignmentFormData({
      matter_id: matters?.[0]?.id || 0,
      teacher_id: teachers?.[0]?.id || 0,
      hours_per_week: 1,
    });
    setIsAssignmentModalOpen(true);
  };

  const closeAssignmentModal = () => {
    setIsAssignmentModalOpen(false);
    setAssignmentFormData({
      matter_id: 0,
      teacher_id: 0,
      hours_per_week: 1,
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
      createAssignmentMutation.mutate({
        classId: selectedClass.id,
        data: assignmentFormData,
      });
    }
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
    return <div className="loading">Loading classes...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h2>Classes</h2>
        <p>Manage school classes and their subject assignments</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        {/* Classes List */}
        <div className="card">
          <div className="card-header">
            <h3>All Classes</h3>
            <button className="btn btn-primary" onClick={openCreateClassModal}>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="16" height="16">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Add Class
            </button>
          </div>

          {classes && classes.length > 0 ? (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Class</th>
                    <th>Actions</th>
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
                            Edit
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteClass(schoolClass.id);
                            }}
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
            {selectedClass && (
              <button className="btn btn-primary btn-sm" onClick={openAssignmentModal}>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="16" height="16">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Add Subject
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
                    </div>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDeleteAssignment(assignment)}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>No subjects assigned to this class yet.</p>
              </div>
            )
          ) : (
            <div className="empty-state">
              <p>Select a class to view and manage its subjects.</p>
            </div>
          )}
        </div>
      </div>

      {/* Class Modal */}
      <Modal
        isOpen={isClassModalOpen}
        onClose={closeClassModal}
        title={editingClass ? "Edit Class" : "Add New Class"}
      >
        <form onSubmit={handleClassSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="year">Year</label>
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
              <label htmlFor="section">Section</label>
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
              Class name will be: <strong>{classFormData.year}{classFormData.section}</strong>
            </p>
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={closeClassModal}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={createClassMutation.isPending || updateClassMutation.isPending}
            >
              {editingClass ? "Update" : "Create"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Assignment Modal */}
      <Modal
        isOpen={isAssignmentModalOpen}
        onClose={closeAssignmentModal}
        title={`Add Subject to ${selectedClass?.name}`}
      >
        <form onSubmit={handleAssignmentSubmit}>
          <div className="form-group">
            <label htmlFor="matter">Subject</label>
            {getAvailableMatters().length > 0 ? (
              <select
                id="matter"
                value={assignmentFormData.matter_id}
                onChange={(e) =>
                  setAssignmentFormData({
                    ...assignmentFormData,
                    matter_id: Number(e.target.value),
                  })
                }
              >
                <option value={0}>Select a subject...</option>
                {getAvailableMatters().map((matter) => (
                  <option key={matter.id} value={matter.id}>
                    {matter.name}
                  </option>
                ))}
              </select>
            ) : (
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                All available subjects have been assigned to this class.
              </p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="teacher">Teacher</label>
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
                <option value={0}>Select a teacher...</option>
                {teachers.map((teacher) => (
                  <option key={teacher.id} value={teacher.id}>
                    {teacher.first_name} {teacher.last_name}
                  </option>
                ))}
              </select>
            ) : (
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                No teachers available. Add teachers first.
              </p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="hours">Hours per Week</label>
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

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={closeAssignmentModal}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={
                createAssignmentMutation.isPending ||
                assignmentFormData.matter_id === 0 ||
                assignmentFormData.teacher_id === 0
              }
            >
              Add Subject
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
