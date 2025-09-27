// Email actions component for bulk operations
import React, { useState } from 'react';
import { useBatchEmailOperationMutation } from '@/services/emailApi';

interface EmailActionsProps {
  selectedEmails: string[];
  onClear: () => void;
  className?: string;
}

export const EmailActions: React.FC<EmailActionsProps> = ({
  selectedEmails,
  onClear,
  className = '',
}) => {
  const [batchOperation] = useBatchEmailOperationMutation();
  const [isProcessing, setIsProcessing] = useState(false);
  
  const handleBatchOperation = async (operation: 'mark_read' | 'mark_unread' | 'delete' | 'move', targetFolder?: string) => {
    if (selectedEmails.length === 0) return;
    
    setIsProcessing(true);
    
    try {
      await batchOperation({
        email_ids: selectedEmails,
        operation,
        target_folder: targetFolder,
      }).unwrap();
      
      onClear(); // Clear selection after successful operation
    } catch (error) {
      console.error('Batch operation failed:', error);
      // TODO: Show user-friendly error message
    } finally {
      setIsProcessing(false);
    }
  };
  
  const handleMarkAsRead = () => handleBatchOperation('mark_read');
  const handleMarkAsUnread = () => handleBatchOperation('mark_unread');
  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete ${selectedEmails.length} email(s)?`)) {
      handleBatchOperation('delete');
    }
  };
  
  const containerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    backgroundColor: '#e3f2fd',
    border: '1px solid #90caf9',
    borderRadius: '8px',
    margin: '16px 0',
  };
  
  const countStyle = {
    fontSize: '14px',
    fontWeight: '600',
    color: '#1976d2',
  };
  
  const buttonBaseStyle = {
    padding: '8px 16px',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    disabled: isProcessing,
  };
  
  const primaryButtonStyle = {
    ...buttonBaseStyle,
    backgroundColor: '#007acc',
    color: 'white',
  };
  
  const secondaryButtonStyle = {
    ...buttonBaseStyle,
    backgroundColor: '#6c757d',
    color: 'white',
  };
  
  const dangerButtonStyle = {
    ...buttonBaseStyle,
    backgroundColor: '#dc3545',
    color: 'white',
  };
  
  const clearButtonStyle = {
    ...buttonBaseStyle,
    backgroundColor: 'transparent',
    color: '#6c757d',
    border: '1px solid #6c757d',
  };
  
  const disabledStyle = {
    opacity: 0.6,
    cursor: 'not-allowed',
  };
  
  if (selectedEmails.length === 0) {
    return null;
  }
  
  return (
    <div className={`email-actions ${className}`} style={containerStyle}>
      <style>
        {`
          .email-actions button:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          }
          
          .primary-action:hover:not(:disabled) {
            background-color: #0056b3 !important;
          }
          
          .secondary-action:hover:not(:disabled) {
            background-color: #5a6268 !important;
          }
          
          .danger-action:hover:not(:disabled) {
            background-color: #c82333 !important;
          }
          
          .clear-action:hover:not(:disabled) {
            background-color: #6c757d !important;
            color: white !important;
          }
        `}
      </style>
      
      <div style={countStyle}>
        {selectedEmails.length} email{selectedEmails.length !== 1 ? 's' : ''} selected
      </div>
      
      <button
        className="primary-action"
        onClick={handleMarkAsRead}
        disabled={isProcessing}
        style={{
          ...primaryButtonStyle,
          ...(isProcessing ? disabledStyle : {}),
        }}
        title="Mark selected emails as read"
      >
        {isProcessing ? '⟳ ' : ''}Mark as Read
      </button>
      
      <button
        className="secondary-action"
        onClick={handleMarkAsUnread}
        disabled={isProcessing}
        style={{
          ...secondaryButtonStyle,
          ...(isProcessing ? disabledStyle : {}),
        }}
        title="Mark selected emails as unread"
      >
        {isProcessing ? '⟳ ' : ''}Mark as Unread
      </button>
      
      <button
        className="danger-action"
        onClick={handleDelete}
        disabled={isProcessing}
        style={{
          ...dangerButtonStyle,
          ...(isProcessing ? disabledStyle : {}),
        }}
        title="Delete selected emails"
      >
        {isProcessing ? '⟳ ' : ''}Delete
      </button>
      
      <div style={{ marginLeft: 'auto' }}>
        <button
          className="clear-action"
          onClick={onClear}
          disabled={isProcessing}
          style={{
            ...clearButtonStyle,
            ...(isProcessing ? disabledStyle : {}),
          }}
          title="Clear selection"
        >
          Clear Selection
        </button>
      </div>
    </div>
  );
};