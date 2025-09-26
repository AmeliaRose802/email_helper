// Main types export file
export * from './api';
export * from './auth';
export * from './email';
export * from './ai';
export * from './task';

// Route types
export interface RouteParams {
  id?: string;
  [key: string]: string | undefined;
}

// UI Component types
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export interface FormState<T> {
  data: T;
  errors: Record<string, string>;
  isSubmitting: boolean;
  isDirty: boolean;
}

// Theme and styling
export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    background: string;
    surface: string;
    text: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
}
