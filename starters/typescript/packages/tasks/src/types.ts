export interface Task {
  readonly id: string;
  readonly title: string;
  /** Id of the assigned user, referenced by string only — no import of the users domain. */
  assigneeId?: string;
}
