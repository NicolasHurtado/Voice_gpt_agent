'use client';

import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MicrophoneIcon,
  StopIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { Button, Badge } from '@/components/ui';
import { useVoiceRecording } from '@/hooks/useVoiceRecording';
import { useAudioAnalyzer } from '@/hooks/useAudioAnalyzer';
import { AudioWaveform } from './AudioWaveform';
import { formatDuration } from '@/utils/helpers';
import { cn } from '@/utils/helpers';

interface VoiceRecorderProps {
  onRecordingComplete?: (audioBlob: Blob) => void;
  onError?: (error: string) => void;
  maxDuration?: number;
  className?: string;
}

export function VoiceRecorder({
  onRecordingComplete,
  onError,
  maxDuration = 300,
  className,
}: VoiceRecorderProps) {
  const {
    state,
    startRecording,
    stopRecording,
    cancelRecording,
    clearError,
    isSupported,
  } = useVoiceRecording({
    onRecordingComplete,
    onError,
    maxDuration,
  });

  const { analyzerData, initializeAnalyzer, stopAnalyzing } =
    useAudioAnalyzer();

  // Initialize analyzer when recording starts
  useEffect(() => {
    if (state.isRecording) {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then(initializeAnalyzer)
        .catch(console.error);
    } else {
      stopAnalyzing();
    }
  }, [state.isRecording, initializeAnalyzer, stopAnalyzing]);

  if (!isSupported) {
    return (
      <div className={cn('text-center p-6', className)}>
        <p className='text-gray-600'>
          Voice recording is not supported in your browser.
        </p>
      </div>
    );
  }

  return (
    <div className={cn('w-full max-w-2xl mx-auto', className)}>
      {/* Error Display */}
      <AnimatePresence>
        {state.error && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className='mb-4 rounded-lg bg-red-50 p-4'
          >
            <div className='flex items-center justify-between'>
              <p className='text-sm text-red-600'>{state.error}</p>
              <Button
                variant='ghost'
                size='sm'
                onClick={clearError}
                className='text-red-600 hover:bg-red-100'
              >
                <XMarkIcon className='h-4 w-4' />
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Recording Interface */}
      <div className='rounded-lg border border-gray-200 bg-white p-6 shadow-sm'>
        {/* Status Bar */}
        <div className='mb-6 flex items-center justify-between'>
          <div className='flex items-center space-x-3'>
            <Badge
              variant={state.isRecording ? 'error' : 'default'}
              dot={state.isRecording}
            >
              {state.isRecording ? 'Recording' : 'Ready'}
            </Badge>
            {state.isRecording && (
              <span className='text-sm text-gray-600'>
                {formatDuration(state.duration * 1000)}
              </span>
            )}
          </div>

          {maxDuration && (
            <span className='text-xs text-gray-500'>
              Max: {formatDuration(maxDuration * 1000)}
            </span>
          )}
        </div>

        {/* Waveform Visualization */}
        <div className='mb-6'>
          <AudioWaveform
            analyzerData={analyzerData}
            isRecording={state.isRecording}
            height={80}
            className='w-full'
          />
        </div>

        {/* Controls */}
        <div className='flex items-center justify-center space-x-4'>
          {!state.isRecording ? (
            <Button
              onClick={startRecording}
              disabled={state.isLoading}
              isLoading={state.isLoading}
              variant='primary'
              size='lg'
              leftIcon={<MicrophoneIcon className='h-6 w-6' />}
              className='min-w-[160px]'
            >
              {state.isLoading ? 'Starting...' : 'Start Recording'}
            </Button>
          ) : (
            <>
              <Button
                onClick={stopRecording}
                variant='primary'
                size='lg'
                leftIcon={<StopIcon className='h-6 w-6' />}
                className='min-w-[120px]'
              >
                Stop
              </Button>

              <Button
                onClick={cancelRecording}
                variant='outline'
                size='lg'
                leftIcon={<XMarkIcon className='h-6 w-6' />}
                className='min-w-[120px]'
              >
                Cancel
              </Button>
            </>
          )}
        </div>

        {/* Recording Indicator */}
        <AnimatePresence>
          {state.isRecording && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className='mt-4 text-center'
            >
              <motion.div
                className='mx-auto h-3 w-3 rounded-full bg-red-500'
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
              />
              <p className='mt-2 text-xs text-gray-500'>
                Speak clearly into your microphone
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
