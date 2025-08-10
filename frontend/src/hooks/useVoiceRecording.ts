'use client';

import { useState, useRef, useCallback } from 'react';
import { AudioRecordingState } from '@/types/audio';

interface UseVoiceRecordingProps {
  onRecordingComplete?: (audioBlob: Blob) => void;
  onError?: (error: string) => void;
  maxDuration?: number; // in seconds
}

export function useVoiceRecording({
  onRecordingComplete,
  onError,
  maxDuration = 300, // 5 minutes default
}: UseVoiceRecordingProps = {}) {
  const [state, setState] = useState<AudioRecordingState>({
    isRecording: false,
    isPlaying: false,
    isLoading: false,
    duration: 0,
    error: null,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100,
        },
      });

      streamRef.current = stream;

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      startTimeRef.current = Date.now();

      // Handle data available
      mediaRecorder.ondataavailable = event => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: 'audio/webm;codecs=opus',
        });
        onRecordingComplete?.(audioBlob);
      };

      // Start recording
      mediaRecorder.start(100); // Collect data every 100ms

      // Start timer
      timerRef.current = setInterval(() => {
        setState(prev => {
          const newDuration = (Date.now() - startTimeRef.current) / 1000;

          // Check max duration
          if (newDuration >= maxDuration) {
            stopRecording();
            return prev;
          }

          return { ...prev, duration: newDuration };
        });
      }, 100);

      setState(prev => ({
        ...prev,
        isRecording: true,
        isLoading: false,
        duration: 0,
      }));
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to start recording';
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      onError?.(errorMessage);
    }
  }, [onRecordingComplete, onError, maxDuration]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && state.isRecording) {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    setState(prev => ({
      ...prev,
      isRecording: false,
    }));
  }, [state.isRecording]);

  // Cancel recording
  const cancelRecording = useCallback(() => {
    stopRecording();
    audioChunksRef.current = [];
    setState(prev => ({
      ...prev,
      duration: 0,
      error: null,
    }));
  }, [stopRecording]);

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    state,
    startRecording,
    stopRecording,
    cancelRecording,
    clearError,
    isSupported:
      typeof navigator !== 'undefined' &&
      !!navigator.mediaDevices?.getUserMedia,
  };
}
