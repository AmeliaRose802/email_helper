// Email actions component for bulk operations
import React, { useState } from 'react';
import { useBatchEmailOperationMutation, useBulkApplyToOutlookMutation } from '@/services/emailApi';

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
  const [bulkApplyToOutlook] = useBulkApplyToOutlookMutation();
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
  
  const handleApplyToOutlook = async () => {
    if (selectedEmails.length === 0) return;
    
    if (!window.confirm(`Apply AI classifications and move ${selectedEmails.length} email(s) to their respective Outlook folders?`)) {
      return;
    }
    
    setIsProcessing(true);
    
    try {
      const result = await bulkApplyToOutlook({
        emailIds: selectedEmails,
        applyToOutlook: true,
      }).unwrap();
      
      if (result.success) {
        alert(`✅ Successfully processed ${result.successful} email(s)!${result.failed > 0 ? `\n⚠️ Failed: ${result.failed}` : ''}`);
        onClear(); // Clear selection after successful operation
      } else {
        alert(`⚠️ Processed ${result.successful}/${result.processed} emails.\nErrors: ${result.errors.join('\n')}`);
      }
    } catch (error) {
      console.error('Bulk apply to Outlook failed:', error);
      alert('❌ Failed to apply classifications to Outlook. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };
  
  if (selectedEmails.length === 0) {
    return null;
  }
  
  return (
    <div className={`email-actions ${className}`}>
      <div className="email-actions__count">
        {selectedEmails.length} email{selectedEmails.length !== 1 ? 's' : ''} selected
      </div>
      
      <button
        className="email-actions__button--primary"
        onClick={handleMarkAsRead}
        disabled={isProcessing}
        title="Mark selected emails as read"
      >
        {isProcessing ? '⟳ ' : ''}Mark as Read
      </button>
      
      <button
        className="email-actions__button--secondary"
        onClick={handleMarkAsUnread}
        disabled={isProcessing}
        title="Mark selected emails as unread"
      >
        {isProcessing ? '⟳ ' : ''}Mark as Unread
      </button>
      
      <button
        className="email-actions__button--success"
        onClick={handleApplyToOutlook}
        disabled={isProcessing}
        title="Apply AI classifications and move to Outlook folders"
      >
        {isProcessing ? '⟳ Processing...' : '📁 Apply to Outlook'}
      </button>
      
      <button
        className="email-actions__button--danger"
        onClick={handleDelete}
        disabled={isProcessing}
        title="Delete selected emails"
      >
        {isProcessing ? '⟳ ' : ''}Delete
      </button>
      
      <div className="email-actions__spacer">
        <button
          className="email-actions__button--clear"
          onClick={onClear}
          disabled={isProcessing}
          title="Clear selection"
        >
          Clear Selection
        </button>
      </div>
    </div>
  );
};