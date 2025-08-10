'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { AudioAnalyzerData } from '@/types/audio';

interface UseAudioAnalyzerProps {
  fftSize?: number;
  smoothingTimeConstant?: number;
}

export function useAudioAnalyzer({
  fftSize = 256,
  smoothingTimeConstant = 0.8,
}: UseAudioAnalyzerProps = {}) {
  const [analyzerData, setAnalyzerData] = useState<AudioAnalyzerData>({
    frequencyData: new Uint8Array(0),
    timeData: new Uint8Array(0),
    volume: 0,
  });

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animationRef = useRef<number | null>(null);

  // Initialize audio analyzer
  const initializeAnalyzer = useCallback(
    async (stream: MediaStream) => {
      try {
        // Create audio context
        audioContextRef.current = new (window.AudioContext ||
          (window as any).webkitAudioContext)();

        // Create analyzer node
        analyzerRef.current = audioContextRef.current.createAnalyser();
        analyzerRef.current.fftSize = fftSize;
        analyzerRef.current.smoothingTimeConstant = smoothingTimeConstant;

        // Create source from stream
        sourceRef.current =
          audioContextRef.current.createMediaStreamSource(stream);
        sourceRef.current.connect(analyzerRef.current);

        // Start analyzing
        startAnalyzing();
      } catch (error) {
        console.error('Failed to initialize audio analyzer:', error);
      }
    },
    [fftSize, smoothingTimeConstant]
  );

  // Start analyzing audio
  const startAnalyzing = useCallback(() => {
    if (!analyzerRef.current) return;

    const bufferLength = analyzerRef.current.frequencyBinCount;
    const frequencyData = new Uint8Array(bufferLength);
    const timeData = new Uint8Array(bufferLength);

    const analyze = () => {
      if (!analyzerRef.current) return;

      // Get frequency and time domain data
      analyzerRef.current.getByteFrequencyData(frequencyData);
      analyzerRef.current.getByteTimeDomainData(timeData);

      // Calculate volume (RMS)
      let sum = 0;
      for (let i = 0; i < timeData.length; i++) {
        const sample = (timeData[i] - 128) / 128;
        sum += sample * sample;
      }
      const volume = Math.sqrt(sum / timeData.length);

      setAnalyzerData({
        frequencyData: new Uint8Array(frequencyData),
        timeData: new Uint8Array(timeData),
        volume,
      });

      animationRef.current = requestAnimationFrame(analyze);
    };

    analyze();
  }, []);

  // Stop analyzing
  const stopAnalyzing = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }

    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    analyzerRef.current = null;

    // Reset data
    setAnalyzerData({
      frequencyData: new Uint8Array(0),
      timeData: new Uint8Array(0),
      volume: 0,
    });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAnalyzing();
    };
  }, [stopAnalyzing]);

  return {
    analyzerData,
    initializeAnalyzer,
    stopAnalyzing,
    isAnalyzing: !!animationRef.current,
  };
}
