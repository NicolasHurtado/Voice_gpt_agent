// Audio related types

export interface AudioRecordingState {
  isRecording: boolean;
  isPlaying: boolean;
  isLoading: boolean;
  duration: number;
  error: string | null;
}

export interface AudioSettings {
  sampleRate: number;
  channelCount: number;
  bitDepth: number;
  format: 'wav' | 'mp3' | 'webm';
}

export interface VoiceSettings {
  voice: 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer';
  speed: number;
  language: string;
}

export interface AudioAnalyzerData {
  frequencyData: Uint8Array;
  timeData: Uint8Array;
  volume: number;
}
