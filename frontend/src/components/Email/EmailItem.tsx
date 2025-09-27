// Individual email item component with AI categorization
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useMarkEmailReadMutation } from '@/services/emailApi';
import { CategoryBadge } from './CategoryBadge';
import { formatEmailDate, getEmailPreview, getPriorityIcon } from '@/utils/emailUtils';
import type { Email } from '@/types/email';

interface EmailItemProps {
  email: Email;
  isSelected: boolean;
  onSelect: () => void;
  showCategory?: boolean;
  className?: string;
}

export const EmailItem: React.FC<EmailItemProps> = ({
  email,
  isSelected,
  onSelect,
  showCategory = true,
  className = '',
}) => {
  const navigate = useNavigate();
  const [markAsRead] = useMarkEmailReadMutation();
  
  const handleClick = async () => {
    // Mark as read if unread
    if (!email.is_read) {
      try {
        await markAsRead({ id: email.id, read: true });
      } catch (error) {
        console.error('Failed to mark email as read:', error);
      }
    }
    
    // Navigate to email detail
    navigate(`/emails/${email.id}`);
  };
  
  const handleCheckboxClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect();
  };
  
  const containerStyle = {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    padding: '16px',
    backgroundColor: isSelected ? '#e3f2fd' : (email.is_read ? '#fff' : '#f8f9fa'),
    border: `1px solid ${isSelected ? '#2196f3' : '#e0e0e0'}`,
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    marginBottom: '8px',
    position: 'relative' as const,
  };
  
  const checkboxStyle = {
    marginTop: '2px',
    cursor: 'pointer',
  };
  
  const contentStyle = {
    flex: 1,
    minWidth: 0, // Allow text to truncate
  };
  
  const headerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '12px',
    marginBottom: '8px',
  };
  
  const senderStyle = {
    fontSize: '14px',
    fontWeight: email.is_read ? '500' : '700',
    color: '#333',
    minWidth: '120px',
    flexShrink: 0,
  };
  
  const subjectStyle = {
    fontSize: '16px',
    fontWeight: email.is_read ? '500' : '700',
    color: '#333',
    marginBottom: '4px',
    lineHeight: '1.3',
  };
  
  const previewStyle = {
    fontSize: '14px',
    color: '#6c757d',
    lineHeight: '1.4',
    marginBottom: '8px',
  };
  
  const metaStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    flexWrap: 'wrap' as const,
  };
  
  const timestampStyle = {
    fontSize: '12px',
    color: '#6c757d',
    whiteSpace: 'nowrap' as const,
    marginLeft: 'auto',
  };
  
  const indicatorsStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  };
  
  const unreadIndicatorStyle = {
    width: '8px',
    height: '8px',
    backgroundColor: '#007acc',
    borderRadius: '50%',
    position: 'absolute' as const,
    left: '4px',
    top: '20px',
  };
  
  return (
    <div
      className={`email-item ${!email.is_read ? 'unread' : ''} ${className}`}
      style={containerStyle}
      onClick={handleClick}
    >
      <style>
        {`
          .email-item:hover {
            background-color: ${isSelected ? '#e3f2fd' : '#f5f5f5'} !important;
            border-color: #007acc !important;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          }
          
          .email-item .subject {
            transition: color 0.2s ease;
          }
          
          .email-item:hover .subject {
            color: #007acc !important;
          }
        `}
      </style>
      
      {/* Unread indicator */}
      {!email.is_read && <div style={unreadIndicatorStyle} />}
      
      {/* Selection checkbox */}
      <input
        type="checkbox"
        checked={isSelected}
        onChange={() => {}}
        onClick={handleCheckboxClick}
        style={checkboxStyle}
        title="Select email"
      />
      
      {/* Email content */}
      <div style={contentStyle}>
        {/* Header with sender and timestamp */}
        <div style={headerStyle}>
          <div style={senderStyle}>
            {email.sender}
          </div>
          <div style={timestampStyle}>
            {formatEmailDate(email.date)}
          </div>
        </div>
        
        {/* Subject */}
        <div className="subject" style={subjectStyle}>
          {email.subject}
        </div>
        
        {/* Preview */}
        <div style={previewStyle}>
          {getEmailPreview(email.body, 120)}
        </div>
        
        {/* Metadata and indicators */}
        <div style={metaStyle}>
          {/* AI Category Badge */}
          {showCategory && email.categories && email.categories.length > 0 && (
            <CategoryBadge 
              category={email.categories[0]} 
              size="small"
            />
          )}
          
          {/* Priority indicator */}
          {email.importance !== 'Normal' && (
            <span title={`${email.importance} priority`} style={{ fontSize: '12px' }}>
              {getPriorityIcon(email.importance.toLowerCase())}
            </span>
          )}
          
          {/* Attachments indicator */}
          {email.has_attachments && (
            <span title="Has attachments" style={{ fontSize: '12px' }}>
              📎
            </span>
          )}
          
          {/* Additional indicators */}
          <div style={indicatorsStyle}>
            {/* Conversation indicator */}
            {email.conversation_id && (
              <span title="Part of conversation" style={{ fontSize: '10px', color: '#6c757d' }}>
                💬
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};