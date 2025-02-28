const defaultTheme = require('tailwindcss/defaultTheme'); // tailwindcss/defaultTheme v3.3.0

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/web/**/*.{js,jsx,ts,tsx}',
    './src/web/**/*.html',
    './public/index.html',
  ],
  theme: {
    extend: {
      colors: {
        // Primary colors
        primary: {
          DEFAULT: '#2C6ECB', // Primary Blue for buttons, links, primary actions
          hover: '#2561B7', // 10% darker for hover states
          active: '#225AAA', // 15% darker for active states
        },
        secondary: {
          DEFAULT: '#20B2AA', // Secondary Teal for highlights, secondary actions
          hover: '#1CA099', // 10% darker
          active: '#198F88', // 15% darker
        },
        neutral: {
          DEFAULT: '#F5F7FA', // Neutral Gray for backgrounds, containers
        },
        
        // Text colors
        text: {
          primary: '#333333', // Main document text
          secondary: '#666666', // Labels, descriptions
          tertiary: '#999999', // Hints, placeholders
        },
        
        // Track changes colors
        trackChanges: {
          deletion: '#FF6B6B', // Red, struck-through text
          addition: '#20A779', // Green, underlined text
          comment: '#F9A826', // Orange, comment indicators
        },
        
        // Status colors
        status: {
          success: '#28A745', // Confirmation messages
          warning: '#FFC107', // Alert notifications
          error: '#DC3545', // Error messages
          info: '#17A2B8', // Information messages
        },
      },
      fontFamily: {
        sans: ['Inter', ...defaultTheme.fontFamily.sans], // Primary UI font
        serif: ['Source Serif Pro', ...defaultTheme.fontFamily.serif], // Document text font
        mono: ['Roboto Mono', ...defaultTheme.fontFamily.mono], // Code blocks font
      },
      fontSize: {
        'xs': ['12px', { lineHeight: '1.4' }], // Small Text (hints, metadata)
        'sm': ['14px', { lineHeight: '1.4' }], // UI Elements (buttons, inputs, labels)
        'base': ['16px', { lineHeight: '1.6' }], // Document Text (base size for content)
        'lg': ['18px', { lineHeight: '1.2' }], // H3
        'xl': ['20px', { lineHeight: '1.2' }], // H2
        '2xl': ['24px', { lineHeight: '1.2' }], // H1
      },
      lineHeight: {
        'document': '1.6', // Document Content
        'ui': '1.4', // UI Elements
        'heading': '1.2', // Headings
      },
      screens: {
        'tablet': '768px',  // Tablet and up (768px - 1024px)
        'desktop': '1025px', // Desktop and up (> 1024px)
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'), // @tailwindcss/forms v0.5.3
    require('@tailwindcss/typography'), // @tailwindcss/typography v0.5.9
  ],
  safelist: [
    // Status colors
    'text-status-success', 'text-status-warning', 'text-status-error', 'text-status-info',
    'bg-status-success', 'bg-status-warning', 'bg-status-error', 'bg-status-info',
    // Track changes
    'text-trackChanges-deletion', 'text-trackChanges-addition', 'text-trackChanges-comment',
    'bg-trackChanges-deletion', 'bg-trackChanges-addition', 'bg-trackChanges-comment',
  ],
};