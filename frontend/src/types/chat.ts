// Chat related types

import { Message } from './api';

export interface ChatMessage extends Message {
  isLoading?: boolean;
  hasAudio?: boolean;
  audioUrl?: string;
}

export interface ChatSession {
  id: string;
  messages: ChatMessage[];
  isTyping: boolean;
  lastActivity: string;
}

export interface ChatState {
  currentSession: ChatSession | null;
  sessions: ChatSession[];
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
}

export type MessageInput = {
  type: 'text' | 'audio';
  content: string | Blob;
  sessionId?: string;
};
