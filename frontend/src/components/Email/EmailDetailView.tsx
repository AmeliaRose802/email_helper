// Reusable email detail view component - can be used inline or as a page
import React from 'react';
import { 
  useGetEmailByIdQuery
} from '@/services/emailApi';
import { CategoryBadge } from '@/components/Email/CategoryBadge';
// import { formatEmailDate, getPriorityIcon } from '@/utils/emailUtils';

// Helper function to strip email metadata from HTML body
const stripEmailMetadata = (html: string): string => {
  if (!html) return '';
  
  // Remove the metadata section that Outlook adds (From:/To:/Sent:/Subject: lines)
  // These appear at the start of the HTML body before the actual content
  let cleaned = html;
  
  // Pattern to match the metadata block (From:, Sent:, To:, Subject: lines)
  // This typically appears before the main email content
  const metadataPattern = /(^|<body[^>]*>)([\s\S]*?)(From:|FYI From:|Sent:|To:|Subject:|Cc:)([\s\S]*?)(Hello|Hi|Dear|<p|<div|$)/i;
  
  const match = cleaned.match(metadataPattern);
  if (match && match.index !== undefined) {
    // Find where "Hello", "Hi", "Dear", or actual content starts
    const contentStart = match[0].lastIndexOf(match[5]);
    if (contentStart > 0) {
      const beforeMetadata = match[1] || '';
      const afterMetadata = match[0].substring(contentStart);
      cleaned = beforeMetadata + afterMetadata + cleaned.substring(match.index + match[0].length);
    }
  }
  
  return cleaned;
};

// Helper function to sanitize and prepare HTML email content for display
const prepareEmailHTML = (content: string): string => {
  if (!content) return '';
  
  // Check if content is HTML
  const isHTML = /<[a-z][\s\S]*>/i.test(content);
  
  if (isHTML) {
    // For HTML emails, strip metadata headers and return clean content
    return stripEmailMetadata(content);
  } else {
    // For plain text emails, convert to basic HTML
    let formatted = content;
    
    // Convert URLs to links
    const urlRegex = /(https?:\/\/[^\s<]+[^<.,:;"')\]\s])/g;
    formatted = formatted.replace(urlRegex, (url) => {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
    });
    
    // Convert line breaks to <br> tags
    formatted = formatted.replace(/\n/g, '<br>');
    formatted = formatted.replace(/(<br>){2,}/g, '</p><p>');
    formatted = `<p>${formatted}</p>`;
    
    return formatted;
  }
};

interface EmailDetailViewProps {
  emailId: string;
  onClose?: () => void;
}

export const EmailDetailView: React.FC<EmailDetailViewProps> = ({ 
  emailId, 
  onClose
}) => {
  const { data: email, isLoading, error } = useGetEmailByIdQuery(emailId);

  if (isLoading) {
    return (
      <div className="email-detail-loading">
        <div className="loading-spinner" />
        <div>Loading email...</div>
      </div>
    );
  }

  if (error || !email) {
    return (
      <div className="email-detail-error">
        <h2 className="email-detail-error__title">Error Loading Email</h2>
        <p className="email-detail-error__message">{error ? 'Failed to load email' : 'Email not found'}</p>
        {onClose && (
          <button onClick={onClose} className="synthwave-button">
            Close
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="email-detail-container">
      {/* AI Summary - prominent display at top */}
      {email.one_line_summary && (
        <div className="email-detail-ai-summary">
          <div className="email-detail-ai-summary__label">
            <span className="email-detail-ai-summary__icon">💡</span> AI Summary
          </div>
          <div className="email-detail-ai-summary__text">
            {email.one_line_summary}
          </div>
        </div>
      )}

      {/* AI Category Badge */}
      {email.ai_category && (
        <div className="email-detail-category-wrapper">
          <CategoryBadge 
            category={email.ai_category} 
            confidence={email.ai_confidence}
          />
        </div>
      )}

      {/* Email Body - renders HTML content directly */}
      {/* Use standardized field name with backward compatibility */}
      <div
        className="email-detail-content"
        dangerouslySetInnerHTML={{ __html: prepareEmailHTML(email.content || email.body || '') }}
      />
    </div>
  );
};
