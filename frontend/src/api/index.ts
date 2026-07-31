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
  Unavailability,
  UnavailabilityCreate,
  SchoolClass,
  SchoolClassWithAssignments,
  SchoolClassCreate,
  SchoolClassUpdate,
  ClassMatterAssignment,
  ClassMatterAssignmentCreate,
  ClassMatterAssignmentUpdate,
  GeneratedSchedule,
  GenerateScheduleRequest,
  SchedulingPreview,
  SavedScheduleListItem,
  SavedSchedule,
  SavedScheduleUpdate,
  AuthSession,
  RegisterRequest,
  LoginRequest,
  ChangePasswordRequest,
  RenameWorkspaceRequest,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || window.location.href;

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const path = window.location.pathname;
      if (path !== "/login" && path !== "/register") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

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

  // Unavailabilities
  listUnavailabilities: async (teacherId: number): Promise<Unavailability[]> => {
    const response = await api.get<Unavailability[]>(
      `/teachers/${teacherId}/unavailabilities`
    );
    return response.data;
  },

  addUnavailability: async (
    teacherId: number,
    data: UnavailabilityCreate
  ): Promise<Unavailability> => {
    const response = await api.post<Unavailability>(
      `/teachers/${teacherId}/unavailabilities`,
      data
    );
    return response.data;
  },

  removeUnavailability: async (
    teacherId: number,
    slotId: number
  ): Promise<void> => {
    await api.delete(`/teachers/${teacherId}/unavailabilities/${slotId}`);
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

// ============ Scheduling API ============

export const schedulingApi = {
  preview: async (): Promise<SchedulingPreview> => {
    const response = await api.get<SchedulingPreview>("/scheduling/preview");
    return response.data;
  },

  generate: async (request: GenerateScheduleRequest = {}): Promise<GeneratedSchedule> => {
    const response = await api.post<GeneratedSchedule>("/scheduling/generate", request);
    return response.data;
  },

  // Saved schedules
  listSaved: async (): Promise<SavedScheduleListItem[]> => {
    const response = await api.get<SavedScheduleListItem[]>("/scheduling/schedules");
    return response.data;
  },

  getSaved: async (id: number): Promise<SavedSchedule> => {
    const response = await api.get<SavedSchedule>(`/scheduling/schedules/${id}`);
    return response.data;
  },

  updateSaved: async (id: number, data: SavedScheduleUpdate): Promise<SavedScheduleListItem> => {
    const response = await api.patch<SavedScheduleListItem>(`/scheduling/schedules/${id}`, data);
    return response.data;
  },

  deleteSaved: async (id: number): Promise<void> => {
    await api.delete(`/scheduling/schedules/${id}`);
  },
};

// ============ Auth API ============

export const authApi = {
  register: async (data: RegisterRequest): Promise<AuthSession> => {
    const response = await api.post<AuthSession>("/auth/register", data);
    return response.data;
  },

  login: async (data: LoginRequest): Promise<AuthSession> => {
    const response = await api.post<AuthSession>("/auth/login", data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post("/auth/logout");
  },

  me: async (): Promise<AuthSession> => {
    const response = await api.get<AuthSession>("/auth/me");
    return response.data;
  },
};

// ============ Account API ============

export const accountApi = {
  get: async (): Promise<AuthSession> => {
    const response = await api.get<AuthSession>("/account");
    return response.data;
  },

  changePassword: async (data: ChangePasswordRequest): Promise<void> => {
    await api.patch("/account/password", data);
  },

  renameWorkspace: async (data: RenameWorkspaceRequest): Promise<AuthSession> => {
    const response = await api.patch<AuthSession>("/account/workspace", data);
    return response.data;
  },
};

export default api;
