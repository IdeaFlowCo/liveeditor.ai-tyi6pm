/**
 * Utility functions for formatting text, dates, numbers, and suggestions for the AI writing enhancement interface.
 */

import { Document } from '../types/document';
import { Suggestion } from '../types/suggestion';
import * as EDITOR_CONSTANTS from '../constants/editor';
import { format, formatDistance, formatDistanceToNow } from 'date-fns'; // ^2.29.3

/**
 * Truncates text to a specified length and adds ellipsis if needed
 * 
 * @param text - The text to truncate
 * @param maxLength - Maximum length before truncation
 * @param ellipsis - String to append to truncated text (default: '...')
 * @returns Truncated text with ellipsis if needed
 */
export const truncateText = (text: string, maxLength: number, ellipsis: string = '...'): string => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + ellipsis;
};

/**
 * Strips HTML tags and formats as plain text
 * 
 * @param html - HTML string to convert to plain text
 * @returns Plain text without HTML tags
 */
export const formatPlainText = (html: string): string => {
  if (!html) return '';
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = html;
  return tempDiv.textContent || tempDiv.innerText || '';
};

/**
 * Normalizes whitespace in text (removes extra spaces, newlines, etc.)
 * 
 * @param text - Text to normalize
 * @returns Text with normalized whitespace
 */
export const normalizeWhitespace = (text: string): string => {
  if (!text) return '';
  return text.replace(/\s+/g, ' ').trim();
};

/**
 * Formats a date using a specified format string
 * 
 * @param date - Date to format
 * @param formatString - Format string to use
 * @returns Formatted date string
 */
export const formatDate = (date: Date | string | number, formatString: string): string => {
  if (!date) return '';
  return format(new Date(date), formatString);
};

/**
 * Formats a date as relative time (e.g., '2 hours ago')
 * 
 * @param date - Date to format
 * @returns Relative time string
 */
export const formatRelativeTime = (date: Date | string | number): string => {
  if (!date) return '';
  return formatDistanceToNow(new Date(date), { addSuffix: true });
};

/**
 * Formats a document date/time with the application's standard format
 * 
 * @param date - Date to format
 * @returns Formatted document date
 */
export const formatDocumentDate = (date: Date | string | number): string => {
  if (!date) return '';
  const dateObj = new Date(date);
  const today = new Date();
  const isToday = dateObj.getDate() === today.getDate() &&
    dateObj.getMonth() === today.getMonth() &&
    dateObj.getFullYear() === today.getFullYear();

  if (isToday) {
    return format(dateObj, "'Today at' h:mm a");
  }
  return format(dateObj, 'MMM d, yyyy h:mm a');
};

/**
 * Formats a word count with thousands separator
 * 
 * @param count - Word count to format
 * @returns Formatted word count (e.g., '1,234 words')
 */
export const formatWordCount = (count: number): string => {
  const formatted = count.toLocaleString();
  return `${formatted} ${count === 1 ? 'word' : 'words'}`;
};

/**
 * Formats a character count with thousands separator
 * 
 * @param count - Character count to format
 * @returns Formatted character count (e.g., '1,234 characters')
 */
export const formatCharacterCount = (count: number): string => {
  const formatted = count.toLocaleString();
  return `${formatted} ${count === 1 ? 'character' : 'characters'}`;
};

/**
 * Formats a file size in bytes to a human-readable format
 * 
 * @param bytes - File size in bytes
 * @returns Formatted file size (e.g., '1.23 MB')
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const formattedSize = parseFloat((bytes / Math.pow(k, i)).toFixed(2));
  
  return `${formattedSize} ${sizes[i]}`;
};

/**
 * Formats deleted text for display in track changes
 * 
 * @param text - Text to format as deleted
 * @returns HTML-formatted deletion
 */
export const formatDeletion = (text: string): string => {
  if (!text) return '';
  const escapedText = escapeHtml(text);
  return `<span class="deletion" style="text-decoration: line-through; color: ${EDITOR_CONSTANTS.TRACK_CHANGES_STYLES.DELETION_COLOR};">${escapedText}</span>`;
};

/**
 * Formats added text for display in track changes
 * 
 * @param text - Text to format as added
 * @returns HTML-formatted addition
 */
export const formatAddition = (text: string): string => {
  if (!text) return '';
  const escapedText = escapeHtml(text);
  return `<span class="addition" style="text-decoration: underline; color: ${EDITOR_CONSTANTS.TRACK_CHANGES_STYLES.ADDITION_COLOR};">${escapedText}</span>`;
};

/**
 * Formats an AI suggestion showing original and suggested text
 * 
 * @param suggestion - Suggestion object containing original and suggested text
 * @returns HTML-formatted suggestion
 */
export const formatSuggestion = (suggestion: Suggestion): string => {
  if (!suggestion) return '';
  const deletion = formatDeletion(suggestion.originalText);
  const addition = formatAddition(suggestion.suggestedText);
  return `${deletion}${addition}`;
};

/**
 * Highlights search terms within a text string
 * 
 * @param text - Text to search within
 * @param searchTerm - Term to highlight
 * @returns HTML with highlighted search terms
 */
export const highlightSearchTerms = (text: string, searchTerm: string): string => {
  if (!text || !searchTerm) return text || '';
  
  const escapedText = escapeHtml(text);
  const regex = new RegExp(escapeRegExp(searchTerm), 'gi');
  
  return escapedText.replace(regex, match => 
    `<mark class="highlight" style="background-color: ${EDITOR_CONSTANTS.TRACK_CHANGES_STYLES.HIGHLIGHT_COLOR};">${match}</mark>`
  );
};

/**
 * Helper function to escape HTML special characters
 * 
 * @param text - Text to escape
 * @returns HTML-escaped text
 */
const escapeHtml = (text: string): string => {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
};

/**
 * Helper function to escape special characters in a string for use in a regular expression
 * 
 * @param string - String to escape
 * @returns Escaped string safe for regex
 */
const escapeRegExp = (string: string): string => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
};