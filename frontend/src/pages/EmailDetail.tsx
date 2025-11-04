// Email detail page for viewing individual emails
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  useGetEmailByIdQuery, 
  useMarkEmailReadMutation,
  useGetCategoryMappingsQuery,
  useUpdateEmailClassificationMutation
} from '@/services/emailApi';
import { CategoryBadge } from '@/components/Email/CategoryBadge';
import { getPriorityIcon } from '@/utils/emailUtils';

// Helper function to convert URLs in text to clickable links
const linkifyText = (text: string): string => {
  // Regular expression to match URLs
  const urlRegex = /(https?:\/\/[^\s<]+[^<.,:;"')\]\s])/g;
  
  return text.replace(urlRegex, (url) => {
    // Clean up common URL encoding issues
    const cleanUrl = url
      .replace(/%3A/g, ':')
      .replace(/%2F/g, '/')
      .replace(/%3F/g, '?')
      .replace(/%3D/g, '=')
      .replace(/%26/g, '&')
      .replace(/%23/g, '#');
    
    return `<a href="${cleanUrl}" target="_blank" rel="noopener noreferrer">${cleanUrl}</a>`;
  });
};

// Helper function to format plain text email with basic HTML
const formatPlainTextEmail = (text: string): string => {
  if (!text) return '';
  
  // Convert URLs to links
  let formatted = linkifyText(text);
  
  // Convert line breaks to <br> tags
  formatted = formatted.replace(/\n/g, '<br>');
  
  // Convert double line breaks to paragraphs
  formatted = formatted.replace(/(<br>){2,}/g, '</p><p>');
  
  // Wrap in paragraph tags
  formatted = `<p>${formatted}</p>`;
  
  return formatted;
};

const EmailDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [markAsRead] = useMarkEmailReadMutation();
  const [updateClassification, { isLoading: updateClassificationLoading }] = useUpdateEmailClassificationMutation();
  const [showClassificationMenu, setShowClassificationMenu] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [applyToOutlook, setApplyToOutlook] = useState(true);
  
  const {
    data: email,
    isLoading,
    error,
  } = useGetEmailByIdQuery(id!, {
    skip: !id,
  });
  
  const { 
    data: categoryMappings,
    isLoading: categoryMappingsLoading,
    error: categoryMappingsError
  } = useGetCategoryMappingsQuery();
  
  // Mark as read when viewing
  useEffect(() => {
    if (email && !email.is_read) {
      markAsRead({ id: email.id, read: true }).catch(console.error);
    }
  }, [email, markAsRead]);
  
  const handleUpdateClassification = async (newCategory: string) => {
    if (!email) return;
    
    try {
      const result = await updateClassification({
        emailId: email.id,
        category: newCategory,
        applyToOutlook,
      }).unwrap();
      
      alert(result.message);
      setShowClassificationMenu(false);
      setSelectedCategory('');
      setApplyToOutlook(true);
      
      // RTK Query will automatically update the cache and re-render
      // No need to reload the page
    } catch (error) {
      console.error('Failed to update classification:', error);
      alert('Failed to update classification');
    }
  };
  
  // All styles moved to unified.css
  
  // Loading state
  if (isLoading) {
    return (
      <div className="email-detail-container">
        <div className="email-detail-loading">
          <div>Loading email...</div>
        </div>
      </div>
    );
  }
  
  // Error state
  if (error || !email) {
    return (
      <div className="email-detail-container">
        <div className="email-detail-error">
          <div className="email-detail-error__icon">⚠️</div>
          <div className="email-detail-error__title">Email not found</div>
          <div className="email-detail-error__message">The email you're looking for doesn't exist or has been deleted.</div>
          <Link to="/emails" className="email-detail-back-button">
            ← Back to Inbox
          </Link>
        </div>
      </div>
    );
  }
  
  return (
    <div className="email-detail-container">
      {/* Header with navigation only */}
      <div className="email-detail-header">
        <Link 
          to="/emails" 
          className="email-detail-back-button"
        >
          ← Back to Inbox
        </Link>
      </div>
      
      {/* Email header */}
      <div className="email-detail-email-header">
        <h1 className="email-detail-subject">{email.subject}</h1>
        
        {/* AI Summary - Prominently displayed */}
        {email.one_line_summary && (
          <div className="email-detail-ai-summary">
            <div className="email-detail-ai-summary__label">
              <span className="email-detail-ai-summary__icon">💡</span>
              AI Summary
            </div>
            <div className="email-detail-ai-summary__text">
              {email.one_line_summary}
            </div>
          </div>
        )}
        
        <div className="email-detail-meta-row">
          <div className="email-detail-sender">
            <strong>From:</strong> {email.sender || 'N/A'}
          </div>
        </div>
        
        <div className="email-detail-meta-row">
          <div className="email-detail-recipient">
            <strong>To:</strong> {email.recipient || 'N/A'}
          </div>
        </div>
        
        <div className="email-detail-meta-row">
          <div>
            {/* Use standardized field name with backward compatibility */}
            <strong>Date:</strong> {email.received_time || email.date
              ? new Date(email.received_time || email.date || '').toLocaleString('en-US', { 
                  weekday: 'short', 
                  year: 'numeric', 
                  month: 'short', 
                  day: 'numeric', 
                  hour: 'numeric', 
                  minute: '2-digit' 
                })
                : 'N/A'}
          </div>
          {email.folder_name && (
            <div><strong>Folder:</strong> {email.folder_name}</div>
          )}
        </div>
        
        {/* Badges and indicators */}
        <div className="email-detail-badges">
          {/* AI Categories */}
          {email.categories && email.categories.map((category, index) => (
            <CategoryBadge 
              key={index}
              category={category} 
              size="medium"
            />
          ))}
          
          {/* Classification modification button */}
          <button
            onClick={() => setShowClassificationMenu(!showClassificationMenu)}
            className="email-detail-change-classification-btn"
          >
            Change Classification
          </button>
        </div>
        
        {/* Classification modification menu */}
        {showClassificationMenu && (
          <div className="email-detail-classification-menu">
            <h3 className="email-detail-classification-menu__title">
              Change Email Classification
            </h3>
            
            {categoryMappingsLoading ? (
              <div>Loading categories...</div>
            ) : categoryMappingsError ? (
              <div className="email-detail-classification-menu__error">Error loading categories</div>
            ) : (
              <>
                <div className="email-detail-classification-menu__field">
                  <label className="email-detail-classification-menu__label">
                    Select Category:
                  </label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="email-detail-classification-menu__select"
                  >
                    <option value="">-- Select a category --</option>
                    {categoryMappings?.map((mapping) => (
                      <option key={mapping.category} value={mapping.category}>
                        {mapping.category.replace(/_/g, ' ').toUpperCase()}
                        {mapping.folder_name ? ` → ${mapping.folder_name}` : ' (stays in inbox)'}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="email-detail-classification-menu__field">
                  <label className="email-detail-classification-menu__label--checkbox">
                    <input
                      type="checkbox"
                      checked={applyToOutlook}
                      onChange={(e) => setApplyToOutlook(e.target.checked)}
                      className="email-detail-classification-menu__checkbox"
                    />
                    <span>Apply to Outlook (move email to corresponding folder)</span>
                  </label>
                </div>
                
                <div className="email-detail-classification-menu__actions">
                  <button
                    onClick={() => handleUpdateClassification(selectedCategory)}
                    disabled={!selectedCategory || updateClassificationLoading}
                    className="email-detail-classification-menu__btn email-detail-classification-menu__btn--update"
                  >
                    {updateClassificationLoading ? 'Updating...' : 'Update Classification'}
                  </button>
                  
                  <button
                    onClick={() => {
                      setShowClassificationMenu(false);
                      setSelectedCategory('');
                      setApplyToOutlook(false);
                    }}
                    className="email-detail-classification-menu__btn email-detail-classification-menu__btn--cancel"
                  >
                    Cancel
                  </button>
                </div>
              </>
            )}
          </div>
        )}
        
        {/* Priority indicator */}
        {email.importance && email.importance !== 'Normal' && (
          <span className={`email-detail-badge ${email.importance === 'High' ? 'email-detail-badge--high-priority' : 'email-detail-badge--low-priority'}`}>
            {getPriorityIcon(email.importance.toLowerCase())} {email.importance} Priority
          </span>
        )}
        
        {/* Attachments indicator */}
        {email.has_attachments && (
          <span className="email-detail-badge email-detail-badge--attachments">
            📎 Has Attachments
          </span>
        )}
        
        {/* Read status */}
        {!email.is_read && (
          <span className="email-detail-badge email-detail-badge--unread">
            Unread
          </span>
        )}
      </div>
      
      {/* Email content */}
      <div className="email-detail-content">
        {email.html_body ? (
          <div 
            dangerouslySetInnerHTML={{ __html: email.html_body }}
          />
        ) : (email.content || email.body) ? (
          <div 
            dangerouslySetInnerHTML={{ __html: formatPlainTextEmail(email.content || email.body || '') }}
          />
        ) : (
          <div className="email-detail-no-content">
            No email content available
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailDetail;