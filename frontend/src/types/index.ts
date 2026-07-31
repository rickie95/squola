// ============ Enums (as const objects for erasableSyntaxOnly compatibility) ============

export const SchedulePreference = {
  EARLY: "early",
  LATE: "late",
  MINIMIZE_GAPS: "minimize_gaps",
  MAXIMIZE_GAPS: "maximize_gaps",
  NONE: "none",
} as const;

export type SchedulePreference = (typeof SchedulePreference)[keyof typeof SchedulePreference];

export const MatterRequirement = {
  AT_LEAST_TWICE_PER_WEEK: "at_least_twice_per_week",
  ONE_LESSON_OF_THREE_HOURS_PER_WEEK: "one_lesson_of_three_hours_per_week",
  ONE_LESSON_OF_TWO_HOURS_PER_WEEK: "one_lesson_of_two_hours_per_week",
} as const;

export type MatterRequirement = (typeof MatterRequirement)[keyof typeof MatterRequirement];

// Human-readable labels for requirements
export const REQUIREMENT_LABELS: Record<MatterRequirement, string> = {
  [MatterRequirement.AT_LEAST_TWICE_PER_WEEK]: "Almeno due volte a settimana",
  [MatterRequirement.ONE_LESSON_OF_THREE_HOURS_PER_WEEK]: "Almeno una lezione da 3 ore",
  [MatterRequirement.ONE_LESSON_OF_TWO_HOURS_PER_WEEK]: "Almeno una lezione da 2 ore",
};

// ============ Matter Types ============

export interface Matter {
  id: number;
  name: string;
  default_requirements: MatterRequirement[];
}

export interface MatterWithTeachers extends Matter {
  teachers: Teacher[];
}

export interface MatterCreate {
  name: string;
  default_requirements?: MatterRequirement[];
}

export interface MatterUpdate {
  name?: string;
  default_requirements?: MatterRequirement[];
}

// ============ Unavailability Types ============

export interface Unavailability {
  id: number;
  day_of_week: number; // 0=Monday, 4=Friday
  hour_slot: number; // 1-based
}

export interface UnavailabilityCreate {
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
  unavailabilities: Unavailability[];
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
  requirements: MatterRequirement[];
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
  requirements?: MatterRequirement[];
}

export interface ClassMatterAssignmentUpdate {
  teacher_id?: number;
  hours_per_week?: number;
  requirements?: MatterRequirement[];
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
  unavailabilities_count: number;
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
    unavailabilities_count: number;
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

// ============ Auth & Account Types ============

export interface AuthUser {
  id: number;
  username: string;
}

export interface Workspace {
  id: number;
  name: string;
}

export interface AuthSession {
  user: AuthUser;
  workspace: Workspace;
}

export interface RegisterRequest {
  username: string;
  password: string;
  workspace_name?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface RenameWorkspaceRequest {
  name: string;
}
