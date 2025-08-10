'use client';

import { forwardRef } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/utils/helpers';

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helper?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  variant?: 'default' | 'filled';
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type = 'text',
      label,
      error,
      helper,
      leftIcon,
      rightIcon,
      variant = 'default',
      ...props
    },
    ref
  ) => {
    const hasError = !!error;

    return (
      <div className='w-full'>
        {label && (
          <label className='mb-2 block text-sm font-medium text-gray-700'>
            {label}
          </label>
        )}

        <div className='relative'>
          {leftIcon && (
            <div className='absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400'>
              {leftIcon}
            </div>
          )}

          <motion.input
            ref={ref}
            type={type}
            className={cn(
              // Base styles
              'block w-full rounded-lg border px-3 py-2 text-sm transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-offset-1',
              'disabled:cursor-not-allowed disabled:opacity-50',

              // Variants
              variant === 'default' && [
                'border-gray-300 bg-white text-gray-900',
                'focus:border-blue-500 focus:ring-blue-500',
                hasError &&
                  'border-red-500 focus:border-red-500 focus:ring-red-500',
              ],
              variant === 'filled' && [
                'border-transparent bg-gray-100 text-gray-900',
                'focus:bg-white focus:border-blue-500 focus:ring-blue-500',
                hasError && 'bg-red-50 focus:border-red-500 focus:ring-red-500',
              ],

              // Icon spacing
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',

              className
            )}
            whileFocus={{ scale: 1.01 }}
            transition={{ duration: 0.15 }}
            {...props}
          />

          {rightIcon && (
            <div className='absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400'>
              {rightIcon}
            </div>
          )}
        </div>

        {(error || helper) && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className='mt-1'
          >
            {error && <p className='text-sm text-red-600'>{error}</p>}
            {helper && !error && (
              <p className='text-sm text-gray-500'>{helper}</p>
            )}
          </motion.div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
