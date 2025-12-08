/**
 * Design Tokens
 * Central source of truth for design values
 */

export const tokens = {
  colors: {
    // Primary brand colors
    primary: '#667eea',
    primaryHover: '#5568d3',
    primaryLight: '#8b9fef',
    
    // Secondary colors
    secondary: '#764ba2',
    secondaryHover: '#5f3d85',
    
    // Semantic colors
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
    
    // Neutrals
    background: '#0f1419',
    surface: '#1a1f2e',
    surfaceHover: '#252b3b',
    
    // Text
    textPrimary: '#ffffff',
    textSecondary: '#94a3b8',
    textMuted: '#64748b',
    
    // Borders
    border: '#334155',
    borderLight: '#475569',
    
    // Overlay
    overlay: 'rgba(0, 0, 0, 0.8)',
  },
  
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
  },
  
  typography: {
    fonts: {
      body: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      heading: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      mono: '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", monospace',
    },
    sizes: {
      xs: '12px',
      sm: '14px',
      md: '16px',
      lg: '18px',
      xl: '20px',
      '2xl': '24px',
      '3xl': '30px',
      '4xl': '36px',
    },
    weights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeights: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },
  
  radius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px',
  },
  
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    glow: '0 0 20px rgba(102, 126, 234, 0.4)',
  },
  
  transitions: {
    fast: '150ms ease',
    normal: '250ms ease',
    slow: '350ms ease',
  },
  
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
  },
};

export default tokens;
