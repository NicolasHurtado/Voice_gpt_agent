// API Types matching backend schemas

export interface Session {
  id: string;
  status: 'ACTIVE' | 'INACTIVE';
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  session_id: string;
  type: 'USER' | 'ASSISTANT';
  content: string;
  timestamp: string;
  extra_data?: Record<string, any>;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  language?: string;
}

export interface ChatResponse {
  message: string;
  session_id: string;
  message_id: string;
}

export interface TextToSpeechRequest {
  text: string;
  voice?: string;
  language?: string;
}

export interface SpeechToTextResponse {
  text: string;
  confidence?: number;
  language?: string;
  duration?: number;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  services?: Array<{
    service: string;
    status: 'healthy' | 'unhealthy';
  }>;
}

export interface ApiError {
  detail: string;
  error_code?: string;
}
