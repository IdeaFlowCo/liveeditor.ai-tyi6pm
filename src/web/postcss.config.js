/**
 * PostCSS Configuration
 * 
 * This file defines the CSS processing pipeline for the AI writing enhancement interface.
 * The configuration integrates TailwindCSS for utility-first styling and Autoprefixer
 * for cross-browser compatibility.
 */

module.exports = {
  plugins: [
    // tailwindcss v3.3.0 - Utility-first CSS framework for efficient UI development with responsive design
    require('tailwindcss'),
    
    // autoprefixer v10.4.14 - Add vendor prefixes to CSS rules for cross-browser compatibility
    require('autoprefixer')
  ],
};