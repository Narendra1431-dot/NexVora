/*
 * Design System Tokens
 * Centralized token definitions for NexVora premium UI
 */

// Color palette - Premium career intelligence palette
const tokens = {
  // Core surface colors
  colors: {
    // Background hierarchy
    bg: {
      primary: '#FFFFFF',
      secondary: '#F8FAFC',
      tertiary: '#F1F5F9',
      elevated: '#FFFFFF',
      overlay: 'rgba(15, 23, 42, 0.5)',
    },
    
    // Text hierarchy
    text: {
      primary: '#0F172A',
      secondary: '#334155',
      muted: '#64748B',
      subtle: '#94A3B8',
    },
    
    // Border hierarchy
    border: {
      primary: '#E2E8F0',
      secondary: '#CBD5E1',
      subtle: '#E5E7EB',
      focus: '#818CF8',
    },
    
    // Interactive states
    interactive: {
      primary: '#6366F1',
      primaryHover: '#4338CA',
      primaryActive: '#312E81',
      secondary: '#F1F5F9',
      secondaryHover: '#E2E8F0',
      secondaryActive: '#CBD5E1',
      danger: '#EF4444',
      dangerHover: '#DC2626',
      dangerActive: '#B91C1C',
    },
    
    // Semantic colors
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
    
    // Premium accent palette
    navy: {
      900: '#0F172A',
      800: '#1E293B',
      700: '#334155',
      600: '#475569',
      500: '#64748B',
      400: '#94A3B8',
      300: '#CBD5E1',
      200: '#E2E8F0',
      100: '#F1F5F9',
      50: '#F8FAFC',
    },
    
    indigo: {
      900: '#312E81',
      800: '#4338CA',
      700: '#6366F1',
      600: '#818CF8',
      500: '#A5B4FC',
      400: '#C7D2FE',
      300: '#E0E7FF',
    },
    
    violet: {
      900: '#581C87',
      800: '#7C3AED',
      700: '#8B5CF6',
      600: '#A78BFA',
      500: '#C4B5FD',
      400: '#DDD6FE',
    },
    
    pink: {
      900: '#831843',
      800: '#BE185D',
      700: '#EC4899',
      600: '#F472B6',
      500: '#F9A8D4',
      400: '#FBCFE8',
    },
  },
  
  // Typography scale
  typography: {
    fontFamily: {
      sans: 'Inter, system-ui, sans-serif',
      heading: 'Manrope, Inter, system-ui, sans-serif',
      mono: 'SF Mono, Monaco, Cascadia Code, monospace',
    },
    
    fontSize: {
      '2xs': '0.625rem',  // 10px
      xs: '0.75rem',      // 12px
      sm: '0.875rem',    // 14px
      base: '1rem',       // 16px
      lg: '1.125rem',    // 18px
      xl: '1.25rem',     // 20px
      '2xl': '1.5rem',   // 24px
      '3xl': '1.875rem', // 30px
      '4xl': '2.25rem',  // 36px
    },
    
    fontWeight: {
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
    },
    
    lineHeight: {
      none: '1',
      tight: '1.25',
      snug: '1.375',
      normal: '1.5',
      relaxed: '1.625',
      loose: '2',
    },
  },
  
  // Spacing scale (4px base)
  spacing: {
    '0': '0',
    '1': '0.25rem',  // 4px
    '2': '0.5rem',   // 8px
    '3': '0.75rem',  // 12px
    '4': '1rem',     // 16px
    '5': '1.25rem', // 20px
    '6': '1.5rem',  // 24px
    '7': '1.75rem', // 28px
    '8': '2rem',    // 32px
    '9': '2.5rem',  // 40px
    '10': '3rem',   // 48px
    '11': '3.5rem', // 56px
    '12': '4rem',   // 64px
  },
  
  // Shadow scale for depth
  shadows: {
    xs: '0 1px 2px rgba(0, 0, 0, 0.05)',
    sm: '0 1px 3px rgba(0, 0, 0, 0.1)',
    md: '0 4px 6px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px rgba(0, 0, 0, 0.1)',
  },
  
  // Border radius scale
  borderRadius: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
  },
  
  // Transition durations
  transitions: {
    fast: '150ms ease-in-out',
    normal: '300ms ease-in-out',
    slow: '500ms ease-in-out',
  },
  
  // Z-index scale
  zIndex: {
    dropdown: '1000',
    sticky: '1020',
    fixed: '1030',
    modal: '1040',
    popover: '1050',
    tooltip: '1060',
  },
};

export default tokens;
