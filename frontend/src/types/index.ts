export interface Conversation {
  id: string;
  title: string | null;
  conversation_type: string;
  summary: string | null;
  status: string;
  started_at: string;
  last_message_at: string | null;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_type: "user" | "agent" | "system";
  sender_id: string | null;
  content_text: string | null;
  content_json: Record<string, unknown> | null;
  message_type: string;
  model_provider: string | null;
  model_name: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  latency_ms: number | null;
  created_at: string;
}

export interface Memory {
  id: string;
  memory_type: string;
  title: string;
  content: string;
  summary: string | null;
  importance_score: number;
  confidence_score: number;
  sensitivity_level: string;
  status: string;
  confirmed_by_user: boolean;
  valid_until: string | null;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  title: string;
  description: string | null;
  task_type: string;
  project_id: string | null;
  assigned_to: string | null;
  priority: string;
  status: string;
  start_date: string | null;
  due_date: string | null;
  completed_at: string | null;
  risk_level: string;
  ai_generated: boolean;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  objective: string | null;
  status: string;
  priority: string;
  start_date: string | null;
  target_date: string | null;
  progress_percent: number;
  budget: number | null;
  currency: string;
  current_summary: string | null;
  next_action: string | null;
  risk_level: string;
  created_at: string;
}

export interface Decision {
  id: string;
  title: string;
  problem_statement: string | null;
  context: string | null;
  options_json: Record<string, unknown> | null;
  selected_option: string | null;
  rationale: string | null;
  decision_status: string;
  risk_level: string;
  created_at: string;
}

export interface Notification {
  id: string;
  notification_type: string;
  title: string;
  content: string | null;
  priority: string;
  read_at: string | null;
  action_required: boolean;
  created_at: string;
}

export interface StreamEvent {
  type: string;
  content?: string;
  error?: string;
  message_id?: string;
  agent_run_id?: string;
  tasks?: string[];
  memories?: string[];
  decisions?: string[];
  count?: number;
  latency_ms?: number;
}
