// Custom hook for email filter state management
import { useState, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { EmailFilter } from '@/types/email';

interface UseEmailFiltersResult {
  filters: EmailFilter;
  setFilters: (filters: Partial<EmailFilter>) => void;
  clearFilters: () => void;
  hasActiveFilters: boolean;
  getFilterParams: () => EmailFilter & { page: number; per_page: number };
  page: number;
  setPage: (page: number) => void;
}

export const useEmailFilters = (defaultPerPage: number = 20): UseEmailFiltersResult => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Initialize filters from URL params
  const initialFilters = useMemo((): EmailFilter => {
    const params: EmailFilter = {};
    
    if (searchParams.get('sender')) params.sender = searchParams.get('sender') || undefined;
    if (searchParams.get('subject')) params.subject = searchParams.get('subject') || undefined;
    if (searchParams.get('folder')) params.folder = searchParams.get('folder') || undefined;
    if (searchParams.get('date_from')) params.date_from = searchParams.get('date_from') || undefined;
    if (searchParams.get('date_to')) params.date_to = searchParams.get('date_to') || undefined;
    if (searchParams.get('importance')) params.importance = searchParams.get('importance') as 'Low' | 'Normal' | 'High' || undefined;
    
    const isReadParam = searchParams.get('is_read');
    if (isReadParam === 'true') params.is_read = true;
    else if (isReadParam === 'false') params.is_read = false;
    
    const hasAttachmentsParam = searchParams.get('has_attachments');
    if (hasAttachmentsParam === 'true') params.has_attachments = true;
    else if (hasAttachmentsParam === 'false') params.has_attachments = false;
    
    return params;
  }, [searchParams]);
  
  const [filters, setFiltersState] = useState<EmailFilter>(initialFilters);
  const [page, setPage] = useState(() => {
    const pageParam = searchParams.get('page');
    return pageParam ? parseInt(pageParam, 10) : 1;
  });
  
  // Update URL params when filters change
  const updateSearchParams = useCallback((newFilters: EmailFilter, newPage: number = 1) => {
    const params = new URLSearchParams();
    
    // Add filter params
    Object.entries(newFilters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.set(key, String(value));
      }
    });
    
    // Add page param if not the first page
    if (newPage > 1) {
      params.set('page', String(newPage));
    }
    
    setSearchParams(params, { replace: true });
  }, [setSearchParams]);
  
  // Set filters function
  const setFilters = useCallback((newFilters: Partial<EmailFilter>) => {
    const updatedFilters = { ...filters, ...newFilters };
    
    // Remove undefined values
    Object.keys(updatedFilters).forEach(key => {
      if (updatedFilters[key as keyof EmailFilter] === undefined) {
        delete updatedFilters[key as keyof EmailFilter];
      }
    });
    
    setFiltersState(updatedFilters);
    setPage(1); // Reset to first page when filters change
    updateSearchParams(updatedFilters, 1);
  }, [filters, updateSearchParams]);
  
  // Clear all filters
  const clearFilters = useCallback(() => {
    setFiltersState({});
    setPage(1);
    updateSearchParams({}, 1);
  }, [updateSearchParams]);
  
  // Check if any filters are active
  const hasActiveFilters = useMemo(() => {
    return Object.values(filters).some(value => value !== undefined && value !== null && value !== '');
  }, [filters]);
  
  // Get filter params for API calls
  const getFilterParams = useCallback(() => {
    return {
      ...filters,
      page,
      per_page: defaultPerPage,
    };
  }, [filters, page, defaultPerPage]);
  
  // Handle page changes
  const setPageNumber = useCallback((newPage: number) => {
    setPage(newPage);
    updateSearchParams(filters, newPage);
  }, [filters, updateSearchParams]);
  
  return {
    filters,
    setFilters,
    clearFilters,
    hasActiveFilters,
    getFilterParams,
    page,
    setPage: setPageNumber,
  };
};