/*
 * DesignButton Component
 * Shared button component with built-in buttonPress animation
 * Integrates with design system tokens and animations
 */

import React, { forwardRef } from 'react';
import { motion, MotionProps } from 'motion/react';
import { useReducedMotionPreference } from '../../hooks/useReducedMotionPreference';

interface DesignButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
  size?: 'sm' | 'md' | 'lg';
  asChild?: boolean;
  motionVariant?: 'buttonPress' | 'hover' | 'active' | 'focus';
}

const DesignButton = forwardRef<HTMLButtonElement, DesignButtonProps>(
  (
    {
      variant = 'primary',
      loading = false,
      size = 'md',
      disabled = false,
      className = '',
      children,
      onClick,
      motionVariant = 'buttonPress',
      ...props
    },
    ref
  ) => {
  const prefersReducedMotion = useReducedMotionPreference();
  const isDisabled = disabled || loading;

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'px-3 py-1.5 text-xs';
      case 'lg':
        return 'px-6 py-3 text-base';
      default:
        return 'px-4 py-2 text-sm';
    }
  };

  const getVariantClasses = () => {
    switch (variant) {
      case 'secondary':
        return 'bg-gray-100 text-gray-900 border border-gray-300 hover:bg-gray-200';
      case 'danger':
        return 'bg-red-600 text-white hover:bg-red-700';
      default:
        return 'bg-blue-600 text-white hover:bg-blue-700';
    }
  };

  const baseClasses = `
    ${getSizeClasses()}
    ${getVariantClasses()}
    rounded-lg
    font-medium
    transition-all
    duration-200
    ease-in-out
    cursor-pointer
    focus:outline-none
    focus:ring-2
    focus:ring-blue-500
    focus:ring-offset-2
    disabled:opacity-50
    disabled:cursor-not-allowed
    ${className}
  `.trim().replace(/\s+/g, ' ');

  const motionConfigs = {
    buttonPress: {
      whileHover: !prefersReducedMotion && !isDisabled ? { scale: 1.02 } : {},
      whileTap: !prefersReducedMotion && !isDisabled ? { scale: 0.98 } : {},
      transition: { duration: 0.2, ease: 'easeInOut' },
    },
    hover: {
      whileHover: !prefersReducedMotion && !isDisabled ? { scale: 1.02 } : {},
      transition: { duration: 0.2, ease: 'easeInOut' },
    },
    active: {
      whileTap: !prefersReducedMotion && !isDisabled ? { scale: 0.98 } : {},
      transition: { duration: 0.2, ease: 'easeInOut' },
    },
    focus: {
      whileHover: !prefersReducedMotion && !isDisabled ? { scale: 1.02 } : {},
      transition: { duration: 0.2, ease: 'easeInOut' },
    },
  };

  const currentMotion = prefersReducedMotion || isDisabled ? {} : motionConfigs[motionVariant];

  return (
    <motion.button
      ref={ref}
      className={baseClasses}
      disabled={isDisabled}
      onClick={onClick}
      {...currentMotion}
      {...(props as MotionProps)}
    >
      {loading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
      )}
      {children}
    </motion.button>
  );
});

DesignButton.displayName = 'DesignButton';

export default DesignButton;