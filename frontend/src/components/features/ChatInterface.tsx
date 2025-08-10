'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PaperAirplaneIcon } from '@heroicons/react/24/outline';
import { Button, Input, Card, Badge } from '@/components/ui';
import { VoiceRecorder } from './VoiceRecorder';
import { ChatMessage } from './ChatMessage';
import { useChatStore } from '@/stores/chatStore';
import { cn } from '@/utils/helpers';

interface ChatInterfaceProps {
  className?: string;
}

export function ChatInterface({ className }: ChatInterfaceProps) {
  const [textInput, setTextInput] = useState('');
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    currentSession,
    connectionStatus,
    isConnected,
    createSession,
    sendMessage,
    setConnectionStatus,
  } = useChatStore();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages]);

  // Initialize session on mount
  useEffect(() => {
    if (!currentSession) {
      createSession().catch(console.error);
    }
  }, [currentSession, createSession]);

  const handleSendText = async () => {
    if (!textInput.trim() || !isConnected) return;

    try {
      await sendMessage({
        type: 'text',
        content: textInput,
        sessionId: currentSession?.id,
      });
      setTextInput('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleSendAudio = async (audioBlob: Blob) => {
    if (!isConnected) return;

    try {
      setShowVoiceRecorder(false);
      await sendMessage({
        type: 'audio',
        content: audioBlob,
        sessionId: currentSession?.id,
      });
    } catch (error) {
      console.error('Failed to send audio:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };

  return (
    <div className={cn('flex h-full flex-col', className)}>
      {/* Header */}
      <div className="border-b border-gray-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              AI Voice Assistant
            </h2>
            <p className="text-sm text-gray-500">
              Type or speak to start a conversation
            </p>
          </div>
          
          <Badge
            variant={
              connectionStatus === 'connected'
                ? 'success'
                : connectionStatus === 'connecting'
                ? 'warning'
                : 'error'
            }
            dot={connectionStatus === 'connecting'}
          >
            {connectionStatus === 'connected'
              ? 'Connected'
              : connectionStatus === 'connecting'
              ? 'Connecting...'
              : 'Disconnected'}
          </Badge>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto bg-gray-50 p-4">
        <div className="mx-auto max-w-3xl space-y-4">
          {/* Welcome Message */}
          {(!currentSession?.messages || currentSession.messages.length === 0) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center"
            >
              <Card className="p-6">
                <div className="mb-4">
                  <div className="mx-auto h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-2xl">🎤</span>
                  </div>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Welcome to Voice GPT Agent
                </h3>
                <p className="text-gray-600">
                  Start a conversation by typing a message or recording your voice.
                  I can understand speech and respond with both text and audio.
                </p>
              </Card>
            </motion.div>
          )}

          {/* Messages */}
          <AnimatePresence>
            {currentSession?.messages.map((message, index) => (
              <ChatMessage
                key={message.id}
                message={message}
                isLast={index === currentSession.messages.length - 1}
              />
            ))}
          </AnimatePresence>

          {/* Typing Indicator */}
          {currentSession?.isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex justify-start"
            >
              <div className="rounded-lg bg-white border border-gray-200 px-4 py-3">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        className="h-2 w-2 rounded-full bg-gray-400"
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{
                          duration: 0.6,
                          repeat: Infinity,
                          delay: i * 0.2,
                        }}
                      />
                    ))}
                  </div>
                  <span className="text-sm text-gray-500">AI is thinking...</span>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="mx-auto max-w-3xl">
          {/* Voice Recorder */}
          <AnimatePresence>
            {showVoiceRecorder && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-4"
              >
                <VoiceRecorder
                  onRecordingComplete={handleSendAudio}
                  onError={(error) => {
                    console.error('Voice recording error:', error);
                    setShowVoiceRecorder(false);
                  }}
                  maxDuration={120} // 2 minutes
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Text Input */}
          <div className="flex space-x-2">
            <div className="flex-1">
              <Input
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  isConnected
                    ? 'Type your message...'
                    : 'Connecting to server...'
                }
                disabled={!isConnected}
                className="w-full"
              />
            </div>
            
            <Button
              onClick={() => setShowVoiceRecorder(!showVoiceRecorder)}
              variant={showVoiceRecorder ? 'secondary' : 'outline'}
              className="flex-shrink-0"
              disabled={!isConnected}
            >
              🎤
            </Button>
            
            <Button
              onClick={handleSendText}
              disabled={!textInput.trim() || !isConnected}
              leftIcon={<PaperAirplaneIcon className="h-4 w-4" />}
              className="flex-shrink-0"
            >
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}