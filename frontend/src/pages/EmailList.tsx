// Complete email list interface with search, filtering, and AI categorization
import React, { useState, useMemo, useCallback } from 'react';
import { useGetEmailsQuery, useSearchEmailsQuery } from '@/services/emailApi';
import { useEmailFilters } from '@/hooks/useEmailFilters';
import { EmailItem } from '@/components/Email/EmailItem';
import { SearchBar } from '@/components/Email/SearchBar';
import { EmailFilters } from '@/components/Email/EmailFilters';
import { EmailActions } from '@/components/Email/EmailActions';

const EmailList: React.FC = () => {
  const { filters, setFilters, hasActiveFilters, getFilterParams } = useEmailFilters();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEmails, setSelectedEmails] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<'date' | 'sender' | 'subject'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Use search query if present, otherwise use filters
  const shouldSearch = searchQuery.trim().length > 0;
  
  const {
    data: emailData,
    isLoading,
    error,
    refetch,
  } = useGetEmailsQuery(getFilterParams(), {
    skip: shouldSearch,
  });

  const {
    data: searchData,
    isLoading: isSearching,
    error: searchError,
  } = useSearchEmailsQuery(
    { 
      query: searchQuery.trim(),
      page: 1,
      per_page: 100, // Get more results for search
    },
    {
      skip: !shouldSearch,
    }
  );

  // Current data based on search or filter mode
  const currentData = shouldSearch ? searchData : emailData;
  const currentLoading = shouldSearch ? isSearching : isLoading;
  const currentError = shouldSearch ? searchError : error;

  // Handle email selection
  const handleEmailSelect = useCallback((emailId: string) => {
    setSelectedEmails(prev => 
      prev.includes(emailId) 
        ? prev.filter(id => id !== emailId)
        : [...prev, emailId]
    );
  }, []);

  // Handle select all toggle
  const handleSelectAll = useCallback(() => {
    if (!currentData?.emails) return;
    
    const allCurrentIds = currentData.emails.map(email => email.id);
    const allSelected = allCurrentIds.every(id => selectedEmails.includes(id));
    
    if (allSelected) {
      // Deselect all current emails
      setSelectedEmails(prev => prev.filter(id => !allCurrentIds.includes(id)));
    } else {
      // Select all current emails
      setSelectedEmails(prev => [...new Set([...prev, ...allCurrentIds])]);
    }
  }, [currentData?.emails, selectedEmails]);

  // Handle clear selection
  const handleClearSelection = useCallback(() => {
    setSelectedEmails([]);
  }, []);

  // Handle sort change
  const handleSortChange = useCallback((newSortBy: 'date' | 'sender' | 'subject') => {
    if (sortBy === newSortBy) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
  }, [sortBy]);

  // Sort emails
  const sortedEmails = useMemo(() => {
    if (!currentData?.emails) return [];
    
    return [...currentData.emails].sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'date':
          comparison = new Date(a.date).getTime() - new Date(b.date).getTime();
          break;
        case 'sender':
          comparison = a.sender.localeCompare(b.sender);
          break;
        case 'subject':
          comparison = a.subject.localeCompare(b.subject);
          break;
      }
      
      return sortOrder === 'desc' ? -comparison : comparison;
    });
  }, [currentData?.emails, sortBy, sortOrder]);

  // Main container style
  const containerStyle = {
    display: 'flex',
    flexDirection: 'column' as const,
    height: '100%',
    backgroundColor: '#f8f9fa',
  };

  const headerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '24px',
    backgroundColor: '#fff',
    borderBottom: '1px solid #e0e0e0',
    gap: '16px',
    flexWrap: 'wrap' as const,
  };

  const titleStyle = {
    margin: 0,
    fontSize: '28px',
    fontWeight: '700',
    color: '#333',
  };

  const statsStyle = {
    fontSize: '14px',
    color: '#6c757d',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  };

  const contentStyle = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    padding: '16px 24px',
    gap: '16px',
    minHeight: 0, // Important for virtual scrolling
  };

  const listContainerStyle = {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: '8px',
    border: '1px solid #e0e0e0',
    minHeight: '400px',
  };

  const sortControlsStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '16px',
    borderBottom: '1px solid #e0e0e0',
    backgroundColor: '#f8f9fa',
  };

  const sortButtonStyle = (active: boolean) => ({
    padding: '6px 12px',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    backgroundColor: active ? '#007acc' : '#fff',
    color: active ? '#fff' : '#333',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: '500',
    transition: 'all 0.2s ease',
  });

  // Loading state
  if (currentLoading) {
    return (
      <div style={containerStyle}>
        <div style={{...headerStyle, justifyContent: 'center'}}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>⟳</div>
            <div>Loading emails...</div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (currentError) {
    return (
      <div style={containerStyle}>
        <div style={{...headerStyle, justifyContent: 'center'}}>
          <div style={{ textAlign: 'center', color: '#dc3545' }}>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>⚠️</div>
            <div>Error loading emails</div>
            <button 
              onClick={refetch}
              style={{
                marginTop: '16px',
                padding: '8px 16px',
                backgroundColor: '#007acc',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <h1 style={titleStyle}>
          {shouldSearch ? 'Search Results' : 'Inbox'}
        </h1>
        
        <div style={statsStyle}>
          {currentData && (
            <>
              <span>
                {currentData.emails.length} of {currentData.total_count} emails
              </span>
              {selectedEmails.length > 0 && (
                <span>• {selectedEmails.length} selected</span>
              )}
              {hasActiveFilters && !shouldSearch && (
                <span>• Filtered</span>
              )}
            </>
          )}
        </div>
        
        <SearchBar 
          value={searchQuery}
          onChange={setSearchQuery}
          isLoading={isSearching}
          placeholder="Search emails..."
        />
      </div>

      {/* Content */}
      <div style={contentStyle}>
        {/* Filters */}
        {!shouldSearch && (
          <EmailFilters 
            filters={filters}
            onChange={setFilters}
          />
        )}

        {/* Bulk Actions */}
        <EmailActions 
          selectedEmails={selectedEmails}
          onClear={handleClearSelection}
        />

        {/* Email List */}
        <div style={listContainerStyle}>
          {/* Sort Controls */}
          <div style={sortControlsStyle}>
            <span style={{ fontSize: '14px', fontWeight: '500', color: '#6c757d' }}>
              Sort by:
            </span>
            <button
              onClick={() => handleSortChange('date')}
              style={sortButtonStyle(sortBy === 'date')}
            >
              Date {sortBy === 'date' && (sortOrder === 'desc' ? '↓' : '↑')}
            </button>
            <button
              onClick={() => handleSortChange('sender')}
              style={sortButtonStyle(sortBy === 'sender')}
            >
              Sender {sortBy === 'sender' && (sortOrder === 'desc' ? '↓' : '↑')}
            </button>
            <button
              onClick={() => handleSortChange('subject')}
              style={sortButtonStyle(sortBy === 'subject')}
            >
              Subject {sortBy === 'subject' && (sortOrder === 'desc' ? '↓' : '↑')}
            </button>
            
            {/* Select All */}
            {sortedEmails.length > 0 && (
              <button
                onClick={handleSelectAll}
                style={{
                  ...sortButtonStyle(false),
                  marginLeft: 'auto',
                  backgroundColor: '#f8f9fa',
                }}
              >
                {sortedEmails.every(email => selectedEmails.includes(email.id)) ? 'Deselect All' : 'Select All'}
              </button>
            )}
          </div>

          {/* Email Items */}
          {sortedEmails.length === 0 ? (
            <div style={{ 
              padding: '48px 24px',
              textAlign: 'center',
              color: '#6c757d'
            }}>
              {shouldSearch ? (
                <>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                  <div>No emails found matching "{searchQuery}"</div>
                </>
              ) : (
                <>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>📭</div>
                  <div>No emails found matching your filters</div>
                </>
              )}
            </div>
          ) : (
            <div style={{ 
              maxHeight: '500px', 
              overflowY: 'auto',
              padding: '8px'
            }}>
              {sortedEmails.map((email) => (
                <EmailItem
                  key={email.id}
                  email={email}
                  isSelected={selectedEmails.includes(email.id)}
                  onSelect={() => handleEmailSelect(email.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmailList;
