/**
 * Validation Utilities
 * 
 * This module provides utility functions for client-side validation of user inputs,
 * documents, AI prompts, and form data. These functions ensure data integrity and security
 * throughout the application by enforcing consistent validation rules.
 * 
 * @version 1.0.0
 */

import { Document } from '../types/document';
import { User } from '../types/user';
import { MAX_DOCUMENT_SIZE } from '../constants/editor';
import DOMPurify from 'dompurify'; // v2.4.0
import zxcvbn from 'zxcvbn'; // v4.4.2

/**
 * Password validation result interface
 */
export interface PasswordValidationResult {
  isValid: boolean;
  errorMessage?: string;
  score?: number;
}

/**
 * Document size validation result interface
 */
export interface DocumentSizeValidationResult {
  isValid: boolean;
  wordCount: number;
  errorMessage?: string;
}

/**
 * Document format validation result interface
 */
export interface DocumentFormatValidationResult {
  isValid: boolean;
  format?: string;
  errorMessage?: string;
}

/**
 * Prompt validation result interface
 */
export interface PromptValidationResult {
  isValid: boolean;
  errorMessage?: string;
}

/**
 * Generic form validation result interface
 */
export interface FormValidationResult {
  isValid: boolean;
  errorMessage?: string;
}

/**
 * Validation rule interface for form fields
 */
export interface ValidationRule {
  validator: (value: any) => boolean;
  errorMessage: string;
}

/**
 * Validates email format using RFC 5322 standard
 * 
 * @param email - Email address to validate
 * @returns Boolean indicating if email is valid
 */
export const validateEmail = (email: string): boolean => {
  if (!email) return false;
  
  // Standard email regex that balances correctness with maintainability
  const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
  
  return emailRegex.test(email.trim());
};

/**
 * Validates password strength and compliance with security requirements
 * 
 * @param password - Password to validate
 * @returns Object containing validation result and optional error message
 */
export const validatePassword = (password: string): PasswordValidationResult => {
  if (!password) {
    return { isValid: false, errorMessage: 'Password is required' };
  }
  
  // Collect all validation errors
  const errors = [];
  
  // Check minimum length (10 characters)
  if (password.length < 10) {
    errors.push('at least 10 characters long');
  }
  
  // Check for uppercase letter
  if (!/[A-Z]/.test(password)) {
    errors.push('one uppercase letter');
  }
  
  // Check for lowercase letter
  if (!/[a-z]/.test(password)) {
    errors.push('one lowercase letter');
  }
  
  // Check for number
  if (!/[0-9]/.test(password)) {
    errors.push('one number');
  }
  
  // Check for special character
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push('one special character');
  }
  
  // If there are basic requirement errors, return them
  if (errors.length > 0) {
    return { 
      isValid: false, 
      errorMessage: `Password must contain ${errors.join(', ')}`,
      score: errors.length >= 4 ? 0 : 1
    };
  }
  
  // Use zxcvbn for comprehensive password strength analysis
  const result = zxcvbn(password);
  
  // Score 0-1 is too weak, 2 is weak, 3 is good, 4 is strong
  if (result.score < 3) {
    return { 
      isValid: false, 
      errorMessage: 'Password is too weak. Try adding more variety or length.',
      score: result.score
    };
  }
  
  return { isValid: true, score: result.score };
};

/**
 * Validates that password and confirmation password match
 * 
 * @param password - Original password
 * @param confirmPassword - Confirmation password to compare
 * @returns Boolean indicating if passwords match
 */
export const validatePasswordMatch = (password: string, confirmPassword: string): boolean => {
  if (!password || !confirmPassword) return false;
  return password === confirmPassword;
};

/**
 * Validates that a required field has a value
 * 
 * @param value - Value to check
 * @returns Boolean indicating if value exists and is not empty
 */
export const validateRequired = (value: any): boolean => {
  if (value === undefined || value === null) return false;
  
  // For strings, check if non-empty after trimming
  if (typeof value === 'string') return value.trim().length > 0;
  
  // For arrays, check if non-empty
  if (Array.isArray(value)) return value.length > 0;
  
  // For objects, check if it has properties (and is not a Date)
  if (typeof value === 'object' && !(value instanceof Date)) {
    return Object.keys(value).length > 0;
  }
  
  // For other types, consider them valid if they exist
  return true;
};

/**
 * Counts words in a text string
 * 
 * @param text - Text string to count words in
 * @returns Number of words in the text
 */
export const getWordCount = (text: string): number => {
  if (!text) return 0;
  
  // Split by whitespace and filter out empty strings
  const words = text.trim().split(/\s+/).filter(word => word.length > 0);
  return words.length;
};

/**
 * Validates that document content is within the allowed size limit
 * 
 * @param content - Document content to validate
 * @returns Object containing validation result and word count
 */
