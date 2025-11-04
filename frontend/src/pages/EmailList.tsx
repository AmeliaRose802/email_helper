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
  
  // Initialize refs from sessionStorage to persist across page reloads
  const classifiedEmailsRef = React.useRef<Map<string, Email>>(new Map());
  
  // Load from sessionStorage on mount
  React.useEffect(() => {
    try {
      const stored = sessionStorage.getItem('classifiedEmails');
      if (stored) {
        const parsed = JSON.parse(stored);
        const map = new Map(Object.entries(parsed)) as Map<string, Email>;
        classifiedEmailsRef.current = map;
        setClassifiedEmails(map);
        console.log('[EmailList] Restored', map.size, 'classified emails from sessionStorage');
      }
    } catch (e) {
      console.warn('Failed to load classified emails from sessionStorage:', e);
    }
  }, []); // Run once on mount
  
  const [classifiedEmails, setClassifiedEmails] = useState<Map<string, Email>>(new Map());
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
  } = useGetEmailsQuery({ limit: 50000 });

  // Debug logging to diagnose email loading issues
  useEffect(() => {
    console.log('[EmailList Debug] Query state:', {
      isLoading,
      hasError: !!error,
      error: error,
      hasData: !!emailData,
      emailCount: emailData?.emails?.length || 0,
      totalEmails: emailData?.total || 0
    });
  }, [isLoading, error, emailData]);

  // Persist classification state to sessionStorage
  useEffect(() => {
    try {
      // Convert Map to object for JSON serialization
      const emailsObj = Object.fromEntries(classifiedEmailsRef.current);
      sessionStorage.setItem('classifiedEmails', JSON.stringify(emailsObj));
      
      // Persist classified pages
      const pagesArray = Array.from(classifiedPagesRef.current);
      sessionStorage.setItem('classifiedPages', JSON.stringify(pagesArray));
    } catch (e) {
      console.warn('Failed to persist classification state:', e);
    }
  }, [classifiedEmails]); // Trigger when classifiedEmails state changes

  // Current data
  const currentData = emailData;
  const currentLoading = isLoading;
  const currentError = error;

  // Cleanup on unmount - abort any pending prefetch operations
  useEffect(() => {
    return () => {
      if (prefetchAbortControllerRef.current) {
        prefetchAbortControllerRef.current.abort();
      }
    };
  }, []);

  // Group emails by conversation (like Python app)
  const conversationGroups = useMemo(() => {
    console.log('[EmailList Debug] Building conversation groups from data:', {
      hasData: !!currentData,
      emailsArray: currentData?.emails,
      emailCount: currentData?.emails?.length || 0
    });
    
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
    // Use standardized field name with backward compatibility
    const result = Array.from(groups.entries())
      .map(([conversationId, emails]) => ({
        conversationId,
        emails: emails.sort((a, b) => {
          const aDate = new Date(a.received_time || a.date || 0);
          const bDate = new Date(b.received_time || b.date || 0);
          return bDate.getTime() - aDate.getTime();
        }),
        latestDate: emails.reduce((latest, email) => {
          const emailDate = new Date(email.received_time || email.date || 0);
          return emailDate > latest ? emailDate : latest;
        }, new Date(0)),
        // Representative email is the most recent one
        representativeEmail: emails.sort((a, b) => {
          const aDate = new Date(a.received_time || a.date || 0);
          const bDate = new Date(b.received_time || b.date || 0);
          return bDate.getTime() - aDate.getTime();
        })[0]
      }))
      .sort((a, b) => b.latestDate.getTime() - a.latestDate.getTime());
    
    console.log('[EmailList Debug] Conversation groups built:', {
      totalGroups: result.length,
      firstGroup: result[0],
      groupSizes: result.slice(0, 5).map(g => g.emails.length)
    });
    
    return result;
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
  
  // Load classified pages from sessionStorage on mount
  React.useEffect(() => {
    try {
      const stored = sessionStorage.getItem('classifiedPages');
      if (stored) {
        classifiedPagesRef.current = new Set(JSON.parse(stored));
      }
    } catch (e) {
      console.warn('Failed to load classified pages from sessionStorage:', e);
    }
  }, []); // Run once on mount
  
  const prefetchAbortControllerRef = React.useRef<AbortController | null>(null);
  const isPrefetchingRef = React.useRef(false);
  const [isPrefetchingState, setIsPrefetchingState] = useState(false);
  
  // Helper function to classify a batch of conversations
  const classifyConversations = useCallback(async (
    conversations: typeof currentPageConversations,
    isPrefetch = false,
    abortSignal?: AbortSignal
  ) => {
    if (conversations.length === 0) return;
    
    // Get representative emails from conversations that need classification
    const conversationsToClassify = conversations.filter(conv => {
      const repEmail = conv.representativeEmail;
      // Skip if already classified (check both state and ref) or currently classifying
      if (classifiedEmailsRef.current.has(repEmail.id) || classifyingIds.has(repEmail.id)) {
        return false;
      }
      // Only classify if no AI category yet
      return !repEmail.ai_category;
    });

    if (conversationsToClassify.length === 0) {
      return;
    }

    // Only show progress for current page, not prefetch
    if (!isPrefetch) {
      setIsClassifying(true);
      setClassificationProgress({ current: 0, total: conversationsToClassify.length });
    }

    // Classify one conversation at a time to avoid API limits
    for (let i = 0; i < conversationsToClassify.length; i++) {
      // Check for abort signal
      if (abortSignal?.aborted) {
        console.log('[Prefetch] Classification aborted');
        break;
      }

      const conversation = conversationsToClassify[i];
      const repEmail = conversation.representativeEmail;
      
      // Mark email as classifying
      setClassifyingIds(prev => new Set(prev).add(repEmail.id));

      try {
        // Use standardized field name with backward compatibility
        const result = await classifyEmail({
          subject: repEmail.subject,
          sender: repEmail.sender,
          content: repEmail.content || repEmail.body || '',
        }).unwrap();

        // Apply classification to all emails in the conversation
        // BUT: Don't overwrite manually classified emails
        setClassifiedEmails(prev => {
          const next = new Map(prev);
          conversation.emails.forEach(email => {
            // Check if email was already manually classified
            const existingClassification = classifiedEmailsRef.current.get(email.id);
            if (existingClassification && existingClassification.ai_category) {
              // Email was already classified manually - keep it
              console.log(`[Classification] Skipping email ${email.id.substring(0, 20)}... - already classified as ${existingClassification.ai_category}`);
              return;
            }
            
            const classified: Email = {
              ...email,
              ai_category: result.category as Email['ai_category'],
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

        // Update progress only for current page
        if (!isPrefetch) {
          setClassificationProgress({ current: i + 1, total: conversationsToClassify.length });
        }
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
    if (!isPrefetch) {
      setIsClassifying(false);
    }
  }, [classifyEmail, classifyingIds]);
  
  // Classify current page conversations
  useEffect(() => {
    const classifyCurrentPageConversations = async () => {
      if (currentPageConversations.length === 0) return;
      
      // Check if ALL representative emails on this page have been classified
      const allClassified = currentPageConversations.every(conv => {
        const repEmail = conv.representativeEmail;
        return classifiedEmailsRef.current.has(repEmail.id) || repEmail.ai_category;
      });
      
      // Skip if this page has already been fully classified
      if (allClassified) {
        classifiedPagesRef.current.add(currentConversationPage);
        return;
      }

      // Mark this page as being classified
      classifiedPagesRef.current.add(currentConversationPage);

      // Classify current page
      await classifyConversations(currentPageConversations, false);
    };

    classifyCurrentPageConversations();
    // Don't include classifiedEmails in dependencies since we're using ref for persistence
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPageConversations, currentConversationPage, classifyConversations]);

  // PREFETCH: Classify next page in background for instant navigation
  useEffect(() => {
    // Abort any existing prefetch operation when page changes
    if (prefetchAbortControllerRef.current) {
      prefetchAbortControllerRef.current.abort();
      prefetchAbortControllerRef.current = null;
      isPrefetchingRef.current = false;
    }

    // Wait for current page to finish classifying before prefetching
    if (isClassifying || isPrefetchingRef.current) {
      return;
    }

    const prefetchNextPage = async () => {
      const nextPage = currentConversationPage + 1;
      
      // Check if there is a next page
      if (nextPage >= totalPages) {
        return;
      }

      // Get next page conversations
      const nextPageStartIdx = nextPage * CONVERSATIONS_PER_PAGE;
      const nextPageEndIdx = nextPageStartIdx + CONVERSATIONS_PER_PAGE;
      const nextPageConversations = conversationGroups.slice(nextPageStartIdx, nextPageEndIdx);

      if (nextPageConversations.length === 0) {
        return;
      }

      // Check if any conversations on next page need classification
      const needsClassification = nextPageConversations.some(conv => {
        const repEmail = conv.representativeEmail;
        // Check both ref and current state to ensure we don't re-classify
        return !classifiedEmailsRef.current.has(repEmail.id) && 
               !classifiedEmails.has(repEmail.id) && 
               !repEmail.ai_category;
      });

      if (!needsClassification) {
        // Mark as classified even though we didn't do work
        classifiedPagesRef.current.add(nextPage);
        return;
      }

      // Start prefetch after a short delay (user is reading current page)
      const timer = setTimeout(async () => {
        console.log(`[Prefetch] Starting background classification for page ${nextPage + 1} (${nextPageConversations.length} conversations)`);
        isPrefetchingRef.current = true;
        setIsPrefetchingState(true);
        
        // Create abort controller for this prefetch operation
        const abortController = new AbortController();
        prefetchAbortControllerRef.current = abortController;

        // Mark page as being classified
        classifiedPagesRef.current.add(nextPage);

        try {
          await classifyConversations(nextPageConversations, true, abortController.signal);
          console.log(`[Prefetch] Completed background classification for page ${nextPage + 1}`);
        } catch (error) {
          if (error instanceof Error && error.name === 'AbortError') {
            console.log('[Prefetch] Classification was aborted');
          } else {
            console.error('[Prefetch] Error during background classification:', error);
          }
        } finally {
          isPrefetchingRef.current = false;
          setIsPrefetchingState(false);
          if (prefetchAbortControllerRef.current === abortController) {
            prefetchAbortControllerRef.current = null;
          }
        }
      }, 2000); // 2 second delay before starting prefetch

      // Cleanup timer on unmount or page change
      return () => clearTimeout(timer);
    };

    prefetchNextPage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentConversationPage, isClassifying, conversationGroups, totalPages, classifyConversations]);

  // Get emails from current page conversations with classification
  const currentPageEmails = useMemo(() => {
    const emails = currentPageConversations.flatMap(conv => conv.emails);
    
    // Deduplicate emails by ID (some emails may appear in multiple conversations)
    const seenIds = new Set<string>();
    const uniqueEmails = emails.filter(email => {
      if (seenIds.has(email.id)) {
        return false;
      }
      seenIds.add(email.id);
      return true;
    });
    
    console.log('[EmailList Debug] currentPageEmails calculation:', {
      conversationsOnPage: currentPageConversations.length,
      totalEmailsFromConversations: emails.length,
      uniqueEmailsAfterDedup: uniqueEmails.length,
      duplicatesRemoved: emails.length - uniqueEmails.length,
      sampleConversation: currentPageConversations[0]
    });
    
    return uniqueEmails.map(email => {
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
          // Use standardized field name with backward compatibility
          const aDate = new Date(a.received_time || a.date || 0).getTime();
          const bDate = new Date(b.received_time || b.date || 0).getTime();
          comparison = aDate - bDate;
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

  // All styles moved to unified.css

  // Loading state
  if (currentLoading) {
    return (
      <div className="email-list-container">
        <div className="email-list-header email-list-header--centered">
          <div className="email-list-loading-overlay">
            <div className="email-list-loading-overlay__icon">📧</div>
            <h2 className="email-list-loading-overlay__title">Loading Emails</h2>
            <ProgressBar
              current={0}
              total={100}
              label="Fetching emails from Outlook..."
              showPercentage={false}
              color="#4a90e2"
            />
            <p className="email-list-loading-overlay__message">
              This may take a moment...
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (currentError) {
    console.error('[EmailList] Error loading emails:', currentError);
    const errorMessage = 'message' in currentError ? currentError.message : 
                         'data' in currentError ? JSON.stringify(currentError.data) :
                         'status' in currentError ? `HTTP ${currentError.status}` :
                         'Unknown error';
    
    return (
      <div className="email-list-container">
        <div className="email-list-header email-list-header--centered">
          <div className="email-list-error-overlay">
            <div className="email-list-error-overlay__icon">⚠️</div>
            <h2 className="email-list-error-overlay__title">Error Loading Emails</h2>
            <div className="email-list-error-overlay__details">
              <strong>Error Details:</strong><br/>
              {errorMessage}
            </div>
            <p className="email-list-error-overlay__help">
              Make sure the backend server is running on http://localhost:8000
            </p>
            <button 
              onClick={refetch}
              className="email-list-error-overlay__retry-btn"
            >
              🔄 Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="email-list-container">
      {/* Header */}
      <div className="email-list-header">
        <h1 className="email-list-title">Inbox</h1>
        <div className="email-list-stats">
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
              {isPrefetchingState && (
                <span className="email-list-prefetch-indicator">
                  ⚡ Pre-loading next page...
                </span>
              )}
            </>
          )}
        </div>
        
        {/* Single Approve Button - Does Both Operations (Current Page Only) */}
        <button
          onClick={async () => {
            // Get only classified emails from current page
            const currentPageEmailIds = currentPageEmails
              .filter(email => email.ai_category)
              .map(email => email.id);
            
            if (currentPageEmailIds.length === 0) {
              alert('No classified emails on current page to process');
              return;
            }

            const emailCount = currentPageEmailIds.length;
            if (!window.confirm(`Process ${emailCount} classified email${emailCount !== 1 ? 's' : ''} from current page?\n\n✅ Apply classifications to Outlook folders\n✅ Extract tasks and summaries\n\nThis will run in the background.`)) {
              return;
            }

            // Run both operations
            setIsApplyingToOutlook(true);
            setIsExtractingTasks(true);

            try {
              // 1. Apply to Outlook
              const applyResult = await bulkApplyToOutlook({
                emailIds: currentPageEmailIds,
                applyToOutlook: true,
              }).unwrap();

              console.log('✅ Applied to Outlook:', applyResult);

              // 2. Sync to database - only current page emails
              const currentPageClassifiedEmails = currentPageEmails.filter(email => 
                currentPageEmailIds.includes(email.id)
              );
              const syncResult = await syncEmailsToDatabase({
                emails: currentPageClassifiedEmails
              }).unwrap();

              console.log('✅ Synced to database:', syncResult);

              // 3. Extract tasks
              const extractResult = await extractTasksFromEmails({
                email_ids: currentPageEmailIds
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
          disabled={
            isApplyingToOutlook || 
            isExtractingTasks || 
            isClassifying || 
            currentPageEmails.filter(e => e.ai_category).length === 0
          }
          className="email-approve-button"
          title={
            isClassifying 
              ? 'Please wait for classification to complete'
              : currentPageEmails.filter(e => e.ai_category).length === 0
              ? 'No classified emails on current page'
              : 'Apply classifications to Outlook AND extract tasks for current page only!'
          }
        >
          <span className="email-list-checkmark">✅</span>
          {isApplyingToOutlook || isExtractingTasks ? 'Processing...' : `Approve ${currentPageEmails.filter(e => e.ai_category).length} Email${currentPageEmails.filter(e => e.ai_category).length !== 1 ? 's' : ''}`}
        </button>
      </div>

      {/* Content */}
      <div className="email-content-area">
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
          <div className="email-pagination">
            <button
              onClick={handlePreviousPage}
              disabled={currentConversationPage === 0}
              className="email-pagination-button"
            >
              ← Previous 10 Conversations
            </button>
            
            <span className="email-pagination-info">
              Showing conversations {currentConversationPage * CONVERSATIONS_PER_PAGE + 1}-
              {Math.min((currentConversationPage + 1) * CONVERSATIONS_PER_PAGE, totalConversations)} of {totalConversations}
            </span>
            
            <button
              onClick={handleNextPage}
              disabled={currentConversationPage >= totalPages - 1}
              className="email-pagination-button"
            >
              Next 10 Conversations →
            </button>
          </div>
        )}

        {/* Email List and Detail - Split View */}
        <div className="email-list-split-view">
          {/* Email List - Left Side */}
          <div className={`email-list-panel ${selectedEmailId ? 'email-list-panel--split' : ''}`}>
            {/* Sort Controls */}
            <div className="email-list-sort-controls">
              <span className="email-list-sort-label">
                Sort by:
              </span>
              <button
                onClick={() => handleSortChange('date')}
                className={`email-list-sort-btn ${sortBy === 'date' ? 'email-list-sort-btn--active' : ''}`}
              >
                Date {sortBy === 'date' && (sortOrder === 'desc' ? '↓' : '↑')}
              </button>
              <button
                onClick={() => handleSortChange('sender')}
                className={`email-list-sort-btn ${sortBy === 'sender' ? 'email-list-sort-btn--active' : ''}`}
              >
                Sender {sortBy === 'sender' && (sortOrder === 'desc' ? '↓' : '↑')}
              </button>
              <button
                onClick={() => handleSortChange('subject')}
                className={`email-list-sort-btn ${sortBy === 'subject' ? 'email-list-sort-btn--active' : ''}`}
              >
                Subject {sortBy === 'subject' && (sortOrder === 'desc' ? '↓' : '↑')}
              </button>
              
              {/* Select All */}
              {sortedEmails.length > 0 && (
                <button
                  onClick={handleSelectAll}
                  className="email-list-sort-btn email-list-sort-btn--select-all"
                >
                  {sortedEmails.every(email => selectedEmails.includes(email.id)) ? 'Deselect All' : 'Select All'}
                </button>
              )}
            </div>

            {/* Email Items */}
            {sortedEmails.length === 0 ? (
              <div className="email-list-empty-state">
                <div className="email-list-empty-state__icon">📭</div>
                <div className="email-list-empty-state__title">No emails found</div>
              </div>
            ) : (
              <div className="email-list-items-container">
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
              ← Select an email to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmailList;
