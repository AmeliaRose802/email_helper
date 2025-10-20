// Reusable email detail view component - can be used inline or as a page
import React, { useState } from 'react';
import { 
  useGetEmailByIdQuery, 
  useMarkEmailReadMutation, 
  useDeleteEmailMutation,
  useGetCategoryMappingsQuery,
  useUpdateEmailClassificationMutation
} from '@/services/emailApi';
import { CategoryBadge } from '@/components/Email/CategoryBadge';
import { formatEmailDate, getPriorityIcon } from '@/utils/emailUtils';

// Helper function to convert URLs in text to clickable links
const linkifyText = (text: string): string => {
  const urlRegex = /(https?:\/\/[^\s<]+[^<.,:;"')\]\s])/g;
  
  return text.replace(urlRegex, (url) => {
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
  
  let formatted = linkifyText(text);
  formatted = formatted.replace(/\n/g, '<br>');
  formatted = formatted.replace(/(<br>){2,}/g, '</p><p>');
  formatted = `<p>${formatted}</p>`;
  
  return formatted;
};

interface EmailDetailViewProps {
  emailId: string;
  onClose?: () => void;
  showBackButton?: boolean;
}

export const EmailDetailView: React.FC<EmailDetailViewProps> = ({ 
  emailId, 
  onClose,
  showBackButton = false
}) => {
  const [markAsRead] = useMarkEmailReadMutation();
  const [deleteEmail] = useDeleteEmailMutation();
  const [updateClassification, { isLoading: updateClassificationLoading }] = useUpdateEmailClassificationMutation();
  const [showClassificationMenu, setShowClassificationMenu] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [applyToOutlook, setApplyToOutlook] = useState(true);
  
  const { data: email, isLoading, error } = useGetEmailByIdQuery(emailId);
  const { data: categoryMappings } = useGetCategoryMappingsQuery();

  if (isLoading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div className="spinner">Loading email...</div>
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

  const handleUnread = async () => {
    try {
      await markAsRead({ id: email.id, read: false });
      alert('Email marked as unread');
    } catch (error) {
      console.error('Failed to mark as unread:', error);
      alert('Failed to mark as unread');
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this email?')) {
      try {
        await deleteEmail(email.id).unwrap();
        alert('Email deleted successfully');
        onClose?.();
      } catch (error) {
        console.error('Failed to delete email:', error);
        alert('Failed to delete email');
      }
    }
  };

  const handleUpdateClassification = async () => {
    if (!selectedCategory) {
      alert('Please select a category');
      return;
    }

    try {
      const result = await updateClassification({
        emailId: email.id,
        category: selectedCategory,
        applyToOutlook,
      }).unwrap();
      
      alert(result.message);
      setShowClassificationMenu(false);
      setSelectedCategory('');
      setApplyToOutlook(true);
    } catch (error) {
      console.error('Failed to update classification:', error);
      alert('Failed to update classification');
    }
  };

  const containerStyle: React.CSSProperties = {
    maxWidth: '100%',
    height: '100%',
    overflowY: 'auto',
    padding: '24px',
    backgroundColor: '#fff',
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '24px',
    paddingBottom: '16px',
    borderBottom: '1px solid #e0e0e0',
  };

  const actionButtonStyle: React.CSSProperties = {
    padding: '8px 16px',
    margin: '0 4px',
    backgroundColor: '#f0f0f0',
    border: '1px solid #d0d0d0',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  };

  const metadataStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'auto 1fr',
    gap: '12px',
    marginBottom: '24px',
    padding: '16px',
    backgroundColor: '#f8f9fa',
    borderRadius: '8px',
  };

  const labelStyle: React.CSSProperties = {
    fontWeight: '600',
    color: '#495057',
  };

  const valueStyle: React.CSSProperties = {
    color: '#212529',
  };

  const bodyStyle: React.CSSProperties = {
    padding: '24px',
    backgroundColor: '#fff',
    borderRadius: '8px',
    border: '1px solid #e0e0e0',
    lineHeight: '1.6',
  };

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <div style={{ flex: 1 }}>
          {showBackButton && onClose && (
            <button onClick={onClose} style={actionButtonStyle}>
              ← Back to List
            </button>
          )}
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={handleUnread} style={actionButtonStyle}>
            Mark Unread
          </button>
          <button onClick={handleDelete} style={{ ...actionButtonStyle, color: '#dc3545' }}>
            Delete
          </button>
        </div>
      </div>

      {/* Subject */}
      <h1 style={{ fontSize: '24px', marginBottom: '16px', color: '#212529' }}>
        {getPriorityIcon(email.importance)} {email.subject}
      </h1>

      {/* AI Category Badge */}
      {email.ai_category ? (
        <div style={{ marginBottom: '16px' }}>
          <CategoryBadge 
            category={email.ai_category} 
            confidence={email.ai_confidence}
          />
        </div>
      ) : (
        <div style={{ 
          marginBottom: '16px',
          padding: '8px 12px',
          backgroundColor: '#fff3cd',
          border: '1px solid #ffc107',
          borderRadius: '4px',
          color: '#856404',
          fontSize: '14px',
        }}>
          ⏳ Classification pending... AI is analyzing this email
        </div>
      )}

      {/* AI Summary */}
      {email.one_line_summary && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#e7f3ff',
          borderLeft: '4px solid #007acc',
          marginBottom: '16px',
          borderRadius: '4px',
        }}>
          <strong>AI Summary:</strong> {email.one_line_summary}
        </div>
      )}

      {/* Classification Menu */}
      {showClassificationMenu && (
        <div style={{
          padding: '16px',
          backgroundColor: '#f8f9fa',
          border: '1px solid #d0d0d0',
          borderRadius: '8px',
          marginBottom: '16px',
        }}>
          <h3 style={{ marginBottom: '12px', fontSize: '16px' }}>Update Classification</h3>
          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Category:
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #ced4da',
              }}
            >
              <option value="">Select category...</option>
              {categoryMappings?.map((mapping: any) => (
                <option key={mapping.category} value={mapping.category}>
                  {mapping.category.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                checked={applyToOutlook}
                onChange={(e) => setApplyToOutlook(e.target.checked)}
              />
              Apply to Outlook
            </label>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handleUpdateClassification}
              disabled={updateClassificationLoading}
              className="synthwave-button"
            >
              {updateClassificationLoading ? 'Updating...' : 'Update'}
            </button>
            <button
              onClick={() => {
                setShowClassificationMenu(false);
                setSelectedCategory('');
                setApplyToOutlook(true);
              }}
              className="synthwave-button-secondary"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {!showClassificationMenu && (
        <button
          onClick={() => setShowClassificationMenu(true)}
          style={{ ...actionButtonStyle, marginBottom: '16px' }}
        >
          Change Category
        </button>
      )}

      {/* Metadata */}
      <div style={metadataStyle}>
        <span style={labelStyle}>From:</span>
        <span style={valueStyle}>{email.sender}</span>
        
        <span style={labelStyle}>To:</span>
        <span style={valueStyle}>{email.recipient || 'N/A'}</span>
        
        <span style={labelStyle}>Date:</span>
        <span style={valueStyle}>{formatEmailDate(email.date)}</span>
        
        {/* Only show confidence when AI has actually classified this email */}
        {email.ai_confidence && (
          <>
            <span style={labelStyle}>Confidence:</span>
            <span style={valueStyle}>{Math.round(email.ai_confidence * 100)}%</span>
          </>
        )}
      </div>

      {/* Email Body */}
      <div
        style={bodyStyle}
        dangerouslySetInnerHTML={{ __html: formatPlainTextEmail(email.body || '') }}
      />
    </div>
  );
};
