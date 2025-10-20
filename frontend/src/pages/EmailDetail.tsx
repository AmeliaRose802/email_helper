// Email detail page for viewing individual emails
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
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
  const navigate = useNavigate();
  const [markAsRead] = useMarkEmailReadMutation();
  const [deleteEmail] = useDeleteEmailMutation();
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
  
  const handleDelete = async () => {
    if (!email) return;
    
    if (window.confirm('Are you sure you want to delete this email?')) {
      try {
        await deleteEmail(email.id).unwrap();
        navigate('/emails');
      } catch (error) {
        console.error('Failed to delete email:', error);
      }
    }
  };
  
  const handleMarkAsUnread = async () => {
    if (!email) return;
    
    try {
      await markAsRead({ id: email.id, read: false }).unwrap();
    } catch (error) {
      console.error('Failed to mark as unread:', error);
    }
  };

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
  
  // Styles
  const containerStyle = {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '24px',
    backgroundColor: '#fff',
    minHeight: '100vh',
  };
  
  const headerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '24px',
    paddingBottom: '16px',
    borderBottom: '1px solid #e0e0e0',
  };
  
  const backButtonStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    backgroundColor: '#f8f9fa',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    textDecoration: 'none',
    color: '#333',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'all 0.2s ease',
  };
  
  const actionsStyle = {
    display: 'flex',
    gap: '8px',
  };
  
  const actionButtonStyle = (variant: 'primary' | 'secondary' | 'danger' = 'secondary') => {
    const colors = {
      primary: { bg: '#007acc', color: '#fff' },
      secondary: { bg: '#6c757d', color: '#fff' },
      danger: { bg: '#dc3545', color: '#fff' },
    };
    
    return {
      padding: '8px 16px',
      border: 'none',
      borderRadius: '4px',
      fontSize: '14px',
      fontWeight: '500',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      backgroundColor: colors[variant].bg,
      color: colors[variant].color,
    };
  };
  
  const emailHeaderStyle = {
    marginBottom: '24px',
  };
  
  const subjectStyle = {
    fontSize: '28px',
    fontWeight: '700',
    color: '#333',
    marginBottom: '16px',
    lineHeight: '1.3',
  };
  
  const metaRowStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    marginBottom: '8px',
    fontSize: '14px',
    color: '#6c757d',
  };
  
  const senderStyle = {
    fontSize: '16px',
    fontWeight: '600',
    color: '#333',
  };
  
  const recipientStyle = {
    fontSize: '14px',
    color: '#6c757d',
  };
  
  const contentStyle = {
    lineHeight: '1.6',
    fontSize: '16px',
    color: '#333',
    backgroundColor: '#f8f9fa',
    padding: '24px',
    borderRadius: '8px',
    border: '1px solid #e0e0e0',
    marginTop: '24px',
  };
  
  const badgeContainerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginTop: '16px',
    flexWrap: 'wrap' as const,
  };
  
  const loadingStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '50vh',
    fontSize: '18px',
    color: '#6c757d',
  };
  
  const errorStyle = {
    display: 'flex',
    flexDirection: 'column' as const,
    justifyContent: 'center',
    alignItems: 'center',
    height: '50vh',
    color: '#dc3545',
    textAlign: 'center' as const,
  };
  
  // Loading state
  if (isLoading) {
    return (
      <div style={containerStyle}>
        <div style={loadingStyle}>
          <div>Loading email...</div>
        </div>
      </div>
    );
  }
  
  // Error state
  if (error || !email) {
    return (
      <div style={containerStyle}>
        <div style={errorStyle}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
          <div style={{ fontSize: '20px', marginBottom: '8px' }}>Email not found</div>
          <div style={{ marginBottom: '24px' }}>The email you're looking for doesn't exist or has been deleted.</div>
          <Link to="/emails" style={backButtonStyle}>
            ← Back to Inbox
          </Link>
        </div>
      </div>
    );
  }
  
  return (
    <div style={containerStyle}>
      <style>
        {`
          .back-button:hover {
            background-color: #e9ecef !important;
            transform: translateY(-1px);
          }
          
          .action-button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          }
          
          .email-content {
            line-height: 1.6;
            color: #333;
          }
          
          .email-content p {
            margin-bottom: 16px;
            margin-top: 0;
          }
          
          .email-content a {
            color: #007acc;
            text-decoration: none;
            word-break: break-all;
          }
          
          .email-content a:hover {
            text-decoration: underline;
          }
          
          .email-content blockquote {
            border-left: 4px solid #e0e0e0;
            padding-left: 16px;
            margin: 16px 0;
            color: #6c757d;
            font-style: italic;
          }
          
          .email-content img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            margin: 8px 0;
          }
          
          .email-content pre {
            background-color: #f8f9fa;
            padding: 12px;
            border-radius: 4px;
            overflow-x: auto;
            border: 1px solid #e0e0e0;
          }
          
          .email-content code {
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
          }
          
          .email-content table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
          }
          
          .email-content table td,
          .email-content table th {
            border: 1px solid #e0e0e0;
            padding: 8px;
            text-align: left;
          }
          
          .email-content table th {
            background-color: #f8f9fa;
            font-weight: 600;
          }
          
          .email-content ul,
          .email-content ol {
            margin: 12px 0;
            padding-left: 24px;
          }
          
          .email-content li {
            margin-bottom: 8px;
          }
        `}
      </style>
      
      {/* Header with navigation and actions */}
      <div style={headerStyle}>
        <Link 
          to="/emails" 
          className="back-button" 
          style={backButtonStyle}
        >
          ← Back to Inbox
        </Link>
        
        <div style={actionsStyle}>
          <button
            className="action-button"
            onClick={handleMarkAsUnread}
            style={actionButtonStyle('secondary')}
            title="Mark as unread"
          >
            Mark as Unread
          </button>
          
          <button
            className="action-button"
            onClick={handleDelete}
            style={actionButtonStyle('danger')}
            title="Delete email"
          >
            Delete
          </button>
        </div>
      </div>
      
      {/* Email header */}
      <div style={emailHeaderStyle}>
        <h1 style={subjectStyle}>{email.subject}</h1>
        
        {/* AI Summary - Prominently displayed */}
        {email.one_line_summary && (
          <div style={{
            backgroundColor: '#e7f3ff',
            border: '2px solid #007acc',
            borderRadius: '8px',
            padding: '16px',
            marginTop: '16px',
            marginBottom: '16px',
          }}>
            <div style={{
              fontSize: '13px',
              fontWeight: '600',
              color: '#0066cc',
              marginBottom: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <span style={{ fontSize: '16px' }}>💡</span>
              AI Summary
            </div>
            <div style={{
              fontSize: '15px',
              color: '#333',
              lineHeight: '1.5'
            }}>
              {email.one_line_summary}
            </div>
          </div>
        )}
        
        <div style={metaRowStyle}>
          <div style={senderStyle}>From: {email.sender || 'Unknown'}</div>
          <div style={recipientStyle}>To: {email.recipient || 'Unknown'}</div>
          <div>{email.date ? formatEmailDate(email.date) : email.received_time ? formatEmailDate(email.received_time) : 'No date'}</div>
        </div>
        
        <div style={metaRowStyle}>
          <div>Date: {email.date ? new Date(email.date).toLocaleString() : email.received_time ? new Date(email.received_time).toLocaleString() : 'Invalid Date'}</div>
          {email.folder_name && (
            <div>Folder: {email.folder_name}</div>
          )}
        </div>
        
        {/* Badges and indicators */}
        <div style={badgeContainerStyle}>
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
            style={{
              padding: '6px 12px',
              backgroundColor: '#4a90e2',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
              marginLeft: '12px'
            }}
          >
            Change Classification
          </button>
        </div>
        
        {/* Classification modification menu */}
        {showClassificationMenu && (
          <div style={{
            marginTop: '16px',
            padding: '16px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #dee2e6'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '12px', fontSize: '16px' }}>
              Change Email Classification
            </h3>
            
            {categoryMappingsLoading ? (
              <div>Loading categories...</div>
            ) : categoryMappingsError ? (
              <div style={{ color: '#dc3545' }}>Error loading categories</div>
            ) : (
              <>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                    Select Category:
                  </label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderRadius: '4px',
                      border: '1px solid #ced4da',
                      fontSize: '14px'
                    }}
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
                
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={applyToOutlook}
                      onChange={(e) => setApplyToOutlook(e.target.checked)}
                      style={{ marginRight: '8px' }}
                    />
                    <span>Apply to Outlook (move email to corresponding folder)</span>
                  </label>
                </div>
                
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => handleUpdateClassification(selectedCategory)}
                    disabled={!selectedCategory || updateClassificationLoading}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: selectedCategory ? '#28a745' : '#6c757d',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: selectedCategory ? 'pointer' : 'not-allowed',
                      fontSize: '14px',
                      opacity: selectedCategory ? 1 : 0.6
                    }}
                  >
                    {updateClassificationLoading ? 'Updating...' : 'Update Classification'}
                  </button>
                  
                  <button
                    onClick={() => {
                      setShowClassificationMenu(false);
                      setSelectedCategory('');
                      setApplyToOutlook(false);
                    }}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#6c757d',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '14px'
                    }}
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
          <span 
            style={{
              padding: '4px 8px',
              backgroundColor: email.importance === 'High' ? '#dc3545' : '#28a745',
              color: 'white',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: '600',
            }}
          >
            {getPriorityIcon(email.importance.toLowerCase())} {email.importance} Priority
          </span>
        )}
        
        {/* Attachments indicator */}
        {email.has_attachments && (
          <span 
            style={{
              padding: '4px 8px',
              backgroundColor: '#17a2b8',
              color: 'white',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: '600',
            }}
          >
            📎 Has Attachments
          </span>
        )}
        
        {/* Read status */}
        {!email.is_read && (
          <span 
            style={{
              padding: '4px 8px',
              backgroundColor: '#007acc',
              color: 'white',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: '600',
            }}
          >
            Unread
          </span>
        )}
      </div>
      
      {/* Email content */}
      <div style={contentStyle} className="email-content">
        {email.html_body ? (
          <div 
            dangerouslySetInnerHTML={{ __html: email.html_body }}
          />
        ) : email.body ? (
          <div 
            dangerouslySetInnerHTML={{ __html: formatPlainTextEmail(email.body) }}
          />
        ) : (
          <div style={{ color: '#6c757d', fontStyle: 'italic', padding: '24px 0' }}>
            No email content available
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailDetail;