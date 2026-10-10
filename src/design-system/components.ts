/*
 * Component Style Patterns
 * Reusable component style patterns for consistency
 */

import tokens from './tokens';

const components = {
  // Card component pattern
  card: {
    backgroundColor: tokens.colors.bg.elevated,
    borderRadius: tokens.borderRadius.lg,
    border: `1px solid ${tokens.colors.border.primary}`,
    boxShadow: tokens.shadows.sm,
    transition: tokens.transitions.normal,
    padding: tokens.spacing['4'],
    
    hover: {
      boxShadow: tokens.shadows.md,
      borderColor: tokens.colors.border.secondary,
    },
  },
  
  // Button component pattern
  button: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: `${tokens.spacing['2']} ${tokens.spacing['4']}`,
    borderRadius: tokens.borderRadius.md,
    fontSize: tokens.typography.fontSize.sm,
    fontWeight: tokens.typography.fontWeight.semibold,
    transition: tokens.transitions.fast,
    cursor: 'pointer',
    border: 'none',
    outline: 'none',
    position: 'relative',
    whiteSpace: 'nowrap',
    
    variants: {
      primary: {
        backgroundColor: tokens.colors.interactive.primary,
        color: '#FFFFFF',
        '&:hover': {
          backgroundColor: tokens.colors.interactive.primaryHover,
          transform: 'translateY(-1px)',
        },
        '&:active': {
          backgroundColor: tokens.colors.interactive.primaryActive,
          transform: 'translateY(0)',
        },
      },
      
      secondary: {
        backgroundColor: tokens.colors.interactive.secondary,
        color: tokens.colors.text.primary,
        border: `1px solid ${tokens.colors.border.primary}`,
        '&:hover': {
          backgroundColor: tokens.colors.interactive.secondaryHover,
        },
        '&:active': {
          backgroundColor: tokens.colors.interactive.secondaryActive,
        },
      },
      
      danger: {
        backgroundColor: tokens.colors.interactive.danger,
        color: '#FFFFFF',
        '&:hover': {
          backgroundColor: tokens.colors.interactive.dangerHover,
        },
        '&:active': {
          backgroundColor: tokens.colors.interactive.dangerActive,
        },
      },
    },
  },
  
  // Input component pattern
  input: {
    padding: `${tokens.spacing['2']} ${tokens.spacing['3']}`,
    borderRadius: tokens.borderRadius.md,
    border: `1px solid ${tokens.colors.border.primary}`,
    backgroundColor: tokens.colors.bg.primary,
    fontSize: tokens.typography.fontSize.sm,
    color: tokens.colors.text.primary,
    transition: tokens.transitions.fast,
    '&:focus': {
      outline: 'none',
      borderColor: tokens.colors.border.focus,
      boxShadow: `0 0 0 3px ${tokens.colors.interactive.primary}20`,
    },
  },
  
  // Layout patterns
  layout: {
    container: {
      maxWidth: '1280px',
      margin: '0 auto',
      padding: tokens.spacing['4'],
    },
    
    section: {
      padding: `${tokens.spacing['8']} 0`,
    },
    
    grid: {
      display: 'grid',
      gap: tokens.spacing['4'],
    },
  },
};

export default components;
