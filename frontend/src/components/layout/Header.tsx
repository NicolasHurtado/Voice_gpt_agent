'use client';

import { motion } from 'framer-motion';
import { Badge } from '@/components/ui';
import { MicrophoneIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';

interface HeaderProps {
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
}

export function Header({ isConnected, connectionStatus }: HeaderProps) {
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'success';
      case 'connecting':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return 'Connection Error';
      default:
        return 'Disconnected';
    }
  };

  return (
    <motion.header
      className='sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-sm'
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className='mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8'>
        {/* Logo and Title */}
        <div className='flex items-center space-x-3'>
          <motion.div
            className='flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600'
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <MicrophoneIcon className='h-6 w-6 text-white' />
          </motion.div>
          <div>
            <h1 className='text-xl font-bold text-gray-900'>Voice GPT Agent</h1>
            <p className='text-sm text-gray-500'>AI-powered voice assistant</p>
          </div>
        </div>

        {/* Status and Actions */}
        <div className='flex items-center space-x-4'>
          {/* Connection Status */}
          <Badge
            variant={getStatusColor()}
            dot={connectionStatus === 'connecting'}
          >
            {getStatusText()}
          </Badge>

          {/* Settings Button */}
          <motion.button
            className='flex h-10 w-10 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600'
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Cog6ToothIcon className='h-5 w-5' />
          </motion.button>
        </div>
      </div>
    </motion.header>
  );
}
