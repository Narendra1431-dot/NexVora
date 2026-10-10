/*
 * Animation Utilities
 * Animation utilities for smooth interactions
 */

import tokens from './tokens';

const animations = {
  // Micro-interactions
  hover: {
    transform: 'translateY(-1px)',
    boxShadow: tokens.shadows.md,
  },
  
  active: {
    transform: 'translateY(0)',
    boxShadow: tokens.shadows.sm,
  },
  
  focus: {
    borderColor: tokens.colors.border.focus,
    boxShadow: `0 0 0 3px ${tokens.colors.interactive.primary}20`,
  },
  
  // Entrance animations
  fadeIn: {
    from: { opacity: 0 },
    to: { opacity: 1 },
  },
  
  slideUp: {
    from: { opacity: 0, transform: 'translateY(20px)' },
    to: { opacity: 1, transform: 'translateY(0)' },
  },
  
  scaleIn: {
    from: { opacity: 0, transform: 'scale(0.95)' },
    to: { opacity: 1, transform: 'scale(1)' },
  },
  
  // Staggered animations
  staggerContainer: {
    from: { opacity: 0 },
    to: { 
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      }
    },
  },
  
  // Page transitions
  pageSlide: {
    from: { opacity: 0, transform: 'translateX(10px)' },
    to: { opacity: 1, transform: 'translateX(0)' },
  },
  
  // Toast notifications
  toastSlideIn: {
    from: { opacity: 0, transform: 'translateX(100%)' },
    to: { opacity: 1, transform: 'translateX(0)' },
  },
  
  toastSlideOut: {
    from: { opacity: 1, transform: 'translateX(0)' },
    to: { opacity: 0, transform: 'translateX(100%)' },
  },
  
  // Dialog/drawer transitions
  dialogFade: {
    from: { opacity: 0 },
    to: { opacity: 1 },
  },
  
  drawerSlide: {
    from: { opacity: 0, transform: 'translateX(-100%)' },
    to: { opacity: 1, transform: 'translateX(0)' },
  },
  
  // Reduced motion support
  reducedMotion: {
    transition: 'none',
    animation: 'none',
  },
  
  // Button press
  buttonPress: {
    from: { transform: 'scale(1)' },
    to: { transform: 'scale(0.98)' },
  },
  
  // Loading skeleton
  pulse: {
    from: { opacity: 0.6 },
    to: { opacity: 1 },
  },
};

export default animations;
