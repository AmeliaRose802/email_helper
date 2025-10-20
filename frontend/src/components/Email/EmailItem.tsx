// Individual email item component with AI categorization
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMarkEmailReadMutation, useGetCategoryMappingsQuery, useUpdateEmailClassificationMutation } from '@/services/emailApi';
import { formatEmailDate, getEmailPreview, getPriorityIcon } from '@/utils/emailUtils';
import type { Email } from '@/types/email';

interface EmailItemProps {
  email: Email;
  isSelected: boolean;
  onSelect: () => void;
  onEmailClick?: (emailId: string) => void; // Optional callback for custom click handling
  className?: string;
}

export const EmailItem: React.FC<EmailItemProps> = ({
  email,
  isSelected,
  onSelect,
  onEmailClick,
  className = '',
}) => {
  const navigate = useNavigate();
  const [markAsRead] = useMarkEmailReadMutation();
  const [updateClassification, { isLoading: isUpdating }] = useUpdateEmailClassificationMutation();
  const { data: categoryMappings, isLoading: isLoadingMappings } = useGetCategoryMappingsQuery();
  
  const [applyToOutlook, setApplyToOutlook] = useState(true);
  const [localCategory, setLocalCategory] = useState(email.ai_category || '');
  
  // Sync local category with email prop when it changes
  React.useEffect(() => {
    setLocalCategory(email.ai_category || '');
  }, [email.ai_category]);
  
  // Ensure categoryMappings is an array
  const mappings = Array.isArray(categoryMappings) ? categoryMappings : [];
  
  // Get color for category
  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      'required_personal_action': '#dc3545',  // Red
      'team_action': '#fd7e14',               // Orange
      'optional_action': '#ffc107',           // Yellow
      'job_listing': '#6f42c1',               // Purple
      'optional_event': '#20c997',            // Teal
      'work_relevant': '#0dcaf0',             // Cyan
      'fyi': '#6c757d',                       // Gray
      'newsletter': '#0d6efd',                // Blue
      'spam_to_delete': '#212529',            // Dark
    };
    return colors[category] || '#007acc';
  };
  
  const handleClick = async () => {
    // Mark as read if unread
    if (!email.is_read) {
      try {
        await markAsRead({ id: email.id, read: true });
      } catch (error) {
        console.error('Failed to mark email as read:', error);
      }
    }
    
    // Use custom click handler if provided, otherwise navigate
    if (onEmailClick) {
      onEmailClick(email.id);
    } else {
      navigate(`/emails/${email.id}`);
    }
  };
  
  const handleCheckboxClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect();
  };
  
  const handleCategoryChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    e.stopPropagation();
    const category = e.target.value;
    
    if (!category) return;
    
    // Update local state immediately for responsive UI
    setLocalCategory(category);
    
    try {
      await updateClassification({
        emailId: email.id,
        category,
        applyToOutlook,
      }).unwrap();
      
      // RTK Query will automatically invalidate cache and update UI
      // No need to manually trigger refresh
    } catch (error) {
      console.error('Failed to update classification:', error);
      alert('Failed to update classification. Please try again.');
      // Revert local state on error
      setLocalCategory(email.ai_category || '');
    }
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
    fontSize: '11px',
    fontWeight: email.is_read ? '400' : '500',
    color: '#8A8886',
    minWidth: '100px',
    maxWidth: '150px',
    flexShrink: 0,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
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
            {email.sender || 'Unknown Sender'}
          </div>
          <div style={timestampStyle}>
            {formatEmailDate(email.date)}
          </div>
        </div>
        
        {/* Subject */}
        <div className="subject" style={subjectStyle}>
          {email.subject || '(No Subject)'}
        </div>
        
        {/* One-line AI Summary (prioritize over body preview) */}
        {email.one_line_summary ? (
          <div style={{ ...previewStyle, fontWeight: '500', color: '#007acc', fontStyle: 'italic' }}>
            💡 {email.one_line_summary}
          </div>
        ) : (
          /* Fallback to body preview if no AI summary */
          <div style={previewStyle}>
            {email.body ? getEmailPreview(email.body, 120) : '(No content)'}
          </div>
        )}
        
        {/* Metadata and indicators */}
        <div style={metaStyle}>
          {/* Holistic Classification Info */}
          {email.holistic_classification && (
            <>
              {email.holistic_classification.priority && (
                <span 
                  style={{ 
                    fontSize: '11px', 
                    padding: '2px 6px', 
                    borderRadius: '3px',
                    backgroundColor: email.holistic_classification.priority === 'high' ? '#dc3545' : 
                                     email.holistic_classification.priority === 'medium' ? '#ffc107' : '#28a745',
                    color: '#fff',
                    fontWeight: '600'
                  }}
                  title={`Priority: ${email.holistic_classification.priority}`}
                >
                  {email.holistic_classification.priority.toUpperCase()}
                </span>
              )}
              {email.holistic_classification.deadline && (
                <span style={{ fontSize: '11px', color: '#dc3545' }} title="Deadline">
                  ⏰ {email.holistic_classification.deadline}
                </span>
              )}
              {email.holistic_classification.blocking_others && (
                <span style={{ fontSize: '11px', color: '#dc3545' }} title="Blocking other tasks">
                  🚫 BLOCKING
                </span>
              )}
              {email.holistic_classification.is_superseded && (
                <span style={{ fontSize: '11px', color: '#6c757d', textDecoration: 'line-through' }} title="Superseded by newer email">
                  Superseded
                </span>
              )}
              {email.holistic_classification.is_duplicate && (
                <span style={{ fontSize: '11px', color: '#6c757d' }} title="Duplicate email">
                  📋 Duplicate
                </span>
              )}
            </>
          )}
          
          {/* Classification status indicator */}
          {email.classification_status === 'pending' && (
            <span style={{ fontSize: '12px', color: '#6c757d' }} title="Waiting for AI classification">
              ⏳ Pending...
            </span>
          )}
          {email.classification_status === 'classifying' && (
            <span style={{ fontSize: '12px', color: '#007acc' }} title="AI is classifying this email">
              ⟳ Classifying...
            </span>
          )}
          {email.classification_status === 'error' && (
            <span style={{ fontSize: '12px', color: '#dc3545' }} title="Classification failed">
              ⚠️ Classification failed
            </span>
          )}
          
          {/* Priority indicator */}
          {email.importance && email.importance !== 'Normal' && (
            <span title={`${email.importance} priority`} style={{ fontSize: '12px' }}>
              {getPriorityIcon(typeof email.importance === 'string' ? email.importance.toLowerCase() : 'normal')}
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
          
          {/* Quick classification dropdown */}
          {isLoadingMappings ? (
            <span style={{ fontSize: '11px', color: '#6c757d', marginLeft: 'auto' }}>
              Loading...
            </span>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: 'auto' }}>
              {/* Classification dropdown with visual styling */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <select
                  value={localCategory}
                  onChange={handleCategoryChange}
                  onClick={(e) => e.stopPropagation()}
                  disabled={isUpdating}
                  style={{
                    padding: '4px 8px',
                    fontSize: '11px',
                    backgroundColor: localCategory ? getCategoryColor(localCategory) : (isUpdating ? '#e9ecef' : '#fff'),
                    color: localCategory ? '#fff' : '#333',
                    border: '1px solid #ced4da',
                    borderRadius: '4px',
                    cursor: isUpdating ? 'not-allowed' : 'pointer',
                    minWidth: '140px',
                    fontWeight: localCategory ? '600' : '400',
                  }}
                  title={email.ai_confidence ? `Classification confidence: ${Math.round(email.ai_confidence * 100)}%` : "Change classification"}
                >
                  <option value="" style={{ backgroundColor: '#fff', color: '#333' }}>-- Classify --</option>
                  {mappings.map((mapping) => (
                    <option key={mapping.category} value={mapping.category} style={{ backgroundColor: '#fff', color: '#333' }}>
                      {mapping.category.replace(/_/g, ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
                {/* Confidence indicator */}
                {email.ai_confidence && localCategory && (
                  <span 
                    style={{ 
                      fontSize: '10px', 
                      color: email.ai_confidence >= 0.8 ? '#28a745' : email.ai_confidence >= 0.6 ? '#ffc107' : '#dc3545',
                      fontWeight: '600'
                    }}
                    title={`Confidence: ${Math.round(email.ai_confidence * 100)}%`}
                  >
                    {Math.round(email.ai_confidence * 100)}%
                  </span>
                )}
              </div>
              
              <label 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  fontSize: '11px', 
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                }} 
                title="Apply changes to Outlook folders"
                onClick={(e) => e.stopPropagation()}
              >
                <input
                  type="checkbox"
                  checked={applyToOutlook}
                  onChange={(e) => {
                    e.stopPropagation();
                    setApplyToOutlook(e.target.checked);
                  }}
                  onClick={(e) => e.stopPropagation()}
                  style={{ marginRight: '4px' }}
                />
                Apply to Outlook
              </label>
            </div>
          )}
        </div>
        
      </div>
    </div>
  );
};