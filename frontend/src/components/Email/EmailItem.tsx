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
  

  
  return (
    <div
      className={`synthwave-email-item email-item__container ${!email.is_read ? 'unread' : ''} ${isSelected ? 'selected' : ''} ${className}`}
      onClick={handleClick}
    >
      {/* Selection checkbox */}
      <input
        type="checkbox"
        checked={isSelected}
        onChange={() => {}}
        onClick={handleCheckboxClick}
        title="Select email"
        className="email-item__checkbox"
      />
      
      {/* Email content */}
      <div className="email-item-content">
        {/* Header with sender and timestamp */}
        <div className="email-item-header">
          <div className="email-item-sender">
            {email.sender || 'Unknown Sender'}
          </div>
          <div className="email-item-timestamp">
            {formatEmailDate(email.date)}
          </div>
        </div>
        
        {/* Subject */}
        <div className="email-item-subject">
          {email.subject || '(No Subject)'}
        </div>
        
        {/* One-line AI Summary (prioritize over body preview) */}
        {email.one_line_summary ? (
          <div className="email-item-ai-summary">
            💡 {email.one_line_summary}
          </div>
        ) : (
          /* Fallback to body preview if no AI summary */
          <div className="email-item-preview">
            {email.body ? getEmailPreview(email.body, 120) : '(No content)'}
          </div>
        )}
        
        {/* Metadata and indicators */}
        <div className="email-item-metadata">
          {/* Holistic Classification Info */}
          {email.holistic_classification && (
            <>
              {email.holistic_classification.priority && (
                <span 
                  className={`email-priority-badge ${email.holistic_classification.priority}`}
                  title={`Priority: ${email.holistic_classification.priority}`}
                >
                  {email.holistic_classification.priority.toUpperCase()}
                </span>
              )}
              {email.holistic_classification.deadline && (
                <span className="email-item__flag--deadline" title="Deadline">
                  ⏰ {email.holistic_classification.deadline}
                </span>
              )}
              {email.holistic_classification.blocking_others && (
                <span className="email-item__flag--blocking" title="Blocking other tasks">
                  🚫 BLOCKING
                </span>
              )}
              {email.holistic_classification.is_superseded && (
                <span className="email-item__flag--superseded" title="Superseded by newer email">
                  Superseded
                </span>
              )}
              {email.holistic_classification.is_duplicate && (
                <span className="email-item__flag--duplicate" title="Duplicate email">
                  📋 Duplicate
                </span>
              )}
            </>
          )}
          
          {/* Classification status indicator */}
          {email.classification_status === 'pending' && (
            <span className="email-status-indicator pending" title="Waiting for AI classification">
              ⏳ Pending...
            </span>
          )}
          {email.classification_status === 'classifying' && (
            <span className="email-status-indicator classifying" title="AI is classifying this email">
              ⟳ Classifying...
            </span>
          )}
          {email.classification_status === 'error' && (
            <span className="email-status-indicator error" title="Classification failed">
              ⚠️ Classification failed
            </span>
          )}
          
          {/* Priority indicator */}
          {email.importance && email.importance !== 'Normal' && (
            <span title={`${email.importance} priority`} className="email-item__icon--priority">
              {getPriorityIcon(typeof email.importance === 'string' ? email.importance.toLowerCase() : 'normal')}
            </span>
          )}
          
          {/* Attachments indicator */}
          {email.has_attachments && (
            <span title="Has attachments" className="email-item__icon--attachment">
              📎
            </span>
          )}
          
          {/* Conversation indicator */}
          {email.conversation_id && (
            <span title="Part of conversation" className="email-item__icon--conversation">
              💬
            </span>
          )}
          
          {/* Quick classification dropdown */}
          {isLoadingMappings ? (
            <span className="email-item__date">
              Loading...
            </span>
          ) : (
            <div className="email-item__actions">
              {/* Classification dropdown with visual styling */}
              <div className="email-item__tasks-container">
                <select
                  value={localCategory}
                  onChange={handleCategoryChange}
                  onClick={(e) => e.stopPropagation()}
                  disabled={isUpdating}
                  className={`email-classification-dropdown ${localCategory ? 'classified' : ''}`}
                  title={email.ai_confidence ? `Classification confidence: ${Math.round(email.ai_confidence * 100)}%` : "Change classification"}
                >
                  <option value="">-- Classify --</option>
                  {mappings.map((mapping) => (
                    <option key={mapping.category} value={mapping.category}>
                      {mapping.category.replace(/_/g, ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
                {/* Confidence indicator */}
                {email.ai_confidence && localCategory && (
                  <span 
                    className={`email-confidence-indicator ${
                      email.ai_confidence >= 0.8 ? 'high' : 
                      email.ai_confidence >= 0.6 ? 'medium' : 'low'
                    }`}
                    title={`Confidence: ${Math.round(email.ai_confidence * 100)}%`}
                  >
                    {Math.round(email.ai_confidence * 100)}%
                  </span>
                )}
              </div>
              
              <label 
                className="email-item__apply-label"
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
                  className="mr-4"
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