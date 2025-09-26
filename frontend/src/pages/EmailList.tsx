// Email list page component - placeholder for T7
import React, { useState } from 'react';
import { useGetEmailsQuery } from '@/services/emailApi';
import type { EmailFilter } from '@/types/email';

const EmailList: React.FC = () => {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<EmailFilter>({});

  const {
    data: emailData,
    isLoading,
    error,
  } = useGetEmailsQuery({
    page,
    per_page: 20,
    ...filters,
  });

  const handleFilterChange = (newFilters: Partial<EmailFilter>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
    setPage(1); // Reset to first page when filters change
  };

  if (isLoading) {
    return <div className="email-list-loading">Loading emails...</div>;
  }

  if (error) {
    return <div className="email-list-error">Error loading emails</div>;
  }

  return (
    <div className="email-list">
      <h1>Email List</h1>

      <div className="email-filters">
        <h3>Filters</h3>
        <div className="filter-controls">
          <label>
            Show unread only:
            <input
              type="checkbox"
              checked={filters.is_read === false}
              onChange={(e) =>
                handleFilterChange({
                  is_read: e.target.checked ? false : undefined,
                })
              }
            />
          </label>

          <label>
            Sender:
            <input
              type="text"
              value={filters.sender || ''}
              onChange={(e) => handleFilterChange({ sender: e.target.value || undefined })}
              placeholder="Filter by sender"
            />
          </label>

          <label>
            Subject:
            <input
              type="text"
              value={filters.subject || ''}
              onChange={(e) => handleFilterChange({ subject: e.target.value || undefined })}
              placeholder="Filter by subject"
            />
          </label>
        </div>
      </div>

      <div className="email-results">
        {emailData && (
          <>
            <p>
              Showing {emailData.emails.length} of {emailData.total_count} emails
            </p>

            {emailData.emails.length === 0 ? (
              <p>No emails found matching your filters.</p>
            ) : (
              <div className="email-items">
                {emailData.emails.map((email) => (
                  <div key={email.id} className={`email-item ${!email.is_read ? 'unread' : ''}`}>
                    <div className="email-header">
                      <strong>{email.subject}</strong>
                      <span className="email-date">{email.date}</span>
                    </div>
                    <div className="email-sender">From: {email.sender}</div>
                    <div className="email-preview">{email.body.substring(0, 150)}...</div>
                  </div>
                ))}
              </div>
            )}

            <div className="pagination">
              <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
                Previous
              </button>
              <span>Page {page}</span>
              <button disabled={!emailData.has_more} onClick={() => setPage((p) => p + 1)}>
                Next
              </button>
            </div>
          </>
        )}
      </div>

      <div className="email-actions">
        <p>
          <em>Note: Full email management features will be implemented in T7</em>
        </p>
      </div>
    </div>
  );
};

export default EmailList;
