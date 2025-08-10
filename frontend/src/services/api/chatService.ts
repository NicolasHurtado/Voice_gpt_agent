'use client';

import { apiClient } from './client';
import { API_ENDPOINTS } from '@/utils/constants';
import {
  ChatRequest,
  ChatResponse,
  Session,
  SpeechToTextResponse,
} from '@/types/api';

export class ChatService {
  // Create new session
  static async createSession(): Promise<Session> {
    return apiClient.post<Session>(API_ENDPOINTS.SESSIONS);
  }

  // Get session info
  static async getSession(sessionId: string): Promise<Session> {
    return apiClient.get<Session>(`${API_ENDPOINTS.SESSIONS}/${sessionId}`);
  }

  // Delete session
  static async deleteSession(sessionId: string): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.SESSIONS}/${sessionId}`);
  }

  // Send chat message
  static async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return apiClient.post<ChatResponse>(API_ENDPOINTS.CHAT, request);
  }

  // Convert speech to text
  static async speechToText(
    audioBlob: Blob,
    language?: string,
    sessionId?: string
  ): Promise<SpeechToTextResponse> {
    const formData = new FormData();
    
    // Convert blob to file with proper extension
    const audioFile = new File([audioBlob], 'recording.webm', {
      type: 'audio/webm',
    });
    
    formData.append('audio_file', audioFile);
    
    if (language) {
      formData.append('language', language);
    }
    
    if (sessionId) {
      formData.append('session_id', sessionId);
    }

    return apiClient.postFormData<SpeechToTextResponse>(
      API_ENDPOINTS.SPEECH_TO_TEXT,
      formData
    );
  }

  // Convert text to speech
  static async textToSpeech(
    text: string,
    voice?: string,
    language?: string
  ): Promise<Blob> {
    const response = await fetch(`${apiClient['baseURL']}${API_ENDPOINTS.TEXT_TO_SPEECH}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        voice: voice || 'alloy',
        language: language || 'en',
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));
      throw new Error(errorData.detail);
    }

    return response.blob();
  }
}