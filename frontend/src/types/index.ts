// ============ Enums ============

export enum SchedulePreference {
  EARLY = "early",
  LATE = "late",
  MINIMIZE_GAPS = "minimize_gaps",
  MAXIMIZE_GAPS = "maximize_gaps",
  NONE = "none",
}

// ============ Matter Types ============

export interface Matter {
  id: number;
  name: string;
}

export interface MatterWithTeachers extends Matter {
  teachers: Teacher[];
}

export interface MatterCreate {
  name: string;
}

export interface MatterUpdate {
  name?: string;
}

// ============ Blacklisted Slot Types ============

export interface BlacklistedSlot {
  id: number;
  day_of_week: number; // 0=Monday, 4=Friday
  hour_slot: number; // 1-based
}

export interface BlacklistedSlotCreate {
  day_of_week: number;
  hour_slot: number;
}

// ============ Teacher Types ============

export interface Teacher {
  id: number;
  first_name: string;
  last_name: string;
  email: string | null;
  schedule_preference: SchedulePreference;
}

export interface TeacherWithMatters extends Teacher {
  matters: Matter[];
  blacklisted_slots: BlacklistedSlot[];
}

export interface TeacherCreate {
  first_name: string;
  last_name: string;
  email?: string | null;
  schedule_preference?: SchedulePreference;
  matter_ids?: number[];
}

export interface TeacherUpdate {
  first_name?: string;
  last_name?: string;
  email?: string | null;
  schedule_preference?: SchedulePreference;
  matter_ids?: number[];
}

// ============ School Class Types ============

export interface SchoolClass {
  id: number;
  year: string; // Roman numeral
  section: string; // Letter
  name: string; // Combined (e.g., "IIIA")
}

export interface ClassMatterAssignment {
  id: number;
  class_id: number;
  matter_id: number;
  teacher_id: number;
  hours_per_week: number;
  matter: Matter;
  teacher: Teacher;
}

export interface SchoolClassWithAssignments extends SchoolClass {
  matter_assignments: ClassMatterAssignment[];
}

export interface SchoolClassCreate {
  year: string;
  section: string;
}

export interface SchoolClassUpdate {
  year?: string;
  section?: string;
}

export interface ClassMatterAssignmentCreate {
  matter_id: number;
  teacher_id: number;
  hours_per_week: number;
}

export interface ClassMatterAssignmentUpdate {
  teacher_id?: number;
  hours_per_week?: number;
}

// ============ Scheduling Types ============

export interface ScheduleSlot {
  day: string;
  hour: string;
  teacher: string;
  matter: string;
  class?: string;
}

export interface ScheduleMetadata {
  status: string;
  solve_time_seconds: number;
  generated_at: string;
  total_slots: number;
}

export interface GeneratedSchedule {
  metadata: ScheduleMetadata;
  schedule: {
    by_class: Record<string, ScheduleSlot[]>;
    by_teacher: Record<string, ScheduleSlot[]>;
    by_day: Record<string, ScheduleSlot[]>;
  };
}

export interface GenerateScheduleRequest {
  time_limit_seconds?: number;
  nickname?: string;
  save_to_file?: boolean;
  output_path?: string;
}

export interface SchedulingPreviewTeacher {
  id: number;
  name: string;
  hours_assigned: number;
  blacklisted_slots: number;
  preference: string;
}

export interface SchedulingPreviewClass {
  id: number;
  name: string;
  assignments_count: number;
  total_hours: number;
}

export interface SchedulingPreview {
  summary: {
    teachers_count: number;
    classes_count: number;
    assignments_count: number;
    total_hours_to_schedule: number;
    total_slots_available: number;
    blacklisted_slots_count: number;
  };
  teachers: SchedulingPreviewTeacher[];
  classes: SchedulingPreviewClass[];
  issues: string[];
}

// ============ Saved Schedule Types ============

export interface SavedScheduleListItem {
  id: number;
  name: string;
  nickname: string | null;
  status: string;
  solve_time_seconds: number;
  total_slots: number;
  created_at: string;
}

export interface SavedSchedule extends SavedScheduleListItem {
  schedule_data: {
    by_class: Record<string, ScheduleSlot[]>;
    by_teacher: Record<string, ScheduleSlot[]>;
    by_day: Record<string, ScheduleSlot[]>;
  };
}

export interface SavedScheduleUpdate {
  nickname?: string;
}
