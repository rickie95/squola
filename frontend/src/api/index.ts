import axios from "axios";
import type {
  Matter,
  MatterWithTeachers,
  MatterCreate,
  MatterUpdate,
  Teacher,
  TeacherWithMatters,
  TeacherCreate,
  TeacherUpdate,
  BlacklistedSlot,
  BlacklistedSlotCreate,
  SchoolClass,
  SchoolClassWithAssignments,
  SchoolClassCreate,
  SchoolClassUpdate,
  ClassMatterAssignment,
  ClassMatterAssignmentCreate,
  ClassMatterAssignmentUpdate,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ============ Matters API ============

export const mattersApi = {
  list: async (): Promise<Matter[]> => {
    const response = await api.get<Matter[]>("/matters");
    return response.data;
  },

  get: async (id: number): Promise<MatterWithTeachers> => {
    const response = await api.get<MatterWithTeachers>(`/matters/${id}`);
    return response.data;
  },

  create: async (data: MatterCreate): Promise<Matter> => {
    const response = await api.post<Matter>("/matters", data);
    return response.data;
  },

  update: async (id: number, data: MatterUpdate): Promise<Matter> => {
    const response = await api.put<Matter>(`/matters/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/matters/${id}`);
  },
};

// ============ Teachers API ============

export const teachersApi = {
  list: async (): Promise<Teacher[]> => {
    const response = await api.get<Teacher[]>("/teachers");
    return response.data;
  },

  get: async (id: number): Promise<TeacherWithMatters> => {
    const response = await api.get<TeacherWithMatters>(`/teachers/${id}`);
    return response.data;
  },

  create: async (data: TeacherCreate): Promise<TeacherWithMatters> => {
    const response = await api.post<TeacherWithMatters>("/teachers", data);
    return response.data;
  },

  update: async (id: number, data: TeacherUpdate): Promise<TeacherWithMatters> => {
    const response = await api.put<TeacherWithMatters>(`/teachers/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/teachers/${id}`);
  },

  // Blacklisted slots
  listBlacklistedSlots: async (teacherId: number): Promise<BlacklistedSlot[]> => {
    const response = await api.get<BlacklistedSlot[]>(
      `/teachers/${teacherId}/blacklisted-slots`
    );
    return response.data;
  },

  addBlacklistedSlot: async (
    teacherId: number,
    data: BlacklistedSlotCreate
  ): Promise<BlacklistedSlot> => {
    const response = await api.post<BlacklistedSlot>(
      `/teachers/${teacherId}/blacklisted-slots`,
      data
    );
    return response.data;
  },

  removeBlacklistedSlot: async (
    teacherId: number,
    slotId: number
  ): Promise<void> => {
    await api.delete(`/teachers/${teacherId}/blacklisted-slots/${slotId}`);
  },
};

// ============ Classes API ============

export const classesApi = {
  list: async (): Promise<SchoolClass[]> => {
    const response = await api.get<SchoolClass[]>("/classes");
    return response.data;
  },

  get: async (id: number): Promise<SchoolClassWithAssignments> => {
    const response = await api.get<SchoolClassWithAssignments>(`/classes/${id}`);
    return response.data;
  },

  create: async (data: SchoolClassCreate): Promise<SchoolClass> => {
    const response = await api.post<SchoolClass>("/classes", data);
    return response.data;
  },

  update: async (id: number, data: SchoolClassUpdate): Promise<SchoolClass> => {
    const response = await api.put<SchoolClass>(`/classes/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/classes/${id}`);
  },

  // Matter assignments
  listAssignments: async (classId: number): Promise<ClassMatterAssignment[]> => {
    const response = await api.get<ClassMatterAssignment[]>(
      `/classes/${classId}/assignments`
    );
    return response.data;
  },

  createAssignment: async (
    classId: number,
    data: ClassMatterAssignmentCreate
  ): Promise<ClassMatterAssignment> => {
    const response = await api.post<ClassMatterAssignment>(
      `/classes/${classId}/assignments`,
      data
    );
    return response.data;
  },

  updateAssignment: async (
    classId: number,
    assignmentId: number,
    data: ClassMatterAssignmentUpdate
  ): Promise<ClassMatterAssignment> => {
    const response = await api.put<ClassMatterAssignment>(
      `/classes/${classId}/assignments/${assignmentId}`,
      data
    );
    return response.data;
  },

  deleteAssignment: async (classId: number, assignmentId: number): Promise<void> => {
    await api.delete(`/classes/${classId}/assignments/${assignmentId}`);
  },
};

export default api;
