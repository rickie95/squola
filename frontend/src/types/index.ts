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
