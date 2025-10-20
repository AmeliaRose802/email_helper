// Complete email list interface with AI categorization
import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useGetEmailsQuery, useBulkApplyToOutlookMutation, useSyncEmailsToDatabaseMutation, useExtractTasksFromEmailsMutation } from '@/services/emailApi';
import { useClassifyEmailMutation } from '@/services/aiApi';
import { EmailItem } from '@/components/Email/EmailItem';
import { EmailActions } from '@/components/Email/EmailActions';
import { ProgressBar } from '@/components/Email/ProgressBar';
import { EmailDetailView } from '@/components/Email/EmailDetailView';
import type { Email } from '@/types/email';

const EmailList: React.FC = () => {
  const [selectedEmails, setSelectedEmails] = useState<string[]>([]);
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null); // For split view
  const [sortBy, setSortBy] = useState<'date' | 'sender' | 'subject'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [classifyEmail] = useClassifyEmailMutation();
  const [bulkApplyToOutlook] = useBulkApplyToOutlookMutation();
  const [syncEmailsToDatabase] = useSyncEmailsToDatabaseMutation();
  const [extractTasksFromEmails] = useExtractTasksFromEmailsMutation();
  const [isApplyingToOutlook, setIsApplyingToOutlook] = useState(false);
  const [isExtractingTasks, setIsExtractingTasks] = useState(false);
  // Use ref to persist classification state across re-renders and page changes
  const classifiedEmailsRef = React.useRef<Map<string, Email>>(new Map());
  const [classifiedEmails, setClassifiedEmails] = useState<Map<string, Email>>(classifiedEmailsRef.current);
  const [classifyingIds, setClassifyingIds] = useState<Set<string>>(new Set());
  
  // Progress tracking for classification
  const [classificationProgress, setClassificationProgress] = useState({ current: 0, total: 0 });
  const [isClassifying, setIsClassifying] = useState(false);
  
  // Pagination state for conversations
  const [currentConversationPage, setCurrentConversationPage] = useState(0);
  const CONVERSATIONS_PER_PAGE = 10;
  
  const {
    data: emailData,
    isLoading,
    error,
    refetch,
  } = useGetEmailsQuery({ limit: 10000 });

  // Current data
  const currentData = emailData;
  const currentLoading = isLoading;
  const currentError = error;

  // Group emails by conversation (like Python app)
  const conversationGroups = useMemo(() => {
    if (!currentData?.emails) return [];
    
    const groups = new Map<string, Email[]>();
    
    currentData.emails.forEach(email => {
      const conversationId = email.conversation_id || `single_${email.id}`;
      if (!groups.has(conversationId)) {
        groups.set(conversationId, []);
      }
      groups.get(conversationId)!.push(email);
    });
    
    // Convert to array and sort by latest email date (most recent first)
    return Array.from(groups.entries())
      .map(([conversationId, emails]) => ({
        conversationId,
        emails: emails.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()),
        latestDate: emails.reduce((latest, email) => {
          const emailDate = new Date(email.date);
          return emailDate > latest ? emailDate : latest;
        }, new Date(0)),
        // Representative email is the most recent one
        representativeEmail: emails.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())[0]
      }))
      .sort((a, b) => b.latestDate.getTime() - a.latestDate.getTime());
  }, [currentData?.emails]);

  // Get current page of conversations
  const totalConversations = conversationGroups.length;
  const totalPages = Math.ceil(totalConversations / CONVERSATIONS_PER_PAGE);
  const currentPageConversations = useMemo(() => {
    const startIdx = currentConversationPage * CONVERSATIONS_PER_PAGE;
    const endIdx = startIdx + CONVERSATIONS_PER_PAGE;
    return conversationGroups.slice(startIdx, endIdx);
  }, [conversationGroups, currentConversationPage]);

  // Auto-classify conversations when page changes (like Python app: classify 10 conversations at a time)
  // Use a ref to track which pages have been classified to prevent re-classification
  const classifiedPagesRef = React.useRef<Set<number>>(new Set());
  
  useEffect(() => {
    const classifyCurrentPageConversations = async () => {
      if (currentPageConversations.length === 0) return;
      
      // Skip if this page has already been classified
      if (classifiedPagesRef.current.has(currentConversationPage)) {
        return;
      }
      
      // Get representative emails from conversations that need classification
      const conversationsToClassify = currentPageConversations.filter(conv => {
        const repEmail = conv.representativeEmail;
        // Skip if already classified (check both state and ref) or currently classifying
        if (classifiedEmailsRef.current.has(repEmail.id) || classifyingIds.has(repEmail.id)) {
          return false;
        }
        // Only classify if no AI category yet
        return !repEmail.ai_category;
      });

      if (conversationsToClassify.length === 0) {
        // Mark page as processed even if no conversations to classify
        classifiedPagesRef.current.add(currentConversationPage);
        return;
      }

      // Mark this page as being classified
      classifiedPagesRef.current.add(currentConversationPage);

      // Initialize progress tracking
      setIsClassifying(true);
      setClassificationProgress({ current: 0, total: conversationsToClassify.length });

      // Classify one conversation at a time to avoid API limits
      for (let i = 0; i < conversationsToClassify.length; i++) {
        const conversation = conversationsToClassify[i];
        const repEmail = conversation.representativeEmail;
        
        // Mark email as classifying
        setClassifyingIds(prev => new Set(prev).add(repEmail.id));

        try {
          const result = await classifyEmail({
            subject: repEmail.subject,
            sender: repEmail.sender,
            content: repEmail.body || '',
          }).unwrap();

          // Apply classification to all emails in the conversation
          setClassifiedEmails(prev => {
            const next = new Map(prev);
            conversation.emails.forEach(email => {
              const classified = {
                ...email,
                ai_category: result.category as any,
                ai_confidence: result.confidence,
                ai_reasoning: result.reasoning,
                one_line_summary: result.one_line_summary, // Store the AI-generated one-line summary
                classification_status: 'classified' as const,
              };
              next.set(email.id, classified);
              // Also update ref to persist across page changes
              classifiedEmailsRef.current.set(email.id, classified);
            });
            return next;
          });

          // Update progress
          setClassificationProgress({ current: i + 1, total: conversationsToClassify.length });
        } catch (error) {
          console.error(`Failed to classify conversation ${repEmail.id}:`, error);
          // Store as error status for all emails in conversation
          setClassifiedEmails(prev => {
            const next = new Map(prev);
            conversation.emails.forEach(email => {
              const errored = {
                ...email,
                classification_status: 'error' as const,
              };
              next.set(email.id, errored);
              // Also update ref to persist across page changes
              classifiedEmailsRef.current.set(email.id, errored);
            });
            return next;
          });
        } finally {
          // Remove from classifying set
          setClassifyingIds(prev => {
            const next = new Set(prev);
            next.delete(repEmail.id);
            return next;
          });
        }

        // Delay between classifications to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // Classification complete
      setIsClassifying(false);
    };

    classifyCurrentPageConversations();
    // Don't include classifiedEmails in dependencies since we're using ref for persistence
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPageConversations, classifyEmail, classifyingIds, currentConversationPage]);

  // Get emails from current page conversations with classification
  const currentPageEmails = useMemo(() => {
    const emails = currentPageConversations.flatMap(conv => conv.emails);
    
    return emails.map(email => {
      // Check ref first for persisted classifications
      const classified = classifiedEmailsRef.current.get(email.id);
      if (classified) {
        return classified;
      }
      // Mark as classifying if in progress
      if (classifyingIds.has(email.id)) {
        return { ...email, classification_status: 'classifying' as const };
      }
      // If no AI category yet, mark as pending
      if (!email.ai_category) {
        return { ...email, classification_status: 'pending' as const };
      }
      return email;
    });
  }, [currentPageConversations, classifiedEmails, classifyingIds]);

  // Auto-select first email when page loads
  useEffect(() => {
    if (currentPageEmails.length > 0 && !selectedEmailId) {
      setSelectedEmailId(currentPageEmails[0].id);
    }
  }, [currentPageEmails.length, selectedEmailId]);

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

  // Handle apply all classified emails to Outlook
  // @ts-expect-error - Function defined for future use
  const handleApplyAllToOutlook = async () => {
    if (!currentData?.emails) return;
    
    // Get all emails that have been classified (check both API data and local state)
    const allEmailIds = currentData.emails.map(e => e.id);
    const classifiedEmailIds = allEmailIds.filter(id => {
      const classified = classifiedEmailsRef.current.get(id);
      return classified?.ai_category;
    });
    
    if (classifiedEmailIds.length === 0) {
      alert('No classified emails to apply. Please wait for AI classification to complete.');
      return;
    }
    
    if (!window.confirm(`Apply AI classifications and move ${classifiedEmailIds.length} classified email(s) to their respective Outlook folders?\n\nThis will run in the background so you can continue working.`)) {
      return;
    }
    
    setIsApplyingToOutlook(true);
    
    // Run in background and show immediate feedback
    setTimeout(() => {
      alert(`📁 Applying classifications to ${classifiedEmailIds.length} emails in the background...\n\nYou can continue working. Check your Outlook folders in a moment.`);
    }, 100);
    
    try {
      const result = await bulkApplyToOutlook({
        emailIds: classifiedEmailIds,
        applyToOutlook: true,
      }).unwrap();
      
      // Build clear message
      const successCount = result.successful || 0;
      const failCount = result.failed || 0;
      const totalProcessed = result.processed || 0;
      
      if (successCount > 0 && failCount === 0) {
        console.log(`✅ Successfully moved ${successCount} email(s) to Outlook folders`);
      } else if (successCount > 0 && failCount > 0) {
        console.log(`⚠️ Moved ${successCount}/${totalProcessed} emails. ${failCount} emails couldn't be moved (may have been deleted or moved already).`);
      } else {
        console.error('❌ Failed to move emails to Outlook folders.');
        if (result.errors && result.errors.length > 0) {
          console.error('Errors:', result.errors.slice(0, 5).join(', '));
        }
      }
      
      refetch(); // Refresh the email list
    } catch (error) {
      console.error('Bulk apply to Outlook failed:', error);
    } finally {
      setIsApplyingToOutlook(false);
    }
  };

  // Handle extract tasks from classified emails
  // @ts-expect-error - Function defined for future use
  const handleExtractTasks = async () => {
    if (!currentData?.emails) return;
    
    // Get all classified emails
    const classifiedEmails = Array.from(classifiedEmailsRef.current.values());
    
    if (classifiedEmails.length === 0) {
      alert('No classified emails found. Please wait for AI classification to complete.');
      return;
    }
    
    if (!window.confirm(`Extract tasks from ${classifiedEmails.length} classified emails?\n\nThis will create tasks for action items, newsletters, FYI items, and more.`)) {
      return;
    }
    
    setIsExtractingTasks(true);
    
    try {
      // First, sync classified emails to database
      console.log('Syncing emails to database...');
      const syncResult = await syncEmailsToDatabase({
        emails: classifiedEmails
      }).unwrap();
      
      console.log('Sync result:', syncResult);
      
      // Then extract tasks
      console.log('Extracting tasks from emails...');
      const extractResult = await extractTasksFromEmails({
        email_ids: classifiedEmails.map(e => e.id)
      }).unwrap();
      
      console.log('Extract result:', extractResult);
      
      alert(`✅ Success!\n\n📧 Synced ${syncResult.synced_count} emails to database\n📋 Started task extraction for ${extractResult.email_count} emails\n\nTasks are being created in the background. Check the Tasks page in a moment.`);
      
    } catch (error) {
      console.error('Task extraction failed:', error);
      alert('❌ Failed to extract tasks. Please try again or check the console for details.');
    } finally {
      setIsExtractingTasks(false);
    }
  };

  // Handle sort change
  const handleSortChange = useCallback((newSortBy: 'date' | 'sender' | 'subject') => {
    if (sortBy === newSortBy) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
  }, [sortBy]);

  // Pagination handlers
  const handleNextPage = useCallback(() => {
    if (currentConversationPage < totalPages - 1) {
      setCurrentConversationPage(prev => prev + 1);
    }
  }, [currentConversationPage, totalPages]);

  const handlePreviousPage = useCallback(() => {
    if (currentConversationPage > 0) {
      setCurrentConversationPage(prev => prev - 1);
    }
  }, [currentConversationPage]);

  // Sort emails from current page
  const sortedEmails = useMemo(() => {
    if (!currentPageEmails || currentPageEmails.length === 0) return [];
    
    return [...currentPageEmails].sort((a, b) => {
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
  }, [currentPageEmails, sortBy, sortOrder]);

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
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📧</div>
            <h2 style={{ marginBottom: '24px', color: '#495057' }}>Loading Emails</h2>
            <ProgressBar
              current={0}
              total={100}
              label="Fetching emails from Outlook..."
              showPercentage={false}
              color="#4a90e2"
            />
            <p style={{ marginTop: '16px', color: '#6c757d', fontSize: '14px' }}>
              This may take a moment...
            </p>
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
        <h1 style={titleStyle}>Inbox</h1>
        <div style={statsStyle}>
          {currentData && (
            <>
              <span>
                {totalConversations} conversations | Page {currentConversationPage + 1} of {totalPages || 1}
              </span>
              <span>
                | {currentPageEmails.length} emails on this page
              </span>
              {selectedEmails.length > 0 && (
                <span> | {selectedEmails.length} selected</span>
              )}
            </>
          )}
        </div>
        
        {/* Single Approve Button - Does Both Operations */}
        <button
          onClick={async () => {
            if (!currentData?.emails || classifiedEmailsRef.current.size === 0) {
              alert('No classified emails to process');
              return;
            }

            if (!window.confirm(`Process ${classifiedEmailsRef.current.size} classified emails?\n\n✅ Apply classifications to Outlook folders\n✅ Extract tasks and summaries\n\nThis will run in the background.`)) {
              return;
            }

            // Run both operations
            setIsApplyingToOutlook(true);
            setIsExtractingTasks(true);

            try {
              // 1. Apply to Outlook
              const classifiedEmailIds = Array.from(classifiedEmailsRef.current.keys());
              const applyResult = await bulkApplyToOutlook({
                emailIds: classifiedEmailIds,
                applyToOutlook: true,
              }).unwrap();

              console.log('✅ Applied to Outlook:', applyResult);

              // 2. Sync to database
              const classifiedEmails = Array.from(classifiedEmailsRef.current.values());
              const syncResult = await syncEmailsToDatabase({
                emails: classifiedEmails
              }).unwrap();

              console.log('✅ Synced to database:', syncResult);

              // 3. Extract tasks
              const extractResult = await extractTasksFromEmails({
                email_ids: classifiedEmailIds
              }).unwrap();

              console.log('✅ Extracting tasks:', extractResult);

              alert(`✅ Success!\n\n📁 Moved ${applyResult.successful} emails to Outlook folders\n💾 Synced ${syncResult.synced_count} emails to database\n📋 Extracting tasks from ${extractResult.email_count} emails\n\nCheck the Tasks page in a moment!`);

              refetch();
            } catch (error) {
              console.error('Error processing emails:', error);
              alert('❌ Some operations failed. Check console for details.');
            } finally {
              setIsApplyingToOutlook(false);
              setIsExtractingTasks(false);
            }
          }}
          disabled={isApplyingToOutlook || isExtractingTasks || isClassifying || classifiedEmailsRef.current.size === 0}
          style={{
            padding: '12px 24px',
            backgroundColor: isApplyingToOutlook || isExtractingTasks || isClassifying || classifiedEmailsRef.current.size === 0
              ? '#6c757d' 
              : '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: '700',
            cursor: isApplyingToOutlook || isExtractingTasks || isClassifying || classifiedEmailsRef.current.size === 0
              ? 'not-allowed' 
              : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            transition: 'all 0.2s ease',
            boxShadow: '0 3px 6px rgba(0,0,0,0.15)',
          }}
          title={
            isClassifying 
              ? 'Please wait for classification to complete'
              : classifiedEmailsRef.current.size === 0
              ? 'No classified emails to process'
              : 'Apply classifications to Outlook AND extract tasks - all in one click!'
          }
        >
          <span style={{ fontSize: '22px' }}>✅</span>
          {isApplyingToOutlook || isExtractingTasks ? 'Processing...' : 'Approve All (Apply + Extract Tasks)'}
        </button>
      </div>

      {/* Content */}
      <div style={contentStyle}>
        {/* Classification Progress Bar */}
        {isClassifying && classificationProgress.total > 0 ? (
          <ProgressBar
            current={classificationProgress.current}
            total={classificationProgress.total}
            label="Classifying emails with AI..."
            showPercentage={true}
            color="#4a90e2"
          />
        ) : null}

        {/* Bulk Actions */}
        <EmailActions
          selectedEmails={selectedEmails}
          onClear={handleClearSelection}
        />

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #e0e0e0',
          }}>
            <button
              onClick={handlePreviousPage}
              disabled={currentConversationPage === 0}
              style={{
                padding: '8px 16px',
                backgroundColor: currentConversationPage === 0 ? '#e0e0e0' : '#007acc',
                color: currentConversationPage === 0 ? '#6c757d' : '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: currentConversationPage === 0 ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: '500',
              }}
            >
              ← Previous 10 Conversations
            </button>
            
            <span style={{ fontSize: '14px', color: '#6c757d' }}>
              Showing conversations {currentConversationPage * CONVERSATIONS_PER_PAGE + 1}-
              {Math.min((currentConversationPage + 1) * CONVERSATIONS_PER_PAGE, totalConversations)} of {totalConversations}
            </span>
            
            <button
              onClick={handleNextPage}
              disabled={currentConversationPage >= totalPages - 1}
              style={{
                padding: '8px 16px',
                backgroundColor: currentConversationPage >= totalPages - 1 ? '#e0e0e0' : '#007acc',
                color: currentConversationPage >= totalPages - 1 ? '#6c757d' : '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: currentConversationPage >= totalPages - 1 ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: '500',
              }}
            >
              Next 10 Conversations →
            </button>
          </div>
        )}

        {/* Email List and Detail - Split View */}
        <div style={{ display: 'flex', gap: '16px', height: 'calc(100vh - 300px)' }}>
          {/* Email List - Left Side */}
          <div style={{ ...listContainerStyle, flex: selectedEmailId ? '0 0 40%' : '1', minWidth: '400px' }}>
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
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📭</div>
                <div>No emails found</div>
              </div>
            ) : (
              <div style={{ 
                height: 'calc(100% - 60px)', 
                overflowY: 'auto',
                padding: '8px'
              }}>
                {sortedEmails.map((email) => (
                  <EmailItem
                    key={email.id}
                    email={email}
                    isSelected={selectedEmails.includes(email.id)}
                    onSelect={() => handleEmailSelect(email.id)}
                    onEmailClick={(emailId) => setSelectedEmailId(emailId)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Email Detail - Right Side */}
          {selectedEmailId && (
            <div style={{ 
              flex: '1',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              backgroundColor: '#fff',
              overflow: 'hidden'
            }}>
              <EmailDetailView
                emailId={selectedEmailId}
                onClose={() => setSelectedEmailId(null)}
                showBackButton={true}
              />
            </div>
          )}

          {/* Placeholder when no email selected */}
          {!selectedEmailId && (
            <div style={{
              flex: '1',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#6c757d',
              fontSize: '18px',
              border: '2px dashed #e0e0e0',
              borderRadius: '8px',
            }}>
              ← Select an email to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmailList;
