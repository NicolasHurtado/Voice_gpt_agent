'use client';

import { Header } from '@/components/layout/Header';
import { ChatInterface } from '@/components/features';
import { useChatStore } from '@/stores/chatStore';

export default function ChatPage() {
  const { isConnected, connectionStatus } = useChatStore();

  return (
    <div className='min-h-screen flex flex-col'>
      <Header isConnected={isConnected} connectionStatus={connectionStatus} />
      <div className='flex-1'>
        <ChatInterface className='h-full' />
      </div>
    </div>
  );
}