export const validateDocumentSize = (content: string): DocumentSizeValidationResult => {
  const wordCount = getWordCount(content);
  
  return {
    isValid: wordCount <= MAX_DOCUMENT_SIZE,
    wordCount,
    errorMessage: wordCount > MAX_DOCUMENT_SIZE 
      ? `Document exceeds the maximum size of ${MAX_DOCUMENT_SIZE} words (current size: ${wordCount} words)`
      : undefined
  };
};

/**
 * Validates that document format is supported
 * 
 * @param fileName - Name of the file to validate
 * @returns Object containing validation result and format information
 */
export const validateDocumentFormat = (fileName: string): DocumentFormatValidationResult => {
  if (!fileName) {
    return { isValid: false, errorMessage: 'No file name provided' };
  }
  
  // Extract file extension
  const extension = fileName.split('.').pop()?.toLowerCase();
  
  if (!extension) {
    return { isValid: false, errorMessage: 'Could not determine file format' };
  }
  
  // Map file extensions to supported formats
  const supportedExtensions: Record<string, string> = {
    'txt': 'TEXT',
    'html': 'HTML',
    'md': 'MARKDOWN',
    'docx': 'DOCX',
    'rtf': 'TEXT'
  };
  
  // Check if extension is supported
  if (!Object.keys(supportedExtensions).includes(extension)) {
    return { 
      isValid: false, 
      format: extension,
      errorMessage: `Format .${extension} is not supported. Please use: txt, html, md, docx, rtf`
    };
  }
  
  return { 
    isValid: true, 
    format: supportedExtensions[extension]
  };
};

/**
 * Sanitizes HTML content to prevent XSS attacks
 * 
 * @param content - HTML content to sanitize
 * @returns Sanitized content safe for rendering
 */
export const sanitizeContent = (content: string): string => {
  if (!content) return '';
  
  // Configure DOMPurify to allow only specific HTML tags and attributes
  const purifyConfig = {
    ALLOWED_TAGS: [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'div', 
      'ul', 'ol', 'li', 'a', 'br', 'strong', 'em', 'i', 'b',
      'blockquote', 'code', 'pre', 'hr'
    ],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'id'],
    FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'style'],
    FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'style']
  };
  
  return DOMPurify.sanitize(content, purifyConfig);
};

/**
 * Validates AI prompt for potential injection attacks and content policy compliance
 * 
 * @param prompt - AI prompt to validate
 * @returns Object containing validation result and possible error information
 */
export const validatePrompt = (prompt: string): PromptValidationResult => {
  if (!prompt || prompt.trim().length === 0) {
    return { isValid: false, errorMessage: 'Prompt cannot be empty' };
  }
  
  // Check length - limit to reasonable size (e.g., 500 characters)
  if (prompt.length > 500) {
    return { isValid: false, errorMessage: 'Prompt is too long (maximum 500 characters)' };
  }
  
  // Check for potential code injection patterns
  const codeInjectionPatterns = [
    /<script/i, // Script tag
    /<iframe/i, // iFrame tag
    /\beval\s*\(/i, // Eval function
    /\bprocess\.env/i, // Environment variables
    /\bfs\s*\.\s*(read|write)/i, // File system operations
    /\bexec\s*\(/i, // Exec command
    /\bsystem\s*\(/i // System command
  ];
  
  for (const pattern of codeInjectionPatterns) {
    if (pattern.test(prompt)) {
      return { 
        isValid: false, 
        errorMessage: 'Your prompt contains patterns that are not allowed for security reasons'
      };
    }
  }
  
  // Check for attempts to override system instructions
  const systemOverridePatterns = [
    /ignore (previous|above|all) instructions/i,
    /disregard (your|all) (programming|instructions)/i,
    /bypass (your|system) constraints/i,
    /override (your|system) (guidelines|instructions)/i,
    /ignore (content|safety) (policies|restrictions)/i
  ];
  
  for (const pattern of systemOverridePatterns) {
    if (pattern.test(prompt)) {
      return { 
        isValid: false, 
        errorMessage: 'Your prompt appears to be asking the AI to ignore its guidelines'
      };
    }
  }
  
  return { isValid: true };
};

/**
 * Generic validation function for form fields with provided validation rules
 * 
 * @param value - Value to validate
 * @param validationRules - Array of validation rules to apply
 * @returns Validation result with isValid flag and possible error message
 */
export const validateFormField = (
  value: any, 
  validationRules: ValidationRule[]
): FormValidationResult => {
  if (!validationRules || validationRules.length === 0) {
    return { isValid: true };
  }
  
  for (const rule of validationRules) {
    if (!rule.validator(value)) {
      return { isValid: false, errorMessage: rule.errorMessage };
    }
  }
  
  return { isValid: true };
};