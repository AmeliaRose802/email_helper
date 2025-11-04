// FYI page - Shows emails classified as FYI
import React, { useMemo, useState } from 'react';
import { useGetEmailsQuery } from '@/services/emailApi';
import { EmailItem } from '@/components/Email/EmailItem';
import { EmailDetailView } from '@/components/Email/EmailDetailView';

const FYI: React.FC = () => {
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [selectedEmails, setSelectedEmails] = useState<string[]>([]);

  const {
    data: emailData,
    isLoading,
    error,
    refetch,
  } = useGetEmailsQuery({ limit: 1000 });

  // Filter for FYI emails
  const fyiEmails = useMemo(() => {
    if (!emailData?.emails) return [];
    return emailData.emails.filter(email => email.ai_category === 'fyi');
  }, [emailData?.emails]);

  const handleEmailSelect = (emailId: string) => {
    setSelectedEmails(prev => 
      prev.includes(emailId) 
        ? prev.filter(id => id !== emailId)
        : [...prev, emailId]
    );
  };

  if (isLoading) {
    return (
      <div className="page-container">
        <div className="loading-container">
          <div className="loading-container__icon">ℹ️</div>
          <h2 className="loading-container__title">Loading FYI Emails</h2>
          <p className="loading-container__message">Please wait...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-container">
          <div className="text-2xl mb-sm">⚠️</div>
          <div>Error loading FYI emails</div>
          <button 
            onClick={refetch}
            className="synthwave-button mt-md"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">ℹ️ FYI</h1>
        <div className="page-stats">
          {fyiEmails.length} FYI item{fyiEmails.length !== 1 ? 's' : ''}
        </div>
      </div>

      <div className="page-content">
        {fyiEmails.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__icon">📭</div>
            <div className="empty-state__title">No FYI items yet</div>
            <div className="empty-state__description">
              FYI summaries will appear here after emails are classified.
              <br /><br />
              <strong>To get started:</strong>
              <br />1. Go to the <a href="#/emails" style={{color: '#00f9ff', textDecoration: 'underline'}}>📧 Emails</a> tab
              <br />2. Wait for emails to be classified (happens automatically)
              <br />3. Emails classified as FYI will appear here
            </div>
          </div>
        ) : (
          <div className="email-list-split-view">
            {/* Email List - Left Side */}
            <div className={`email-list-panel ${selectedEmailId ? 'email-list-panel--split' : ''}`}>
              <div className="email-list-items-container">
                {fyiEmails.map((email) => (
                  <EmailItem
                    key={email.id}
                    email={email}
                    isSelected={selectedEmails.includes(email.id)}
                    onSelect={() => handleEmailSelect(email.id)}
                    onEmailClick={(emailId) => setSelectedEmailId(emailId)}
                  />
                ))}
              </div>
            </div>

            {/* Email Detail - Right Side */}
            {selectedEmailId && (
              <div className="email-list-panel" key={selectedEmailId}>
                <EmailDetailView
                  emailId={selectedEmailId}
                  onClose={() => setSelectedEmailId(null)}
                />
              </div>
            )}

            {/* Placeholder when no email selected */}
            {!selectedEmailId && (
              <div className="email-list-placeholder">
                ← Select an FYI item to view details
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default FYI;
