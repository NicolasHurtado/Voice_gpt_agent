// Application constants

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export const API_ENDPOINTS = {
  SESSIONS: '/api/v1/sessions',
  CHAT: '/api/v1/chat',
  SPEECH_TO_TEXT: '/api/v1/speech-to-text',
  TEXT_TO_SPEECH: '/api/v1/text-to-speech',
  HEALTH: '/api/v1/health',
  WEBSOCKET: '/ws',
} as const;

export const AUDIO_CONFIG = {
  SAMPLE_RATE: 44100,
  CHANNEL_COUNT: 1,
  BIT_DEPTH: 16,
  MAX_RECORDING_TIME: 300, // 5 minutes
  CHUNK_SIZE: 4096,
} as const;

export const VOICE_OPTIONS = [
  'alloy',
  'echo',
  'fable',
  'onyx',
  'nova',
  'shimmer',
] as const;

export const THEME = {
  COLORS: {
    PRIMARY: '#3b82f6',
    SECONDARY: '#64748b',
    SUCCESS: '#10b981',
    WARNING: '#f59e0b',
    ERROR: '#ef4444',
    BACKGROUND: '#ffffff',
    SURFACE: '#f8fafc',
  },
  ANIMATIONS: {
    DURATION: {
      FAST: 150,
      NORMAL: 300,
      SLOW: 500,
    },
    EASING: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
} as const;
