/**
 * Email Filters Hook
 * Manages email filtering state and provides utility functions
 */

import { useState, useCallback, useMemo } from 'react';
import type { EmailFilter } from '@/types';

export interface UseEmailFiltersReturn {
  filters: EmailFilter;
  setFilters: (filters: EmailFilter | ((prev: EmailFilter) => EmailFilter)) => void;
  hasActiveFilters: boolean;
  getFilterParams: () => Record<string, any>;
  clearFilters: () => void;
}

const defaultFilters: EmailFilter = {
  folder: 'Inbox',
};

export function useEmailFilters(): UseEmailFiltersReturn {
  const [filters, setFilters] = useState<EmailFilter>(defaultFilters);

  // Check if any filters are active (beyond defaults)
  const hasActiveFilters = useMemo(() => {
    return (
      (filters.sender !== undefined && filters.sender !== '') ||
      (filters.subject !== undefined && filters.subject !== '') ||
      filters.date_from !== undefined ||
      filters.date_to !== undefined ||
      filters.is_read !== undefined ||
      filters.has_attachments !== undefined ||
      filters.importance !== undefined ||
      (filters.folder !== undefined && filters.folder !== 'Inbox')
    );
  }, [filters]);

  // Convert filters to API query parameters
  const getFilterParams = useCallback(() => {
    const params: Record<string, any> = {
      folder: filters.folder || 'Inbox',
      limit: 50,
      offset: 0,
    };

    // Add optional filter parameters if they exist
    if (filters.sender) params.sender = filters.sender;
    if (filters.subject) params.subject = filters.subject;
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;
    if (filters.is_read !== undefined) params.is_read = filters.is_read;
    if (filters.has_attachments !== undefined) params.has_attachments = filters.has_attachments;
    if (filters.importance) params.importance = filters.importance;

    return params;
  }, [filters]);

  // Clear all filters to defaults
  const clearFilters = useCallback(() => {
    setFilters(defaultFilters);
  }, []);

  return {
    filters,
    setFilters,
    hasActiveFilters,
    getFilterParams,
    clearFilters,
  };
}
