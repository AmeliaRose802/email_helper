// Email detail page for viewing individual emails
import React, { useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useGetEmailByIdQuery, useMarkEmailReadMutation, useDeleteEmailMutation } from '@/services/emailApi';
import { CategoryBadge } from '@/components/Email/CategoryBadge';
import { formatEmailDate, getPriorityIcon } from '@/utils/emailUtils';

const EmailDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [markAsRead] = useMarkEmailReadMutation();
  const [deleteEmail] = useDeleteEmailMutation();
  
  const {
    data: email,
    isLoading,
    error,
  } = useGetEmailByIdQuery(id!, {
    skip: !id,
  });
  
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
          
          .email-content p {
            margin-bottom: 16px;
          }
          
          .email-content a {
            color: #007acc;
            text-decoration: underline;
          }
          
          .email-content blockquote {
            border-left: 4px solid #e0e0e0;
            padding-left: 16px;
            margin: 16px 0;
            color: #6c757d;
            font-style: italic;
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
        
        <div style={metaRowStyle}>
          <div style={senderStyle}>From: {email.sender}</div>
          <div style={recipientStyle}>To: {email.recipient}</div>
          <div>{formatEmailDate(email.date)}</div>
        </div>
        
        <div style={metaRowStyle}>
          <div>Date: {new Date(email.date).toLocaleString()}</div>
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
          
          {/* Priority indicator */}
          {email.importance !== 'Normal' && (
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
      </div>
      
      {/* Email content */}
      <div style={contentStyle} className="email-content">
        {email.html_body ? (
          <div 
            dangerouslySetInnerHTML={{ __html: email.html_body }}
          />
        ) : (
          <div style={{ whiteSpace: 'pre-wrap' }}>
            {email.body}
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailDetail;