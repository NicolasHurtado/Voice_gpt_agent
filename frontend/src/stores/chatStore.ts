'use client';

import { create } from 'zustand';
import { ChatState, ChatMessage, MessageInput } from '@/types/chat';
import { ChatService } from '@/services/api/chatService';
import { generateId } from '@/utils/helpers';

interface ChatStore extends ChatState {
  // Actions
  createSession: () => Promise<void>;
  sendMessage: (input: MessageInput) => Promise<void>;
  addMessage: (message: ChatMessage) => void;
  setTyping: (isTyping: boolean) => void;
  setConnectionStatus: (
    status: 'connecting' | 'connected' | 'disconnected' | 'error'
  ) => void;
  clearError: () => void;
  resetChat: () => void;
}

const initialState: ChatState = {
  currentSession: null,
  sessions: [],
  isConnected: false,
  connectionStatus: 'disconnected',
};

export const useChatStore = create<ChatStore>((set, get) => ({
  ...initialState,

  createSession: async () => {
    try {
      set({ connectionStatus: 'connecting' });
      
      const session = await ChatService.createSession();
      
      const newSession = {
        id: session.id,
        messages: [],
        isTyping: false,
        lastActivity: new Date().toISOString(),
      };

      set({
        currentSession: newSession,
        sessions: [newSession],
        isConnected: true,
        connectionStatus: 'connected',
      });
    } catch (error) {
      console.error('Failed to create session:', error);
      set({
        connectionStatus: 'error',
        isConnected: false,
      });
      throw error;
    }
  },

  sendMessage: async (input: MessageInput) => {
    const { currentSession } = get();
    
    if (!currentSession) {
      throw new Error('No active session');
    }

    try {
      // Add user message immediately
      const userMessage: ChatMessage = {
        id: generateId(),
        session_id: currentSession.id,
        type: 'USER',
        content: input.type === 'text' ? input.content as string : '[Audio Message]',
        timestamp: new Date().toISOString(),
        hasAudio: input.type === 'audio',
      };

      get().addMessage(userMessage);

      let messageText = '';

      // Handle audio input
      if (input.type === 'audio' && input.content instanceof Blob) {
        set({ connectionStatus: 'connecting' });
        
        // Convert speech to text
        const sttResult = await ChatService.speechToText(
          input.content,
          'en',
          currentSession.id
        );
        
        messageText = sttResult.text;
        
        // Update user message with transcribed text
        const updatedUserMessage = {
          ...userMessage,
          content: messageText,
        };
        
        get().addMessage(updatedUserMessage);
      } else {
        messageText = input.content as string;
      }

      // Set typing indicator
      get().setTyping(true);

      // Send to chat service
      const chatResponse = await ChatService.sendMessage({
        message: messageText,
        session_id: currentSession.id,
      });

      // Add AI response
      const aiMessage: ChatMessage = {
        id: chatResponse.message_id,
        session_id: currentSession.id,
        type: 'ASSISTANT',
        content: chatResponse.message,
        timestamp: new Date().toISOString(),
        isLoading: true, // Will be used for TTS
      };

      get().addMessage(aiMessage);

      // Generate speech for AI response
      try {
        const audioBlob = await ChatService.textToSpeech(chatResponse.message);
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Update message with audio
        const updatedAiMessage = {
          ...aiMessage,
          hasAudio: true,
          audioUrl,
          isLoading: false,
        };
        
        get().addMessage(updatedAiMessage);
      } catch (error) {
        console.warn('TTS failed:', error);
        // Update message without audio
        const updatedAiMessage = {
          ...aiMessage,
          isLoading: false,
        };
        get().addMessage(updatedAiMessage);
      }

      set({ connectionStatus: 'connected' });
    } catch (error) {
      console.error('Failed to send message:', error);
      set({ connectionStatus: 'error' });
      throw error;
    } finally {
      get().setTyping(false);
    }
  },

  addMessage: (message: ChatMessage) => {
    set(state => {
      if (!state.currentSession) return state;

      const existingIndex = state.currentSession.messages.findIndex(
        m => m.id === message.id
      );

      let updatedMessages;
      if (existingIndex >= 0) {
        // Update existing message
        updatedMessages = [...state.currentSession.messages];
        updatedMessages[existingIndex] = message;
      } else {
        // Add new message
        updatedMessages = [...state.currentSession.messages, message];
      }

      const updatedSession = {
        ...state.currentSession,
        messages: updatedMessages,
        lastActivity: new Date().toISOString(),
      };

      return {
        ...state,
        currentSession: updatedSession,
        sessions: state.sessions.map(s =>
          s.id === updatedSession.id ? updatedSession : s
        ),
      };
    });
  },

  setTyping: (isTyping: boolean) => {
    set(state => {
      if (!state.currentSession) return state;

      const updatedSession = {
        ...state.currentSession,
        isTyping,
      };

      return {
        ...state,
        currentSession: updatedSession,
      };
    });
  },

  setConnectionStatus: (status) => {
    set({
      connectionStatus: status,
      isConnected: status === 'connected',
    });
  },

  clearError: () => {
    set(state => ({
      ...state,
      connectionStatus: state.isConnected ? 'connected' : 'disconnected',
    }));
  },

  resetChat: () => {
    set(initialState);
  },
}));