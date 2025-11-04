// Newsletters page - Shows emails classified as newsletters
import React, { useMemo, useState } from 'react';
import { useGetEmailsQuery } from '@/services/emailApi';
import { EmailItem } from '@/components/Email/EmailItem';
import { EmailDetailView } from '@/components/Email/EmailDetailView';

const Newsletters: React.FC = () => {
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [selectedEmails, setSelectedEmails] = useState<string[]>([]);

  const {
    data: emailData,
    isLoading,
    error,
    refetch,
  } = useGetEmailsQuery({ limit: 1000 });

  // Filter for newsletter emails
  const newsletterEmails = useMemo(() => {
    if (!emailData?.emails) return [];
    return emailData.emails.filter(email => email.ai_category === 'newsletter');
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
          <div className="loading-container__icon">📰</div>
          <h2 className="loading-container__title">Loading Newsletters</h2>
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
          <div>Error loading newsletters</div>
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
        <h1 className="page-title">📰 Newsletters</h1>
        <div className="page-stats">
          {newsletterEmails.length} newsletter{newsletterEmails.length !== 1 ? 's' : ''}
        </div>
      </div>

      <div className="page-content">
        {newsletterEmails.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__icon">📭</div>
            <div className="empty-state__title">No newsletters yet</div>
            <div className="empty-state__description">
              Newsletters will appear here after emails are classified.
              <br /><br />
              <strong>To get started:</strong>
              <br />1. Go to the <a href="#/emails" style={{color: '#00f9ff', textDecoration: 'underline'}}>📧 Emails</a> tab
              <br />2. Wait for emails to be classified (happens automatically)
              <br />3. Emails classified as newsletters will appear here
            </div>
          </div>
        ) : (
          <div className="email-list-split-view">
            {/* Email List - Left Side */}
            <div className={`email-list-panel ${selectedEmailId ? 'email-list-panel--split' : ''}`}>
              <div className="email-list-items-container">
                {newsletterEmails.map((email) => (
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
                ← Select a newsletter to view details
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Newsletters;
