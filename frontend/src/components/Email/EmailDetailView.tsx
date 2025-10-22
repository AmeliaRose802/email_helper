// Reusable email detail view component - can be used inline or as a page
import React from 'react';
import { 
  useGetEmailByIdQuery
} from '@/services/emailApi';
import { CategoryBadge } from '@/components/Email/CategoryBadge';
import { formatEmailDate, getPriorityIcon } from '@/utils/emailUtils';

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
      <div style={{ 
        padding: '40px', 
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '16px'
      }}>
        <div className="loading-spinner" />
        <div style={{ color: '#666', fontSize: '14px' }}>Loading email...</div>
      </div>
    );
  }

  if (error || !email) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#dc3545' }}>
        <h2>Error Loading Email</h2>
        <p>{error ? 'Failed to load email' : 'Email not found'}</p>
        {onClose && (
          <button onClick={onClose} className="synthwave-button">
            Close
          </button>
        )}
      </div>
    );
  }

  const containerStyle: React.CSSProperties = {
    maxWidth: '100%',
    height: '100%',
    overflowY: 'auto',
    padding: '24px',
    backgroundColor: '#fff',
  };

  return (
    <div style={containerStyle}>
      {/* AI Summary - prominent display at top */}
      {email.one_line_summary && (
        <div style={{
          padding: '20px 24px',
          background: 'linear-gradient(135deg, #e7f3ff 0%, #f0f8ff 100%)',
          borderLeft: '5px solid #007acc',
          marginBottom: '24px',
          borderRadius: '12px',
          fontSize: '15px',
          lineHeight: '1.7',
          boxShadow: '0 4px 12px rgba(0, 122, 204, 0.15)',
        }}>
          <div style={{ 
            color: '#007acc', 
            fontSize: '12px', 
            fontWeight: '700',
            textTransform: 'uppercase', 
            letterSpacing: '1px',
            marginBottom: '10px'
          }}>
            💡 AI Summary
          </div>
          <div style={{ 
            color: '#1a1a1a', 
            fontSize: '16px',
            fontWeight: '500'
          }}>
            {email.one_line_summary}
          </div>
        </div>
      )}

      {/* AI Category Badge */}
      {email.ai_category && (
        <div style={{ marginBottom: '20px' }}>
          <CategoryBadge 
            category={email.ai_category} 
            confidence={email.ai_confidence}
          />
        </div>
      )}

      {/* Email Body - renders HTML content directly */}
      <div
        className="email-detail-content"
        style={{
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          lineHeight: '1.65',
          fontSize: '15px'
        }}
        dangerouslySetInnerHTML={{ __html: prepareEmailHTML(email.body || '') }}
      />
    </div>
  );
};
