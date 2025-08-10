'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  PlayIcon,
  PauseIcon,
  SpeakerWaveIcon,
} from '@heroicons/react/24/outline';
import { Button, Badge } from '@/components/ui';
import { ChatMessage as ChatMessageType } from '@/types/chat';
import { formatDuration } from '@/utils/helpers';
import { cn } from '@/utils/helpers';

interface ChatMessageProps {
  message: ChatMessageType;
  isLast?: boolean;
}

export function ChatMessage({ message, isLast }: ChatMessageProps) {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [audioDuration, setAudioDuration] = useState<number>(0);
  
  const isUser = message.type === 'USER';
  const isAssistant = message.type === 'ASSISTANT';

  const handlePlayAudio = async () => {
    if (!message.audioUrl) return;

    try {
      if (isPlayingAudio) {
        // Pause logic would go here
        setIsPlayingAudio(false);
        return;
      }

      const audio = new Audio(message.audioUrl);
      
      audio.addEventListener('loadedmetadata', () => {
        setAudioDuration(audio.duration);
      });

      audio.addEventListener('ended', () => {
        setIsPlayingAudio(false);
      });

      audio.addEventListener('error', (e) => {
        console.error('Audio playback failed:', e);
        setIsPlayingAudio(false);
      });

      setIsPlayingAudio(true);
      await audio.play();
    } catch (error) {
      console.error('Failed to play audio:', error);
      setIsPlayingAudio(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'flex w-full',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-3',
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-white border border-gray-200 text-gray-900'
        )}
      >
        {/* Message Header */}
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-medium opacity-70">
              {isUser ? 'You' : 'AI Assistant'}
            </span>
            {message.isLoading && (
              <Badge variant="default" className="text-xs">
                Generating...
              </Badge>
            )}
          </div>
          
          <span className="text-xs opacity-50">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>

        {/* Message Content */}
        <div className="mb-2">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        </div>

        {/* Audio Controls */}
        {message.hasAudio && message.audioUrl && (
          <div className="mt-3 flex items-center space-x-2">
            <Button
              onClick={handlePlayAudio}
              variant={isUser ? 'secondary' : 'primary'}
              size="sm"
              leftIcon={
                isPlayingAudio ? (
                  <PauseIcon className="h-4 w-4" />
                ) : (
                  <PlayIcon className="h-4 w-4" />
                )
              }
              className="text-xs"
            >
              {isPlayingAudio ? 'Pause' : 'Play'}
            </Button>
            
            <SpeakerWaveIcon className="h-4 w-4 opacity-60" />
            
            {audioDuration > 0 && (
              <span className="text-xs opacity-60">
                {formatDuration(audioDuration * 1000)}
              </span>
            )}
          </div>
        )}

        {/* Loading Indicator */}
        {message.isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-2 flex items-center space-x-2"
          >
            <div className="flex space-x-1">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className={cn(
                    'h-2 w-2 rounded-full',
                    isUser ? 'bg-blue-200' : 'bg-gray-400'
                  )}
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{
                    duration: 0.6,
                    repeat: Infinity,
                    delay: i * 0.2,
                  }}
                />
              ))}
            </div>
            <span className="text-xs opacity-60">
              Processing audio...
            </span>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}