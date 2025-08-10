'use client';

import { forwardRef } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '@/utils/helpers';

export interface ButtonProps extends HTMLMotionProps<'button'> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const buttonVariants = {
  primary:
    'bg-blue-600 hover:bg-blue-700 text-white shadow-sm focus:ring-blue-500',
  secondary:
    'bg-gray-600 hover:bg-gray-700 text-white shadow-sm focus:ring-gray-500',
  outline:
    'border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 shadow-sm focus:ring-blue-500',
  ghost: 'bg-transparent hover:bg-gray-100 text-gray-700 focus:ring-gray-500',
  danger: 'bg-red-600 hover:bg-red-700 text-white shadow-sm focus:ring-red-500',
};

const sizeVariants = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
  xl: 'px-8 py-4 text-lg',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <motion.button
        ref={ref}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center rounded-lg font-medium transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          // Variants
          buttonVariants[variant],
          sizeVariants[size],
          className
        )}
        disabled={disabled || isLoading}
        whileHover={{ scale: disabled || isLoading ? 1 : 1.02 }}
        whileTap={{ scale: disabled || isLoading ? 1 : 0.98 }}
        transition={{ duration: 0.15 }}
        {...props}
      >
        {isLoading && (
          <motion.div
            className='mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent'
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
          />
        )}
        {leftIcon && !isLoading && (
          <span className='mr-2 flex items-center'>{leftIcon}</span>
        )}
        {children}
        {rightIcon && (
          <span className='ml-2 flex items-center'>{rightIcon}</span>
        )}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
