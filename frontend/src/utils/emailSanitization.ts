/**
 * Email content sanitization utilities
 * 
 * These utilities clean and sanitize email HTML content for safe display,
 * removing problematic elements like embedded CID images that cause CSP violations.
 */

/**
 * Remove CID (Content-ID) image references from HTML content.
 * 
 * CID images are embedded in emails but cannot be loaded in browser context
 * due to Content Security Policy restrictions. This function removes them
 * to prevent console errors and improve performance.
 * 
 * @param html - HTML content to sanitize
 * @returns Sanitized HTML with CID images removed
 */
export function removeCIDImages(html: string): string {
  if (!html) return '';
  
  // Remove <img> tags with cid: sources
  let sanitized = html.replace(/<img[^>]+src=["']cid:[^"']*["'][^>]*>/gi, '');
  
  // Remove any remaining cid: references in various attributes
  sanitized = sanitized.replace(/\s+src=["']cid:[^"']*["']/gi, '');
  sanitized = sanitized.replace(/\s+href=["']cid:[^"']*["']/gi, '');
  sanitized = sanitized.replace(/\s+background=["']cid:[^"']*["']/gi, '');
  
  // Clean up empty image tags that might be left behind
  sanitized = sanitized.replace(/<img[^>]*src=["']["'][^>]*>/gi, '');
  
  return sanitized;
}

/**
 * Sanitize email HTML for safe display.
 * 
 * Performs multiple sanitization steps:
 * - Removes CID images
 * - Optionally removes external images
 * - Removes dangerous scripts and event handlers
 * 
 * @param html - HTML content to sanitize
 * @param options - Sanitization options
 * @returns Sanitized HTML safe for display
 */
export function sanitizeEmailHTML(
  html: string,
  options: {
    removeExternalImages?: boolean;
    removeScripts?: boolean;
  } = {}
): string {
  if (!html) return '';
  
  let sanitized = html;
  
  // Always remove CID images
  sanitized = removeCIDImages(sanitized);
  
  // Optionally remove external images (http/https)
  if (options.removeExternalImages) {
    sanitized = sanitized.replace(/<img[^>]+src=["']https?:[^"']*["'][^>]*>/gi, '[Image removed]');
  }
  
  // Always remove scripts and event handlers for security
  if (options.removeScripts !== false) {
    // Remove script tags
    sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    
    // Remove event handler attributes
    sanitized = sanitized.replace(/\s+on\w+\s*=\s*["'][^"']*["']/gi, '');
    sanitized = sanitized.replace(/\s+on\w+\s*=\s*[^\s>]*/gi, '');
  }
  
  return sanitized;
}

/**
 * Format plain text email content as HTML.
 * 
 * Converts plain text to HTML with basic formatting:
 * - Preserves line breaks
 * - Converts URLs to clickable links
 * - Escapes HTML entities
 * 
 * @param text - Plain text content
 * @returns HTML formatted text
 */
export function formatPlainTextEmail(text: string): string {
  if (!text) return '';
  
  // Escape HTML entities
  let formatted = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
  
  // Convert URLs to links
  const urlRegex = /(https?:\/\/[^\s<]+[^<.,:;"')\]\s])/g;
  formatted = formatted.replace(urlRegex, (url) => {
    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
  });
  
  // Convert line breaks to <br> tags
  formatted = formatted.replace(/\n/g, '<br>');
  
  return formatted;
}

/**
 * Strip email metadata headers from HTML content.
 * 
 * Outlook and other email clients often include metadata headers
 * (From, To, Sent, Subject) in the HTML body. This removes them.
 * 
 * @param html - HTML content with metadata
 * @returns HTML with metadata removed
 */
export function stripEmailMetadata(html: string): string {
  if (!html) return '';
  
  let cleaned = html;
  
  // Pattern to match the metadata block (From:, Sent:, To:, Subject: lines)
  const metadataPattern = /(^|<body[^>]*>)([\s\S]*?)(From:|FYI From:|Sent:|To:|Subject:|Cc:)([\s\S]*?)(Hello|Hi|Dear|<p|<div|$)/i;
  
  const match = cleaned.match(metadataPattern);
  if (match && match.index !== undefined) {
    // Find where actual content starts
    const contentStart = match[0].lastIndexOf(match[5]);
    if (contentStart > 0) {
      const beforeMetadata = match[1] || '';
      const afterMetadata = match[0].substring(contentStart);
      cleaned = beforeMetadata + afterMetadata + cleaned.substring(match.index + match[0].length);
    }
  }
  
  return cleaned;
}
